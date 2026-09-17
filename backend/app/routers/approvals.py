"""Pending approval counts for the current portal identity."""
from fastapi import APIRouter, Request

from backend.app.approval import pending_draft_count
from backend.app.identity import is_portal_admin, portal_identity
from backend.app.storage import load_lessons_with_lock

router = APIRouter()


@router.get("/approvals/pending-count")
async def get_pending_approval_count(request: Request):
    """Return how many Draft lessons the caller may approve.

    Uses the same admin / technical-block / General-fallback rules as Approve.
    Missing identity yields count 0 (nothing to approve).
    """
    ident = portal_identity(request)
    count = pending_draft_count(
        load_lessons_with_lock(),
        is_admin=is_portal_admin(request),
        email=ident.get("email"),
    )
    return {"count": count}
