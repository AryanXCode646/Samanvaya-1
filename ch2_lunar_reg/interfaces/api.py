"""
FastAPI REST API Service for ISRO Chandrayaan-2 Registration Pipeline.
SIH PS 26166: Multi-modal, Sun angle and scale invariant image correspondence.
"""

import asyncio
import base64
import io
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid
import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from ch2_lunar_reg.domain.models import SensorModality, SunAngles, TransformationModel
from ch2_lunar_reg.application.pipeline import LunarRegistrationPipeline
from ch2_lunar_reg.infrastructure.synthetic_generator import LunarTerrainSimulator

logger = logging.getLogger("ch2_lunar_reg.interfaces.api")


class AlignmentWorkerQueue:
    """
    Lightweight asynchronous worker pool ensuring concurrent non-blocking execution.
    """
    def __init__(self, max_concurrent_jobs: int = 4) -> None:
        self.semaphore = asyncio.Semaphore(max_concurrent_jobs)
        self.active_jobs: Dict[str, Dict[str, Any]] = {}

    async def execute_job(self, func, *args, **kwargs):
        async with self.semaphore:
            return await asyncio.to_thread(func, *args, **kwargs)


worker_queue = AlignmentWorkerQueue(max_concurrent_jobs=4)


app = FastAPI(
    title="ISRO Chandrayaan-2 Image Correspondence Engine",
    description="Enterprise REST & WebSocket API for multi-modal, sun angle & scale invariant lunar registration (SIH PS 26166)",
    version="1.0.0",
)


class SunAngleInput(BaseModel):
    azimuth_deg: float = Field(..., ge=0.0, le=360.0, description="Sun azimuth [0, 360]")
    elevation_deg: float = Field(..., ge=-90.0, le=90.0, description="Sun elevation [-90, 90]")


class RegistrationRequest(BaseModel):
    ref_image_b64: Optional[str] = Field(None, description="Base64 encoded PNG/JPEG reference image")
    target_image_b64: Optional[str] = Field(None, description="Base64 encoded PNG/JPEG target image")
    ref_sun: Optional[SunAngleInput] = None
    target_sun: Optional[SunAngleInput] = None
    ref_gsd: float = Field(1.0, gt=0.0, description="Reference GSD (meters/pixel)")
    target_gsd: float = Field(1.0, gt=0.0, description="Target GSD (meters/pixel)")
    transformation_model: TransformationModel = TransformationModel.AFFINE
    enable_anms: bool = True
    enable_subpixel: bool = True
    target_features: int = 500


class SimulateBenchmarkRequest(BaseModel):
    ref_azimuth: float = 60.0
    ref_elevation: float = 25.0
    target_azimuth: float = 240.0  # 180 deg shadow reversal
    target_elevation: float = 35.0
    rotation_deg: float = 4.0
    shift_x: float = 12.5
    shift_y: float = -8.3
    transformation_model: TransformationModel = TransformationModel.AFFINE


class TiePointInput(BaseModel):
    ref_x: float
    ref_y: float
    src_x: float
    src_y: float
    confidence: float = 1.0
    subpixel_refined: bool = True


class ControlPointInput(BaseModel):
    ref_x: float
    ref_y: float
    src_x: float
    src_y: float


class EvaluationApiRequest(BaseModel):
    tie_points: List[TiePointInput]
    transformation_matrix: List[List[float]]
    ground_truth_control_points: Optional[List[ControlPointInput]] = None
    total_matches: Optional[int] = None
    image_shape: Tuple[int, int] = (1024, 1024)


MAX_B64_PAYLOAD_BYTES = 50 * 1024 * 1024  # 50 MiB payload limit


def b64_to_cv2(b64_str: str) -> np.ndarray:
    if len(b64_str) > MAX_B64_PAYLOAD_BYTES * 4 // 3 + 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Payload size exceeds 50MB ceiling",
        )
    try:
        raw = base64.b64decode(b64_str)
        arr = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError("Failed to decode image buffer")
        return img
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid image encoding: {str(e)}")


def cv2_to_b64(img: np.ndarray) -> str:
    uint8_img = (np.clip(img, 0.0, 1.0) * 255.0).astype(np.uint8) if img.dtype != np.uint8 else img
    success, buffer = cv2.imencode(".png", uint8_img)
    if not success:
        return ""
    return base64.b64encode(buffer).decode("utf-8")


@app.get("/health", tags=["Monitoring"])
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "ISRO Chandrayaan-2 Lunar Registration Engine",
        "supported_modalities": [m.value for m in SensorModality],
        "isro_sih_mandate": "Sub-pixel RMSE < 0.4 pixels",
    }


