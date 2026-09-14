"""
SLLR FastAPI application.
"""
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse

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
    """Resolve static directory path like pvDesign: env, then repo-root, then cwd."""
    raw = os.environ.get("STATIC_DIR", "").strip()
    candidates = []
    if raw:
        candidates.append(Path(raw))
    # Resolve from repo root using __file__
    repo_root = Path(__file__).resolve().parents[2]
    candidates.append(repo_root / "frontend" / "dist")
    # Fallback to cwd relative
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

# Create single app that serves at both / and BASE_PATH
app = FastAPI(
    title="SLLR API",
    description="Structured Lessons Learned Registry API",
    version="2.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers at both / and BASE_PATH
for prefix in ["/api", f"{BASE_PATH}/api"]:
    app.include_router(references.router, prefix=prefix, tags=["references"])
    app.include_router(lessons.router, prefix=prefix, tags=["lessons"])
    app.include_router(kpis.router, prefix=prefix, tags=["kpis"])
    app.include_router(reports.router, prefix=prefix, tags=["reports"])
    app.include_router(export_router.router, prefix=prefix, tags=["export"])


@app.get("/api/health")
async def health_root():
    """Health check endpoint at /api/health."""
    return {"ok": True}


@app.get(f"{BASE_PATH}/api/health")
async def health_base():
    """Health check endpoint at /sllr/api/health."""
    return {"ok": True}


# Redirect /sllr to /sllr/ (must be before catchall)
@app.get(BASE_PATH, include_in_schema=False)
async def redirect_base_to_slash():
    """Redirect /sllr to /sllr/ like pvDesign."""
    return RedirectResponse(url=f"{BASE_PATH}/", status_code=307)


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
# Serve SPA at both / and BASE_PATH/
if STATIC_DIR is not None and STATIC_DIR.is_dir():

    @app.get("/")
    def spa_root():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get(f"{BASE_PATH}/")
    def spa_base_root():
        return FileResponse(STATIC_DIR / "index.html")

    # Register /sllr/{full_path:path} BEFORE /{full_path:path} so it matches first
    @app.get(f"{BASE_PATH}/{{full_path:path}}")
    def spa_base_path(full_path: str):
        # Don't catch API routes
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        # Try to serve static file
        found = _safe_static(full_path)
        if found is not None:
            return FileResponse(found)
        # Fallback to SPA
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{full_path:path}")
    def spa_path(full_path: str):
        # Don't catch API routes
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        # Try to serve static file
        found = _safe_static(full_path)
        if found is not None:
            return FileResponse(found)
        # Fallback to SPA
        return FileResponse(STATIC_DIR / "index.html")
else:
    # When STATIC_DIR is not available, still provide basic routes

    @app.get("/")
    def spa_root_missing():
        raise HTTPException(status_code=404, detail="Static files not configured")

    @app.get(f"{BASE_PATH}/")
    def spa_base_root_missing():
        raise HTTPException(status_code=404, detail="Static files not configured")
