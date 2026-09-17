"""Lesson approval: Draft → Approved requires admin or a matching technical-block mapping."""
from typing import Any, Iterable, Optional

from fastapi import HTTPException, Request

from backend.app.identity import is_portal_admin, normalize_email, portal_identity
from backend.app.storage import has_approver_mapping
from src.sllr.config import GENERAL_TECHNICAL_BLOCK
from src.sllr.store import block_has_specific_approvers


def allowed_blocks_for(email: Optional[str]) -> list[str]:
    from backend.app.storage import effective_approver_blocks

    return effective_approver_blocks(email or "")


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
    if has_approver_mapping(email or "", block):
        return True
    if block_has_specific_approvers(block):
        return False
    return has_approver_mapping(email or "", GENERAL_TECHNICAL_BLOCK)


def pending_draft_count(
    lessons: Iterable[dict[str, Any]],
    *,
    is_admin: bool,
    email: Optional[str],
) -> int:
    """How many Draft lessons the current identity may approve."""
    count = 0
    for lesson in lessons:
        if lesson.get("Status") != "Draft":
            continue
        if can_approve_lesson(
            is_admin=is_admin,
            email=email,
            technical_block=lesson.get("Technical Block") or "",
        ):
            count += 1
    return count


def visible_lessons_for_approve(
    lessons: Iterable[dict[str, Any]],
    *,
    is_admin: bool,
    allowed_blocks: Iterable[str],
    empty_blocks: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Admins see all lessons. Non-admins see Draft lessons they can approve.

    ``allowed_blocks`` may include ``General``. When General is present, Draft
    lessons whose Technical Block has no specific mappings (``empty_blocks``)
    are included.
    """
    rows = list(lessons)
    if is_admin:
        return rows
    allowed = set(allowed_blocks)
    has_general = GENERAL_TECHNICAL_BLOCK in allowed
    empty = set(empty_blocks or [])
    visible: list[dict[str, Any]] = []
    for lesson in rows:
        if lesson.get("Status") != "Draft":
            continue
        block = (lesson.get("Technical Block") or "").strip()
        if block in allowed and block != GENERAL_TECHNICAL_BLOCK:
            visible.append(lesson)
            continue
        if has_general and block in empty:
            visible.append(lesson)
    return visible


def can_change_status(
    *,
    is_admin: bool,
    allowed_blocks: Iterable[str],
    lesson: dict[str, Any],
    empty_blocks: Iterable[str] | None = None,
) -> bool:
    """Whether the Approve UI should show a status control for this lesson."""
    if is_admin:
        return True
    if lesson.get("Status") != "Draft":
        return False
    block = (lesson.get("Technical Block") or "").strip()
    allowed = set(allowed_blocks)
    if block in allowed and block != GENERAL_TECHNICAL_BLOCK:
        return True
    if GENERAL_TECHNICAL_BLOCK in allowed and block in set(empty_blocks or []):
        return True
    return False


def enforce_implementation_on_approve(
    existing: dict[str, Any],
    updated: dict[str, Any],
) -> None:
    """422 if Draft → Approved without Implementation Owner and Due Date."""
    new_status = (updated.get("Status") or "").strip()
    old_status = (existing.get("Status") or "").strip()
    if new_status != "Approved" or old_status == "Approved":
        return
    owner = (updated.get("Implementation Owner") or "").strip()
    due = (updated.get("Implementation Due Date") or "").strip()
    missing: list[str] = []
    if not owner:
        missing.append("Implementation Owner")
    elif "@" not in owner:
        raise HTTPException(
            status_code=422,
            detail="Implementation Owner must be a user email.",
        )
    if not due:
        missing.append("Implementation Due Date")
    if missing:
        raise HTTPException(
            status_code=422,
            detail=(
                "Approving a lesson requires "
                + " and ".join(missing)
                + "."
            ),
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
            "A portal admin must assign this block (or General) to your email on the Approvers screen."
        ),
    )
