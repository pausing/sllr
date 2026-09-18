"""Hard-delete lessons: admin any, owner draft only, activity snapshot."""
import os

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

os.environ.setdefault("SLLR_BASE_PATH", "/sllr")

from backend.app.identity import can_delete_lesson, owner_may_delete_lesson
from tests.lesson_fixtures import APPROVE_ASSIGNMENT, lesson_body

OWNER = {
    "X-Powerlearn-User-Id": "u-owner",
    "X-Powerlearn-Email": "owner@powerlearn.us",
    "X-Powerlearn-Admin": "false",
}
OWNER_CASED = {
    "X-Powerlearn-User-Id": "u-owner",
    "X-Powerlearn-Email": "  Owner@Powerlearn.us  ",
    "X-Powerlearn-Admin": "false",
}
OTHER = {
    "X-Powerlearn-User-Id": "u-other",
    "X-Powerlearn-Email": "other@powerlearn.us",
    "X-Powerlearn-Admin": "false",
}
ADMIN = {
    "X-Powerlearn-User-Id": "u-admin",
    "X-Powerlearn-Email": "admin@powerlearn.us",
    "X-Powerlearn-Admin": "true",
}


def _request(headers: dict[str, str]) -> Request:
    scope = {
        "type": "http",
        "method": "DELETE",
        "path": "/",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
    }
    return Request(scope)


def _lesson_body(lesson_id: str, owner: str = "owner@powerlearn.us") -> dict:
    return lesson_body(lesson_id, owner=owner, Title=f"Lesson {lesson_id}")


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


def test_can_delete_rules():
    draft = {"Owner": "owner@powerlearn.us", "Status": "Draft", "Implementation Status": "Not Implemented"}
    approved = {**draft, "Status": "Approved"}
    implemented = {**draft, "Implementation Status": "Implemented"}
    assert owner_may_delete_lesson(draft)
    assert not owner_may_delete_lesson(approved)
    assert not owner_may_delete_lesson(implemented)
    assert can_delete_lesson(_request(ADMIN), approved)
    assert can_delete_lesson(_request(OWNER_CASED), draft)
    assert not can_delete_lesson(_request(OWNER), approved)
    assert not can_delete_lesson(_request(OTHER), draft)
    assert not can_delete_lesson(_request({}), draft)


def test_admin_can_delete_any(client):
    created = client.post("/sllr/api/lessons", json=_lesson_body("LL-DEL-1"), headers=OWNER)
    assert created.status_code == 201
    approved = client.patch(
        "/sllr/api/lessons/LL-DEL-1",
        json={"Status": "Approved", **APPROVE_ASSIGNMENT},
        headers=ADMIN,
    )
    assert approved.status_code == 200, approved.text
    deleted = client.delete("/api/lessons/LL-DEL-1", headers=ADMIN)
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["Lesson ID"] == "LL-DEL-1"
    assert client.get("/sllr/api/lessons/LL-DEL-1").status_code == 404
    listed = client.get("/sllr/api/lessons")
    assert all(row.get("Lesson ID") != "LL-DEL-1" for row in listed.json())


def test_owner_can_delete_draft(client):
    created = client.post("/sllr/api/lessons", json=_lesson_body("LL-DEL-2"), headers=OWNER)
    assert created.status_code == 201
    deleted = client.delete("/sllr/api/lessons/LL-DEL-2", headers=OWNER_CASED)
    assert deleted.status_code == 200, deleted.text
    assert client.get("/api/lessons/LL-DEL-2").status_code == 404


def test_owner_cannot_delete_approved(client):
    created = client.post("/sllr/api/lessons", json=_lesson_body("LL-DEL-3"), headers=OWNER)
    assert created.status_code == 201
    approved = client.patch(
        "/sllr/api/lessons/LL-DEL-3",
        json={"Status": "Approved", **APPROVE_ASSIGNMENT},
        headers=ADMIN,
    )
    assert approved.status_code == 200, approved.text
    denied = client.delete("/sllr/api/lessons/LL-DEL-3", headers=OWNER)
    assert denied.status_code == 403
    assert client.get("/sllr/api/lessons/LL-DEL-3").status_code == 200


def test_non_owner_approver_cannot_delete(client):
    created = client.post("/sllr/api/lessons", json=_lesson_body("LL-DEL-4"), headers=OWNER)
    assert created.status_code == 201
    denied = client.delete("/sllr/api/lessons/LL-DEL-4", headers=OTHER)
    assert denied.status_code == 403
    assert client.get("/sllr/api/lessons/LL-DEL-4").json()["Title"] == "Lesson LL-DEL-4"


def test_missing_lesson_is_404(client):
    missing = client.delete("/sllr/api/lessons/LL-DOES-NOT-EXIST", headers=ADMIN)
    assert missing.status_code == 404
    assert client.delete("/api/lessons/LL-DOES-NOT-EXIST", headers=ADMIN).status_code == 404


def test_delete_writes_activity_without_leaving_row(client):
    created = client.post("/sllr/api/lessons", json=_lesson_body("LL-DEL-5"), headers=OWNER)
    assert created.status_code == 201
    deleted = client.delete("/sllr/api/lessons/LL-DEL-5", headers=OWNER)
    assert deleted.status_code == 200

    assert client.get("/sllr/api/lessons/LL-DEL-5").status_code == 404

    listed = client.get("/sllr/api/activity", headers=ADMIN, params={"action": "delete_lesson", "entity_id": "LL-DEL-5"})
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 1
    row = body["items"][0]
    assert row["action"] == "delete_lesson"
    assert row["email"] == "owner@powerlearn.us"
    assert row["user_id"] == "u-owner"
    assert row["entity_id"] == "LL-DEL-5"
    assert row["values"]["title"] == "Lesson LL-DEL-5"
    assert row["values"]["lesson_id"] == "LL-DEL-5"
    assert row["values"]["before"]["Lesson ID"] == "LL-DEL-5"
    assert row["values"]["before"]["Title"] == "Lesson LL-DEL-5"
    assert row["values"]["before"]["Status"] == "Draft"
