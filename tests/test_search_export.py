"""Search, filtered export, legacy aliases, and new-lesson instructions file."""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.lesson_fixtures import lesson_body

os.environ.setdefault("SLLR_BASE_PATH", "/sllr")

INSTRUCTIONS = Path(__file__).resolve().parent.parent / "docs" / "recording-a-new-lesson-learned.md"
FRONTEND_INSTRUCTIONS = (
    Path(__file__).resolve().parent.parent / "frontend" / "src" / "content" / "new-lesson-instructions.md"
)

PABLO_TEXT = """Recording a new lesson learned
Describe the engineering situation clearly enough that a colleague on a different project could understand and reuse it without asking you. Explain what happened and why it matters technically — name the component, its ratings or specification, the applicable standard or design assumption, and the conditions under which the issue appeared — and note where in the project it was observed. Keep the entry blameless, focusing on the design, equipment, interface, or process rather than on individuals, and attach supporting evidence where you can (drawings, datasheets, test reports, photos, or calculations).
Then capture the root cause rather than the symptom, the impact on safety, cost, schedule, or performance, and a clear, actionable recommendation: what to do differently and which specification, checklist, RFQ template, or review step should be created or updated. Finally, classify the lesson so others can act on it: select the Technical Block — the engineering area responsible for the solution — and the Project Phase — the stage in the project life where the solution has to be implemented. Base both on where the fix belongs, which is often earlier than where the problem was found.
"""


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


def test_instructions_file_matches_pablo_text():
    assert INSTRUCTIONS.is_file()
    assert INSTRUCTIONS.read_text(encoding="utf-8").strip() == PABLO_TEXT.strip()
    assert FRONTEND_INSTRUCTIONS.is_file()
    assert FRONTEND_INSTRUCTIONS.read_text(encoding="utf-8").strip() == PABLO_TEXT.strip()


def test_search_matches_event_description_and_keywords(client):
    assert client.post(
        "/sllr/api/lessons",
        json=lesson_body("LL-S1", Title="Alpha", **{"Event Description": "inverter trip on site"}),
    ).status_code == 201
    assert client.post(
        "/sllr/api/lessons",
        json=lesson_body("LL-S2", Title="Beta", Keywords="cable-tray"),
    ).status_code == 201

    by_event = client.get("/sllr/api/lessons", params={"q": "inverter trip"})
    assert by_event.status_code == 200
    assert [row["Lesson ID"] for row in by_event.json()] == ["LL-S1"]

    by_kw = client.get("/sllr/api/lessons", params={"q": "cable-tray"})
    assert [row["Lesson ID"] for row in by_kw.json()] == ["LL-S2"]


def test_html_export_filtered_ids(client):
    client.post("/sllr/api/lessons", json=lesson_body("LL-E1", Title="Keep me"))
    client.post("/sllr/api/lessons", json=lesson_body("LL-E2", Title="Drop me"))
    resp = client.post("/sllr/api/export/html", json={"ids": ["LL-E1"]})
    assert resp.status_code == 200
    assert "Keep me" in resp.text
    assert "Drop me" not in resp.text
    assert "Event Description" in resp.text


def test_legacy_csv_what_happened_maps_to_event_description(client):
    csv_text = (
        "Lesson ID,Title,Technical Block,Project Phase,What Happened,Root Cause,"
        "Impact,Lesson Learned,Recommendation,Status,Implementation Status,Owner\n"
        "LL-LEG,Legacy title,PV,Construction,old what happened,cause,impact,"
        "learned,rec,Draft,Not Implemented,csv-owner\n"
    )
    imported = client.post(
        "/sllr/api/import/csv",
        files={"file": ("lessons_master.csv", csv_text, "text/csv")},
    )
    assert imported.status_code == 200
    assert imported.json()["imported"] == 1
    lesson = client.get("/sllr/api/lessons/LL-LEG").json()
    assert lesson["Event Description"] == "old what happened"
    assert "Category" not in lesson
    assert "What Happened" not in lesson
