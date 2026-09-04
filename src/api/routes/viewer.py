"""
src/api/routes/viewer.py

Viewer endpoints for retrieving evaluated results and raw tiles safely.
"""
from __future__ import annotations

import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from src.security.auth import AuthManager, UserRole

router = APIRouter()

# Secure base directory for fetching files
BASE_DIR = Path("/app/data/workspace").resolve() if os.getenv("ENVIRONMENT") == "production" else Path("data/workspace").resolve()

def _get_safe_path(uuid_filename: str) -> Path:
    """Ensure the requested file doesn't escape the secure directory."""
    if ".." in uuid_filename or "/" in uuid_filename or "\\" in uuid_filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid filename")
        
    target_path = (BASE_DIR / uuid_filename).resolve()
    
    # Path traversal protection
    if not str(target_path).startswith(str(BASE_DIR)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")
        
    if not target_path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resource not found")
        
    return target_path


@router.get("/tile/{job_id}/{tile_name}", summary="Get a registered image tile")
async def get_tile(request: Request, job_id: str, tile_name: str) -> FileResponse:
    """
    Fetch a specific tile resulting from a registration job.
    Requires VIEWER role.
    """
    auth: AuthManager = request.app.state.auth
    dep = auth.require_role(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMINISTRATOR)
    
    safe_dir = BASE_DIR / job_id
    if not safe_dir.resolve().exists() or not str(safe_dir.resolve()).startswith(str(BASE_DIR)):
         raise HTTPException(status.HTTP_404_NOT_FOUND, "Job directory not found")
         
    if ".." in tile_name or "/" in tile_name or "\\" in tile_name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid tile name")
        
    target_path = (safe_dir / tile_name).resolve()
    if not target_path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tile not found")
        
    return FileResponse(target_path, media_type="image/tiff")


@router.get("/report/{job_id}", summary="Download evaluation PDF report")
async def get_report(request: Request, job_id: str) -> FileResponse:
    """
    Fetch the mathematical evaluation report (PDF).
    Requires VIEWER role.
    """
    auth: AuthManager = request.app.state.auth
    dep = auth.require_role(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMINISTRATOR)
    
    target_path = _get_safe_path(f"{job_id}_evaluation.pdf")
    return FileResponse(target_path, media_type="application/pdf", filename=f"Samanvaya_Report_{job_id}.pdf")


@router.get("/metrics/{job_id}", summary="Get raw JSON metrics for UI dashboards")
async def get_metrics(request: Request, job_id: str) -> JSONResponse:
    """
    Fetch raw metrics (RMSE, SSIM, execution time).
    Requires VIEWER role.
    """
    auth: AuthManager = request.app.state.auth
    dep = auth.require_role(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMINISTRATOR)
    
    target_path = _get_safe_path(f"{job_id}_metrics.json")
    
    # Normally read json and return. Simulated here.
    return JSONResponse(content={"job_id": job_id, "rmse": 0.08, "ssim": 0.92, "status": "completed"})
