"""Owner/admin required for lesson PUT and content PATCH."""
import os

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

os.environ.setdefault("SLLR_BASE_PATH", "/sllr")

from backend.app.identity import can_edit_lesson, emails_match, normalize_email
from tests.lesson_fixtures import lesson_body

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
        "method": "GET",
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


def test_normalize_and_owner_compare():
    assert normalize_email("  Owner@Powerlearn.us  ") == "owner@powerlearn.us"
    assert emails_match("  Owner@Powerlearn.us  ", "owner@powerlearn.us")
    assert not emails_match("", "")
    assert not emails_match("owner@powerlearn.us", "other@powerlearn.us")


def test_can_edit_lesson_admin_or_owner():
    assert can_edit_lesson(_request(ADMIN), "someone@powerlearn.us")
    assert can_edit_lesson(_request(OWNER_CASED), "owner@powerlearn.us")
    assert not can_edit_lesson(_request(OTHER), "owner@powerlearn.us")
    assert not can_edit_lesson(_request({}), "owner@powerlearn.us")


def test_owner_can_put(client):
    created = client.post("/sllr/api/lessons", json=_lesson_body("LL-OWN-1"), headers=OWNER)
    assert created.status_code == 201
    put = client.put(
        "/sllr/api/lessons/LL-OWN-1",
        json={"Title": "Updated by owner"},
        headers=OWNER_CASED,
    )
    assert put.status_code == 200, put.text
    assert put.json()["Title"] == "Updated by owner"


def test_other_user_put_forbidden(client):
    created = client.post("/sllr/api/lessons", json=_lesson_body("LL-OWN-2"), headers=OWNER)
    assert created.status_code == 201
    put = client.put(
        "/sllr/api/lessons/LL-OWN-2",
        json={"Title": "Hijack"},
        headers=OTHER,
    )
    assert put.status_code == 403
    assert client.get("/sllr/api/lessons/LL-OWN-2").json()["Title"] == "Lesson LL-OWN-2"


def test_admin_can_put(client):
    created = client.post("/sllr/api/lessons", json=_lesson_body("LL-OWN-3"), headers=OWNER)
    assert created.status_code == 201
    put = client.put(
        "/sllr/api/lessons/LL-OWN-3",
        json={"Title": "Updated by admin"},
        headers=ADMIN,
    )
    assert put.status_code == 200, put.text
    assert put.json()["Title"] == "Updated by admin"


def test_content_patch_forbidden_for_other_user(client):
    created = client.post("/sllr/api/lessons", json=_lesson_body("LL-OWN-4"), headers=OWNER)
    assert created.status_code == 201
    patch = client.patch(
        "/sllr/api/lessons/LL-OWN-4",
        json={"Title": "Patched"},
        headers=OTHER,
    )
    assert patch.status_code == 403


def test_content_patch_allowed_for_owner(client):
    created = client.post("/sllr/api/lessons", json=_lesson_body("LL-OWN-5"), headers=OWNER)
    assert created.status_code == 201
    patch = client.patch(
        "/sllr/api/lessons/LL-OWN-5",
        json={"Title": "Patched by owner"},
        headers=OWNER,
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["Title"] == "Patched by owner"


def test_status_patch_still_allowed_without_owner(client):
    """Status-only PATCH stays on the approval path, not owner-edit."""
    created = client.post("/sllr/api/lessons", json=_lesson_body("LL-OWN-6"), headers=OWNER)
    assert created.status_code == 201
    patch = client.patch(
        "/sllr/api/lessons/LL-OWN-6",
        json={"Implementation Status": "Implemented"},
        headers=OTHER,
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["Implementation Status"] == "Implemented"


def test_put_without_identity_forbidden(client):
    created = client.post("/sllr/api/lessons", json=_lesson_body("LL-OWN-7"), headers=OWNER)
    assert created.status_code == 201
    put = client.put("/sllr/api/lessons/LL-OWN-7", json={"Title": "Anon"})
    assert put.status_code == 403
