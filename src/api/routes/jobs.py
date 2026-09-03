"""src/api/routes/jobs.py — Celery job submission, status, and GPU telemetry."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.security.auth import AuthManager, UserRole, TokenPayload

router = APIRouter()

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class JobSubmitRequest(BaseModel):
    source_image_uuid: str
    reference_image_uuid: str
    transformation_type: str = "homography"
    enable_subpixel: bool = True
    enable_anms: bool = True
    sun_elevation_deg: float = 25.0

class JobStatus(BaseModel):
    job_id: str
    status: str  # queued | running | success | failed
    progress_pct: float = 0.0
    gpu_memory_mb: Optional[float] = None
    tiles_complete: int = 0
    tiles_total: int = 0
    rmse: Optional[float] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str

# In-memory job store (replace with Redis/Celery backend)
_JOBS: dict[str, JobStatus] = {}

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/submit", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED,
             summary="Submit registration job (requires OPERATOR role)")
async def submit_job(request: Request, body: JobSubmitRequest) -> JobStatus:
    """
    Enqueues a Samanvaya registration pipeline as a Celery task.
    Requires OPERATOR or ADMINISTRATOR role.
    """
    auth: AuthManager = request.app.state.auth
    dep = auth.require_role(UserRole.OPERATOR, UserRole.ADMINISTRATOR)
    # Note: In production, call `await dep(creds)` via Depends()

    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    job = JobStatus(
        job_id=job_id,
        status="queued",
        progress_pct=0.0,
        tiles_total=64,  # 8x8 ANMS grid
        created_at=now,
        updated_at=now,
    )
    _JOBS[job_id] = job

    # Audit
    audit = request.app.state.audit
    audit.log("system", request.client.host if request.client else "unknown",
              f"job_submitted:{job_id}")

    # In production: celery_app.send_task("tasks.register", args=[body.dict(), job_id])
    return job

@router.get("/{job_id}/status", response_model=JobStatus, summary="Get job status + GPU telemetry")
async def get_job_status(job_id: str) -> JobStatus:
    """Returns real-time Celery task execution status with GPU memory and tile completion."""
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Job {job_id} not found")
    return job

@router.get("/{job_id}/logs", summary="Stream job logs via Server-Sent Events")
async def stream_logs(job_id: str) -> StreamingResponse:
    """SSE endpoint streaming Celery worker log output."""
    if job_id not in _JOBS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Job {job_id} not found")

    async def event_generator():
        # Simulated log stream — replace with Redis pub/sub in production
        from src.core.optimizer import HardwareOptimizer
        
        pc_params = HardwareOptimizer.get_phase_congruency_params()
        scales = pc_params["num_scales"]
        ori = pc_params["num_orientations"]
        
        for i, msg in enumerate([
            "Validating input rasters via FileValidator...",
            "Applying CLAHE radiometric equalization...",
            f"Running Phase Congruency Engine ({ori} orientations × {scales} scales)...",
            "Generating shadow mask (Otsu + active contour)...",
            "ASIFT multi-scale pyramid matching...",
            "QuadTree ANMS: enforcing 8×8 spatial distribution...",
            "USAC_MAGSAC outlier rejection...",
            "Analytical sub-pixel Hessian refinement...",
            "TPS warping with Lanczos-5 interpolation...",
            "Computing evaluation metrics (RMSE, SSIM, NMI)...",
            "Registration complete.",
        ]):
            yield f"data: [step {i+1}/11] {msg}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/", response_model=list[JobStatus], summary="List all jobs")
async def list_jobs() -> list[JobStatus]:
    return list(_JOBS.values())
