"""Admin activity log: writes produce rows; GET is admin-only."""
import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SLLR_BASE_PATH", "/sllr")

ADMIN = {
    "X-Powerlearn-User-Id": "u-admin",
    "X-Powerlearn-Email": "pablo@powerlearn.us",
    "X-Powerlearn-Admin": "true",
}
USER = {
    "X-Powerlearn-User-Id": "u-user",
    "X-Powerlearn-Email": "user@powerlearn.us",
    "X-Powerlearn-Admin": "false",
}


def _lesson_body(lesson_id: str, owner: str = "user@powerlearn.us") -> dict:
    return {
        "Lesson ID": lesson_id,
        "Title": f"Lesson {lesson_id}",
        "Category": "Engineering",
        "Technical Block": "PV",
        "Sub-category": "Modules",
        "Project Phase": "Construction",
        "Root Cause": "Test root cause",
        "What Happened": "Test what happened",
        "Impact": "Test impact",
        "Lesson Learned": "Test lesson learned",
        "Recommendation": "Test recommendation",
        "Owner": owner,
    }


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


def test_create_and_update_produce_log_rows(client):
    created = client.post(
        "/sllr/api/lessons",
        json=_lesson_body("LL-900"),
        headers=USER,
    )
    assert created.status_code == 201, created.text

    updated = client.put(
        "/sllr/api/lessons/LL-900",
        json={"Title": "Renamed title", "Owner": "user@powerlearn.us"},
        headers=USER,
    )
    assert updated.status_code == 200, updated.text

    listed = client.get("/sllr/api/activity", headers=ADMIN)
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] >= 2
    actions = [row["action"] for row in body["items"]]
    assert "create_lesson" in actions
    assert "update_lesson" in actions

    create_row = next(row for row in body["items"] if row["action"] == "create_lesson")
    assert create_row["email"] == "user@powerlearn.us"
    assert create_row["user_id"] == "u-user"
    assert create_row["entity_id"] == "LL-900"
    assert create_row["created_at"]
    assert create_row["values"]["after"]["Lesson ID"] == "LL-900"
    assert create_row["values"]["after"]["Title"] == "Lesson LL-900"

    update_row = next(row for row in body["items"] if row["action"] == "update_lesson")
    assert update_row["values"]["changed"]["Title"]["before"] == "Lesson LL-900"
    assert update_row["values"]["changed"]["Title"]["after"] == "Renamed title"


def test_non_admin_activity_get_is_403(client):
    assert client.get("/sllr/api/activity").status_code == 403
    assert client.get("/sllr/api/activity", headers=USER).status_code == 403
    assert client.get("/api/activity", headers=USER).status_code == 403


def test_admin_activity_get_returns_action_time_values(client):
    client.post("/sllr/api/lessons", json=_lesson_body("LL-901"), headers=ADMIN)
    for path in ("/sllr/api/activity", "/api/activity"):
        resp = client.get(path, headers=ADMIN, params={"action": "create_lesson", "entity_id": "LL-901"})
        assert resp.status_code == 200, path
        data = resp.json()
        assert data["total"] == 1
        row = data["items"][0]
        assert row["action"] == "create_lesson"
        assert row["created_at"]
        assert row["email"] == "pablo@powerlearn.us"
        assert "values" in row
        assert row["values"]["after"]["Lesson ID"] == "LL-901"


def test_reads_are_not_logged(client):
    client.get("/sllr/api/lessons")
    client.get("/sllr/api/kpis")
    listed = client.get("/sllr/api/activity", headers=ADMIN)
    assert listed.status_code == 200
    assert listed.json()["total"] == 0
    assert listed.json()["items"] == []
