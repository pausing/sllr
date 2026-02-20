"""
SLLR configuration: paths and controlled vocabulary file names.
"""
from pathlib import Path

# Project root (parent of src)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Reference CSV files (controlled vocabularies)
REFERENCE_FILES = {
    "categories": DATA_DIR / "categories.csv",
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
    "Category": {"required": True, "reference": "categories"},
    "Technical Block": {"required": True, "reference": "technical_blocks"},
    "Sub-category": {"required": True, "reference": None},
    "Project Phase": {"required": True, "reference": "phases"},
    "Root Cause": {"required": True, "reference": None},
    "What Happened": {"required": True, "reference": None},
    "Impact": {"required": True, "reference": None},
    "Lesson Learned": {"required": True, "reference": None},
    "Recommendation": {"required": True, "reference": None},
    "Recommendation Due Date": {"required": False, "reference": None},
    "Keywords": {"required": False, "reference": None},
    "Status": {"required": True, "reference": "statuses"},
    "Implementation Status": {"required": True, "reference": "implementation_statuses"},
    "Owner": {"required": True, "reference": None},
    "Created Date": {"required": False, "reference": None},
    "Modified Date": {"required": False, "reference": None},
}
