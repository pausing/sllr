"""Current portal user (ForwardAuth headers)."""
from fastapi import APIRouter, Request

from backend.app.identity import portal_identity

router = APIRouter()


@router.get("/me")
async def get_me(request: Request):
    """Return portal identity headers, or nulls when ForwardAuth is not present."""
    return portal_identity(request)
