"""
Export API router - PDF, HTML, and CSV import/export.
CSV is not the live store; live lessons live in SQLite.
"""
import json
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.app.activity import log_activity
from backend.app.storage import import_lessons_csv, lessons_to_csv_text, load_lessons_with_lock
from src.sllr.export_pdf import build_pdf, REPORTLAB_AVAILABLE
from src.sllr.export_html import build_html_string


router = APIRouter()


class ExportSelection(BaseModel):
    """Optional filtered set. When ``ids`` is set, only those lessons are exported."""
    ids: Optional[list[str]] = Field(None)


async def _selection_from_request(request: Request) -> ExportSelection:
    raw = await request.body()
    if not raw or not raw.strip():
        return ExportSelection()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ExportSelection()
    if not isinstance(data, dict):
        return ExportSelection()
    return ExportSelection.model_validate(data)


def _lessons_for_export(selection: ExportSelection) -> list[dict]:
    lessons = load_lessons_with_lock()
    if not selection.ids:
        return lessons
    wanted = [i.strip() for i in selection.ids if (i or "").strip()]
    by_id = {row.get("Lesson ID"): row for row in lessons}
    return [by_id[i] for i in wanted if i in by_id]


@router.post("/export/pdf")
async def export_pdf(request: Request):
    """
    Generate PDF export (phase → technical block grouping).
    Body may include ``ids`` for the currently filtered View Report set.
    """
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="PDF export requires reportlab. Install with: pip install reportlab"
        )

    lessons = _lessons_for_export(await _selection_from_request(request))
    if not lessons:
        raise HTTPException(status_code=400, detail="No lessons to export")

    from pathlib import Path
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = Path(tmp.name)

    try:
        build_pdf(lessons, tmp_path)
        pdf_bytes = tmp_path.read_bytes()
        tmp_path.unlink()

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=lessons_learned.pdf"}
        )
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/html")
async def export_html(request: Request):
    """
    Generate HTML export (standalone with filters and expandable cards).
    Body may include ``ids`` for the currently filtered View Report set.
    """
    lessons = _lessons_for_export(await _selection_from_request(request))
    if not lessons:
        raise HTTPException(status_code=400, detail="No lessons to export")

    html_content = build_html_string(lessons, title="Lessons Learned Registry")

    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=lessons_learned.html"}
    )


@router.get("/export/csv")
async def export_csv():
    """Download live lessons as lessons_master.csv (export only)."""
    csv_content = lessons_to_csv_text()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=lessons_master.csv"},
    )


@router.post("/import/csv")
async def import_csv(request: Request, file: UploadFile = File(...)):
    """Replace the live SQLite store from an uploaded lessons_master.csv."""
    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8") from exc
    previous = load_lessons_with_lock()
    count = import_lessons_csv(text)
    imported_ids = [row.get("Lesson ID", "") for row in load_lessons_with_lock()]
    log_activity(
        request,
        "import_csv",
        entity_type="lessons",
        entity_id="",
        values={
            "imported": count,
            "before_count": len(previous),
            "after_ids": imported_ids,
            "filename": file.filename,
        },
    )
    return {"imported": count}
