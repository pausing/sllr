"""
Live lesson store: SQLite (same file for list/create/update/patch and KPIs).

CSV is import/export only. File-lock CSV I/O is gone from the live path.
"""
from pathlib import Path
from typing import Any, Optional

from src.sllr.config import get_lessons_db_path, get_live_data_dir
from src.sllr.store import (
    export_lessons_csv,
    find_lesson_by_id,
    import_lessons_csv,
    import_lessons_csv_path,
    init_store,
    insert_lesson,
    lesson_id_exists,
    lessons_to_csv_text,
    load_lessons,
    replace_lessons,
    suggest_next_id,
    update_lesson_row,
)


def get_data_dir() -> Path:
    return get_live_data_dir()


def get_lessons_path() -> Path:
    """Live SQLite path (shared with KPI / load_lessons_master)."""
    return get_lessons_db_path()


def load_lessons_with_lock() -> list[dict[str, Any]]:
    return load_lessons()


def save_lessons_with_lock(
    rows: list[dict[str, Any]],
    fieldnames: Optional[list[str]] = None,
) -> None:
    del fieldnames
    replace_lessons(rows)


__all__ = [
    "export_lessons_csv",
    "find_lesson_by_id",
    "get_data_dir",
    "get_lessons_path",
    "import_lessons_csv",
    "import_lessons_csv_path",
    "init_store",
    "insert_lesson",
    "lesson_id_exists",
    "lessons_to_csv_text",
    "load_lessons",
    "load_lessons_with_lock",
    "replace_lessons",
    "save_lessons_with_lock",
    "suggest_next_id",
    "update_lesson_row",
]