@app.post("/api/v1/simulate-and-register", tags=["Pipeline"])
def simulate_and_register(req: SimulateBenchmarkRequest) -> Dict[str, Any]:
    """
    Simulates high-fidelity lunar crater scene under extreme morning vs afternoon
    shadow inversion and executes full registration pipeline with validation metrics.
    """
    sim = LunarTerrainSimulator(size=(384, 384), seed=42)
    sun_ref = SunAngles(azimuth_deg=req.ref_azimuth, elevation_deg=req.ref_elevation)
    sun_tgt = SunAngles(azimuth_deg=req.target_azimuth, elevation_deg=req.target_elevation)

    img_ref, img_tgt, true_affine, _ = sim.generate_registered_pair_with_ground_truth(
        sun_ref=sun_ref,
        sun_tgt=sun_tgt,
        true_translation=(req.shift_x, req.shift_y),
        true_rotation_deg=req.rotation_deg,
    )

    pipeline = LunarRegistrationPipeline(
        target_features=400,
        enable_photometric_norm=True,
        enable_anms=True,
        enable_subpixel=True,
        transformation_model=req.transformation_model,
    )

    result = pipeline.register(
        ref_image=img_ref,
        target_image=img_tgt,
        ref_sun=sun_ref,
        target_sun=sun_tgt,
    )

    return {
        "status": "success",
        "transformation_model": result.transformation_model.value,
        "metrics": {
            "num_detected_ref": result.metrics.num_detected_ref,
            "num_detected_target": result.metrics.num_detected_target,
            "num_initial_matches": result.metrics.num_initial_matches,
            "num_inliers": result.metrics.num_inliers,
            "inlier_ratio": round(result.metrics.inlier_ratio, 4),
            "rmse_pixels": round(result.metrics.rmse_pixels, 4),
            "mean_residual_pixels": round(result.metrics.mean_residual_pixels, 4),
            "max_residual_pixels": round(result.metrics.max_residual_pixels, 4),
            "spatial_coverage_score": round(result.metrics.spatial_coverage_score, 4),
            "spatial_uniformity_entropy": round(result.metrics.spatial_uniformity_entropy, 4),
            "processing_time_ms": round(result.metrics.processing_time_ms, 2),
            "meets_isro_subpixel_mandate": result.metrics.meets_isro_subpixel_mandate,
        },
        "transform_matrix": result.transform_matrix.tolist() if result.transform_matrix is not None else None,
        "true_affine_matrix": true_affine.tolist(),
        "vector_field": [
            {
                "ref_xy": [round(m.ref_xy[0], 3), round(m.ref_xy[1], 3)],
                "target_xy": [round(m.target_xy[0], 3), round(m.target_xy[1], 3)],
                "dx": round(m.target_xy[0] - m.ref_xy[0], 3),
                "dy": round(m.target_xy[1] - m.ref_xy[1], 3),
                "magnitude": round(float(np.sqrt((m.target_xy[0] - m.ref_xy[0])**2 + (m.target_xy[1] - m.ref_xy[1])**2)), 3),
                "residual_px": round(m.residual_error, 4) if m.residual_error is not None else 0.0,
                "confidence": round(m.confidence, 4),
            }
            for m in result.inliers
        ],
        "warped_target_b64": cv2_to_b64(result.warped_target) if result.warped_target is not None else None,
    }


@app.post("/api/v1/register", tags=["Pipeline"])
def register_images(req: RegistrationRequest) -> Dict[str, Any]:
    """
    Registers arbitrary user-provided reference and target lunar imagery.
    """
    if not req.ref_image_b64 or not req.target_image_b64:
        raise HTTPException(status_code=400, detail="Both ref_image_b64 and target_image_b64 are required.")

    img_ref = b64_to_cv2(req.ref_image_b64)
    img_tgt = b64_to_cv2(req.target_image_b64)

    sun_ref = SunAngles(azimuth_deg=req.ref_sun.azimuth_deg, elevation_deg=req.ref_sun.elevation_deg) if req.ref_sun else None
    sun_tgt = SunAngles(azimuth_deg=req.target_sun.azimuth_deg, elevation_deg=req.target_sun.elevation_deg) if req.target_sun else None

    pipeline = LunarRegistrationPipeline(
        target_features=req.target_features,
        enable_photometric_norm=True,
        enable_anms=req.enable_anms,
        enable_subpixel=req.enable_subpixel,
        transformation_model=req.transformation_model,
    )

    result = pipeline.register(
        ref_image=img_ref,
        target_image=img_tgt,
        ref_sun=sun_ref,
        target_sun=sun_tgt,
        ref_gsd=req.ref_gsd,
        target_gsd=req.target_gsd,
    )

    return {
        "status": "success",
        "metrics": {
            "num_inliers": result.metrics.num_inliers,
            "rmse_pixels": round(result.metrics.rmse_pixels, 4),
            "inlier_ratio": round(result.metrics.inlier_ratio, 4),
            "meets_isro_subpixel_mandate": result.metrics.meets_isro_subpixel_mandate,
        },
        "warped_target_b64": cv2_to_b64(result.warped_target) if result.warped_target is not None else None,
    }


