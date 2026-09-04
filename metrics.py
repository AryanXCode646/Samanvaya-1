"""
Samanvaya: Autonomous Lunar Optical Image Registration & Correspondence Framework
ISRO SIH PS 26166 — Phase 1 Comprehensive Evaluation Metric Dashboard.

Computes:
1. RMSE (Root Mean Square Error) of ground-truth control points and registered tie-points:
   RMSE = sqrt( (1 / N) * sum( ||x_ref - H * x_src||^2 ) )
2. Inlier Match Count and Inlier Ratio (%) post-RANSAC outlier rejection:
   Inlier Ratio (%) = (Inlier Count / Total Matches) * 100
3. Spatial Distribution Uniformity Score:
   Normalized 2D Shannon Spatial Entropy (H_spatial in [0.0, 1.0]) across grid cells
   to quantify non-clumping and uniform coverage across crater fields.
4. Clean export to structured JSON (evaluation_report.json) and CSV (evaluation_report.csv).
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("samanvaya.metrics")


@dataclass
class EvaluationReport:
    """
    Structured Evaluation Metric Report for Lunar Optical Registration.
    """
    total_matches: int
    inlier_count: int
    inlier_ratio_percent: float
    rmse_pixels: float
    spatial_uniformity_score: float
    mean_residual_pixels: float
    median_residual_pixels: float
    max_residual_pixels: float
    std_residual_pixels: float
    ce90_pixels: float
    meets_isro_mandate: bool
    control_point_rmse_pixels: Optional[float] = None
    processing_time_ms: float = 0.0
    transformation_matrix: Optional[List[List[float]]] = None
    tie_points: List[Dict[str, Any]] = field(default_factory=list)
    image_shape: Tuple[int, int] = (1024, 1024)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serializes report into clean dictionary."""
        return {
            "metadata": {
                "framework": "Samanvaya (समान्वय)",
                "mission": "ISRO Chandrayaan-2 Planetary Remote Sensing",
                "problem_statement": "SIH PS 26166",
                "timestamp_utc": self.timestamp,
                "isro_mandate_threshold_px": 0.40,
            },
            "metrics": {
                "total_matches": self.total_matches,
                "inlier_count": self.inlier_count,
                "inlier_ratio_percent": round(self.inlier_ratio_percent, 2),
                "rmse_pixels": round(self.rmse_pixels, 4),
                "control_point_rmse_pixels": (
                    round(self.control_point_rmse_pixels, 4)
                    if self.control_point_rmse_pixels is not None
                    else None
                ),
                "spatial_uniformity_score": round(self.spatial_uniformity_score, 4),
                "mean_residual_pixels": round(self.mean_residual_pixels, 4),
                "median_residual_pixels": round(self.median_residual_pixels, 4),
                "max_residual_pixels": round(self.max_residual_pixels, 4),
                "std_residual_pixels": round(self.std_residual_pixels, 4),
                "ce90_pixels": round(self.ce90_pixels, 4),
                "meets_isro_mandate": self.meets_isro_mandate,
                "processing_time_ms": round(self.processing_time_ms, 2),
                "image_shape_hw": list(self.image_shape),
            },
            "transformation_matrix": self.transformation_matrix,
            "tie_points_count": len(self.tie_points),
            "tie_points": self.tie_points,
        }

    def export_json(self, output_path: Union[str, Path] = "evaluation_report.json", indent: int = 2) -> str:
        """Exports report to structured JSON format."""
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(self.to_dict(), indent=indent)
        out_file.write_text(content, encoding="utf-8")
        logger.info(f"Exported JSON evaluation report to: {out_file.resolve()}")
        return content

    def export_csv(self, output_path: Union[str, Path] = "evaluation_report.csv") -> str:
        """Exports report summary metrics and tie-point residuals to CSV format."""
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        lines: List[str] = [
            "# SAMANVAYA ISRO SIH PS 26166 PLANETARY REGISTRATION EVALUATION REPORT",
            "# Metric,Value,Unit",
            f"total_matches,{self.total_matches},count",
            f"inlier_count,{self.inlier_count},count",
            f"inlier_ratio_percent,{self.inlier_ratio_percent:.2f},%",
            f"rmse_pixels,{self.rmse_pixels:.4f},pixels",
            f"control_point_rmse_pixels,{f'{self.control_point_rmse_pixels:.4f}' if self.control_point_rmse_pixels is not None else 'N/A'},pixels",
            f"spatial_uniformity_score,{self.spatial_uniformity_score:.4f},normalized_shannon",
            f"mean_residual_pixels,{self.mean_residual_pixels:.4f},pixels",
            f"median_residual_pixels,{self.median_residual_pixels:.4f},pixels",
            f"max_residual_pixels,{self.max_residual_pixels:.4f},pixels",
            f"std_residual_pixels,{self.std_residual_pixels:.4f},pixels",
            f"ce90_pixels,{self.ce90_pixels:.4f},pixels",
            f"meets_isro_mandate,{self.meets_isro_mandate},boolean",
            f"processing_time_ms,{self.processing_time_ms:.2f},ms",
            "#",
            "# TIE POINT RESIDUAL TABLE",
            "id,ref_x,ref_y,src_x,src_y,reprojected_ref_x,reprojected_ref_y,residual_pixels,confidence,subpixel_refined",
        ]
        for pt in self.tie_points:
            lines.append(
                f"{pt.get('id', 0)},{pt.get('ref_x', 0.0):.3f},{pt.get('ref_y', 0.0):.3f},"
                f"{pt.get('src_x', 0.0):.3f},{pt.get('src_y', 0.0):.3f},"
                f"{pt.get('reprojected_ref_x', 0.0):.3f},{pt.get('reprojected_ref_y', 0.0):.3f},"
                f"{pt.get('residual_pixels', 0.0):.4f},{pt.get('confidence', 1.0):.4f},{pt.get('subpixel_refined', False)}"
            )
        csv_str = "\n".join(lines) + "\n"
        out_file.write_text(csv_str, encoding="utf-8")
        logger.info(f"Exported CSV evaluation report to: {out_file.resolve()}")
        return csv_str


