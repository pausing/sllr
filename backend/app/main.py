"""
SLLR FastAPI application.
"""
import mimetypes
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from starlette.datastructures import Headers
from starlette.responses import Response
from starlette.staticfiles import NotModifiedResponse, StaticFiles
from starlette.types import Scope

from backend.app.routers import lessons, references, kpis, reports, export as export_router, me, approvers
from backend.app.storage import init_store

# Nixpacks/Nix images often have no /etc/mime.types. Without these, FileResponse
# falls back to application/octet-stream and the browser refuses <script type="module">.
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("application/json", ".map")

_ASSET_SUFFIXES = (".js", ".css", ".map", ".svg", ".woff2", ".json")

_MIME_BY_SUFFIX = {
    ".js": "application/javascript",
    ".css": "text/css",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
    ".map": "application/json",
}


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
    repo_root = Path(__file__).resolve().parents[2]
    candidates.append(repo_root / "frontend" / "dist")
    candidates.append(Path("frontend/dist"))
    for path in candidates:
        if path.is_dir() and (path / "index.html").is_file():
            return path.resolve()
    return None


def _base_path() -> str:
    """Get base path for deployment (e.g., /sllr)."""
    return os.environ.get("SLLR_BASE_PATH", "/sllr").rstrip("/")


def _media_type_for(path: Path) -> Optional[str]:
    return _MIME_BY_SUFFIX.get(path.suffix.lower())


def _looks_like_asset(path: str) -> bool:
    return path.lower().endswith(_ASSET_SUFFIXES)


def _safe_static(static_dir: Path, full_path: str) -> Optional[Path]:
    """Safely resolve a file under static_dir."""
    if not static_dir.is_dir():
        return None
    root = static_dir.resolve()
    candidate = (root / full_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if candidate.is_file():
        return candidate
    return None


def _asset_list(static_dir: Optional[Path]) -> list[str]:
    if static_dir is None:
        return []
    assets_dir = static_dir / "assets"
    if not assets_dir.is_dir():
        return []
    return sorted(p.name for p in assets_dir.iterdir() if p.is_file())


class AssetStaticFiles(StaticFiles):
    """StaticFiles that always sends JS/CSS with browser-accepted MIME types."""

    def file_response(
        self,
        full_path,
        stat_result,
        scope: Scope,
        status_code: int = 200,
    ) -> Response:
        media_type = _media_type_for(Path(full_path))
        request_headers = Headers(scope=scope)
        response = FileResponse(
            full_path,
            status_code=status_code,
            stat_result=stat_result,
            media_type=media_type,
        )
        if self.is_not_modified(response.headers, request_headers):
            return NotModifiedResponse(response.headers)
        return response


def _static_info_payload(static_dir: Optional[Path]) -> dict:
    exists = static_dir is not None and static_dir.is_dir()
    return {
        "static_dir": str(static_dir) if static_dir is not None else None,
        "exists": exists,
        "assets": _asset_list(static_dir),
    }


def create_app() -> FastAPI:
    """Build the app so static mounts are registered before any SPA catch-all."""
    static_dir = _resolve_static_dir()
    base_path = _base_path()

    app = FastAPI(
        title="SLLR API",
        description="Structured Lessons Learned Registry API",
        version="2.0.0",
    )
    app.state.static_dir = static_dir
    app.state.base_path = base_path
    init_store()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for prefix in ["/api", f"{base_path}/api"] if base_path else ["/api"]:
        app.include_router(references.router, prefix=prefix, tags=["references"])
        app.include_router(lessons.router, prefix=prefix, tags=["lessons"])
        app.include_router(kpis.router, prefix=prefix, tags=["kpis"])
        app.include_router(reports.router, prefix=prefix, tags=["reports"])
        app.include_router(export_router.router, prefix=prefix, tags=["export"])
        app.include_router(me.router, prefix=prefix, tags=["me"])
        app.include_router(approvers.router, prefix=prefix, tags=["approvers"])

    @app.get("/api/health")
    async def health_root():
        return {"ok": True}

    if base_path:
        @app.get(f"{base_path}/api/health")
        async def health_base():
            return {"ok": True}

    @app.get("/api/static-info")
    async def static_info_root(request: Request):
        return _static_info_payload(request.app.state.static_dir)

    if base_path:
        @app.get(f"{base_path}/api/static-info")
        async def static_info_base(request: Request):
            return _static_info_payload(request.app.state.static_dir)

        @app.get(base_path, include_in_schema=False)
        async def redirect_base_to_slash():
            return RedirectResponse(url=f"{base_path}/", status_code=307)

    if static_dir is not None and static_dir.is_dir():
        assets_dir = static_dir / "assets"
        if assets_dir.is_dir():
            prefixes = ["/assets"]
            if base_path:
                prefixes.append(f"{base_path}/assets")
            for i, prefix in enumerate(dict.fromkeys(prefixes)):
                app.mount(
                    prefix,
                    AssetStaticFiles(directory=str(assets_dir)),
                    name=f"assets-{i}",
                )

        @app.get("/")
        def spa_root():
            return FileResponse(static_dir / "index.html", media_type="text/html")

        if base_path:
            @app.get(f"{base_path}/")
            def spa_base_root():
                return FileResponse(static_dir / "index.html", media_type="text/html")

            @app.get(f"{base_path}/{{full_path:path}}")
            def spa_base_path(full_path: str):
                return _spa_fallback(static_dir, full_path)

        @app.get("/{full_path:path}")
        def spa_path(full_path: str):
            return _spa_fallback(static_dir, full_path)
    else:
        @app.get("/")
        def spa_root_missing():
            raise HTTPException(status_code=404, detail="Static files not configured")

        if base_path:
            @app.get(f"{base_path}/")
            def spa_base_root_missing():
                raise HTTPException(status_code=404, detail="Static files not configured")

    return app


def _spa_fallback(static_dir: Path, full_path: str):
    """Serve real dist files first.

    FastAPI/Starlette path operations beat mounts, so
    ``/sllr/{full_path:path}`` matches ``/sllr/assets/index-HASH.js`` before
    ``app.mount("/sllr/assets", StaticFiles)``. The catch-all must look up the
    file (like pvDesign) instead of 404-ing on ``.js``/``.css`` before
    ``_safe_static``. Mounts are belt-and-suspenders only.
    """
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(status_code=404)
    found = _safe_static(static_dir, full_path)
    if found is not None:
        media_type = _media_type_for(found)
        return FileResponse(found, media_type=media_type)
    if _looks_like_asset(full_path):
        raise HTTPException(status_code=404)
    return FileResponse(static_dir / "index.html", media_type="text/html")


# Module-level app for uvicorn backend.app.main:app
app = create_app()
