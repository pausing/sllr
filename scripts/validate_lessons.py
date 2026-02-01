#!/usr/bin/env python3
"""
Validate lessons_master.csv against schema and reference vocabularies.
Usage: python scripts/validate_lessons.py
"""
import sys
from pathlib import Path

# Add src to path when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sllr.loaders import load_lessons_master
from sllr.validation import validate_lessons_file, get_missing_columns


def main() -> int:
    rows = load_lessons_master()
    missing = get_missing_columns(rows)
    if missing:
        print("ERROR: Missing required columns:", ", ".join(missing))
        return 1
    issues = validate_lessons_file(rows)
    if not issues:
        print("OK: All", len(rows), "rows passed validation.")
        return 0
    for row_num, errs in issues:
        print(f"Row {row_num}:")
        for e in errs:
            print(f"  - {e}")
    print(f"\nTotal: {len(issues)} row(s) with errors.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
