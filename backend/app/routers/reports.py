"""
Reports API router - validation, duplicates, KPI text reports, dashboard CSV.
"""
from io import StringIO
import csv

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, StreamingResponse

from backend.app.storage import load_lessons_with_lock
from src.sllr.config import LESSON_SCHEMA
from src.sllr.loaders import load_all_references
from src.sllr.validation import validate_lessons_file
from src.sllr.duplicate_detection import find_duplicates, find_near_duplicates
from src.sllr.kpi import kpi_summary_text
from src.sllr.validation import validate_lesson


router = APIRouter()


@router.get("/reports/validation", response_class=PlainTextResponse)
async def validation_report():
    """
    Generate validation report as plain text.
    """
    lessons = load_lessons_with_lock()
    issues = validate_lessons_file(lessons)
    
    lines = [
        "SLLR Validation Report",
        "======================",
        f"Total rows: {len(lessons)}",
        f"Rows with errors: {len(issues)}",
        "",
    ]
    
    for row_num, errs in issues:
        lines.append(f"Row {row_num}:")
        for e in errs:
            lines.append(f"  - {e}")
        lines.append("")
    
    return "\n".join(lines)


@router.get("/reports/duplicates", response_class=PlainTextResponse)
async def duplicates_report():
    """
    Generate duplicates report as plain text.
    """
    lessons = load_lessons_with_lock()
    exact = find_duplicates(lessons)
    near = find_near_duplicates(lessons)
    
    lines = [
        "SLLR Duplicates Report",
        "======================",
        f"Exact duplicate groups: {len(exact)}",
        f"Near-duplicate pairs (by title similarity): {len(near)}",
        "",
    ]
    
    for i, group in enumerate(exact, 1):
        lines.append(f"Exact group {i} ({len(group)} lessons):")
        for r in group:
            lines.append(f"  - [{r.get('Lesson ID')}] {r.get('Title', '')[:60]}...")
        lines.append("")
    
    lines.append("--- Near duplicates (top 20 by similarity) ---")
    for r1, r2, sim in near[:20]:
        lines.append(f"  Sim={sim}: [{r1.get('Lesson ID')}] vs [{r2.get('Lesson ID')}]")
        lines.append(f"    A: {str(r1.get('Title', ''))[:70]}")
        lines.append(f"    B: {str(r2.get('Title', ''))[:70]}")
    
    return "\n".join(lines)


@router.get("/reports/kpi", response_class=PlainTextResponse)
async def kpi_report():
    """
    Generate KPI summary as plain text.
    """
    return kpi_summary_text()


@router.get("/reports/dashboard-export")
async def dashboard_export():
    """
    Export dashboard CSV with Validation_Errors column.
    """
    lessons = load_lessons_with_lock()
    refs = load_all_references()
    
    fieldnames = list(LESSON_SCHEMA.keys()) + ["Validation_Errors"]
    out_rows = []
    
    for r in lessons:
        row = {k: r.get(k, "") for k in LESSON_SCHEMA}
        errs = validate_lesson(row, refs)
        row["Validation_Errors"] = "; ".join(errs) if errs else ""
        out_rows.append(row)
    
    # Build CSV in memory
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(out_rows)
    
    csv_content = output.getvalue()
    output.close()
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dashboard_export.csv"}
    )
