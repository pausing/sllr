"""
Static file serving tests with a real Vite-like dist/.

Hashed JS/CSS must be served by the SPA catch-all via _safe_static.
Starlette path operations beat mounts, so 200-on-real-files (not just
404-on-missing) is the regression that PR #12/#13 missed.
"""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.routing import Mount

os.environ.setdefault("SLLR_DATA_DIR", "/tmp/sllr_test_data")
os.environ.setdefault("SLLR_BASE_PATH", "/sllr")


INDEX_HTML = """<!doctype html>
<html><head>
<link rel="stylesheet" href="/sllr/assets/app.css">
</head>
<body>
<script type="module" src="/sllr/assets/app.js"></script>
</body></html>
"""

JS_BODY = "console.log('sllr-app')\n"
CSS_BODY = "body{background:#0c0e12;color:#e8e6e3}\n"


def _write_dist(tmp_path: Path) -> Path:
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text(INDEX_HTML)
    (assets / "app.js").write_text(JS_BODY)
    (assets / "app.css").write_text(CSS_BODY)
    return dist


@pytest.fixture
def static_client(tmp_path: Path):
    dist = _write_dist(tmp_path)

    os.environ["STATIC_DIR"] = str(dist)
    os.environ["SLLR_BASE_PATH"] = "/sllr"
    os.environ["SLLR_DATA_DIR"] = str(tmp_path / "data")

    from backend.app.main import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client, dist, app
    os.environ.pop("STATIC_DIR", None)


def test_health_both_paths(static_client):
    client, _, _ = static_client
    for path in ("/api/health", "/sllr/api/health"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == {"ok": True}


def test_sllr_redirect(static_client):
    client, _, _ = static_client
    response = client.get("/sllr", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/sllr/"


def test_sllr_assets_app_js_is_javascript_not_html(static_client):
    """Catch-all must 200 real hashed JS (PR #13 404'd existing .js before _safe_static)."""
    client, _, _ = static_client
    response = client.get("/sllr/assets/app.js")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/javascript")
    assert response.text == JS_BODY
    assert "<!doctype html>" not in response.text.lower()
    assert "<html" not in response.text.lower()


def test_sllr_assets_app_css_is_css(static_client):
    client, _, _ = static_client
    response = client.get("/sllr/assets/app.css")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert response.text == CSS_BODY


def test_stripped_prefix_assets_app_js(static_client):
    """Strip-path / Traefik-without-prefix case: GET /assets/app.js."""
    client, _, _ = static_client
    response = client.get("/assets/app.js")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/javascript")
    assert response.text == JS_BODY


def test_missing_js_is_404_not_html(static_client):
    client, _, _ = static_client
    response = client.get("/sllr/assets/missing.js")
    assert response.status_code == 404
    content_type = response.headers.get("content-type", "")
    assert "text/html" not in content_type
    assert b"INDEX" not in response.content
    assert b"<!doctype html>" not in response.content.lower()


def test_missing_js_at_stripped_prefix_is_404(static_client):
    client, _, _ = static_client
    response = client.get("/assets/nope.js")
    assert response.status_code == 404
    assert "text/html" not in response.headers.get("content-type", "")


def test_catchall_serves_assets_without_mounts(static_client):
    """Catch-all must serve JS/CSS even if StaticFiles mounts are removed."""
    client, _, app = static_client
    app.router.routes = [r for r in app.router.routes if not isinstance(r, Mount)]
    response = client.get("/sllr/assets/app.js")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/javascript")
    assert response.text == JS_BODY
    css = client.get("/sllr/assets/app.css")
    assert css.status_code == 200
    assert css.headers["content-type"].startswith("text/css")
    stripped = client.get("/assets/app.js")
    assert stripped.status_code == 200
    assert stripped.text == JS_BODY


def test_spa_index_at_sllr(static_client):
    client, _, _ = static_client
    response = client.get("/sllr/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "/sllr/assets/app.js" in response.text


def test_spa_does_not_fallback_for_static_extensions(static_client):
    client, _, _ = static_client
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
    client, dist, _ = static_client
    for path in ("/api/static-info", "/sllr/api/static-info"):
        response = client.get(path)
        assert response.status_code == 200, path
        data = response.json()
        assert data["exists"] is True
        assert Path(data["static_dir"]) == dist.resolve()
        assert "app.js" in data["assets"]
        assert "app.css" in data["assets"]
