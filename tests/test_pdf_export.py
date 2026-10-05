"""Single-lesson PDF report: fields, filename, no Category/SubCategory."""
import io
import os
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from tests.lesson_fixtures import lesson_body

os.environ.setdefault("SLLR_BASE_PATH", "/sllr")


def _pdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


@pytest.fixture
def client(tmp_path, monkeypatch):
    data_dir = tmp_path / "sllr_data"
    data_dir.mkdir()
    monkeypatch.setenv("SLLR_DATA_DIR", str(data_dir))
    monkeypatch.setenv("SLLR_BASE_PATH", "/sllr")
    from src.sllr.store import reset_init_cache

    reset_init_cache()
    from backend.app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_pdf_export_single_lesson_is_a_report(client):
    created = client.post(
        "/sllr/api/lessons",
        json=lesson_body(
            "LL-PDF-1",
            Title="Cable tray clearance at inverter skid",
            Project="Harbor Wind",
            **{
                "Event Description": "Tray fouled the inverter roof hatch.",
                "Root Cause": "GA drawing omitted the hatch swing.",
                "Impact": "Two-day delay during commissioning.",
                "Lesson Learned": "Check roof hatches on every skid GA.",
                "Recommendation": "Add a hatch-clearance check to the GA review.",
                "Keywords": "inverter, hatch",
            },
        ),
    )
    assert created.status_code == 201

    resp = client.post("/sllr/api/export/pdf", json={"ids": ["LL-PDF-1"]})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    disposition = resp.headers.get("content-disposition", "")
    assert "LL-PDF-1.pdf" in disposition

    text = _pdf_text(resp.content)
    for needle in (
        "Lessons Learned Report",
        "LL-PDF-1",
        "Cable tray clearance at inverter skid",
        "Harbor Wind",
        "Project",
        "Technical Block",
        "Project Phase",
        "Event Description",
        "Tray fouled the inverter roof hatch.",
        "Root Cause",
        "GA drawing omitted the hatch swing.",
        "Impact",
        "Lesson Learned",
        "Recommendation",
        "Owner",
        "Keywords",
        "Status",
        "Implementation Status",
        "Draft",
    ):
        assert needle in text, f"missing {needle!r} in PDF"

    assert "Category" not in text
    assert "SubCategory" not in text
    assert "Sub-category" not in text


def test_pdf_export_filtered_ids_excludes_other_lessons(client):
    client.post("/sllr/api/lessons", json=lesson_body("LL-KEEP", Title="Keep this lesson", Project="Alpha"))
    client.post("/sllr/api/lessons", json=lesson_body("LL-DROP", Title="Drop this lesson", Project="Beta"))
    resp = client.post("/sllr/api/export/pdf", json={"ids": ["LL-KEEP"]})
    assert resp.status_code == 200
    text = _pdf_text(resp.content)
    assert "Keep this lesson" in text
    assert "LL-KEEP" in text
    assert "Drop this lesson" not in text
    assert "LL-DROP" not in text


def test_suggest_pdf_filename_and_build_pdf(tmp_path):
    from src.sllr.export_pdf import REPORTLAB_AVAILABLE, build_pdf, suggest_pdf_filename

    assert REPORTLAB_AVAILABLE
    lesson = {
        "Lesson ID": "LL/weird",
        "Title": "Title",
        "Project": "Must Appear",
        "Technical Block": "PV",
        "Project Phase": "Construction",
        "Event Description": "What happened",
        "Root Cause": "Cause",
        "Impact": "Impact text",
        "Lesson Learned": "Learned",
        "Recommendation": "Do this",
        "Owner": "owner@example.com",
        "Keywords": "kw",
        "Status": "Draft",
        "Implementation Status": "Not Implemented",
        "Created Date": "2026-10-05",
        "Category": "should-not-print",
        "SubCategory": "also-no",
    }
    assert suggest_pdf_filename([lesson]) == "LL_weird.pdf"
    assert suggest_pdf_filename([lesson, lesson]) == "lessons_learned.pdf"

    out = tmp_path / "one.pdf"
    build_pdf([lesson], out)
    assert out.is_file() and out.stat().st_size > 1000
    text = _pdf_text(out.read_bytes())
    assert "Must Appear" in text
    assert "Created Date" in text or "2026-10-05" in text
    assert "should-not-print" not in text
    assert "also-no" not in text
