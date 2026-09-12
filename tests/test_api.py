"""
SLLR API Tests
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health():
    """Test health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_get_references():
    """Test references endpoint."""
    response = client.get("/api/references")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "technical_blocks" in data
    assert "phases" in data
    assert "statuses" in data
    assert "implementation_statuses" in data


def test_list_lessons():
    """Test listing lessons."""
    response = client.get("/api/lessons")
    assert response.status_code == 200
    lessons = response.json()
    assert isinstance(lessons, list)


def test_get_next_id():
    """Test next ID suggestion."""
    response = client.get("/api/lessons/next-id")
    assert response.status_code == 200
    data = response.json()
    assert "suggested_id" in data
    assert data["suggested_id"].startswith("LL-")


def test_create_lesson():
    """Test creating a new lesson."""
    # Get next ID
    next_id_response = client.get("/api/lessons/next-id")
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
    
    response = client.post("/api/lessons", json=lesson_data)
    assert response.status_code == 201
    created = response.json()
    assert created["Lesson ID"] == next_id
    assert created["Status"] == "Draft"
    assert created["Implementation Status"] == "Not Implemented"


def test_create_lesson_duplicate_id():
    """Test that duplicate lesson IDs are rejected."""
    # Create first lesson
    next_id_response = client.get("/api/lessons/next-id")
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
    
    response1 = client.post("/api/lessons", json=lesson_data)
    assert response1.status_code == 201
    
    # Try to create second lesson with same ID
    response2 = client.post("/api/lessons", json=lesson_data)
    assert response2.status_code == 409  # Conflict


def test_create_lesson_invalid_category():
    """Test that invalid categories are rejected."""
    next_id_response = client.get("/api/lessons/next-id")
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
    
    response = client.post("/api/lessons", json=lesson_data)
    assert response.status_code == 422  # Validation error


def test_patch_lesson_status():
    """Test patching lesson status."""
    # Create a lesson
    next_id_response = client.get("/api/lessons/next-id")
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
    
    create_response = client.post("/api/lessons", json=lesson_data)
    assert create_response.status_code == 201
    
    # Patch status to Approved
    patch_response = client.patch(
        f"/api/lessons/{next_id}",
        json={"Status": "Approved"}
    )
    assert patch_response.status_code == 200
    patched = patch_response.json()
    assert patched["Status"] == "Approved"


def test_get_kpis():
    """Test KPIs endpoint."""
    response = client.get("/api/kpis")
    assert response.status_code == 200
    kpis = response.json()
    assert "total_lessons" in kpis
    assert "repeated_issues_count" in kpis
    assert "pct_implemented" in kpis
    assert "by_status" in kpis
    assert "by_category" in kpis
    assert "by_technical_block" in kpis


def test_validation_report():
    """Test validation report endpoint."""
    response = client.get("/api/reports/validation")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_duplicates_report():
    """Test duplicates report endpoint."""
    response = client.get("/api/reports/duplicates")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_kpi_report():
    """Test KPI report endpoint."""
    response = client.get("/api/reports/kpi")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_dashboard_export():
    """Test dashboard CSV export."""
    response = client.get("/api/reports/dashboard-export")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
