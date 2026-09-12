"""
References API router - controlled vocabularies.
"""
from fastapi import APIRouter

from src.sllr.loaders import load_all_references


router = APIRouter()


@router.get("/references")
async def get_references():
    """
    Get all controlled vocabularies (categories, technical_blocks, phases, statuses, implementation_statuses).
    """
    refs = load_all_references()
    return refs
