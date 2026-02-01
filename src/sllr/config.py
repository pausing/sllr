"""
SLLR configuration: paths and controlled vocabulary file names.
"""
from pathlib import Path

# Project root (parent of src)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Reference CSV files (controlled vocabularies)
REFERENCE_FILES = {
    "disciplines": DATA_DIR / "disciplines.csv",
    "phases": DATA_DIR / "phases.csv",
    "failure_types": DATA_DIR / "failure_types.csv",
    "categories": DATA_DIR / "categories.csv",
    "statuses": DATA_DIR / "statuses.csv",
}

LESSONS_MASTER = DATA_DIR / "lessons_master.csv"

# Column used for controlled value lookup in reference files
REF_CODE_COLUMN = "code"

# Mandatory lesson columns and their reference (if any)
LESSON_SCHEMA = {
    "Lesson ID": {"required": True, "reference": None},
    "Title": {"required": True, "reference": None},
    "Category": {"required": True, "reference": "categories"},
    "Sub-category": {"required": True, "reference": None},
    "Discipline": {"required": True, "reference": "disciplines"},
    "Project Phase": {"required": True, "reference": "phases"},
    "Failure Type": {"required": True, "reference": "failure_types"},
    "Root Cause": {"required": True, "reference": None},
    "What Happened": {"required": True, "reference": None},
    "Impact": {"required": True, "reference": None},
    "Lesson Learned": {"required": True, "reference": None},
    "Recommendation": {"required": True, "reference": None},
    "Applicability": {"required": False, "reference": None},
    "Keywords": {"required": False, "reference": None},
    "Status": {"required": True, "reference": "statuses"},
    "Owner": {"required": True, "reference": None},
    "Created Date": {"required": False, "reference": None},
    "Modified Date": {"required": False, "reference": None},
    "Reuse Count": {"required": False, "reference": None},
}
