"""Lesson approval: Draft → Approved requires admin or a matching technical-block mapping."""
from typing import Any, Iterable, Optional

from fastapi import HTTPException, Request

from backend.app.identity import is_portal_admin, normalize_email, portal_identity
from backend.app.storage import get_approver_blocks, has_approver_mapping


def allowed_blocks_for(email: Optional[str]) -> list[str]:
    return get_approver_blocks(email or "")


def can_approve_lesson(
    *,
    is_admin: bool,
    email: Optional[str],
    technical_block: str,
) -> bool:
    if is_admin:
        return True
    block = (technical_block or "").strip()
    if not block:
        return False
    return has_approver_mapping(email or "", block)


def visible_lessons_for_approve(
    lessons: Iterable[dict[str, Any]],
    *,
    is_admin: bool,
    allowed_blocks: Iterable[str],
) -> list[dict[str, Any]]:
    """Admins see all lessons. Non-admins see Draft lessons in their assigned blocks."""
    rows = list(lessons)
    if is_admin:
        return rows
    allowed = set(allowed_blocks)
    return [
        lesson
        for lesson in rows
        if lesson.get("Status") == "Draft" and lesson.get("Technical Block") in allowed
    ]


def can_change_status(
    *,
    is_admin: bool,
    allowed_blocks: Iterable[str],
    lesson: dict[str, Any],
) -> bool:
    """Whether the Approve UI should show a status control for this lesson."""
    if is_admin:
        return True
    return (
        lesson.get("Status") == "Draft"
        and lesson.get("Technical Block") in set(allowed_blocks)
    )


def enforce_approval_if_needed(
    request: Request,
    existing: dict[str, Any],
    updated: dict[str, Any],
) -> None:
    """403 unless admin or mapped for the lesson's Technical Block when transitioning to Approved."""
    new_status = (updated.get("Status") or "").strip()
    old_status = (existing.get("Status") or "").strip()
    if new_status != "Approved" or old_status == "Approved":
        return

    ident = portal_identity(request)
    block = (updated.get("Technical Block") or existing.get("Technical Block") or "").strip()
    if can_approve_lesson(
        is_admin=is_portal_admin(request),
        email=ident.get("email"),
        technical_block=block,
    ):
        return

    email = normalize_email(ident.get("email"))
    if not email:
        raise HTTPException(
            status_code=403,
            detail=(
                "Not allowed to set Status to Approved: portal email is missing "
                "and the caller is not a portal admin."
            ),
        )
    raise HTTPException(
        status_code=403,
        detail=(
            f"Not allowed to approve lessons in technical block {block!r}. "
            "A portal admin must assign this block to your email on the Approvers screen."
        ),
    )
