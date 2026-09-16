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
    REF_CODE_COLUMN,
    REFERENCE_FILES,
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

_CREATE_APPROVERS = """
CREATE TABLE IF NOT EXISTS approvers (
  email TEXT NOT NULL,
  technical_block TEXT NOT NULL,
  PRIMARY KEY (email, technical_block)
)
"""

_CREATE_VOCAB = """
CREATE TABLE IF NOT EXISTS vocab (
  kind TEXT NOT NULL,
  code TEXT NOT NULL,
  label TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  active INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (kind, code)
)
"""

EDITABLE_VOCAB_KINDS = ("categories", "technical_blocks", "phases")

_LESSON_FIELD_BY_KIND = {
    "categories": "Category",
    "technical_blocks": "Technical Block",
    "phases": "Project Phase",
}


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
        already = key in _initialized_paths and db_path.exists()
        with _connect(db_path) as conn:
            conn.execute(_CREATE_LESSONS)
            conn.execute(_CREATE_META)
            conn.execute(_CREATE_APPROVERS)
            conn.execute(_CREATE_VOCAB)
            _seed_vocab_if_empty(conn)
            if not already and _meta_get(conn, "csv_migrated") != "1":
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


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def list_approver_rows() -> list[dict[str, str]]:
    """Return all approver mappings, sorted by email then technical block."""
    init_store()
    with _lock, _connect() as conn:
        cur = conn.execute(
            "SELECT email, technical_block FROM approvers ORDER BY email, technical_block"
        )
        return [
            {"email": row["email"], "technical_block": row["technical_block"]}
            for row in cur.fetchall()
        ]


def list_approvers_grouped() -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {}
    for row in list_approver_rows():
        grouped.setdefault(row["email"], []).append(row["technical_block"])
    return [{"email": email, "technical_blocks": blocks} for email, blocks in grouped.items()]


def get_approver_blocks(email: str) -> list[str]:
    normalized = _normalize_email(email)
    if not normalized:
        return []
    init_store()
    with _lock, _connect() as conn:
        cur = conn.execute(
            "SELECT technical_block FROM approvers WHERE email = ? ORDER BY technical_block",
            (normalized,),
        )
        return [row["technical_block"] for row in cur.fetchall()]


def has_approver_mapping(email: str, technical_block: str) -> bool:
    normalized = _normalize_email(email)
    block = (technical_block or "").strip()
    if not normalized or not block:
        return False
    init_store()
    with _lock, _connect() as conn:
        cur = conn.execute(
            "SELECT 1 FROM approvers WHERE email = ? AND technical_block = ? LIMIT 1",
            (normalized, block),
        )
        return cur.fetchone() is not None


def set_approver_blocks(email: str, technical_blocks: list[str]) -> list[str]:
    """Replace all technical blocks for an email. Returns the stored blocks."""
    normalized = _normalize_email(email)
    if not normalized:
        raise ValueError("email is required")
    unique_blocks: list[str] = []
    seen: set[str] = set()
    for raw in technical_blocks:
        block = (raw or "").strip()
        if not block or block in seen:
            continue
        seen.add(block)
        unique_blocks.append(block)
    init_store()
    with _lock, _connect() as conn:
        conn.execute("DELETE FROM approvers WHERE email = ?", (normalized,))
        conn.executemany(
            "INSERT INTO approvers (email, technical_block) VALUES (?, ?)",
            [(normalized, block) for block in unique_blocks],
        )
        conn.commit()
    return unique_blocks


def add_approver_mapping(email: str, technical_block: str) -> None:
    normalized = _normalize_email(email)
    block = (technical_block or "").strip()
    if not normalized:
        raise ValueError("email is required")
    if not block:
        raise ValueError("technical_block is required")
    init_store()
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO approvers (email, technical_block) VALUES (?, ?)",
            (normalized, block),
        )
        conn.commit()


def list_approvers_by_block() -> list[dict[str, Any]]:
    """Return approver emails grouped by technical block, including empty blocks."""
    grouped: dict[str, list[str]] = {}
    for row in list_approver_rows():
        grouped.setdefault(row["technical_block"], []).append(row["email"])
    blocks = load_live_reference_codes().get("technical_blocks") or []
    ordered: list[dict[str, Any]] = []
    seen: set[str] = set()
    for block in blocks:
        seen.add(block)
        ordered.append({"technical_block": block, "emails": grouped.get(block, [])})
    for block, emails in grouped.items():
        if block not in seen:
            ordered.append({"technical_block": block, "emails": emails})
    return ordered


