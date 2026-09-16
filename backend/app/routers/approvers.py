"""Approvers API: which emails may approve which Technical Blocks."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.app.identity import normalize_email, portal_identity, require_portal_admin
from backend.app.storage import (
    add_approver_mapping,
    delete_approver_mapping,
    get_approver_blocks,
    list_approvers_grouped,
    set_approver_blocks,
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
    require_portal_admin(request)
    return {"approvers": list_approvers_grouped()}


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


@router.put("/approvers")
async def replace_approver_blocks(payload: ApproverSet, request: Request):
    """Replace the technical blocks assigned to an email (admin only)."""
    require_portal_admin(request)
    email = normalize_email(payload.email)
    if not email:
        raise HTTPException(status_code=422, detail="email is required")
    blocks = [b.strip() for b in payload.technical_blocks if (b or "").strip()]
    _require_known_blocks(blocks)
    stored = set_approver_blocks(email, blocks)
    return {"email": email, "technical_blocks": stored}


@router.post("/approvers", status_code=201)
async def add_approver(payload: ApproverAdd, request: Request):
    """Add one or more technical-block mappings for an email (admin only)."""
    require_portal_admin(request)
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
    for block in blocks:
        add_approver_mapping(email, block)
    return {"email": email, "technical_blocks": get_approver_blocks(email)}


@router.delete("/approvers/{email}")
async def delete_approver(email: str, request: Request):
    """Remove all mappings for an email (admin only)."""
    require_portal_admin(request)
    normalized = normalize_email(email)
    deleted = delete_approver_mapping(normalized)
    return {"email": normalized, "deleted": deleted}


@router.delete("/approvers/{email}/{technical_block}")
async def delete_approver_block(email: str, technical_block: str, request: Request):
    """Remove one email + technical block mapping (admin only)."""
    require_portal_admin(request)
    normalized = normalize_email(email)
    deleted = delete_approver_mapping(normalized, technical_block)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Approver mapping not found")
    return {"email": normalized, "technical_block": technical_block, "deleted": deleted}
