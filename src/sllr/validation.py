"""
Validate lesson rows against schema and controlled vocabularies.
"""
from typing import Any

from .config import LESSON_SCHEMA
from .loaders import load_all_references


def validate_lesson(
    row: dict[str, Any],
    references: dict[str, list[str]] | None = None,
    strict: bool = True,
) -> list[str]:
    """
    Validate a single lesson row. Returns list of error messages (empty if valid).
    """
    errors = []
    refs = references or load_all_references()

    for col, spec in LESSON_SCHEMA.items():
        value = (row.get(col) or "").strip() if row.get(col) is not None else ""
        if spec["required"] and not value:
            errors.append(f"Missing required field: {col}")
            continue
        if not value:
            continue
        ref_name = spec.get("reference")
        if ref_name and ref_name in refs:
            allowed = refs[ref_name]
            if allowed and value not in allowed:
                errors.append(
                    f"Invalid value for '{col}': '{value}'. Allowed: {', '.join(allowed)}"
                )

    # Optional: basic length / format checks
    if strict and row.get("Title") and len(str(row["Title"])) > 200:
        errors.append("Title must be one line and under 200 characters.")
    if strict and row.get("Lesson Learned") and len(str(row["Lesson Learned"])) > 500:
        errors.append("Lesson Learned must be a single sentence (max 500 characters).")

    return errors


def validate_lessons_file(
    rows: list[dict[str, Any]],
    references: dict[str, list[str]] | None = None,
) -> list[tuple[int, list[str]]]:
    """
    Validate all lesson rows. Returns list of (row_index_1based, errors).
    """
    refs = references or load_all_references()
    result = []
    for i, row in enumerate(rows):
        errs = validate_lesson(row, refs)
        if errs:
            result.append((i + 1, errs))
    return result


def get_missing_columns(rows: list[dict[str, Any]]) -> list[str]:
    """Return required columns that are missing from the first row's keys."""
    if not rows:
        return []
    keys = set(rows[0].keys())
    return [c for c, s in LESSON_SCHEMA.items() if s["required"] and c not in keys]