@app.post("/api/v1/evaluate", tags=["Evaluation"])
def evaluate_alignment_metrics(req: EvaluationApiRequest) -> Dict[str, Any]:
    """
    Computes rigorous evaluation metrics (RMSE, Inlier Ratio, Spatial Uniformity)
    from registered tie-points, transformation matrix, and optional control points.
    Returns structured JSON and CSV reports.
    """
    from metrics import evaluate_registration

    tie_pts_dicts = [tp.model_dump() for tp in req.tie_points]
    H_mat = np.array(req.transformation_matrix, dtype=np.float64)

    gt_pts = None
    if req.ground_truth_control_points and len(req.ground_truth_control_points) > 0:
        gt_ref = np.array([[cp.ref_x, cp.ref_y] for cp in req.ground_truth_control_points], dtype=np.float64)
        gt_src = np.array([[cp.src_x, cp.src_y] for cp in req.ground_truth_control_points], dtype=np.float64)
        gt_pts = (gt_ref, gt_src)

    report = evaluate_registration(
        tie_points=tie_pts_dicts,
        transformation_matrix=H_mat,
        ground_truth_control_points=gt_pts,
        total_matches=req.total_matches,
        image_shape=req.image_shape,
    )

    report_dict = report.to_dict()
    # Generate CSV string
    csv_str = report.export_csv("/tmp/eval_tmp.csv") if hasattr(report, "export_csv") else ""

    return {
        "status": "success",
        "report": report_dict,
        "csv_content": csv_str,
    }


