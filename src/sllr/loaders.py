"""
Load reference CSVs and lessons master into memory.
"""
import csv
from pathlib import Path
from typing import Any

from sllr.config import REFERENCE_FILES, LESSONS_MASTER, REF_CODE_COLUMN


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
    """Load lessons_master.csv as list of dicts."""
    if not LESSONS_MASTER.exists():
        return []
    with open(LESSONS_MASTER, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_lessons_master(rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    """Write lessons back to lessons_master.csv."""
    if not rows and not fieldnames:
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    LESSONS_MASTER.parent.mkdir(parents=True, exist_ok=True)
    with open(LESSONS_MASTER, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
