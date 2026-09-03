"""
FastAPI REST API Service for ISRO Chandrayaan-2 Registration Pipeline.
SIH PS 26166: Multi-modal, Sun angle and scale invariant image correspondence.
"""

from __future__ import annotations

import base64
import io
from typing import Any, Dict, List, Optional
import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from ch2_lunar_reg.domain.models import SensorModality, SunAngles, TransformationModel
from ch2_lunar_reg.application.pipeline import LunarRegistrationPipeline
from ch2_lunar_reg.infrastructure.synthetic_generator import LunarTerrainSimulator


app = FastAPI(
    title="ISRO Chandrayaan-2 Image Correspondence Engine",
    description="Enterprise REST API for multi-modal, sun angle & scale invariant lunar registration (SIH PS 26166)",
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