def set_approvers_for_block(technical_block: str, emails: list[str]) -> list[str]:
    """Replace all emails mapped to a technical block. Returns stored emails."""
    block = (technical_block or "").strip()
    if not block:
        raise ValueError("technical_block is required")
    unique: list[str] = []
    seen: set[str] = set()
    for raw in emails:
        normalized = _normalize_email(raw)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    init_store()
    with _lock, _connect() as conn:
        conn.execute("DELETE FROM approvers WHERE technical_block = ?", (block,))
        conn.executemany(
            "INSERT INTO approvers (email, technical_block) VALUES (?, ?)",
            [(email, block) for email in unique],
        )
        conn.commit()
    return unique


def delete_approver_mapping(email: str, technical_block: Optional[str] = None) -> int:
    """Delete one mapping, or all mappings for an email. Returns rows deleted."""
    normalized = _normalize_email(email)
    if not normalized:
        return 0
    init_store()
    with _lock, _connect() as conn:
        if technical_block is None:
            cur = conn.execute("DELETE FROM approvers WHERE email = ?", (normalized,))
        else:
            cur = conn.execute(
                "DELETE FROM approvers WHERE email = ? AND technical_block = ?",
                (normalized, technical_block.strip()),
            )
        conn.commit()
        return int(cur.rowcount or 0)


def _seed_vocab_if_empty(conn: sqlite3.Connection) -> None:
    """Copy repo CSV vocab into SQLite the first time a kind has no rows."""
    for kind in EDITABLE_VOCAB_KINDS:
        existing = conn.execute(
            "SELECT COUNT(*) AS n FROM vocab WHERE kind = ?",
            (kind,),
        ).fetchone()["n"]
        if existing:
            continue
        path = REFERENCE_FILES.get(kind)
        if path is None or not path.exists():
            continue
        with open(path, newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        for index, row in enumerate(rows):
            first = list(row.keys())[0] if row else "code"
            col = REF_CODE_COLUMN if REF_CODE_COLUMN in row else first
            code = str(row.get(col) or "").strip()
            if not code:
                continue
            label = str(row.get("label") or code).strip() or code
            order_raw = row.get("order")
            try:
                sort_order = int(str(order_raw).strip()) if order_raw not in (None, "") else index + 1
            except ValueError:
                sort_order = index + 1
            conn.execute(
                "INSERT OR IGNORE INTO vocab (kind, code, label, sort_order, active) VALUES (?, ?, ?, ?, 1)",
                (kind, code, label, sort_order),
            )


def _assert_vocab_kind(kind: str) -> str:
    key = (kind or "").strip()
    if key not in EDITABLE_VOCAB_KINDS:
        raise ValueError(f"Unknown vocab kind: {kind}")
    return key


def load_live_reference_codes() -> dict[str, list[str]]:
    """Active codes for categories, technical blocks, and phases (form/validation)."""
    init_store()
    out: dict[str, list[str]] = {kind: [] for kind in EDITABLE_VOCAB_KINDS}
    with _lock, _connect() as conn:
        cur = conn.execute(
            "SELECT kind, code FROM vocab WHERE active = 1 ORDER BY kind, sort_order, code"
        )
        for row in cur.fetchall():
            out.setdefault(row["kind"], []).append(row["code"])
    return out


def list_vocab(kind: str, *, include_inactive: bool = True) -> list[dict[str, Any]]:
    key = _assert_vocab_kind(kind)
    init_store()
    sql = "SELECT kind, code, label, sort_order, active FROM vocab WHERE kind = ?"
    params: list[Any] = [key]
    if not include_inactive:
        sql += " AND active = 1"
    sql += " ORDER BY sort_order, code"
    with _lock, _connect() as conn:
        cur = conn.execute(sql, params)
        return [
            {
                "kind": row["kind"],
                "code": row["code"],
                "label": row["label"],
                "sort_order": int(row["sort_order"] or 0),
                "active": bool(row["active"]),
            }
            for row in cur.fetchall()
        ]


def list_all_vocab(*, include_inactive: bool = True) -> dict[str, list[dict[str, Any]]]:
    return {kind: list_vocab(kind, include_inactive=include_inactive) for kind in EDITABLE_VOCAB_KINDS}


def _next_sort_order(conn: sqlite3.Connection, kind: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(sort_order), 0) AS n FROM vocab WHERE kind = ?",
        (kind,),
    ).fetchone()
    return int(row["n"] or 0) + 1


