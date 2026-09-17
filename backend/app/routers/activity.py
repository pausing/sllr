"""Admin-only activity / audit log."""
from typing import Optional

from fastapi import APIRouter, Query, Request

from backend.app.identity import require_portal_admin
from src.sllr.store import list_activity_log

router = APIRouter()


@router.get("/activity")
async def get_activity(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    email: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    since: Optional[str] = Query(None),
):
    require_portal_admin(request, "Portal admin required to view the activity log.")
    items, total = list_activity_log(
        limit=limit,
        offset=offset,
        email=email,
        action=action,
        entity_id=entity_id,
        since=since,
    )
    return {
        "items": items,
        "total": total,
        "limit": min(max(limit, 1), 200),
        "offset": max(offset, 0),
    }
