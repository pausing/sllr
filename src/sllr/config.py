"""
SLLR configuration: paths and controlled vocabulary file names.
"""
import os
from pathlib import Path

# Project root (parent of src)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# Reference CSVs always live in the repo/image data/ directory.
DATA_DIR = PROJECT_ROOT / "data"


def get_live_data_dir() -> Path:
    """Directory for the live SQLite file (and optional CSV import/export).

    If ``SLLR_DATA_DIR`` is set, use that directory (Dokploy volume, e.g. ``/data``).
    Otherwise use ``PROJECT_ROOT / data`` (``data/`` in the image). The bare
    relative value ``data`` always maps to ``PROJECT_ROOT / data``, not cwd.
    An empty directory is fine — schema is created on boot.
    """
    raw = (os.getenv("SLLR_DATA_DIR") or "data").strip() or "data"
    data_dir = Path(raw)
    if data_dir == Path("data"):
        return DATA_DIR
    return data_dir


def get_lessons_db_path() -> Path:
    """Live lessons SQLite file (``lessons.db``)."""
    return get_live_data_dir() / "lessons.db"


def get_lessons_csv_path() -> Path:
    """CSV used only for one-time migrate, import, and export."""
    return get_live_data_dir() / "lessons_master.csv"


def get_lessons_master_path() -> Path:
    """CSV path (import/export / one-time migrate). Not the live store."""
    return get_lessons_csv_path()


# Special approver mapping used when a Technical Block has no assignees.
GENERAL_TECHNICAL_BLOCK = "General"

# Reference CSV files (controlled vocabularies)
REFERENCE_FILES = {
    "technical_blocks": DATA_DIR / "technical_blocks.csv",
    "phases": DATA_DIR / "phases.csv",
    "statuses": DATA_DIR / "statuses.csv",
    "implementation_statuses": DATA_DIR / "implementation_statuses.csv",
}

LESSONS_MASTER = DATA_DIR / "lessons_master.csv"

# Column used for controlled value lookup in reference files
REF_CODE_COLUMN = "code"

# Lesson columns and their reference (if any).
# When creating a new lesson, only Status "Draft" is allowed.
LESSON_SCHEMA = {
    "Lesson ID": {"required": True, "reference": None},
    "Title": {"required": True, "reference": None},
    "Technical Block": {"required": True, "reference": "technical_blocks"},
    "Project Phase": {"required": True, "reference": "phases"},
    "Event Description": {"required": True, "reference": None},
    "Root Cause": {"required": True, "reference": None},
    "Impact": {"required": True, "reference": None},
    "Lesson Learned": {"required": True, "reference": None},
    "Recommendation": {"required": True, "reference": None},
    "Implementation Owner": {"required": False, "reference": None},
    "Implementation Due Date": {"required": False, "reference": None},
    "Keywords": {"required": False, "reference": None},
    "Status": {"required": True, "reference": "statuses"},
    "Implementation Status": {"required": True, "reference": "implementation_statuses"},
    "Owner": {"required": True, "reference": None},
    "Created Date": {"required": False, "reference": None},
    "Modified Date": {"required": False, "reference": None},
}

# Legacy CSV / SQLite names mapped into LESSON_SCHEMA on read. Ignored if the
# current field is already populated. Category / Sub-category are dropped.
LEGACY_LESSON_ALIASES = {
    "What Happened": "Event Description",
    "Recommendation Due Date": "Implementation Due Date",
}

LESSON_COLUMNS = list(LESSON_SCHEMA.keys())