def compute_inlier_stats(total_matches: int, inlier_count: int) -> Tuple[int, float]:
    """
    Computes inlier count and inlier ratio percentage:
        Inlier Ratio (%) = (Inlier Count / Total Matches) * 100.
    """
    if total_matches <= 0:
        return 0, 0.0
    safe_inliers = max(0, min(inlier_count, total_matches))
    ratio = float(safe_inliers / total_matches) * 100.0
    return safe_inliers, ratio


def compute_projective_reprojection(
    ref_pts: np.ndarray,
    src_pts: np.ndarray,
    H: np.ndarray,
) -> Tuple[float, np.ndarray, np.ndarray]:
    """
    Computes projective transformation reprojection and RMSE:
        x_proj = H * [x_src, 1]^T
        residual_i = ||x_ref_i - x_proj_i||
        RMSE = sqrt( 1/N * sum( residual_i^2 ) )
    """
    ref_pts = np.asarray(ref_pts, dtype=np.float64)
    src_pts = np.asarray(src_pts, dtype=np.float64)
    n = len(ref_pts)

    if n == 0 or H is None:
        return 999.0, np.array([]), np.array([])

    if H.shape == (2, 3):
        src_h = np.hstack([src_pts, np.ones((n, 1), dtype=np.float64)])
        reproj = src_h @ H.T
    elif H.shape == (3, 3):
        src_h = np.hstack([src_pts, np.ones((n, 1), dtype=np.float64)])
        proj = (H @ src_h.T).T
        denom = proj[:, 2:3]
        denom = np.where(np.abs(denom) < 1e-9, 1e-9, denom)
        reproj = proj[:, :2] / denom
    else:
        raise ValueError(f"Transformation matrix must be 2x3 (affine) or 3x3 (homography), got {H.shape}")

    residuals = np.linalg.norm(ref_pts - reproj, axis=1)
    rmse = float(np.sqrt(np.mean(residuals**2)))
    return rmse, residuals, reproj


def compute_control_points_rmse(
    ground_truth_ref: np.ndarray,
    ground_truth_src: np.ndarray,
    H: np.ndarray,
) -> float:
    """
    Computes Root Mean Square Error (RMSE) against ground-truth control points:
        RMSE_CP = sqrt( 1/N * sum( ||x_gt_ref - H * x_gt_src||^2 ) )
    """
    rmse, _, _ = compute_projective_reprojection(ground_truth_ref, ground_truth_src, H)
    return rmse


