"""
Export lessons learned to PDF: grouped by Phase, then Category (page break between
categories), ordered by Technical Block and Sub-category within each category.
"""
import csv
from pathlib import Path
from typing import Any

from sllr.config import DATA_DIR, PROJECT_ROOT, REFERENCE_FILES

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        PageBreak,
        Table,
        TableStyle,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def _phase_order() -> dict[str, int]:
    """Return phase code -> order (1-based) from phases.csv."""
    path = REFERENCE_FILES.get("phases") or (DATA_DIR / "phases.csv")
    if not path.exists():
        return {}
    order = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = (row.get("code") or row.get("label") or "").strip()
            try:
                order[code] = int(row.get("order", 999))
            except (ValueError, TypeError):
                order[code] = 999
    return order


def _group_lessons_for_pdf(lessons: list[dict[str, Any]]) -> list[tuple[str, str, list[dict[str, Any]]]]:
    """
    Group lessons by Phase, then Category. Within each category, sort by Technical Block, Sub-category.
    Returns list of (phase, category, sorted_lessons).
    """
    phase_order = _phase_order()
    # Group: (phase, category) -> list of lessons
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in lessons:
        phase = (r.get("Project Phase") or "").strip() or "—"
        cat = (r.get("Category") or "").strip() or "—"
        key = (phase, cat)
        if key not in groups:
            groups[key] = []
        groups[key].append(r)

    # Sort within each group by Technical Block, Sub-category
    for key in groups:
        groups[key].sort(
            key=lambda x: (
                (x.get("Technical Block") or "").strip(),
                (x.get("Sub-category") or "").strip(),
            )
        )

    # Build ordered list: sort phases by phase_order, then categories
    result: list[tuple[str, str, list[dict[str, Any]]]] = []
    for (phase, cat), group in sorted(
        groups.items(),
        key=lambda x: (
            phase_order.get(x[0][0], 999),
            x[0][0],
            x[0][1],
        ),
    ):
        result.append((phase, cat, group))
    return result


def _escape(s: str) -> str:
    if not s:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_pdf(
    lessons: list[dict[str, Any]],
    output_path: Path | None = None,
    title: str = "Lessons Learned Registry",
) -> Path:
    """
    Build a PDF with one section per (phase, category); page break between categories.
    Ordered by phase (from phases.csv), then category, then technical block, sub-category.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF export. Install with: pip install reportlab")

    path = output_path or (PROJECT_ROOT / "reports" / "lessons_learned.pdf")
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()
    heading1 = ParagraphStyle(
        name="SLLRHeading1",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=6,
    )
    heading2 = ParagraphStyle(
        name="SLLRHeading2",
        parent=styles["Heading2"],
        fontSize=12,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        name="SLLRBody",
        parent=styles["Normal"],
        fontSize=9,
        spaceAfter=3,
    )
    small = ParagraphStyle(
        name="SLLRSmall",
        parent=styles["Normal"],
        fontSize=8,
        spaceAfter=2,
    )

    story = []
    story.append(Paragraph(_escape(title), heading1))
    story.append(Spacer(1, 6 * mm))

    grouped = _group_lessons_for_pdf(lessons)
    first_section = True
    for phase, category, group in grouped:
        if not first_section:
            story.append(PageBreak())
        first_section = False
        story.append(
            Paragraph(
                f"Phase: {_escape(phase)} — Category: {_escape(category)}",
                heading2,
            )
        )
        story.append(Spacer(1, 3 * mm))
        for r in group:
            lid = _escape(r.get("Lesson ID") or "")
            title_text = _escape(r.get("Title") or "")
            tech_block = _escape(r.get("Technical Block") or "")
            sub = _escape(r.get("Sub-category") or "")
            story.append(Paragraph(f"<b>{lid}</b> {title_text}", body))
            story.append(Paragraph(f"Technical Block: {tech_block} | Sub-category: {sub}", small))
            story.append(Paragraph(f"<b>What happened:</b> {_escape(r.get('What Happened') or '')}", small))
            story.append(Paragraph(f"<b>Lesson learned:</b> {_escape(r.get('Lesson Learned') or '')}", small))
            story.append(Paragraph(f"<b>Recommendation:</b> {_escape(r.get('Recommendation') or '')}", small))
            due = r.get("Recommendation Due Date") or ""
            impl = r.get("Implementation Status") or ""
            if due or impl:
                story.append(Paragraph(f"<b>Due date:</b> {_escape(due)} | <b>Implementation:</b> {_escape(impl)}", small))
            story.append(Spacer(1, 2 * mm))
        story.append(Spacer(1, 4 * mm))

    doc.build(story)
    return path
