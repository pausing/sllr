"""
Live lesson store: SQLite (same file for list/create/update/patch and KPIs).

CSV is import/export only. File-lock CSV I/O is gone from the live path.
"""
from pathlib import Path
from typing import Any, Optional

from src.sllr.config import get_lessons_db_path, get_live_data_dir
from src.sllr.store import (
    add_approver_mapping,
    create_vocab,
    delete_approver_mapping,
    delete_lesson_row,
    delete_vocab,
    effective_approver_blocks,
    empty_technical_blocks,
    export_lessons_csv,
    find_lesson_by_id,
    get_approver_blocks,
    has_approver_mapping,
    import_lessons_csv,
    import_lessons_csv_path,
    init_store,
    insert_activity_log,
    insert_lesson,
    lesson_id_exists,
    lessons_to_csv_text,
    list_activity_log,
    list_all_vocab,
    list_approver_rows,
    list_approvers_by_block,
    list_approvers_grouped,
    list_vocab,
    load_lessons,
    reorder_vocab,
    replace_lessons,
    set_approver_blocks,
    set_approvers_for_block,
    suggest_next_id,
    update_lesson_row,
    update_vocab,
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
    "add_approver_mapping",
    "create_vocab",
    "delete_approver_mapping",
    "delete_lesson_row",
    "delete_vocab",
    "effective_approver_blocks",
    "empty_technical_blocks",
    "export_lessons_csv",
    "find_lesson_by_id",
    "get_approver_blocks",
    "get_data_dir",
    "get_lessons_path",
    "has_approver_mapping",
    "import_lessons_csv",
    "import_lessons_csv_path",
    "init_store",
    "insert_activity_log",
    "insert_lesson",
    "lesson_id_exists",
    "lessons_to_csv_text",
    "list_activity_log",
    "list_all_vocab",
    "list_approver_rows",
    "list_approvers_by_block",
    "list_approvers_grouped",
    "list_vocab",
    "load_lessons",
    "load_lessons_with_lock",
    "reorder_vocab",
    "replace_lessons",
    "save_lessons_with_lock",
    "set_approver_blocks",
    "set_approvers_for_block",
    "suggest_next_id",
    "update_lesson_row",
    "update_vocab",
]
