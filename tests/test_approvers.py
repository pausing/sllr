"""Approvers by technical block: CRUD, Draft→Approved 403/allow, Approve UI filters."""
import os

import pytest
from fastapi.testclient import TestClient

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


def _lesson(lesson_id: str, technical_block: str = "Civil") -> dict:
    return {
        "Lesson ID": lesson_id,
        "Title": f"Lesson {lesson_id}",
        "Category": "Engineering",
        "Technical Block": technical_block,
        "Sub-category": "Modules",
        "Project Phase": "Construction",
        "Root Cause": "Test root cause",
        "What Happened": "Test what happened",
        "Impact": "Test impact",
        "Lesson Learned": "Test lesson learned",
        "Recommendation": "Test recommendation",
        "Owner": "Test Owner",
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


def test_admin_can_assign_approver_blocks(client):
    listed = client.get("/sllr/api/approvers", headers=ADMIN)
    assert listed.status_code == 200
    assert listed.json()["approvers"] == []
    assert {row["technical_block"] for row in listed.json()["blocks"]} == {
        "Civil",
        "HV & Grid",
        "PV",
        "BESS",
    }

    created = client.put(
        "/sllr/api/approvers",
        json={"email": "Civil.Approver@powerlearn.us", "technical_blocks": ["Civil", "PV"]},
        headers=ADMIN,
    )
    assert created.status_code == 200, created.text
    assert created.json()["email"] == "civil.approver@powerlearn.us"
    assert created.json()["technical_blocks"] == ["Civil", "PV"]

    dual = client.get("/api/approvers", headers=ADMIN)
    assert dual.status_code == 200
    rows = dual.json()["approvers"]
    assert rows == [
        {"email": "civil.approver@powerlearn.us", "technical_blocks": ["Civil", "PV"]}
    ]

    added = client.post(
        "/sllr/api/approvers",
        json={"email": "civil.approver@powerlearn.us", "technical_block": "BESS"},
        headers=ADMIN,
    )
    assert added.status_code == 201
    assert "BESS" in added.json()["technical_blocks"]

    deleted = client.delete(
        "/sllr/api/approvers/civil.approver@powerlearn.us/BESS",
        headers=ADMIN,
    )
    assert deleted.status_code == 200

    replaced = client.put(
        "/api/approvers",
        json={"email": "civil.approver@powerlearn.us", "technical_blocks": ["Civil"]},
        headers=ADMIN,
    )
    assert replaced.status_code == 200
    assert replaced.json()["technical_blocks"] == ["Civil"]


def test_non_admin_cannot_mutate_or_list_approvers(client):
    assert client.get("/sllr/api/approvers", headers=CIVIL_USER).status_code == 403
    assert client.get("/sllr/api/approvers").status_code == 403
    denied = client.put(
        "/sllr/api/approvers",
        json={"email": "civil.approver@powerlearn.us", "technical_blocks": ["Civil"]},
        headers=CIVIL_USER,
    )
    assert denied.status_code == 403
    assert "admin" in denied.json()["detail"].lower()
    assert (
        client.post(
            "/sllr/api/approvers",
            json={"email": "x@powerlearn.us", "technical_block": "Civil"},
            headers=CIVIL_USER,
        ).status_code
        == 403
    )
    assert client.delete("/sllr/api/approvers/x@powerlearn.us", headers=CIVIL_USER).status_code == 403


def test_approvers_me_returns_assigned_blocks(client):
    client.put(
        "/sllr/api/approvers",
        json={"email": "civil.approver@powerlearn.us", "technical_blocks": ["Civil"]},
        headers=ADMIN,
    )
    mine = client.get("/sllr/api/approvers/me", headers=CIVIL_USER)
    assert mine.status_code == 200
    body = mine.json()
    assert body["email"] == "civil.approver@powerlearn.us"
    assert body["admin"] is False
    assert body["technical_blocks"] == ["Civil"]

    admin_me = client.get("/sllr/api/approvers/me", headers=ADMIN)
    assert admin_me.status_code == 200
    assert admin_me.json()["admin"] is True


def test_non_admin_without_mapping_gets_403_on_approve(client):
    created = client.post("/sllr/api/lessons", json=_lesson("LL-401"))
    assert created.status_code == 201
    patch = client.patch(
        "/sllr/api/lessons/LL-401",
        json={"Status": "Approved"},
        headers=OTHER_USER,
    )
    assert patch.status_code == 403
    assert "Civil" in patch.json()["detail"]
    assert client.get("/sllr/api/lessons/LL-401").json()["Status"] == "Draft"

    put = client.put(
        "/sllr/api/lessons/LL-401",
        json={"Status": "Approved"},
        headers=OTHER_USER,
    )
    assert put.status_code == 403


def test_mapping_for_civil_can_approve_civil_not_pv(client):
    client.put(
        "/sllr/api/approvers",
        json={"email": "CIVIL.APPROVER@powerlearn.us", "technical_blocks": ["Civil"]},
        headers=ADMIN,
    )
    assert client.post("/sllr/api/lessons", json=_lesson("LL-CIV", "Civil")).status_code == 201
    assert client.post("/sllr/api/lessons", json=_lesson("LL-PV", "PV")).status_code == 201

    allowed = client.patch(
        "/sllr/api/lessons/LL-CIV",
        json={"Status": "Approved"},
        headers=CIVIL_USER,
    )
    assert allowed.status_code == 200, allowed.text
    assert allowed.json()["Status"] == "Approved"

    denied = client.patch(
        "/sllr/api/lessons/LL-PV",
        json={"Status": "Approved"},
        headers=CIVIL_USER,
    )
    assert denied.status_code == 403
    assert "PV" in denied.json()["detail"]
    assert client.get("/sllr/api/lessons/LL-PV").json()["Status"] == "Draft"


def test_admin_can_approve_without_mapping(client):
    assert client.post("/sllr/api/lessons", json=_lesson("LL-ADM", "BESS")).status_code == 201
    patch = client.patch(
        "/sllr/api/lessons/LL-ADM",
        json={"Status": "Approved"},
        headers=ADMIN,
    )
    assert patch.status_code == 200
    assert patch.json()["Status"] == "Approved"


def test_anonymous_approve_is_403(client):
    assert client.post("/sllr/api/lessons", json=_lesson("LL-ANON")).status_code == 201
    patch = client.patch("/sllr/api/lessons/LL-ANON", json={"Status": "Approved"})
    assert patch.status_code == 403
    assert "missing" in patch.json()["detail"].lower() or "admin" in patch.json()["detail"].lower()


def test_approve_ui_filter_logic():
    from backend.app.approval import can_change_status, visible_lessons_for_approve

    lessons = [
        {"Lesson ID": "1", "Status": "Draft", "Technical Block": "Civil"},
        {"Lesson ID": "2", "Status": "Draft", "Technical Block": "PV"},
        {"Lesson ID": "3", "Status": "Approved", "Technical Block": "Civil"},
    ]
    visible = visible_lessons_for_approve(
        lessons, is_admin=False, allowed_blocks=["Civil"]
    )
    assert [row["Lesson ID"] for row in visible] == ["1"]
    assert can_change_status(is_admin=False, allowed_blocks=["Civil"], lesson=lessons[0])
    assert not can_change_status(is_admin=False, allowed_blocks=["Civil"], lesson=lessons[1])
    assert not can_change_status(is_admin=False, allowed_blocks=["Civil"], lesson=lessons[2])

    admin_visible = visible_lessons_for_approve(lessons, is_admin=True, allowed_blocks=[])
    assert [row["Lesson ID"] for row in admin_visible] == ["1", "2", "3"]
    assert can_change_status(is_admin=True, allowed_blocks=[], lesson=lessons[2])


def test_set_approver_by_block_replaces_mappings(client):
    client.put(
        "/sllr/api/approvers/block",
        json={"technical_block": "Civil", "email": "first@powerlearn.us"},
        headers=ADMIN,
    )
    client.post(
        "/sllr/api/approvers/block",
        json={"technical_block": "Civil", "email": "second@powerlearn.us"},
        headers=ADMIN,
    )
    listed = client.get("/sllr/api/approvers/block", headers=ADMIN)
    civil = next(row for row in listed.json()["blocks"] if row["technical_block"] == "Civil")
    assert set(civil["emails"]) == {"first@powerlearn.us", "second@powerlearn.us"}

    replaced = client.put(
        "/api/approvers/block",
        json={"technical_block": "Civil", "email": "civil.approver@powerlearn.us"},
        headers=ADMIN,
    )
    assert replaced.status_code == 200, replaced.text
    assert replaced.json()["emails"] == ["civil.approver@powerlearn.us"]

    grouped = client.get("/sllr/api/approvers", headers=ADMIN).json()["approvers"]
    assert grouped == [
        {"email": "civil.approver@powerlearn.us", "technical_blocks": ["Civil"]}
    ]

    cleared = client.put(
        "/sllr/api/approvers/block",
        json={"technical_block": "Civil", "email": None},
        headers=ADMIN,
    )
    assert cleared.status_code == 200
    assert cleared.json()["emails"] == []
