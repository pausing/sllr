"""
CSV storage with file locking for lessons data.
Last-write-wins is the current behavior; lock prevents torn reads/writes.
"""
import csv
import fcntl
import os
from pathlib import Path
from typing import Any, Optional

from src.sllr.config import LESSONS_MASTER, LESSON_SCHEMA


def get_data_dir() -> Path:
    """Get the data directory from environment or default."""
    data_dir = os.getenv("SLLR_DATA_DIR", "data")
    return Path(data_dir)


def get_lessons_path() -> Path:
    """Get the lessons master CSV path."""
    data_dir = get_data_dir()
    if data_dir == Path("data"):
        return LESSONS_MASTER
    return data_dir / "lessons_master.csv"


def load_lessons_with_lock() -> list[dict[str, Any]]:
    """Load lessons_master.csv with a shared lock."""
    path = get_lessons_path()
    if not path.exists():
        return []
    
    with open(path, "r", newline="", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        try:
            reader = csv.DictReader(f)
            return list(reader)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def save_lessons_with_lock(
    rows: list[dict[str, Any]], 
    fieldnames: Optional[list[str]] = None
) -> None:
    """Write lessons back to lessons_master.csv with an exclusive lock."""
    path = get_lessons_path()
    if not rows and not fieldnames:
        return
    
    if fieldnames is None:
        fieldnames = list(LESSON_SCHEMA.keys())
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def find_lesson_by_id(lesson_id: str) -> Optional[dict[str, Any]]:
    """Find a lesson by ID."""
    lessons = load_lessons_with_lock()
    for lesson in lessons:
        if lesson.get("Lesson ID") == lesson_id:
            return lesson
    return None


def lesson_id_exists(lesson_id: str) -> bool:
    """Check if a lesson ID already exists."""
    return find_lesson_by_id(lesson_id) is not None


def suggest_next_id() -> str:
    """Suggest the next available lesson ID (LL-001, LL-002, ...)."""
    lessons = load_lessons_with_lock()
    existing_ids = {r.get("Lesson ID", "") for r in lessons if r.get("Lesson ID")}
    
    for i in range(1, 10000):
        candidate = f"LL-{i:03d}"
        if candidate not in existing_ids:
            return candidate
    
    return "LL-001"
