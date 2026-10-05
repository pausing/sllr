"""Lesson attachment files on the live data volume (same dir as SQLite)."""
from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path
from urllib.parse import quote

from .config import get_live_data_dir


MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_ATTACHMENT_LABEL = "10 MB"
OVERSIZE_DETAIL = "File is larger than the 10 MB limit."
STORED_NAME_RE = re.compile(r"^[0-9a-f]{32}$")


class OversizeAttachment(Exception):
    """Raised when an upload exceeds MAX_ATTACHMENT_BYTES."""


def get_attachments_root() -> Path:
    root = get_live_data_dir() / "attachments"
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def lesson_dir_name(lesson_id: str) -> str:
    return hashlib.sha256(lesson_id.encode("utf-8")).hexdigest()


def lesson_attachments_dir(lesson_id: str) -> Path:
    root = get_attachments_root()
    path = (root / lesson_dir_name(lesson_id)).resolve()
    path.relative_to(root)
    return path


def attachment_file_path(lesson_id: str, stored_name: str) -> Path:
    if not STORED_NAME_RE.fullmatch(stored_name or ""):
        raise ValueError("Invalid attachment storage name")
    folder = lesson_attachments_dir(lesson_id)
    path = (folder / stored_name).resolve()
    path.relative_to(folder)
    return path


def display_filename(name: str | None) -> str:
    raw = (name or "").replace("\\", "/").strip()
    base = Path(raw).name.strip() or "attachment"
    return base[:255]


def content_disposition(filename: str) -> str:
    name = display_filename(filename)
    ascii_name = name.encode("ascii", "ignore").decode("ascii").replace('"', "") or "attachment"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}"


def delete_lesson_attachment_files(lesson_id: str) -> None:
    folder = lesson_attachments_dir(lesson_id)
    if folder.is_dir():
        shutil.rmtree(folder, ignore_errors=True)


def configure_multipart_limits() -> None:
    """Cap multipart parts at the attachment limit so oversize uploads fail fast."""
    from starlette.formparsers import MultiPartParser

    if hasattr(MultiPartParser, "max_file_size"):
        MultiPartParser.max_file_size = MAX_ATTACHMENT_BYTES
    if hasattr(MultiPartParser, "max_part_size"):
        MultiPartParser.max_part_size = MAX_ATTACHMENT_BYTES
