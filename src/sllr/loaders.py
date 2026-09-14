"""
Load reference CSVs and the live lessons store.
"""
import csv
from pathlib import Path
from typing import Any

from .config import REFERENCE_FILES, REF_CODE_COLUMN
from .store import load_lessons, replace_lessons


def load_reference(path: Path) -> list[str]:
    """Load a reference CSV and return list of valid codes (first column after header)."""
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return []
    # Use 'code' column if present, else first column
    first_header = list(rows[0].keys())[0]
    col = REF_CODE_COLUMN if REF_CODE_COLUMN in rows[0] else first_header
    return [str(r.get(col, "")).strip() for r in rows if r.get(col)]


def load_all_references() -> dict[str, list[str]]:
    """Load all reference files into a dict: ref_name -> list of valid values."""
    out = {}
    for name, path in REFERENCE_FILES.items():
        out[name] = load_reference(path)
    return out


def load_lessons_master() -> list[dict[str, Any]]:
    """Load live lessons from SQLite (same path as the API)."""
    return load_lessons()


def save_lessons_master(rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    """Write lessons to the live SQLite store. fieldnames kept for call-site compat."""
    del fieldnames
    replace_lessons(rows)
