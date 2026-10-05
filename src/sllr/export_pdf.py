"""
Export lessons learned to a printable PDF report.

Single-lesson exports are a standalone report. Multi-lesson exports use the
same per-lesson layout, one lesson starting on a new page, ordered by
Project Phase then Technical Block.
"""
from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .config import DATA_DIR, PROJECT_ROOT, REFERENCE_FILES

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        CondPageBreak,
        KeepTogether,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


ACCENT = colors.HexColor("#3dcc8c")
INK = colors.HexColor("#0c0e12")
MUTED = colors.HexColor("#5c6578")
LINE = colors.HexColor("#d5dae3")
PANEL = colors.HexColor("#f3f6f4")
PAPER = colors.HexColor("#ffffff")
HEADER_INK = colors.HexColor("#0c0e12")

FONT_DIR = Path(__file__).resolve().parent / "fonts"
_FONTS_REGISTERED = False
FONT_SANS = "Helvetica"
FONT_SANS_BOLD = "Helvetica-Bold"
FONT_MONO = "Courier"

NARRATIVE_FIELDS = (
    ("Event Description", "Event Description"),
    ("Root Cause", "Root Cause"),
    ("Impact", "Impact"),
    ("Lesson Learned", "Lesson Learned"),
    ("Recommendation", "Recommendation"),
)

# Classification / identity — always shown (Project included even when empty).
META_ALWAYS = (
    ("Lesson ID", "Lesson ID"),
    ("Project", "Project"),
    ("Technical Block", "Technical Block"),
    ("Project Phase", "Project Phase"),
    ("Owner", "Owner"),
    ("Keywords", "Keywords"),
    ("Status", "Status"),
    ("Implementation Status", "Implementation Status"),
)

# Workflow / dates — shown when the lesson has a value.
META_IF_PRESENT = (
    ("Implementation Owner", "Implementation Owner"),
    ("Implementation Due Date", "Implementation Due Date"),
    ("Created Date", "Created Date"),
    ("Modified Date", "Modified Date"),
)

# Do not emit these even if leftover on a row.
SUPPRESSED_LABELS = frozenset({"Category", "SubCategory", "Sub-category", "Sub-Category"})


def _register_fonts() -> None:
    global _FONTS_REGISTERED, FONT_SANS, FONT_SANS_BOLD, FONT_MONO
    if _FONTS_REGISTERED or not REPORTLAB_AVAILABLE:
        return
    _FONTS_REGISTERED = True
    regular = FONT_DIR / "IBMPlexSans-Regular.ttf"
    semibold = FONT_DIR / "IBMPlexSans-SemiBold.ttf"
    mono = FONT_DIR / "IBMPlexMono-Regular.ttf"
    try:
        if regular.is_file() and semibold.is_file():
            pdfmetrics.registerFont(TTFont("IBMPlexSans", str(regular)))
            pdfmetrics.registerFont(TTFont("IBMPlexSans-SemiBold", str(semibold)))
            FONT_SANS = "IBMPlexSans"
            FONT_SANS_BOLD = "IBMPlexSans-SemiBold"
        if mono.is_file():
            pdfmetrics.registerFont(TTFont("IBMPlexMono", str(mono)))
            FONT_MONO = "IBMPlexMono"
    except Exception:
        FONT_SANS = "Helvetica"
        FONT_SANS_BOLD = "Helvetica-Bold"
        FONT_MONO = "Courier"


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


def _event_description(row: dict[str, Any]) -> str:
    return (row.get("Event Description") or row.get("What Happened") or "") or ""


def _impl_due(row: dict[str, Any]) -> str:
    return (row.get("Implementation Due Date") or row.get("Recommendation Due Date") or "") or ""


def _field(row: dict[str, Any], key: str) -> str:
    if key == "Event Description":
        return str(_event_description(row)).strip()
    if key == "Implementation Due Date":
        return str(_impl_due(row)).strip()
    value = row.get(key)
    if value is None:
        return ""
    return str(value).strip()


