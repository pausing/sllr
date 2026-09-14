"""
SQLite live store for lessons.

CSV is import/export (and a one-time migrate from leftover ``lessons_master.csv``).
list/create/update/patch and ``compute_kpis`` all read this same file.
"""
from __future__ import annotations

import csv
import sqlite3
import threading
from io import StringIO
from pathlib import Path
from typing import Any, Optional

from .config import (
    LESSON_COLUMNS,
    get_lessons_csv_path,
    get_lessons_db_path,
    get_live_data_dir,
)

_lock = threading.Lock()
_initialized_paths: set[str] = set()

_CREATE_LESSONS = (
    "CREATE TABLE IF NOT EXISTS lessons (\n"
    + ",\n".join(f'  "{col}" TEXT' + (' PRIMARY KEY' if col == "Lesson ID" else "") for col in LESSON_COLUMNS)
    + "\n)"
)

_CREATE_META = """
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT
)
"""


def _quoted_columns() -> str:
    return ", ".join(f'"{c}"' for c in LESSON_COLUMNS)


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_lessons_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {col: (row[col] if row[col] is not None else "") for col in LESSON_COLUMNS}


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {col: "" if row.get(col) is None else str(row.get(col, "")) for col in LESSON_COLUMNS}


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [_normalize_row(r) for r in reader]
    return [r for r in rows if (r.get("Lesson ID") or "").strip()]


def _meta_get(conn: sqlite3.Connection, key: str) -> Optional[str]:
    cur = conn.execute("SELECT value FROM meta WHERE key = ?", (key,))
    found = cur.fetchone()
    return None if found is None else found["value"]


def _meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def _insert_rows(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    placeholders = ", ".join("?" for _ in LESSON_COLUMNS)
    sql = f"INSERT OR REPLACE INTO lessons ({_quoted_columns()}) VALUES ({placeholders})"
    conn.executemany(sql, [tuple(_normalize_row(r)[c] for c in LESSON_COLUMNS) for r in rows])


def init_store() -> Path:
    """Create schema if missing; migrate leftover CSV rows once into SQLite."""
    db_path = get_lessons_db_path()
    key = str(db_path.resolve()) if db_path.parent.exists() else str(db_path)
    with _lock:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        key = str(db_path.resolve())
        if key in _initialized_paths and db_path.exists():
            return db_path
        with _connect(db_path) as conn:
            conn.execute(_CREATE_LESSONS)
            conn.execute(_CREATE_META)
            if _meta_get(conn, "csv_migrated") != "1":
                csv_path = get_lessons_csv_path()
                existing = conn.execute("SELECT COUNT(*) AS n FROM lessons").fetchone()["n"]
                leftover = _read_csv_rows(csv_path)
                if leftover and existing == 0:
                    _insert_rows(conn, leftover)
                _meta_set(conn, "csv_migrated", "1")
            conn.commit()
        _initialized_paths.add(key)
    return db_path


def reset_init_cache() -> None:
    """Test helper: allow init_store to run again after SLLR_DATA_DIR changes."""
    _initialized_paths.clear()


def load_lessons() -> list[dict[str, Any]]:
    init_store()
    with _lock, _connect() as conn:
        cur = conn.execute(f'SELECT {_quoted_columns()} FROM lessons ORDER BY "Lesson ID"')
        return [_row_to_dict(r) for r in cur.fetchall()]


def find_lesson_by_id(lesson_id: str) -> Optional[dict[str, Any]]:
    init_store()
    with _lock, _connect() as conn:
        cur = conn.execute(
            f'SELECT {_quoted_columns()} FROM lessons WHERE "Lesson ID" = ?',
            (lesson_id,),
        )
        row = cur.fetchone()
        return _row_to_dict(row) if row else None


def lesson_id_exists(lesson_id: str) -> bool:
    return find_lesson_by_id(lesson_id) is not None


def insert_lesson(row: dict[str, Any]) -> None:
    init_store()
    values = tuple(_normalize_row(row)[c] for c in LESSON_COLUMNS)
    placeholders = ", ".join("?" for _ in LESSON_COLUMNS)
    with _lock, _connect() as conn:
        conn.execute(
            f"INSERT INTO lessons ({_quoted_columns()}) VALUES ({placeholders})",
            values,
        )
        conn.commit()


def update_lesson_row(lesson_id: str, row: dict[str, Any]) -> None:
    init_store()
    assignments = ", ".join(f'"{c}" = ?' for c in LESSON_COLUMNS if c != "Lesson ID")
    values = [ _normalize_row(row)[c] for c in LESSON_COLUMNS if c != "Lesson ID" ]
    values.append(lesson_id)
    with _lock, _connect() as conn:
        conn.execute(
            f'UPDATE lessons SET {assignments} WHERE "Lesson ID" = ?',
            values,
        )
        conn.commit()


def replace_lessons(rows: list[dict[str, Any]]) -> None:
    """Replace the live table (used by CSV import)."""
    init_store()
    with _lock, _connect() as conn:
        conn.execute("DELETE FROM lessons")
        _insert_rows(conn, rows)
        conn.commit()


def suggest_next_id() -> str:
    lessons = load_lessons()
    existing_ids = {r.get("Lesson ID", "") for r in lessons if r.get("Lesson ID")}
    for i in range(1, 10000):
        candidate = f"LL-{i:03d}"
        if candidate not in existing_ids:
            return candidate
    return "LL-001"


def lessons_to_csv_text(rows: list[dict[str, Any]] | None = None) -> str:
    rows = rows if rows is not None else load_lessons()
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=LESSON_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(_normalize_row(r) for r in rows)
    return buf.getvalue()


def export_lessons_csv(path: Path | None = None) -> Path:
    """Write current SQLite lessons to ``lessons_master.csv`` (export only)."""
    dest = path or get_lessons_csv_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(lessons_to_csv_text(), encoding="utf-8")
    return dest


def parse_lessons_csv(text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(StringIO(text))
    return [_normalize_row(r) for r in reader if (r.get("Lesson ID") or "").strip()]


def import_lessons_csv(text: str) -> int:
    """Replace live SQLite lessons from CSV text. Returns imported row count."""
    rows = parse_lessons_csv(text)
    replace_lessons(rows)
    return len(rows)


def import_lessons_csv_path(path: Path | None = None) -> int:
    src = path or get_lessons_csv_path()
    if not src.exists():
        return 0
    return import_lessons_csv(src.read_text(encoding="utf-8"))


def get_data_dir() -> Path:
    return get_live_data_dir()
