"""Live vocab Settings: seed from CSV, CRUD, order, forms pick up changes."""
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


def test_vocab_seeded_from_csv_on_empty_db(client):
    refs = client.get("/sllr/api/references")
    assert refs.status_code == 200
    body = refs.json()
    assert "categories" not in body
    assert body["technical_blocks"] == ["Civil", "HV & Grid", "PV", "BESS"]
    assert body["phases"] == ["Development", "Pre-Execution", "Construction", "O&M"]
    assert "Draft" in body["statuses"]
    assert "Not Implemented" in body["implementation_statuses"]

    listed = client.get("/sllr/api/settings/vocab", headers=ADMIN)
    assert listed.status_code == 200
    assert [item["code"] for item in listed.json()["phases"]] == body["phases"]


def test_non_admin_cannot_manage_vocab(client):
    assert client.get("/sllr/api/settings/vocab", headers=USER).status_code == 403
    assert client.get("/sllr/api/settings/vocab").status_code == 403
    denied = client.post(
        "/sllr/api/settings/vocab/technical_blocks",
        json={"code": "HSE"},
        headers=USER,
    )
    assert denied.status_code == 403


def test_categories_vocab_removed(client):
    assert client.get("/sllr/api/settings/vocab/categories", headers=ADMIN).status_code == 404
    created = client.post(
        "/sllr/api/settings/vocab/categories",
        json={"code": "HSE", "label": "Health & Safety"},
        headers=ADMIN,
    )
    assert created.status_code == 404
    vocab = client.get("/sllr/api/settings/vocab", headers=ADMIN).json()
    assert "categories" not in vocab
    assert "technical_blocks" in vocab
    assert "phases" in vocab


def test_phase_order_is_preserved(client):
    reordered = client.put(
        "/sllr/api/settings/vocab/phases/order",
        json={"codes": ["O&M", "Construction", "Pre-Execution", "Development"]},
        headers=ADMIN,
    )
    assert reordered.status_code == 200, reordered.text
    assert [item["code"] for item in reordered.json()["items"]] == [
        "O&M",
        "Construction",
        "Pre-Execution",
        "Development",
    ]
    assert client.get("/sllr/api/references").json()["phases"] == [
        "O&M",
        "Construction",
        "Pre-Execution",
        "Development",
    ]


def test_rename_technical_block_updates_approvers(client):
    client.put(
        "/sllr/api/approvers/block",
        json={"technical_block": "PV", "email": "pv@powerlearn.us"},
        headers=ADMIN,
    )
    renamed = client.patch(
        "/sllr/api/settings/vocab/technical_blocks/PV",
        json={"code": "Solar PV"},
        headers=ADMIN,
    )
    assert renamed.status_code == 200
    blocks = client.get("/sllr/api/approvers/block", headers=ADMIN).json()["blocks"]
    solar = next(row for row in blocks if row["technical_block"] == "Solar PV")
    assert solar["emails"] == ["pv@powerlearn.us"]
    assert "PV" not in client.get("/sllr/api/references").json()["technical_blocks"]