def _sort_lessons(lessons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    phase_order = _phase_order()

    def key(row: dict[str, Any]) -> tuple:
        phase = _field(row, "Project Phase") or "—"
        block = _field(row, "Technical Block") or "—"
        return (
            phase_order.get(phase, 999),
            phase,
            block,
            _field(row, "Lesson ID"),
        )

    return sorted(lessons, key=key)


def _escape(s: str) -> str:
    if not s:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _rich_text(s: str) -> str:
    text = _escape(s) if s else "—"
    if text == "—":
        return text
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br/>")


def suggest_pdf_filename(lessons: list[dict[str, Any]]) -> str:
    """Attachment name: one lesson uses its ID; otherwise the registry name."""
    if len(lessons) == 1:
        raw = _field(lessons[0], "Lesson ID") or "lesson"
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("._") or "lesson"
        return f"{safe}.pdf"
    return "lessons_learned.pdf"


def content_disposition(filename: str) -> str:
    ascii_name = filename.encode("ascii", "replace").decode("ascii")
    ascii_name = ascii_name.replace('"', "")
    return f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{quote(filename)}'


def _styles() -> dict[str, ParagraphStyle]:
    _register_fonts()
    return {
        "doc_kicker": ParagraphStyle(
            name="SLLRDocKicker",
            fontName=FONT_MONO,
            fontSize=9,
            leading=12,
            textColor=ACCENT,
            spaceAfter=2 * mm,
        ),
        "cover_title": ParagraphStyle(
            name="SLLRCoverTitle",
            fontName=FONT_SANS_BOLD,
            fontSize=22,
            leading=26,
            textColor=INK,
            spaceAfter=4 * mm,
        ),
        "lesson_title": ParagraphStyle(
            name="SLLRLessonTitle",
            fontName=FONT_SANS_BOLD,
            fontSize=16,
            leading=20,
            textColor=INK,
            spaceAfter=2 * mm,
        ),
        "lesson_id": ParagraphStyle(
            name="SLLRLessonId",
            fontName=FONT_MONO,
            fontSize=10,
            leading=13,
            textColor=ACCENT,
            spaceAfter=3 * mm,
        ),
        "meta_label": ParagraphStyle(
            name="SLLRMetaLabel",
            fontName=FONT_SANS_BOLD,
            fontSize=8,
            leading=9,
            textColor=MUTED,
            spaceAfter=0.5 * mm,
        ),
        "meta_value": ParagraphStyle(
            name="SLLRMetaValue",
            fontName=FONT_SANS,
            fontSize=9.5,
            leading=12,
            textColor=INK,
        ),
        "section_h": ParagraphStyle(
            name="SLLRSectionH",
            fontName=FONT_SANS_BOLD,
            fontSize=10,
            leading=13,
            textColor=INK,
            spaceAfter=1.5 * mm,
            keepWithNext=True,
        ),
        "section_body": ParagraphStyle(
            name="SLLRSectionBody",
            fontName=FONT_SANS,
            fontSize=9.5,
            leading=13,
            textColor=INK,
            alignment=TA_LEFT,
        ),
        "muted": ParagraphStyle(
            name="SLLRMuted",
            fontName=FONT_SANS,
            fontSize=9,
            leading=12,
            textColor=MUTED,
        ),
        "footer": ParagraphStyle(
            name="SLLRFooter",
            fontName=FONT_SANS,
            fontSize=8,
            leading=10,
            textColor=MUTED,
            alignment=TA_RIGHT,
        ),
    }


def _draw_page(canvas, doc) -> None:
    _register_fonts()
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, height - 7 * mm, width, 7 * mm, fill=1, stroke=0)
    canvas.setFillColor(HEADER_INK)
    canvas.setFont(FONT_SANS_BOLD, 8)
    canvas.drawString(18 * mm, height - 4.6 * mm, "SLLR  ·  Lessons Learned Report")
    canvas.setFont(FONT_SANS, 8)
    canvas.drawRightString(width - 18 * mm, height - 4.6 * mm, "portal.powerlearn.us/sllr")
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.4)
    canvas.line(18 * mm, 13 * mm, width - 18 * mm, 13 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT_SANS, 8)
    canvas.drawString(18 * mm, 8 * mm, "Confidential  ·  Internal use")
    canvas.drawRightString(width - 18 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _meta_pairs(row: dict[str, Any]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for label, key in META_ALWAYS:
        if label in SUPPRESSED_LABELS:
            continue
        value = _field(row, key)
        pairs.append((label, value or "—"))
    for label, key in META_IF_PRESENT:
        if label in SUPPRESSED_LABELS:
            continue
        value = _field(row, key)
        if value:
            pairs.append((label, value))
    return pairs


def _meta_table(row: dict[str, Any], styles: dict[str, ParagraphStyle], col_width: float) -> Table:
    pairs = _meta_pairs(row)
    half = (len(pairs) + 1) // 2
    left = pairs[:half]
    right = pairs[half:]
    while len(right) < len(left):
        right.append(("", ""))

    def cell(label: str, value: str) -> list:
        if not label:
            return [Paragraph("", styles["meta_label"]), Paragraph("", styles["meta_value"])]
        return [
            Paragraph(_escape(label), styles["meta_label"]),
            Paragraph(_rich_text(value), styles["meta_value"]),
        ]

    data = []
    inner_w = (col_width - 8 * mm) / 2
    for (ll, lv), (rl, rv) in zip(left, right):
        left_inner = Table([[cell(ll, lv)]], colWidths=[inner_w - 4 * mm])
        right_inner = Table([[cell(rl, rv)]], colWidths=[inner_w - 4 * mm])
        left_inner.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        right_inner.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        data.append([left_inner, right_inner])

    table = Table(data, colWidths=[col_width / 2, col_width / 2])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PANEL),
                ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                ("LINEBELOW", (0, 0), (-1, -2), 0.3, LINE),
                ("LINEAFTER", (0, 0), (0, -1), 0.3, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def _section_block(heading: str, text: str, styles: dict[str, ParagraphStyle], col_width: float) -> KeepTogether:
    heading_p = Paragraph(_escape(heading), styles["section_h"])
    body_p = Paragraph(_rich_text(text), styles["section_body"])
    inner = Table([[heading_p], [body_p]], colWidths=[col_width - 7 * mm])
    inner.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    framed = Table([[inner]], colWidths=[col_width])
    framed.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PAPER),
                ("LINEBEFORE", (0, 0), (0, -1), 2.2, ACCENT),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    # CondPageBreak sits outside KeepTogether so a long section can still flow,
    # but a heading will not start in the last ~28mm of a page.
    return [CondPageBreak(28 * mm), KeepTogether([framed, Spacer(1, 3.5 * mm)])]


def _lesson_flowables(row: dict[str, Any], styles: dict[str, ParagraphStyle], col_width: float) -> list:
    lid = _field(row, "Lesson ID") or "—"
    title = _field(row, "Title") or "Untitled lesson"
    header = KeepTogether(
        [
            Paragraph("LESSON REPORT", styles["doc_kicker"]),
            Paragraph(_escape(lid), styles["lesson_id"]),
            Paragraph(_escape(title), styles["lesson_title"]),
            Spacer(1, 2 * mm),
            _meta_table(row, styles, col_width),
            Spacer(1, 5 * mm),
        ]
    )
    blocks: list = [header]
    for label, key in NARRATIVE_FIELDS:
        blocks.extend(_section_block(label, _field(row, key), styles, col_width))
    return blocks


def _cover(lessons: list[dict[str, Any]], styles: dict[str, ParagraphStyle], col_width: float) -> list:
    today = date.today().isoformat()
    count = len(lessons)
    noun = "lesson" if count == 1 else "lessons"
    lines = [
        Paragraph("SLLR REGISTRY", styles["doc_kicker"]),
        Paragraph("Lessons Learned Report", styles["cover_title"]),
        Paragraph(f"{count} {noun}  ·  Generated {today}", styles["muted"]),
        Spacer(1, 8 * mm),
    ]
    rows = []
    for row in lessons:
        lid = _escape(_field(row, "Lesson ID") or "—")
        title = _escape(_field(row, "Title") or "Untitled")
        project = _escape(_field(row, "Project") or "—")
        rows.append(
            [
                Paragraph(lid, styles["lesson_id"]),
                Paragraph(title, styles["meta_value"]),
                Paragraph(project, styles["muted"]),
            ]
        )
    if rows:
        toc = Table(rows, colWidths=[32 * mm, col_width - 72 * mm, 40 * mm])
        toc.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 1.6 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6 * mm),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.3, LINE),
                ]
            )
        )
        lines.append(toc)
    return lines


def build_pdf(
    lessons: list[dict[str, Any]],
    output_path: Path | None = None,
    title: str = "Lessons Learned Registry",
) -> Path:
    """
    Build a light, printable PDF report. Each lesson is a full report section
    (title, classification, narrative, workflow). Multi-lesson files start
    each lesson on a new page so sections are not cut mid-block.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF export. Install with: pip install reportlab")

    path = output_path or (PROJECT_ROOT / "reports" / "lessons_learned.pdf")
    path.parent.mkdir(parents=True, exist_ok=True)

    _register_fonts()
    styles = _styles()
    page_w, _page_h = A4
    left = 18 * mm
    right = 18 * mm
    col_width = page_w - left - right

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=left,
        rightMargin=right,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title=title,
        author="SLLR",
    )

    ordered = _sort_lessons(list(lessons))
    story: list = []
    if len(ordered) > 1:
        story.extend(_cover(ordered, styles, col_width))
        story.append(PageBreak())

    for index, row in enumerate(ordered):
        if index > 0:
            story.append(PageBreak())
        story.extend(_lesson_flowables(row, styles, col_width))

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return path
