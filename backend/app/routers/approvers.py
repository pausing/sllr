"""Approvers API: which emails may approve which Technical Blocks."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.app.activity import log_activity
from backend.app.identity import normalize_email, portal_identity, require_portal_admin
from backend.app.storage import (
    add_approver_mapping,
    delete_approver_mapping,
    get_approver_blocks,
    list_approvers_by_block,
    list_approvers_grouped,
    set_approver_blocks,
    set_approvers_for_block,
)
from src.sllr.loaders import load_all_references

router = APIRouter()


class ApproverSet(BaseModel):
    email: str
    technical_blocks: list[str] = Field(default_factory=list)


class ApproverAdd(BaseModel):
    email: str
    technical_block: Optional[str] = None
    technical_blocks: Optional[list[str]] = None


class ApproverBlockSet(BaseModel):
    technical_block: str
    email: Optional[str] = None
    emails: Optional[list[str]] = None


def _valid_blocks() -> set[str]:
    refs = load_all_references()
    return set(refs.get("technical_blocks") or [])


def _require_known_blocks(blocks: list[str]) -> list[str]:
    valid = _valid_blocks()
    unknown = sorted({b for b in blocks if b not in valid})
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown technical block(s): {', '.join(unknown)}",
        )
    return blocks


@router.get("/approvers")
async def list_approvers(request: Request):
    """List all email → technical block mappings (admin only)."""
    require_portal_admin(request, "Portal admin required to manage approvers.")
    return {"approvers": list_approvers_grouped(), "blocks": list_approvers_by_block()}


@router.get("/approvers/me")
async def get_my_approver_rules(request: Request):
    """Technical blocks the current portal user may approve."""
    ident = portal_identity(request)
    email = normalize_email(ident.get("email"))
    return {
        "email": email or ident.get("email"),
        "admin": ident.get("admin") is True,
        "technical_blocks": get_approver_blocks(email) if email else [],
    }


@router.get("/approvers/block")
async def list_approver_blocks(request: Request):
    """List approvers grouped by technical block (admin only)."""
    require_portal_admin(request, "Portal admin required to manage approvers.")
    return {"blocks": list_approvers_by_block()}


@router.put("/approvers/block")
async def replace_block_approvers(payload: ApproverBlockSet, request: Request):
    """Replace all approvers for one technical block (admin only).

    Pass a single ``email`` (or ``emails``) to set the mapping(s). Empty / null
    email clears the block.
    """
    require_portal_admin(request, "Portal admin required to manage approvers.")
    block = (payload.technical_block or "").strip()
    if not block:
        raise HTTPException(status_code=422, detail="technical_block is required")
    _require_known_blocks([block])
    emails: list[str] = []
    if payload.emails:
        emails.extend(payload.emails)
    elif payload.email:
        emails.append(payload.email)
    before = next(
        (row for row in list_approvers_by_block() if row["technical_block"] == block),
        {"technical_block": block, "emails": []},
    )
    stored = set_approvers_for_block(block, emails)
    log_activity(
        request,
        "set_approvers",
        entity_type="approver_block",
        entity_id=block,
        values={"before": before, "after": {"technical_block": block, "emails": stored}},
    )
    return {"technical_block": block, "emails": stored}


@router.post("/approvers/block", status_code=201)
async def add_block_approver(payload: ApproverBlockSet, request: Request):
    """Add a secondary approver for a technical block without replacing others."""
    require_portal_admin(request, "Portal admin required to manage approvers.")
    block = (payload.technical_block or "").strip()
    email = normalize_email(payload.email)
    if not block:
        raise HTTPException(status_code=422, detail="technical_block is required")
    if not email:
        raise HTTPException(status_code=422, detail="email is required")
    _require_known_blocks([block])
    add_approver_mapping(email, block)
    current = next(
        (row for row in list_approvers_by_block() if row["technical_block"] == block),
        {"technical_block": block, "emails": []},
    )
    log_activity(
        request,
        "add_approver",
        entity_type="approver_block",
        entity_id=block,
        values={"after": current, "added": {"email": email, "technical_block": block}},
    )
    return current


@router.put("/approvers")
async def replace_approver_blocks(payload: ApproverSet, request: Request):
    """Replace the technical blocks assigned to an email (admin only)."""
    require_portal_admin(request, "Portal admin required to manage approvers.")
    email = normalize_email(payload.email)
    if not email:
        raise HTTPException(status_code=422, detail="email is required")
    blocks = [b.strip() for b in payload.technical_blocks if (b or "").strip()]
    _require_known_blocks(blocks)
    before = get_approver_blocks(email)
    stored = set_approver_blocks(email, blocks)
    log_activity(
        request,
        "set_approvers",
        entity_type="approver",
        entity_id=email,
        values={"before": {"email": email, "technical_blocks": before}, "after": {"email": email, "technical_blocks": stored}},
    )
    return {"email": email, "technical_blocks": stored}


@router.post("/approvers", status_code=201)
async def add_approver(payload: ApproverAdd, request: Request):
    """Add one or more technical-block mappings for an email (admin only)."""
    require_portal_admin(request, "Portal admin required to manage approvers.")
    email = normalize_email(payload.email)
    if not email:
        raise HTTPException(status_code=422, detail="email is required")
    blocks: list[str] = []
    if payload.technical_block:
        blocks.append(payload.technical_block.strip())
    if payload.technical_blocks:
        blocks.extend(b.strip() for b in payload.technical_blocks if (b or "").strip())
    blocks = list(dict.fromkeys(b for b in blocks if b))
    if not blocks:
        raise HTTPException(status_code=422, detail="technical_block is required")
    _require_known_blocks(blocks)
    before = get_approver_blocks(email)
    for block in blocks:
        add_approver_mapping(email, block)
    after = get_approver_blocks(email)
    log_activity(
        request,
        "add_approver",
        entity_type="approver",
        entity_id=email,
        values={"before": {"email": email, "technical_blocks": before}, "after": {"email": email, "technical_blocks": after}},
    )
    return {"email": email, "technical_blocks": after}


@router.delete("/approvers/{email}")
async def delete_approver(email: str, request: Request):
    """Remove all mappings for an email (admin only)."""
    require_portal_admin(request, "Portal admin required to manage approvers.")
    normalized = normalize_email(email)
    before = get_approver_blocks(normalized)
    deleted = delete_approver_mapping(normalized)
    log_activity(
        request,
        "delete_approver",
        entity_type="approver",
        entity_id=normalized,
        values={"before": {"email": normalized, "technical_blocks": before}, "deleted": deleted},
    )
    return {"email": normalized, "deleted": deleted}


@router.delete("/approvers/{email}/{technical_block}")
async def delete_approver_block(email: str, technical_block: str, request: Request):
    """Remove one email + technical block mapping (admin only)."""
    require_portal_admin(request, "Portal admin required to manage approvers.")
    normalized = normalize_email(email)
    deleted = delete_approver_mapping(normalized, technical_block)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Approver mapping not found")
    log_activity(
        request,
        "delete_approver",
        entity_type="approver",
        entity_id=normalized,
        values={"before": {"email": normalized, "technical_block": technical_block}, "deleted": deleted},
    )
    return {"email": normalized, "technical_block": technical_block, "deleted": deleted}
