from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.auth.router import router as auth_router
from app.cases.router import router as cases_router
from app.evidence.router import router as evidence_router
from app.observations.router import router as observations_router
from app.entities.router import router as entities_router
from app.timelines.router import router as timelines_router
from app.gap_conflict.router import router as gap_conflict_router
from app.findings.router import router as findings_router
from app.reconstruction.router import router as reconstruction_router
from app.verification.router import router as verification_router
from app.copilot.router import router as copilot_router
from app.reports.router import router as reports_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    description="Reality Reconstruction Engine (RRE) — Evidence Intelligence & Reconstruction Platform for Theft Investigations",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.department_engines.router import router as engines_router

app.include_router(auth_router)
app.include_router(cases_router)
app.include_router(engines_router)
app.include_router(evidence_router)
app.include_router(observations_router)
app.include_router(entities_router)
app.include_router(timelines_router)
app.include_router(gap_conflict_router)
app.include_router(findings_router)
app.include_router(reconstruction_router)
app.include_router(verification_router)
app.include_router(copilot_router)
app.include_router(reports_router)

# Mount Frontend / Static Files
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
frontend_assets = os.path.join(frontend_dist, "assets")
static_dir = os.path.join(os.path.dirname(__file__), "static")

if os.path.exists(frontend_assets):
    app.mount("/assets", StaticFiles(directory=frontend_assets), name="frontend-assets")
elif os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", tags=["UI"])
async def serve_dashboard():
    # Check for Vite built frontend first
    dist_index = os.path.join(frontend_dist, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    # Check for legacy static index
    legacy_index = os.path.join(static_dir, "index.html")
    if os.path.exists(legacy_index):
        return FileResponse(legacy_index)
    return {"message": "RRE 2.0 API is running. UI dist/index.html not found."}

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "storage_backend": settings.STORAGE_BACKEND
    }

@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    # Check if a static file in dist matches (e.g. favicon.svg, icons.svg)
    candidate = os.path.join(frontend_dist, full_path)
    if os.path.isfile(candidate):
        return FileResponse(candidate)
    
    # Check for Vite built frontend index.html for client-side routing
    dist_index = os.path.join(frontend_dist, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    
    # Check for legacy static index
    legacy_index = os.path.join(static_dir, "index.html")
    if os.path.exists(legacy_index):
        return FileResponse(legacy_index)
        
    return Response(content="Not Found", status_code=404)

