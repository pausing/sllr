"""Lesson attachment upload, download, and delete."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from backend.app.activity import log_activity
from backend.app.identity import portal_identity, require_lesson_editor
from backend.app.storage import (
    delete_attachment_row,
    find_attachment,
    find_lesson_by_id,
    insert_attachment,
    list_attachments,
)
from src.sllr.attachments import (
    MAX_ATTACHMENT_BYTES,
    OVERSIZE_DETAIL,
    OversizeAttachment,
    attachment_file_path,
    content_disposition,
    display_filename,
    lesson_attachments_dir,
)

router = APIRouter()


def _public_attachment(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "filename": row["filename"],
        "size_bytes": row["size_bytes"],
        "content_type": row.get("content_type") or "application/octet-stream",
        "uploaded_at": row.get("uploaded_at") or "",
        "uploaded_by": row.get("uploaded_by") or "",
    }


def _require_lesson(lesson_id: str) -> dict[str, Any]:
    lesson = find_lesson_by_id(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")
    return lesson


async def _save_upload(lesson_id: str, upload: UploadFile) -> tuple[str, int]:
    stored = uuid.uuid4().hex
    folder = lesson_attachments_dir(lesson_id)
    folder.mkdir(parents=True, exist_ok=True)
    dest = attachment_file_path(lesson_id, stored)
    tmp = dest.with_suffix(".part")
    size = 0
    try:
        with tmp.open("wb") as out:
            while True:
                chunk = await upload.read(64 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_ATTACHMENT_BYTES:
                    raise OversizeAttachment()
                out.write(chunk)
        tmp.replace(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        dest.unlink(missing_ok=True)
        raise
    return stored, size


@router.get("/lessons/{lesson_id}/attachments")
async def get_attachments(lesson_id: str):
    _require_lesson(lesson_id)
    return {"attachments": [_public_attachment(row) for row in list_attachments(lesson_id)]}


@router.post("/lessons/{lesson_id}/attachments", status_code=201)
async def upload_attachment(
    lesson_id: str,
    request: Request,
    file: UploadFile = File(...),
):
    lesson = _require_lesson(lesson_id)
    ident = require_lesson_editor(request, lesson.get("Owner"))
    filename = display_filename(file.filename)
    declared = file.size
    if declared is not None and declared > MAX_ATTACHMENT_BYTES:
        raise HTTPException(status_code=413, detail=OVERSIZE_DETAIL)
    try:
        stored, size = await _save_upload(lesson_id, file)
    except OversizeAttachment:
        raise HTTPException(status_code=413, detail=OVERSIZE_DETAIL) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await file.close()

    row = insert_attachment(
        {
            "id": uuid.uuid4().hex,
            "lesson_id": lesson_id,
            "filename": filename,
            "stored_name": stored,
            "size_bytes": size,
            "content_type": file.content_type or "application/octet-stream",
            "uploaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "uploaded_by": ident.get("email") or portal_identity(request).get("email") or "",
        }
    )
    log_activity(
        request,
        "upload_attachment",
        entity_type="attachment",
        entity_id=row["id"],
        values={"lesson_id": lesson_id, "filename": filename, "size_bytes": size},
    )
    return _public_attachment(row)


@router.get("/lessons/{lesson_id}/attachments/{attachment_id}")
async def download_attachment(lesson_id: str, attachment_id: str):
    _require_lesson(lesson_id)
    row = find_attachment(attachment_id, lesson_id)
    if not row:
        raise HTTPException(status_code=404, detail="Attachment not found")
    try:
        path = attachment_file_path(lesson_id, row["stored_name"])
    except ValueError:
        raise HTTPException(status_code=404, detail="Attachment not found") from None
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Attachment file is missing")
    return FileResponse(
        path,
        media_type=row.get("content_type") or "application/octet-stream",
        headers={"Content-Disposition": content_disposition(row["filename"])},
    )


@router.delete("/lessons/{lesson_id}/attachments/{attachment_id}")
async def remove_attachment(lesson_id: str, attachment_id: str, request: Request):
    lesson = _require_lesson(lesson_id)
    require_lesson_editor(request, lesson.get("Owner"))
    row = delete_attachment_row(attachment_id, lesson_id)
    if not row:
        raise HTTPException(status_code=404, detail="Attachment not found")
    try:
        path = attachment_file_path(lesson_id, row["stored_name"])
        path.unlink(missing_ok=True)
    except ValueError:
        pass
    log_activity(
        request,
        "delete_attachment",
        entity_type="attachment",
        entity_id=attachment_id,
        values={"lesson_id": lesson_id, "filename": row.get("filename"), "size_bytes": row.get("size_bytes")},
    )
    return _public_attachment(row)
