"""Lesson attachments: 10 MB cap, path safety, owner/admin write, admin storage."""
import io
import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SLLR_BASE_PATH", "/sllr")

from src.sllr.attachments import (
    MAX_ATTACHMENT_BYTES,
    OVERSIZE_DETAIL,
    attachment_file_path,
    get_attachments_root,
    lesson_attachments_dir,
)
from tests.lesson_fixtures import lesson_body

OWNER = {
    "X-Powerlearn-User-Id": "u-owner",
    "X-Powerlearn-Email": "owner@powerlearn.us",
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


def _create_lesson(client: TestClient, lesson_id: str = "LL-ATT-1") -> None:
    created = client.post("/sllr/api/lessons", json=lesson_body(lesson_id, owner="owner@powerlearn.us"), headers=OWNER)
    assert created.status_code == 201, created.text


def test_attachment_paths_reject_traversal(tmp_path, monkeypatch):
    monkeypatch.setenv("SLLR_DATA_DIR", str(tmp_path))
    with pytest.raises(ValueError):
        attachment_file_path("LL-ATT-1", "../secret")
    with pytest.raises(ValueError):
        attachment_file_path("LL-ATT-1", "aabbcc")
    stored = "a" * 32
    path = attachment_file_path("LL-ATT-1", stored)
    assert path.name == stored
    assert path.parent == lesson_attachments_dir("LL-ATT-1")
    assert get_attachments_root() in path.parents


def test_owner_can_upload_list_download_delete(client):
    _create_lesson(client)
    payload = ("notes.txt", io.BytesIO(b"hello attachments"), "text/plain")
    uploaded = client.post(
        "/sllr/api/lessons/LL-ATT-1/attachments",
        files={"file": payload},
        headers=OWNER,
    )
    assert uploaded.status_code == 201, uploaded.text
    body = uploaded.json()
    assert body["filename"] == "notes.txt"
    assert body["size_bytes"] == 17
    assert body["id"]

    listed = client.get("/sllr/api/lessons/LL-ATT-1/attachments")
    assert listed.status_code == 200
    rows = listed.json()["attachments"]
    assert len(rows) == 1
    assert rows[0]["filename"] == "notes.txt"
    assert rows[0]["uploaded_at"]

    downloaded = client.get(f"/sllr/api/lessons/LL-ATT-1/attachments/{body['id']}")
    assert downloaded.status_code == 200
    assert downloaded.content == b"hello attachments"
    assert "notes.txt" in downloaded.headers.get("content-disposition", "")

    deleted = client.delete(f"/sllr/api/lessons/LL-ATT-1/attachments/{body['id']}", headers=OWNER)
    assert deleted.status_code == 200
    empty = client.get("/sllr/api/lessons/LL-ATT-1/attachments")
    assert empty.json()["attachments"] == []


def test_filename_path_is_stripped(client):
    _create_lesson(client, "LL-ATT-PATH")
    uploaded = client.post(
        "/sllr/api/lessons/LL-ATT-PATH/attachments",
        files={"file": ("../../etc/passwd", io.BytesIO(b"x"), "text/plain")},
        headers=OWNER,
    )
    assert uploaded.status_code == 201, uploaded.text
    assert uploaded.json()["filename"] == "passwd"
    stored_root = get_attachments_root()
    files = list(stored_root.rglob("*"))
    assert all("etc" not in p.parts for p in files)


def test_non_owner_cannot_upload_or_delete(client):
    _create_lesson(client, "LL-ATT-2")
    denied = client.post(
        "/sllr/api/lessons/LL-ATT-2/attachments",
        files={"file": ("a.txt", io.BytesIO(b"a"), "text/plain")},
        headers=OTHER,
    )
    assert denied.status_code == 403

    uploaded = client.post(
        "/sllr/api/lessons/LL-ATT-2/attachments",
        files={"file": ("a.txt", io.BytesIO(b"a"), "text/plain")},
        headers=OWNER,
    )
    assert uploaded.status_code == 201
    att_id = uploaded.json()["id"]
    listed = client.get("/sllr/api/lessons/LL-ATT-2/attachments", headers=OTHER)
    assert listed.status_code == 200
    assert len(listed.json()["attachments"]) == 1
    deleted = client.delete(f"/sllr/api/lessons/LL-ATT-2/attachments/{att_id}", headers=OTHER)
    assert deleted.status_code == 403


def test_admin_can_upload_and_storage_overview(client):
    _create_lesson(client, "LL-ATT-3")
    uploaded = client.post(
        "/sllr/api/lessons/LL-ATT-3/attachments",
        files={"file": ("admin.bin", io.BytesIO(b"abcde"), "application/octet-stream")},
        headers=ADMIN,
    )
    assert uploaded.status_code == 201, uploaded.text

    forbidden = client.get("/sllr/api/settings/storage", headers=OWNER)
    assert forbidden.status_code == 403

    overview = client.get("/sllr/api/settings/storage", headers=ADMIN)
    assert overview.status_code == 200, overview.text
    data = overview.json()
    assert data["total_files"] == 1
    assert data["total_bytes"] == 5
    assert data["max_file_bytes"] == MAX_ATTACHMENT_BYTES
    assert data["max_file_label"] == "10 MB"
    assert data["lessons"][0]["lesson_id"] == "LL-ATT-3"
    assert data["lessons"][0]["title"]
    assert data["lessons"][0]["file_count"] == 1
    assert data["lessons"][0]["bytes"] == 5


def test_oversize_upload_rejected(client):
    _create_lesson(client, "LL-ATT-4")
    too_big = b"x" * (MAX_ATTACHMENT_BYTES + 1)
    uploaded = client.post(
        "/sllr/api/lessons/LL-ATT-4/attachments",
        files={"file": ("huge.bin", io.BytesIO(too_big), "application/octet-stream")},
        headers=OWNER,
    )
    assert uploaded.status_code == 413, uploaded.text
    assert OVERSIZE_DETAIL in str(uploaded.json()["detail"])
    listed = client.get("/sllr/api/lessons/LL-ATT-4/attachments")
    assert listed.json()["attachments"] == []
    leftover_files = [p for p in get_attachments_root().rglob("*") if p.is_file()]
    assert leftover_files == []


def test_delete_lesson_removes_attachment_files(client):
    _create_lesson(client, "LL-ATT-5")
    uploaded = client.post(
        "/sllr/api/lessons/LL-ATT-5/attachments",
        files={"file": ("keep-me.txt", io.BytesIO(b"payload"), "text/plain")},
        headers=OWNER,
    )
    assert uploaded.status_code == 201
    lesson_dir = lesson_attachments_dir("LL-ATT-5")
    assert lesson_dir.is_dir()
    assert any(lesson_dir.iterdir())

    deleted = client.delete("/sllr/api/lessons/LL-ATT-5", headers=OWNER)
    assert deleted.status_code == 200
    assert client.get("/sllr/api/lessons/LL-ATT-5").status_code == 404
    assert not lesson_dir.exists()
    overview = client.get("/sllr/api/settings/storage", headers=ADMIN)
    assert overview.json()["total_files"] == 0
    assert overview.json()["lessons"] == []
