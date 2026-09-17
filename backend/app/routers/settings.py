"""Admin Settings: CRUD for live technical blocks and project phases."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.app.activity import changed_values, log_activity
from backend.app.identity import require_portal_admin
from backend.app.storage import (
    create_vocab,
    delete_vocab,
    list_all_vocab,
    list_vocab,
    reorder_vocab,
    update_vocab,
)
from src.sllr.store import EDITABLE_VOCAB_KINDS

router = APIRouter()

_ADMIN = "Portal admin required to manage settings."


class VocabCreate(BaseModel):
    code: str
    label: Optional[str] = None
    sort_order: Optional[int] = None


class VocabUpdate(BaseModel):
    code: Optional[str] = None
    label: Optional[str] = None
    active: Optional[bool] = None
    sort_order: Optional[int] = None


class VocabReorder(BaseModel):
    codes: list[str] = Field(default_factory=list)


def _kind_or_404(kind: str) -> str:
    key = (kind or "").strip()
    if key not in EDITABLE_VOCAB_KINDS:
        raise HTTPException(status_code=404, detail=f"Unknown vocab kind: {kind}")
    return key


def _http_from_value_error(exc: ValueError) -> HTTPException:
    message = str(exc)
    status = 409 if "already exists" in message.lower() else 422
    return HTTPException(status_code=status, detail=message)


@router.get("/settings/vocab")
async def get_all_vocab(request: Request):
    require_portal_admin(request, _ADMIN)
    return list_all_vocab(include_inactive=True)


@router.get("/settings/vocab/{kind}")
async def get_vocab(kind: str, request: Request):
    require_portal_admin(request, _ADMIN)
    key = _kind_or_404(kind)
    return {"kind": key, "items": list_vocab(key, include_inactive=True)}


@router.post("/settings/vocab/{kind}", status_code=201)
async def add_vocab(kind: str, payload: VocabCreate, request: Request):
    require_portal_admin(request, _ADMIN)
    key = _kind_or_404(kind)
    try:
        item = create_vocab(key, payload.code, payload.label, payload.sort_order)
    except ValueError as exc:
        raise _http_from_value_error(exc) from exc
    log_activity(
        request,
        "vocab_create",
        entity_type="vocab",
        entity_id=f"{key}:{item['code']}",
        values={"after": item},
    )
    return item


@router.put("/settings/vocab/{kind}/order")
async def order_vocab(kind: str, payload: VocabReorder, request: Request):
    require_portal_admin(request, _ADMIN)
    key = _kind_or_404(kind)
    before = [row["code"] for row in list_vocab(key, include_inactive=True)]
    try:
        items = reorder_vocab(key, payload.codes)
    except ValueError as exc:
        raise _http_from_value_error(exc) from exc
    after = [row["code"] for row in items]
    log_activity(
        request,
        "vocab_reorder",
        entity_type="vocab",
        entity_id=key,
        values={"before": before, "after": after},
    )
    return {"kind": key, "items": items}


@router.patch("/settings/vocab/{kind}/{code}")
async def patch_vocab(kind: str, code: str, payload: VocabUpdate, request: Request):
    require_portal_admin(request, _ADMIN)
    key = _kind_or_404(kind)
    before = next((row for row in list_vocab(key, include_inactive=True) if row["code"] == code), None)
    try:
        item = update_vocab(
            key,
            code,
            new_code=payload.code,
            label=payload.label,
            active=payload.active,
            sort_order=payload.sort_order,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise _http_from_value_error(exc) from exc
    log_activity(
        request,
        "vocab_update",
        entity_type="vocab",
        entity_id=f"{key}:{item['code']}",
        values={"before": before, "after": item, "changed": changed_values(before, item)},
    )
    return item


@router.delete("/settings/vocab/{kind}/{code}")
async def remove_vocab(kind: str, code: str, request: Request):
    require_portal_admin(request, _ADMIN)
    key = _kind_or_404(kind)
    before = next((row for row in list_vocab(key, include_inactive=True) if row["code"] == code), None)
    deleted = delete_vocab(key, code)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Vocab code not found")
    log_activity(
        request,
        "vocab_delete",
        entity_type="vocab",
        entity_id=f"{key}:{code}",
        values={"before": before, "deleted": deleted},
    )
    return {"kind": key, "code": code, "deleted": deleted}