@app.websocket("/ws/align")
async def websocket_align(websocket: WebSocket) -> None:
    """
    WebSocket endpoint streaming live alignment progress, frame-by-frame
    tie-point coordinates, and latency metrics across concurrent non-blocking workers.
    """
    await websocket.accept()
    job_id = f"JOB-{uuid.uuid4().hex[:8]}"
    t_init = time.perf_counter()

    try:
        data = await websocket.receive_json()
        mode = data.get("mode", "simulate")

        # Stage 1: Initialization
        await websocket.send_json({
            "job_id": job_id,
            "stage": "INITIALIZATION",
            "progress": 0.10,
            "message": "Connected to Samanvaya Autonomous Core. Validating payload...",
            "latency_ms": round((time.perf_counter() - t_init) * 1000, 2),
        })

        if mode == "simulate":
            ref_azimuth = float(data.get("ref_azimuth", 60.0))
            ref_elevation = float(data.get("ref_elevation", 25.0))
            target_azimuth = float(data.get("target_azimuth", 240.0))
            target_elevation = float(data.get("target_elevation", 35.0))
            rotation_deg = float(data.get("rotation_deg", 4.0))
            shift_x = float(data.get("shift_x", 12.5))
            shift_y = float(data.get("shift_y", -8.3))
            t_model = TransformationModel(data.get("transformation_model", "AFFINE"))

            def run_simulation_sync():
                sim = LunarTerrainSimulator(size=(384, 384), seed=42)
                s_ref = SunAngles(azimuth_deg=ref_azimuth, elevation_deg=ref_elevation)
                s_tgt = SunAngles(azimuth_deg=target_azimuth, elevation_deg=target_elevation)
                i_ref, i_tgt, true_aff, _ = sim.generate_registered_pair_with_ground_truth(
                    sun_ref=s_ref,
                    sun_tgt=s_tgt,
                    true_translation=(shift_x, shift_y),
                    true_rotation_deg=rotation_deg,
                )
                return i_ref, i_tgt, s_ref, s_tgt, true_aff

            img_ref, img_tgt, sun_ref, sun_tgt, true_affine = await worker_queue.execute_job(run_simulation_sync)

        else:
            ref_b64 = data.get("ref_image_b64")
            tgt_b64 = data.get("target_image_b64")
            if not ref_b64 or not tgt_b64:
                await websocket.send_json({"error": "Missing image payloads in register mode."})
                await websocket.close()
                return

            img_ref = await asyncio.to_thread(b64_to_cv2, ref_b64)
            img_tgt = await asyncio.to_thread(b64_to_cv2, tgt_b64)
            sun_ref = (
                SunAngles(azimuth_deg=data["ref_azimuth"], elevation_deg=data["ref_elevation"])
                if "ref_azimuth" in data
                else None
            )
            sun_tgt = (
                SunAngles(azimuth_deg=data["target_azimuth"], elevation_deg=data["target_elevation"])
                if "target_azimuth" in data
                else None
            )
            t_model = TransformationModel(data.get("transformation_model", "AFFINE"))
            true_affine = None

        # Stage 2: Photometric Normalization
        await websocket.send_json({
            "job_id": job_id,
            "stage": "PHOTOMETRIC_NORMALIZATION",
            "progress": 0.30,
            "message": "Applying Lommel-Seeliger lunar photometric normalization & shadow correction...",
            "latency_ms": round((time.perf_counter() - t_init) * 1000, 2),
        })

        # Stage 3: Phase Congruency & Kovesi Moments
        await websocket.send_json({
            "job_id": job_id,
            "stage": "PHASE_CONGRUENCY",
            "progress": 0.55,
            "message": "Computing multi-scale Log-Gabor Phase Congruency & RIFT Maximum Index Maps...",
            "latency_ms": round((time.perf_counter() - t_init) * 1000, 2),
        })

        # Execute Pipeline off-thread
        def run_pipeline_sync():
            pipeline = LunarRegistrationPipeline(
                target_features=int(data.get("target_features", 400)),
                enable_photometric_norm=True,
                enable_anms=True,
                enable_subpixel=True,
                transformation_model=t_model,
            )
            return pipeline.register(
                ref_image=img_ref,
                target_image=img_tgt,
                ref_sun=sun_ref,
                target_sun=sun_tgt,
                ref_gsd=float(data.get("ref_gsd", 1.0)),
                target_gsd=float(data.get("target_gsd", 1.0)),
            )

        result = await worker_queue.execute_job(run_pipeline_sync)

        # Stage 4: Streaming Tie-Points
        serialized_tiepoints = [
            {
                "ref_xy": [round(m.ref_xy[0], 3), round(m.ref_xy[1], 3)],
                "target_xy": [round(m.target_xy[0], 3), round(m.target_xy[1], 3)],
                "residual_px": round(m.residual_error, 4) if m.residual_error is not None else 0.0,
                "confidence": round(m.confidence, 4),
                "sigma_x": round(m.sigma_x, 4) if m.sigma_x is not None else 0.2,
                "sigma_y": round(m.sigma_y, 4) if m.sigma_y is not None else 0.2,
                "weight": round(m.weight, 4) if m.weight is not None else 1.0,
            }
            for m in result.inliers
        ]

        await websocket.send_json({
            "job_id": job_id,
            "stage": "CORRESPONDENCE_STREAM",
            "progress": 0.85,
            "message": f"Correspondence consensus established with {len(result.inliers)} verified inliers.",
            "inliers_count": len(result.inliers),
            "tiepoints": serialized_tiepoints[:50],
            "latency_ms": round((time.perf_counter() - t_init) * 1000, 2),
        })

        # Stage 5: Completion & Metrics
        await websocket.send_json({
            "job_id": job_id,
            "stage": "COMPLETED",
            "progress": 1.00,
            "message": "Mission alignment completed successfully. ISRO mandate criteria evaluated.",
            "metrics": {
                "num_detected_ref": result.metrics.num_detected_ref,
                "num_detected_target": result.metrics.num_detected_target,
                "num_initial_matches": result.metrics.num_initial_matches,
                "num_inliers": result.metrics.num_inliers,
                "inlier_ratio": round(result.metrics.inlier_ratio, 4),
                "rmse_pixels": round(result.metrics.rmse_pixels, 4),
                "mean_residual_pixels": round(result.metrics.mean_residual_pixels, 4),
                "max_residual_pixels": round(result.metrics.max_residual_pixels, 4),
                "spatial_coverage_score": round(result.metrics.spatial_coverage_score, 4),
                "spatial_uniformity_entropy": round(result.metrics.spatial_uniformity_entropy, 4),
                "processing_time_ms": round(result.metrics.processing_time_ms, 2),
                "meets_isro_subpixel_mandate": result.metrics.meets_isro_subpixel_mandate,
            },
            "transform_matrix": result.transform_matrix.tolist() if result.transform_matrix is not None else None,
            "true_affine_matrix": true_affine.tolist() if true_affine is not None else None,
            "tiepoints_total": len(result.inliers),
            "latency_ms": round((time.perf_counter() - t_init) * 1000, 2),
        })

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket alignment job {job_id}: {e}")
        try:
            await websocket.send_json({"stage": "FAILED", "error": str(e)})
        except Exception:
            pass
