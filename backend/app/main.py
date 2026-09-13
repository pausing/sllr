"""
SLLR FastAPI application.
"""
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.app.routers import lessons, references, kpis, reports, export as export_router


def _cors_origins() -> list[str]:
    """Build CORS origins list including portal and local dev."""
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://portal.powerlearn.us",
    ]
    extra = os.environ.get("CORS_ORIGINS", "")
    for part in extra.split(","):
        origin = part.strip().rstrip("/")
        if origin and origin not in origins:
            origins.append(origin)
    return origins


def _resolve_static_dir() -> Optional[Path]:
    """Resolve static directory path."""
    raw = os.environ.get("STATIC_DIR", "").strip()
    candidates = []
    if raw:
        candidates.append(Path(raw))
    candidates.append(Path("frontend/dist"))
    for path in candidates:
        if path.is_dir() and (path / "index.html").is_file():
            return path
    return None


STATIC_DIR = _resolve_static_dir()


def _base_path() -> str:
    """Get base path for deployment (e.g., /sllr)."""
    return os.environ.get("SLLR_BASE_PATH", "/sllr").rstrip("/")


BASE_PATH = _base_path()

# Create API application with all routes
api_app = FastAPI(
    title="SLLR API",
    description="Structured Lessons Learned Registry API",
    version="2.0.0",
)

# CORS
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
api_app.include_router(references.router, prefix="/api", tags=["references"])
api_app.include_router(lessons.router, prefix="/api", tags=["lessons"])
api_app.include_router(kpis.router, prefix="/api", tags=["kpis"])
api_app.include_router(reports.router, prefix="/api", tags=["reports"])
api_app.include_router(export_router.router, prefix="/api", tags=["export"])


@api_app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"ok": True}


def _safe_static(full_path: str) -> Optional[Path]:
    """Safely resolve static file path."""
    if STATIC_DIR is None or not STATIC_DIR.is_dir():
        return None
    root = STATIC_DIR.resolve()
    candidate = (root / full_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if candidate.is_file():
        return candidate
    return None


# Static file serving (production) - SPA fallback for all non-API routes
if STATIC_DIR is not None and STATIC_DIR.is_dir():

    @api_app.get("/")
    def spa_root():
        return FileResponse(STATIC_DIR / "index.html")

    @api_app.get("/{full_path:path}")
    def spa_path(full_path: str):
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        found = _safe_static(full_path)
        if found is not None:
            return FileResponse(found)
        return FileResponse(STATIC_DIR / "index.html")


# Main app that mounts api_app at BASE_PATH
app = FastAPI(title="SLLR", version="2.0.0")
app.mount(BASE_PATH, api_app)
