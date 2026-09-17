"""GET /api/approvals/pending-count — Drafts the current identity may approve."""
import os

import pytest
from fastapi.testclient import TestClient

from tests.lesson_fixtures import APPROVE_ASSIGNMENT, lesson_body

os.environ.setdefault("SLLR_BASE_PATH", "/sllr")

ADMIN = {
    "X-Powerlearn-User-Id": "u-admin",
    "X-Powerlearn-Email": "pablo@powerlearn.us",
    "X-Powerlearn-Admin": "true",
}
CIVIL_USER = {
    "X-Powerlearn-User-Id": "u-civil",
    "X-Powerlearn-Email": "civil.approver@powerlearn.us",
    "X-Powerlearn-Admin": "false",
}
OTHER_USER = {
    "X-Powerlearn-User-Id": "u-other",
    "X-Powerlearn-Email": "other@powerlearn.us",
    "X-Powerlearn-Admin": "false",
}
GENERAL_USER = {
    "X-Powerlearn-User-Id": "u-general",
    "X-Powerlearn-Email": "general.approver@powerlearn.us",
    "X-Powerlearn-Admin": "false",
}


def _lesson(lesson_id: str, technical_block: str = "Civil", **overrides) -> dict:
    return lesson_body(lesson_id, technical_block=technical_block, **overrides)


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


def _count(client: TestClient, headers: dict | None = None, path: str = "/sllr/api/approvals/pending-count"):
    return client.get(path, headers=headers or {})


def test_pending_count_zero_when_no_lessons(client):
    assert _count(client, CIVIL_USER).status_code == 200
    assert _count(client, CIVIL_USER).json() == {"count": 0}
    assert _count(client, ADMIN).json() == {"count": 0}


def test_pending_count_zero_without_identity(client):
    assert client.post("/sllr/api/lessons", json=_lesson("LL-ANON", "Civil")).status_code == 201
    res = _count(client)
    assert res.status_code == 200
    assert res.json() == {"count": 0}


def test_pending_count_zero_when_unmapped_user(client):
    assert client.post("/sllr/api/lessons", json=_lesson("LL-OTH", "Civil")).status_code == 201
    res = _count(client, OTHER_USER)
    assert res.status_code == 200
    assert res.json() == {"count": 0}


def test_pending_count_mapped_draft(client):
    client.put(
        "/sllr/api/approvers",
        json={"email": "civil.approver@powerlearn.us", "technical_blocks": ["Civil"]},
        headers=ADMIN,
    )
    assert client.post("/sllr/api/lessons", json=_lesson("LL-C1", "Civil")).status_code == 201
    assert client.post("/sllr/api/lessons", json=_lesson("LL-PV", "PV")).status_code == 201
    assert client.post("/sllr/api/lessons", json=_lesson("LL-C-APP", "Civil")).status_code == 201
    approved = client.patch(
        "/sllr/api/lessons/LL-C-APP",
        json={"Status": "Approved", **APPROVE_ASSIGNMENT},
        headers=ADMIN,
    )
    assert approved.status_code == 200

    civil = _count(client, CIVIL_USER)
    assert civil.status_code == 200
    assert civil.json() == {"count": 1}

    dual = _count(client, CIVIL_USER, "/api/approvals/pending-count")
    assert dual.status_code == 200
    assert dual.json() == {"count": 1}


def test_pending_count_admin_sees_all_drafts(client):
    assert client.post("/sllr/api/lessons", json=_lesson("LL-A", "BESS")).status_code == 201
    assert client.post("/sllr/api/lessons", json=_lesson("LL-B", "PV")).status_code == 201
    assert client.post("/sllr/api/lessons", json=_lesson("LL-C", "Civil")).status_code == 201
    approved = client.patch(
        "/sllr/api/lessons/LL-C",
        json={"Status": "Approved", **APPROVE_ASSIGNMENT},
        headers=ADMIN,
    )
    assert approved.status_code == 200
    res = _count(client, ADMIN)
    assert res.status_code == 200
    assert res.json() == {"count": 2}


def test_pending_count_general_fallback_only_unmapped_blocks(client):
    client.put(
        "/sllr/api/approvers/block",
        json={"technical_block": "General", "email": "general.approver@powerlearn.us"},
        headers=ADMIN,
    )
    client.put(
        "/sllr/api/approvers/block",
        json={"technical_block": "Civil", "email": "civil.approver@powerlearn.us"},
        headers=ADMIN,
    )
    assert client.post("/sllr/api/lessons", json=_lesson("LL-GEN-PV", "PV")).status_code == 201
    assert client.post("/sllr/api/lessons", json=_lesson("LL-GEN-CIV", "Civil")).status_code == 201

    general = _count(client, GENERAL_USER)
    assert general.status_code == 200
    assert general.json() == {"count": 1}

    civil = _count(client, CIVIL_USER)
    assert civil.json() == {"count": 1}


def test_pending_count_admin_header_without_true_is_not_admin(client):
    assert client.post("/sllr/api/lessons", json=_lesson("LL-FAKE", "PV")).status_code == 201
    fake = {
        "X-Powerlearn-User-Id": "u-fake",
        "X-Powerlearn-Email": "fake@powerlearn.us",
        "X-Powerlearn-Admin": "false",
    }
    assert _count(client, fake).json() == {"count": 0}


def test_pending_draft_count_helper():
    from backend.app.approval import pending_draft_count

    lessons = [
        {"Lesson ID": "1", "Status": "Draft", "Technical Block": "Civil"},
        {"Lesson ID": "2", "Status": "Draft", "Technical Block": "PV"},
        {"Lesson ID": "3", "Status": "Approved", "Technical Block": "Civil"},
    ]
    assert pending_draft_count(lessons, is_admin=True, email=None) == 2
    assert pending_draft_count(lessons, is_admin=False, email=None) == 0
