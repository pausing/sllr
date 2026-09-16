"""Portal ForwardAuth identity headers (LearnPower).

Headers are optional on reads. On writes, Owner defaults to the portal email
when the client omits it.
"""
from typing import Any, Optional

from fastapi import HTTPException, Request

HEADER_USER_ID = "X-Powerlearn-User-Id"
HEADER_EMAIL = "X-Powerlearn-Email"
HEADER_ADMIN = "X-Powerlearn-Admin"


def _header(request: Request, name: str) -> Optional[str]:
    value = request.headers.get(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def portal_identity(request: Request) -> dict[str, Any]:
    """Return portal identity from ForwardAuth headers, or nulls if missing."""
    admin_raw = _header(request, HEADER_ADMIN)
    admin: Optional[bool]
    if admin_raw is None:
        admin = None
    else:
        admin = admin_raw.lower() in ("1", "true", "yes")
    return {
        "user_id": _header(request, HEADER_USER_ID),
        "email": _header(request, HEADER_EMAIL),
        "admin": admin,
    }


def normalize_email(email: Optional[str]) -> str:
    return (email or "").strip().lower()


def is_portal_admin(request: Request) -> bool:
    return portal_identity(request)["admin"] is True


def emails_match(left: Optional[str], right: Optional[str]) -> bool:
    """True when both values normalize to the same non-empty email."""
    a = normalize_email(left)
    b = normalize_email(right)
    return bool(a) and a == b


def can_edit_lesson(request: Request, owner: Optional[str]) -> bool:
    """Portal admin or the lesson Owner (case-insensitive, trimmed email)."""
    if is_portal_admin(request):
        return True
    return emails_match(portal_identity(request).get("email"), owner)


def require_lesson_editor(request: Request, owner: Optional[str]) -> dict[str, Any]:
    ident = portal_identity(request)
    if can_edit_lesson(request, owner):
        return ident
    raise HTTPException(
        status_code=403,
        detail="Only the lesson owner or a portal admin can edit this lesson.",
    )


def require_portal_admin(request: Request, detail: str | None = None) -> dict[str, Any]:
    ident = portal_identity(request)
    if ident["admin"] is not True:
        raise HTTPException(
            status_code=403,
            detail=detail or "Portal admin required.",
        )
    return ident


def resolve_owner(
    provided: Optional[str],
    request: Request,
    existing: Optional[str] = None,
) -> str:
    """Prefer an explicit Owner; otherwise keep existing; else portal email."""
    if provided is not None and str(provided).strip():
        return str(provided).strip()
    if provided is None and existing and str(existing).strip():
        return str(existing).strip()
    email = portal_identity(request)["email"]
    if email:
        return email
    if existing:
        return str(existing).strip()
    return (provided or "").strip()
