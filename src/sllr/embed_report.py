"""
Independent module to produce the HTML report for embedding inside Streamlit.
Use get_report_html(lessons) and render with st.components.v1.html(html, height=...).
"""
import tempfile
from pathlib import Path
from typing import Any

from .export_html import build_html

try:
    from .export_html import build_html_string
except ImportError:
    build_html_string = None  # type: ignore[misc, assignment]


DEFAULT_TITLE = "Lessons Learned Registry"
DEFAULT_HEIGHT = 720


def get_report_html(
    lessons: list[dict[str, Any]],
    title: str = DEFAULT_TITLE,
) -> str:
    """
    Return the full HTML string for the lessons-learned report (cards + filters).
    Use in Streamlit with:
        html = get_report_html(lessons)
        st.components.v1.html(html, height=720, scrolling=True)
    """
    if build_html_string is not None:
        return build_html_string(lessons, title=title)
    # Fallback: write to temp file and read back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        p = Path(f.name)
    try:
        build_html(lessons, output_path=p, title=title)
        return p.read_text(encoding="utf-8")
    finally:
        p.unlink(missing_ok=True)