def compute_spatial_uniformity_score(
    keypoints: np.ndarray,
    image_shape: Tuple[int, int] = (1024, 1024),
    grid_bins: int = 8,
) -> float:
    """
    Computes 2D Shannon Spatial Entropy across image grid cells:
        H_spatial = - sum_{k=1}^K p_k * log2(p_k) / log2(K)
    Scores range from 0.0 (all points clustered in single crater) to 1.0 (perfect spatial spread).
    """
    keypoints = np.asarray(keypoints, dtype=np.float64)
    if len(keypoints) == 0:
        return 0.0

    h, w = image_shape[:2]
    if h <= 0 or w <= 0:
        h = max(1.0, float(np.max(keypoints[:, 1]) + 1.0))
        w = max(1.0, float(np.max(keypoints[:, 0]) + 1.0))

    hist, _, _ = np.histogram2d(
        keypoints[:, 1], keypoints[:, 0],
        bins=grid_bins,
        range=[[0, h], [0, w]],
    )
    counts = hist.flatten()
    total = np.sum(counts)
    if total == 0:
        return 0.0

    probs = counts[counts > 0] / total
    entropy = -np.sum(probs * np.log2(probs))
    max_entropy = np.log2(grid_bins * grid_bins)
    return float(np.clip(entropy / max_entropy, 0.0, 1.0))


def evaluate_registration(
    tie_points: List[Dict[str, Any]],
    transformation_matrix: Optional[np.ndarray],
    ground_truth_control_points: Optional[Tuple[np.ndarray, np.ndarray]] = None,
    total_matches: Optional[int] = None,
    image_shape: Tuple[int, int] = (1024, 1024),
    processing_time_ms: float = 0.0,
) -> EvaluationReport:
    """
    Comprehensive evaluation routine taking registered tie-points, transformation matrix,
    and optional ground-truth control points, returning an EvaluationReport.
    """
    inlier_count = len(tie_points)
    if total_matches is None or total_matches < inlier_count:
        total_matches = inlier_count

    _, inlier_ratio_pct = compute_inlier_stats(total_matches, inlier_count)

    control_point_rmse: Optional[float] = None
    if ground_truth_control_points is not None and transformation_matrix is not None:
        gt_ref, gt_src = ground_truth_control_points
        control_point_rmse = compute_control_points_rmse(gt_ref, gt_src, transformation_matrix)

    if inlier_count >= 4 and transformation_matrix is not None:
        ref_pts = np.array([[pt["ref_x"], pt["ref_y"]] for pt in tie_points], dtype=np.float64)
        src_pts = np.array([[pt["src_x"], pt["src_y"]] for pt in tie_points], dtype=np.float64)

        rmse, residuals, reproj_ref = compute_projective_reprojection(
            ref_pts, src_pts, transformation_matrix
        )

        mean_res = float(np.mean(residuals))
        median_res = float(np.median(residuals))
        max_res = float(np.max(residuals))
        std_res = float(np.std(residuals))
        ce90 = float(np.percentile(residuals, 90))
        entropy = compute_spatial_uniformity_score(ref_pts, image_shape, grid_bins=8)

        # Enhance tie points with reprojected coordinates and individual residuals
        formatted_tie_points: List[Dict[str, Any]] = []
        for i, pt in enumerate(tie_points):
            formatted_tie_points.append({
                "id": pt.get("id", i),
                "ref_x": float(pt["ref_x"]),
                "ref_y": float(pt["ref_y"]),
                "src_x": float(pt["src_x"]),
                "src_y": float(pt["src_y"]),
                "reprojected_ref_x": float(reproj_ref[i, 0]),
                "reprojected_ref_y": float(reproj_ref[i, 1]),
                "residual_pixels": float(residuals[i]),
                "confidence": float(pt.get("confidence", 1.0)),
                "subpixel_refined": bool(pt.get("subpixel_refined", True)),
            })

        meets_mandate = bool(rmse < 0.40 and inlier_count >= 4)
        h_list = transformation_matrix.tolist()
    else:
        # Fallback if fewer than 4 inliers
        rmse = 999.0
        mean_res = 999.0
        median_res = 999.0
        max_res = 999.0
        std_res = 0.0
        ce90 = 999.0
        entropy = 0.0
        meets_mandate = False
        formatted_tie_points = tie_points
        h_list = transformation_matrix.tolist() if transformation_matrix is not None else None

    return EvaluationReport(
        total_matches=total_matches,
        inlier_count=inlier_count,
        inlier_ratio_percent=inlier_ratio_pct,
        rmse_pixels=rmse,
        spatial_uniformity_score=entropy,
        mean_residual_pixels=mean_res,
        median_residual_pixels=median_res,
        max_residual_pixels=max_res,
        std_residual_pixels=std_res,
        ce90_pixels=ce90,
        meets_isro_mandate=meets_mandate,
        control_point_rmse_pixels=control_point_rmse,
        processing_time_ms=processing_time_ms,
        transformation_matrix=h_list,
        tie_points=formatted_tie_points,
        image_shape=image_shape,
    )


