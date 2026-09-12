"""
KPIs API router.
"""
from fastapi import APIRouter

from backend.app.storage import load_lessons_with_lock
from src.sllr.kpi import compute_kpis


router = APIRouter()


@router.get("/kpis")
async def get_kpis():
    """
    Compute and return governance KPIs.
    """
    lessons = load_lessons_with_lock()
    kpis = compute_kpis(lessons)
    return kpis
