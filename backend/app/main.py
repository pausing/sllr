"""
SLLR FastAPI application.
"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.routers import lessons, references, kpis, reports, export as export_router


# Environment configuration
STATIC_DIR = os.getenv("STATIC_DIR", "frontend/dist")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
ROOT_PATH = os.getenv("SLLR_ROOT_PATH", "")

app = FastAPI(
    title="SLLR API",
    description="Structured Lessons Learned Registry API",
    version="2.0.0",
    root_path=ROOT_PATH,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(references.router, prefix="/api", tags=["references"])
app.include_router(lessons.router, prefix="/api", tags=["lessons"])
app.include_router(kpis.router, prefix="/api", tags=["kpis"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(export_router.router, prefix="/api", tags=["export"])


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"ok": True}


# Static file serving (production)
static_path = Path(STATIC_DIR)
if static_path.exists() and static_path.is_dir():
    # Mount static assets
    app.mount("/assets", StaticFiles(directory=static_path / "assets"), name="assets")
    
    # SPA fallback: serve index.html for all non-API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api/"):
            return {"error": "Not found"}, 404
        
        # Serve index.html for SPA routing
        index_file = static_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        
        return {"error": "Frontend not built"}, 404