def run_standalone_evaluation_demo(
    json_path: str = "evaluation_report.json",
    csv_path: str = "evaluation_report.csv",
) -> EvaluationReport:
    """
    Generates high-precision synthetic ground-truth control points and tie-point pairs,
    runs full evaluation, and writes JSON and CSV reports.
    """
    np.random.seed(42)
    logger.info("Running Samanvaya Phase 1 Comprehensive Evaluation Metric Dashboard Demo...")

    # True affine transformation: rotation 3.5 deg, translation (14.2, -8.7)
    theta = np.radians(3.5)
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    true_H = np.array([
        [cos_t, -sin_t, 14.2],
        [sin_t,  cos_t, -8.7],
        [0.0,    0.0,    1.0],
    ], dtype=np.float64)

    # 1. Ground-Truth Control Points (e.g. 16 well-surveyed lunar landmarks)
    gt_src_x = np.linspace(100, 900, 4)
    gt_src_y = np.linspace(100, 900, 4)
    gx, gy = np.meshgrid(gt_src_x, gt_src_y)
    gt_src = np.column_stack([gx.ravel(), gy.ravel()])
    gt_src_h = np.hstack([gt_src, np.ones((len(gt_src), 1))])
    gt_ref = (true_H @ gt_src_h.T).T[:, :2]

    # 2. Registered Inlier Tie Points (64 points with sub-pixel Gaussian perturbation sigma=0.15 px)
    tie_src = np.random.uniform(80, 940, size=(64, 2))
    tie_src_h = np.hstack([tie_src, np.ones((len(tie_src), 1))])
    tie_ref_ideal = (true_H @ tie_src_h.T).T[:, :2]
    perturbation = np.random.normal(0.0, 0.15, size=tie_ref_ideal.shape)
    tie_ref = tie_ref_ideal + perturbation

    tie_points: List[Dict[str, Any]] = [
        {
            "id": i,
            "ref_x": float(tie_ref[i, 0]),
            "ref_y": float(tie_ref[i, 1]),
            "src_x": float(tie_src[i, 0]),
            "src_y": float(tie_src[i, 1]),
            "confidence": float(np.random.uniform(0.85, 0.99)),
            "subpixel_refined": True,
        }
        for i in range(len(tie_ref))
    ]

    total_matches = 80  # 64 inliers out of 80 initial matches = 80% inlier ratio

    # Run evaluation
    report = evaluate_registration(
        tie_points=tie_points,
        transformation_matrix=true_H,
        ground_truth_control_points=(gt_ref, gt_src),
        total_matches=total_matches,
        image_shape=(1024, 1024),
        processing_time_ms=132.5,
    )

    # Export structured JSON and CSV
    report.export_json(json_path)
    report.export_csv(csv_path)

    # Pretty-print summary scorecard to stdout
    print("\n" + "=" * 70)
    print(" SAMANVAYA ISRO SIH PS 26166 — REGISTRATION EVALUATION SCORECARD")
    print("=" * 70)
    print(f" Total Candidate Matches       : {report.total_matches}")
    print(f" Post-RANSAC Inliers           : {report.inlier_count}")
    print(f" Inlier Ratio                  : {report.inlier_ratio_percent:.2f}%")
    print(f" Sub-Pixel Tie Point RMSE      : {report.rmse_pixels:.4f} pixels")
    print(f" Control Point RMSE            : {report.control_point_rmse_pixels:.4f} pixels")
    print(f" Spatial Uniformity Score      : {report.spatial_uniformity_score:.4f} (Shannon Entropy H)")
    print(f" Mean Residual Error           : {report.mean_residual_pixels:.4f} pixels")
    print(f" Median Residual Error         : {report.median_residual_pixels:.4f} pixels")
    print(f" Max Residual Error            : {report.max_residual_pixels:.4f} pixels")
    print(f" Circular Error (CE90)         : {report.ce90_pixels:.4f} pixels")
    mandate_badge = "[PASSED] (< 0.40 px)" if report.meets_isro_mandate else "[FAILED] (>= 0.40 px)"
    print(f" ISRO Sub-Pixel Mandate Check  : {mandate_badge}")
    print(f" Structured Reports Generated  : {json_path}, {csv_path}")
    print("=" * 70 + "\n")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Samanvaya Evaluation Metric Dashboard CLI")
    parser.add_argument("--json", default="evaluation_report.json", help="Path to output JSON report")
    parser.add_argument("--csv", default="evaluation_report.csv", help="Path to output CSV report")
    args = parser.parse_args()

    run_standalone_evaluation_demo(json_path=args.json, csv_path=args.csv)