def create_vocab(
    kind: str,
    code: str,
    label: str | None = None,
    sort_order: int | None = None,
) -> dict[str, Any]:
    key = _assert_vocab_kind(kind)
    value = (code or "").strip()
    if not value:
        raise ValueError("code is required")
    name = (label or value).strip() or value
    init_store()
    with _lock, _connect() as conn:
        existing = conn.execute(
            "SELECT 1 FROM vocab WHERE kind = ? AND code = ?",
            (key, value),
        ).fetchone()
        if existing:
            raise ValueError(f"Code {value!r} already exists")
        order = sort_order if sort_order is not None else _next_sort_order(conn, key)
        conn.execute(
            "INSERT INTO vocab (kind, code, label, sort_order, active) VALUES (?, ?, ?, ?, 1)",
            (key, value, name, int(order)),
        )
        conn.commit()
    created = [item for item in list_vocab(key) if item["code"] == value]
    return created[0]


def _rename_vocab_code(conn: sqlite3.Connection, kind: str, old_code: str, new_code: str) -> None:
    conn.execute(
        "UPDATE vocab SET code = ? WHERE kind = ? AND code = ?",
        (new_code, kind, old_code),
    )
    field = _LESSON_FIELD_BY_KIND.get(kind)
    if field:
        conn.execute(
            f'UPDATE lessons SET "{field}" = ? WHERE "{field}" = ?',
            (new_code, old_code),
        )
    if kind == "technical_blocks":
        conn.execute(
            "UPDATE approvers SET technical_block = ? WHERE technical_block = ?",
            (new_code, old_code),
        )


def update_vocab(
    kind: str,
    code: str,
    *,
    new_code: str | None = None,
    label: str | None = None,
    active: bool | None = None,
    sort_order: int | None = None,
) -> dict[str, Any]:
    key = _assert_vocab_kind(kind)
    current = (code or "").strip()
    if not current:
        raise ValueError("code is required")
    init_store()
    with _lock, _connect() as conn:
        row = conn.execute(
            "SELECT kind, code, label, sort_order, active FROM vocab WHERE kind = ? AND code = ?",
            (key, current),
        ).fetchone()
        if row is None:
            raise KeyError(f"Code {current!r} not found")
        next_code = (new_code or current).strip()
        if not next_code:
            raise ValueError("code is required")
        if next_code != current:
            clash = conn.execute(
                "SELECT 1 FROM vocab WHERE kind = ? AND code = ?",
                (key, next_code),
            ).fetchone()
            if clash:
                raise ValueError(f"Code {next_code!r} already exists")
            _rename_vocab_code(conn, key, current, next_code)
            current = next_code
        assignments: list[str] = []
        params: list[Any] = []
        if label is not None:
            assignments.append("label = ?")
            params.append(label.strip() or current)
        if active is not None:
            assignments.append("active = ?")
            params.append(1 if active else 0)
        if sort_order is not None:
            assignments.append("sort_order = ?")
            params.append(int(sort_order))
        if assignments:
            params.extend([key, current])
            conn.execute(
                f"UPDATE vocab SET {', '.join(assignments)} WHERE kind = ? AND code = ?",
                params,
            )
        conn.commit()
    items = list_vocab(key)
    return next(item for item in items if item["code"] == current)


def delete_vocab(kind: str, code: str) -> int:
    key = _assert_vocab_kind(kind)
    value = (code or "").strip()
    if not value:
        return 0
    init_store()
    with _lock, _connect() as conn:
        cur = conn.execute("DELETE FROM vocab WHERE kind = ? AND code = ?", (key, value))
        if key == "technical_blocks":
            conn.execute("DELETE FROM approvers WHERE technical_block = ?", (value,))
        conn.commit()
        return int(cur.rowcount or 0)


def reorder_vocab(kind: str, codes: list[str]) -> list[dict[str, Any]]:
    key = _assert_vocab_kind(kind)
    init_store()
    with _lock, _connect() as conn:
        existing = [
            row["code"]
            for row in conn.execute(
                "SELECT code FROM vocab WHERE kind = ? ORDER BY sort_order, code",
                (key,),
            ).fetchall()
        ]
        requested = [c.strip() for c in codes if (c or "").strip()]
        unknown = [c for c in requested if c not in existing]
        if unknown:
            raise ValueError(f"Unknown code(s): {', '.join(unknown)}")
        rest = [c for c in existing if c not in requested]
        ordered = requested + rest
        for index, value in enumerate(ordered, start=1):
            conn.execute(
                "UPDATE vocab SET sort_order = ? WHERE kind = ? AND code = ?",
                (index, key, value),
            )
        conn.commit()
    return list_vocab(key)
