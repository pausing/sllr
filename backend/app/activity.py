"""Best-effort admin activity logging for SLLR writes."""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import Request

from backend.app.identity import portal_identity
from src.sllr.store import insert_activity_log

logger = logging.getLogger(__name__)


def changed_values(before: Optional[dict[str, Any]], after: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Return only keys that differ, each as {before, after}."""
    left = before or {}
    right = after or {}
    keys = set(left) | set(right)
    out: dict[str, Any] = {}
    for key in sorted(keys):
        old = left.get(key)
        new = right.get(key)
        if old != new:
            out[key] = {"before": old, "after": new}
    return out


def lesson_write_action(method_action: str, existing: dict[str, Any], updated: dict[str, Any]) -> str:
    old = (existing.get("Status") or "").strip()
    new = (updated.get("Status") or "").strip()
    if new == "Approved" and old != "Approved":
        return "approve_lesson"
    return method_action


def log_activity(
    request: Request,
    action: str,
    *,
    entity_type: str = "",
    entity_id: str = "",
    values: Any = None,
) -> None:
    """Record a write. Missing portal headers still log the action. Never fail the caller."""
    try:
        ident = portal_identity(request)
        insert_activity_log(
            user_id=ident.get("user_id") or "",
            email=ident.get("email") or "",
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id or ""),
            values=values,
        )
    except Exception:
        logger.exception("activity log write failed for action=%s", action)
