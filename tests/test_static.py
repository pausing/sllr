"""
Static file serving tests with a real Vite-like dist/.

These must use create_app() after STATIC_DIR is set so mounts exist.
The default test_api client has no dist and cannot prove asset MIME/404.
"""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SLLR_DATA_DIR", "/tmp/sllr_test_data")
os.environ.setdefault("SLLR_BASE_PATH", "/sllr")


INDEX_HTML = """<!doctype html>
<html><head>
<link rel="stylesheet" href="/sllr/assets/app-abc.css">
</head>
<body>
<script type="module" src="/sllr/assets/app-abc.js"></script>
</body></html>
"""


@pytest.fixture
def static_client(tmp_path: Path):
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text(INDEX_HTML)
    (assets / "app-abc.js").write_text("console.log('ok')\n")
    (assets / "app-abc.css").write_text("body{background:#0c0e12}\n")

    os.environ["STATIC_DIR"] = str(dist)
    os.environ["SLLR_BASE_PATH"] = "/sllr"
    os.environ["SLLR_DATA_DIR"] = str(tmp_path / "data")

    from backend.app.main import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client, dist
    os.environ.pop("STATIC_DIR", None)


def test_health_both_paths(static_client):
    client, _ = static_client
    for path in ("/api/health", "/sllr/api/health"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == {"ok": True}


def test_sllr_redirect(static_client):
    client, _ = static_client
    response = client.get("/sllr", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/sllr/"


def test_missing_js_is_404_not_html(static_client):
    client, _ = static_client
    response = client.get("/sllr/assets/nope.js")
    assert response.status_code == 404
    content_type = response.headers.get("content-type", "")
    assert "text/html" not in content_type
    assert b"INDEX" not in response.content
    assert b"<!doctype html>" not in response.content.lower()


def test_missing_js_at_stripped_prefix_is_404(static_client):
    client, _ = static_client
    response = client.get("/assets/nope.js")
    assert response.status_code == 404
    assert "text/html" not in response.headers.get("content-type", "")


def test_js_served_with_javascript_mime(static_client):
    client, _ = static_client
    for path in ("/sllr/assets/app-abc.js", "/assets/app-abc.js"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.headers["content-type"].startswith("application/javascript")
        assert response.text == "console.log('ok')\n"


def test_css_served_with_css_mime(static_client):
    client, _ = static_client
    for path in ("/sllr/assets/app-abc.css", "/assets/app-abc.css"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.headers["content-type"].startswith("text/css")
        assert "#0c0e12" in response.text


def test_spa_index_at_sllr(static_client):
    client, _ = static_client
    response = client.get("/sllr/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "/sllr/assets/app-abc.js" in response.text


def test_spa_does_not_fallback_for_static_extensions(static_client):
    client, _ = static_client
    for path in (
        "/sllr/missing.js",
        "/sllr/foo.css",
        "/sllr/x.map",
        "/sllr/icon.svg",
        "/sllr/font.woff2",
        "/sllr/data.json",
    ):
        response = client.get(path)
        assert response.status_code == 404, path
        assert "text/html" not in response.headers.get("content-type", "")


def test_static_info_lists_assets(static_client):
    client, dist = static_client
    for path in ("/api/static-info", "/sllr/api/static-info"):
        response = client.get(path)
        assert response.status_code == 200, path
        data = response.json()
        assert data["exists"] is True
        assert Path(data["static_dir"]) == dist.resolve()
        assert "app-abc.js" in data["assets"]
        assert "app-abc.css" in data["assets"]
