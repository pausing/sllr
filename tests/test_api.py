"""
SLLR API Tests with /sllr prefix support
"""
import os
import pytest
from fastapi.testclient import TestClient

# Set test data directory and base path before importing app
os.environ["SLLR_DATA_DIR"] = "/tmp/sllr_test_data"
os.environ["SLLR_BASE_PATH"] = "/sllr"

from backend.app.main import app

client = TestClient(app)


def test_health_sllr():
    """Test health endpoint at /sllr/api/health."""
    response = client.get("/sllr/api/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_health_root():
    """Test health endpoint at /api/health (root path)."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_sllr_redirect():
    """Test that /sllr redirects to /sllr/."""
    response = client.get("/sllr", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/sllr/"


def test_get_references():
    """Test references endpoint with /sllr prefix."""
    response = client.get("/sllr/api/references")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "technical_blocks" in data
    assert "phases" in data
    assert "statuses" in data
    assert "implementation_statuses" in data


def test_list_lessons():
    """Test listing lessons with /sllr prefix."""
    response = client.get("/sllr/api/lessons")
    assert response.status_code == 200
    lessons = response.json()
    assert isinstance(lessons, list)


def test_empty_lessons_and_kpis_same_file(tmp_path, monkeypatch):
    """KPI and list_lessons must both read the same (empty) lessons file."""
    from src.sllr.config import LESSON_SCHEMA, get_lessons_master_path
    from backend.app.storage import get_lessons_path, load_lessons_with_lock
    from src.sllr.kpi import compute_kpis
    from src.sllr.loaders import load_lessons_master

    data_dir = tmp_path / "empty_lessons"
    data_dir.mkdir()
    header = ",".join(LESSON_SCHEMA.keys()) + "\n"
    (data_dir / "lessons_master.csv").write_text(header, encoding="utf-8")
    monkeypatch.setenv("SLLR_DATA_DIR", str(data_dir))

    assert get_lessons_path() == get_lessons_master_path()
    assert get_lessons_path() == data_dir / "lessons_master.csv"
    assert load_lessons_with_lock() == []
    assert load_lessons_master() == []
    assert compute_kpis([])["total_lessons"] == 0
    assert compute_kpis()["total_lessons"] == 0

    lessons_resp = client.get("/sllr/api/lessons")
    kpis_resp = client.get("/sllr/api/kpis")
    assert lessons_resp.status_code == 200
    assert lessons_resp.json() == []
    assert kpis_resp.status_code == 200
    assert kpis_resp.json()["total_lessons"] == 0


def test_me_without_headers():
    response = client.get("/sllr/api/me")
    assert response.status_code == 200
    assert response.json() == {"user_id": None, "email": None, "admin": None}


def test_me_with_portal_headers():
    response = client.get(
        "/sllr/api/me",
        headers={
            "X-Powerlearn-User-Id": "u-42",
            "X-Powerlearn-Email": "pablo@powerlearn.us",
            "X-Powerlearn-Admin": "true",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "user_id": "u-42",
        "email": "pablo@powerlearn.us",
        "admin": True,
    }


def test_get_next_id():
    """Test next ID suggestion with /sllr prefix."""
    response = client.get("/sllr/api/lessons/next-id")
    assert response.status_code == 200
    data = response.json()
    assert "suggested_id" in data
    assert data["suggested_id"].startswith("LL-")


def test_create_lesson():
    """Test creating a new lesson with /sllr prefix."""
    # Get next ID
    next_id_response = client.get("/sllr/api/lessons/next-id")
    next_id = next_id_response.json()["suggested_id"]
    
    # Create lesson
    lesson_data = {
        "Lesson ID": next_id,
        "Title": "Test Lesson",
        "Category": "Engineering",
        "Technical Block": "PV",
        "Sub-category": "Modules",
        "Project Phase": "Construction",
        "Root Cause": "Test root cause",
        "What Happened": "Test what happened",
        "Impact": "Test impact",
        "Lesson Learned": "Test lesson learned",
        "Recommendation": "Test recommendation",
        "Owner": "Test Owner",
    }
    
    response = client.post("/sllr/api/lessons", json=lesson_data)
    assert response.status_code == 201
    created = response.json()
    assert created["Lesson ID"] == next_id
    assert created["Status"] == "Draft"
    assert created["Implementation Status"] == "Not Implemented"


def test_create_lesson_owner_defaults_to_portal_email():
    """When the client omits Owner, stamp it from X-Powerlearn-Email."""
    next_id = client.get("/sllr/api/lessons/next-id").json()["suggested_id"]
    lesson_data = {
        "Lesson ID": next_id,
        "Title": "Portal Owner Lesson",
        "Category": "Engineering",
        "Technical Block": "PV",
        "Sub-category": "Modules",
        "Project Phase": "Construction",
        "Root Cause": "Test root cause",
        "What Happened": "Test what happened",
        "Impact": "Test impact",
        "Lesson Learned": "Test lesson learned",
        "Recommendation": "Test recommendation",
    }
    response = client.post(
        "/sllr/api/lessons",
        json=lesson_data,
        headers={
            "X-Powerlearn-User-Id": "u-1",
            "X-Powerlearn-Email": "owner@powerlearn.us",
            "X-Powerlearn-Admin": "false",
        },
    )
    assert response.status_code == 201
    assert response.json()["Owner"] == "owner@powerlearn.us"


def test_create_lesson_duplicate_id():
    """Test that duplicate lesson IDs are rejected with /sllr prefix."""
    # Create first lesson
    next_id_response = client.get("/sllr/api/lessons/next-id")
    next_id = next_id_response.json()["suggested_id"]
    
    lesson_data = {
        "Lesson ID": next_id,
        "Title": "Test Lesson Duplicate",
        "Category": "Engineering",
        "Technical Block": "PV",
        "Sub-category": "Modules",
        "Project Phase": "Construction",
        "Root Cause": "Test root cause",
        "What Happened": "Test what happened",
        "Impact": "Test impact",
        "Lesson Learned": "Test lesson learned",
        "Recommendation": "Test recommendation",
        "Owner": "Test Owner",
    }
    
    response1 = client.post("/sllr/api/lessons", json=lesson_data)
    assert response1.status_code == 201
    
    # Try to create second lesson with same ID
    response2 = client.post("/sllr/api/lessons", json=lesson_data)
    assert response2.status_code == 409  # Conflict


def test_create_lesson_invalid_category():
    """Test that invalid categories are rejected with /sllr prefix."""
    next_id_response = client.get("/sllr/api/lessons/next-id")
    next_id = next_id_response.json()["suggested_id"]
    
    lesson_data = {
        "Lesson ID": next_id,
        "Title": "Test Lesson Invalid",
        "Category": "INVALID_CATEGORY",  # Invalid
        "Technical Block": "PV",
        "Sub-category": "Modules",
        "Project Phase": "Construction",
        "Root Cause": "Test root cause",
        "What Happened": "Test what happened",
        "Impact": "Test impact",
        "Lesson Learned": "Test lesson learned",
        "Recommendation": "Test recommendation",
        "Owner": "Test Owner",
    }
    
    response = client.post("/sllr/api/lessons", json=lesson_data)
    assert response.status_code == 422  # Validation error


def test_patch_lesson_status():
    """Test patching lesson status with /sllr prefix."""
    # Create a lesson
    next_id_response = client.get("/sllr/api/lessons/next-id")
    next_id = next_id_response.json()["suggested_id"]
    
    lesson_data = {
        "Lesson ID": next_id,
        "Title": "Test Lesson for Patch",
        "Category": "Engineering",
        "Technical Block": "PV",
        "Sub-category": "Modules",
        "Project Phase": "Construction",
        "Root Cause": "Test root cause",
        "What Happened": "Test what happened",
        "Impact": "Test impact",
        "Lesson Learned": "Test lesson learned",
        "Recommendation": "Test recommendation",
        "Owner": "Test Owner",
    }
    
    create_response = client.post("/sllr/api/lessons", json=lesson_data)
    assert create_response.status_code == 201
    
    # Patch status to Approved
    patch_response = client.patch(
        f"/sllr/api/lessons/{next_id}",
        json={"Status": "Approved"}
    )
    assert patch_response.status_code == 200
    patched = patch_response.json()
    assert patched["Status"] == "Approved"


def test_get_kpis():
    """Test KPIs endpoint with /sllr prefix."""
    response = client.get("/sllr/api/kpis")
    assert response.status_code == 200
    kpis = response.json()
    assert "total_lessons" in kpis
    assert "repeated_issues_count" in kpis
    assert "pct_implemented" in kpis
    assert "by_status" in kpis
    assert "by_category" in kpis
    assert "by_technical_block" in kpis


def test_validation_report():
    """Test validation report endpoint with /sllr prefix."""
    response = client.get("/sllr/api/reports/validation")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_duplicates_report():
    """Test duplicates report endpoint with /sllr prefix."""
    response = client.get("/sllr/api/reports/duplicates")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_kpi_report():
    """Test KPI report endpoint with /sllr prefix."""
    response = client.get("/sllr/api/reports/kpi")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_dashboard_export():
    """Test dashboard CSV export with /sllr prefix."""
    response = client.get("/sllr/api/reports/dashboard-export")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]


def test_spa_root_served():
    """Test that SPA is served at /sllr/."""
    response = client.get("/sllr/")
    # Should return HTML (index.html) or 404 if STATIC_DIR not set in test
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert "text/html" in response.headers.get("content-type", "")


def test_api_404_not_caught_by_spa():
    """Test that non-existent API routes return 404, not SPA."""
    response = client.get("/sllr/api/nonexistent")
    assert response.status_code == 404


def test_sllr_assets_not_caught_by_root_catchall():
    """Test that /sllr/assets/ paths are handled by /sllr/{full_path:path}, not /{full_path:path}."""
    # Request a non-existent JS file under /sllr/assets/
    response = client.get("/sllr/assets/nonexistent.js")
    assert response.status_code == 404
    # Should NOT return HTML (index.html)
    content_type = response.headers.get("content-type", "")
    assert "text/html" not in content_type


def test_sllr_assets_css_404():
    """Test that non-existent CSS files under /sllr/assets/ return 404, not SPA."""
    response = client.get("/sllr/assets/nonexistent.css")
    assert response.status_code == 404
    content_type = response.headers.get("content-type", "")
    assert "text/html" not in content_type


def test_missing_asset_nope_js_is_404_not_html():
    """Missing hashed JS must 404, never SPA HTML (wrong MIME white-screen)."""
    response = client.get("/sllr/assets/nope.js")
    assert response.status_code == 404
    assert "text/html" not in response.headers.get("content-type", "")


def test_static_info_without_dist():
    """Debug route works even when STATIC_DIR is unset in tests."""
    for path in ("/api/static-info", "/sllr/api/static-info"):
        response = client.get(path)
        assert response.status_code == 200, path
        data = response.json()
        assert "static_dir" in data
        assert "exists" in data
        assert "assets" in data
        assert isinstance(data["assets"], list)
