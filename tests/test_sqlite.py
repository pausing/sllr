"""SQLite live store: empty DB, create roundtrip, KPIs, CSV import/export."""
import os

import pytest
from fastapi.testclient import TestClient

from tests.lesson_fixtures import lesson_body

os.environ.setdefault("SLLR_BASE_PATH", "/sllr")

SAMPLE = lesson_body("LL-001", Title="SQLite roundtrip lesson")


@pytest.fixture
def sqlite_client(tmp_path, monkeypatch):
    data_dir = tmp_path / "sllr_data"
    data_dir.mkdir()
    monkeypatch.setenv("SLLR_DATA_DIR", str(data_dir))
    monkeypatch.setenv("SLLR_BASE_PATH", "/sllr")
    from src.sllr.store import reset_init_cache

    reset_init_cache()
    from backend.app.main import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client, data_dir


def test_empty_db_list_and_kpis(sqlite_client):
    client, data_dir = sqlite_client
    assert (data_dir / "lessons.db").is_file()
    lessons = client.get("/sllr/api/lessons")
    kpis = client.get("/sllr/api/kpis")
    assert lessons.status_code == 200
    assert lessons.json() == []
    assert kpis.status_code == 200
    assert kpis.json()["total_lessons"] == 0

    from src.sllr.kpi import compute_kpis
    from src.sllr.loaders import load_lessons_master
    from backend.app.storage import load_lessons_with_lock

    assert load_lessons_master() == []
    assert load_lessons_with_lock() == []
    assert compute_kpis()["total_lessons"] == 0


def test_create_roundtrip_and_kpi_total(sqlite_client):
    client, _ = sqlite_client
    created = client.post("/sllr/api/lessons", json=SAMPLE)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["Lesson ID"] == "LL-001"
    assert body["Status"] == "Draft"
    assert body["Implementation Status"] == "Not Implemented"

    listed = client.get("/sllr/api/lessons")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["Title"] == SAMPLE["Title"]

    fetched = client.get("/sllr/api/lessons/LL-001")
    assert fetched.status_code == 200
    assert fetched.json()["Owner"] == "Test Owner"

    kpis = client.get("/sllr/api/kpis")
    assert kpis.status_code == 200
    assert kpis.json()["total_lessons"] == 1

    from src.sllr.kpi import compute_kpis

    assert compute_kpis()["total_lessons"] == 1


def test_csv_export_import_roundtrip(sqlite_client):
    client, _ = sqlite_client
    assert client.post("/sllr/api/lessons", json=SAMPLE).status_code == 201

    exported = client.get("/sllr/api/export/csv")
    assert exported.status_code == 200
    assert "text/csv" in exported.headers["content-type"]
    csv_text = exported.text
    assert "LL-001" in csv_text
    assert "SQLite roundtrip lesson" in csv_text

    empty = client.post(
        "/sllr/api/import/csv",
        files={"file": ("lessons_master.csv", "Lesson ID,Title\n", "text/csv")},
    )
    assert empty.status_code == 200
    assert empty.json()["imported"] == 0
    assert client.get("/sllr/api/lessons").json() == []
    assert client.get("/sllr/api/kpis").json()["total_lessons"] == 0

    restored = client.post(
        "/sllr/api/import/csv",
        files={"file": ("lessons_master.csv", csv_text, "text/csv")},
    )
    assert restored.status_code == 200
    assert restored.json()["imported"] == 1
    lessons = client.get("/sllr/api/lessons").json()
    assert len(lessons) == 1
    assert lessons[0]["Lesson ID"] == "LL-001"
    assert lessons[0]["Title"] == SAMPLE["Title"]
    assert client.get("/sllr/api/kpis").json()["total_lessons"] == 1


def test_migrates_leftover_csv_once(tmp_path, monkeypatch):
    from src.sllr.config import LESSON_COLUMNS
    from src.sllr.store import init_store, load_lessons, replace_lessons, reset_init_cache

    data_dir = tmp_path / "migrate"
    data_dir.mkdir()
    row = {col: "" for col in LESSON_COLUMNS}
    row.update(
        {
            "Lesson ID": "LL-009",
            "Title": "Legacy CSV row",
            "Technical Block": "PV",
            "Project Phase": "Construction",
            "Root Cause": "x",
            "Event Description": "y",
            "Impact": "z",
            "Lesson Learned": "l",
            "Recommendation": "r",
            "Status": "Draft",
            "Implementation Status": "Not Implemented",
            "Owner": "csv",
        }
    )
    import csv

    csv_path = data_dir / "lessons_master.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LESSON_COLUMNS)
        writer.writeheader()
        writer.writerow(row)

    monkeypatch.setenv("SLLR_DATA_DIR", str(data_dir))
    reset_init_cache()
    init_store()
    loaded = load_lessons()
    assert len(loaded) == 1
    assert loaded[0]["Lesson ID"] == "LL-009"

    replace_lessons([])
    assert load_lessons() == []
    reset_init_cache()
    init_store()
    assert load_lessons() == []
