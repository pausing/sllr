"""
Export API router - PDF and HTML exports.
"""
from io import BytesIO

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse

from backend.app.storage import load_lessons_with_lock
from src.sllr.export_pdf import build_pdf, REPORTLAB_AVAILABLE
from src.sllr.export_html import build_html_string


router = APIRouter()


@router.post("/export/pdf")
async def export_pdf():
    """
    Generate PDF export (phase → category grouping, page breaks between categories).
    Returns application/pdf.
    """
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="PDF export requires reportlab. Install with: pip install reportlab"
        )
    
    lessons = load_lessons_with_lock()
    if not lessons:
        raise HTTPException(status_code=400, detail="No lessons to export")
    
    # Build PDF in memory
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
async def export_html():
    """
    Generate HTML export (standalone with filters and expandable cards).
    Returns text/html.
    """
    lessons = load_lessons_with_lock()
    if not lessons:
        raise HTTPException(status_code=400, detail="No lessons to export")
    
    html_content = build_html_string(lessons, title="Lessons Learned Registry")
    
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=lessons_learned.html"}
    )
