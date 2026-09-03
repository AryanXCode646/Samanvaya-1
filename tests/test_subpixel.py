"""
Unit Tests for Curvature-Based Sub-Pixel Covariance Matrices and Cartographic Bundle Adjustment Exporter.
Verifies AnalyticalSubpixelRefiner Hessian inversion, directional uncertainty (sigma_x, sigma_y),
weight scaling, and USGS ISIS3 jigsaw GCP CSV compatibility.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import cv2
import numpy as np
import pytest

from lunar_core.models import KeypointMatch
from lunar_core.postprocessing.subpixel import (
    AnalyticalSubpixelRefiner,
    SubpixelSurfaceFit,
)
from lunar_core.data_io.raster_writer import PlanetaryRasterWriter


def create_synthetic_quadratic_patch(
    a: float,
    b: float,
    c: float = 0.0,
    d: float = 0.0,
    e: float = 0.0,
    f: float = 1.0,
) -> np.ndarray:
    """
    Evaluates 2D quadratic patch f(x, y) = a*x^2 + b*y^2 + c*x*y + d*x + e*y + f
    over 3x3 integer grid centered at (0, 0) with coordinates in {-1, 0, 1}.
    """
    patch = np.zeros((3, 3), dtype=np.float32)
    for r_idx, y in enumerate([-1.0, 0.0, 1.0]):
        for c_idx, x in enumerate([-1.0, 0.0, 1.0]):
            patch[r_idx, c_idx] = a * x**2 + b * y**2 + c * x * y + d * x + e * y + f
    return patch


class TestCurvatureSubpixelCovariance:
    """Tests for Hessian inversion, uncertainty derivation, and weight computation."""

    def test_analytical_covariance_mathematics(self):
        a, b, c = -2.5, -2.0, 0.4
        d, e, f = 0.2, -0.1, 10.0
        patch = create_synthetic_quadratic_patch(a, b, c, d, e, f)

        refiner = AnalyticalSubpixelRefiner()
        fit = refiner.fit_quadratic_surface(patch)

        assert fit is not None
        assert isinstance(fit, SubpixelSurfaceFit)

        # Theoretical Hessian: H = [[2a, c], [c, 2b]]
        det_h = 4.0 * a * b - c**2
        expected_dx = (-2.0 * b * d + c * e) / det_h
        expected_dy = (-2.0 * a * e + c * d) / det_h
        assert np.isclose(fit.dx, expected_dx, atol=1e-4)
        assert np.isclose(fit.dy, expected_dy, atol=1e-4)

        # Theoretical Inverse Hessian:
        # H_inv = (1 / det_H) * [[2b, -c], [-c, 2a]]
        expected_var_x = abs((2.0 * b) / det_h)
        expected_var_y = abs((2.0 * a) / det_h)
        expected_cov_xy = -c / det_h
        expected_weight = np.sqrt(det_h)

        assert np.isclose(fit.sigma_x, np.sqrt(expected_var_x), atol=1e-4)
        assert np.isclose(fit.sigma_y, np.sqrt(expected_var_y), atol=1e-4)
        assert np.isclose(fit.cov_xy, expected_cov_xy, atol=1e-4)
        assert np.isclose(fit.weight, expected_weight, atol=1e-4)

        # Verify backward compatibility with tuple unpacking: dx, dy, peak = fit
        dx, dy, peak = fit
        assert np.isclose(dx, fit.dx)
        assert np.isclose(dy, fit.dy)
        assert np.isclose(peak, fit.peak_val)

    def test_sharper_peaks_yield_smaller_sigma_and_higher_weights(self):
        """
        Photogrammetric principle:
        Sharper cross-correlation peaks have greater curvature, yielding
        smaller coordinate variance (uncertainty) and higher bundle adjustment weight.
        Flatter peaks have high positional ambiguity (larger sigma, lower weight).
        """
        refiner = AnalyticalSubpixelRefiner()

        # Sharp, high-curvature peak
        patch_sharp = create_synthetic_quadratic_patch(a=-4.0, b=-4.0, c=0.0, d=0.1, e=-0.1)
        fit_sharp = refiner.fit_quadratic_surface(patch_sharp)

        # Broad, low-curvature peak
        patch_flat = create_synthetic_quadratic_patch(a=-0.5, b=-0.5, c=0.0, d=0.1, e=-0.1)
        fit_flat = refiner.fit_quadratic_surface(patch_flat)

        assert fit_sharp is not None
        assert fit_flat is not None

        # 1. Sharper peak must have smaller coordinate uncertainty sigma
        assert fit_sharp.sigma_x < fit_flat.sigma_x
        assert fit_sharp.sigma_y < fit_flat.sigma_y
        assert fit_sharp.sigma_x == pytest.approx(0.35355, rel=1e-2)
        assert fit_flat.sigma_x == pytest.approx(1.0, rel=1e-2)

        # 2. Sharper peak must have significantly higher weight
        assert fit_sharp.weight > fit_flat.weight
        assert fit_sharp.weight == pytest.approx(8.0, rel=1e-2)
        assert fit_flat.weight == pytest.approx(1.0, rel=1e-2)

    def test_keypoint_match_fields_and_refinement_batch(self):
        refiner = AnalyticalSubpixelRefiner()

        # Create a synthetic target image with an off-grid Gaussian peak
        h, w = 64, 64
        ref_moment = np.zeros((h, w), dtype=np.float32)
        cv2.circle(ref_moment, (32, 32), 6, 1.0, -1)

        tgt_moment = np.zeros((h, w), dtype=np.float32)
        # Shifted by +1.3 x, -0.7 y
        cv2.circle(tgt_moment, (33, 31), 6, 1.0, -1)

        initial_match = KeypointMatch(
            ref_xy=(32.0, 32.0),
            target_xy=(33.0, 31.0),
            confidence=0.95,
        )

        refined_matches = refiner.refine_matches_batch([initial_match], ref_moment, tgt_moment, patch_radius=6)

        assert len(refined_matches) == 1
        m = refined_matches[0]
        assert m.subpixel_refined is True
        assert m.sigma_x is not None and m.sigma_x > 0.0
        assert m.sigma_y is not None and m.sigma_y > 0.0
        assert m.weight is not None and m.weight > 0.0

    def test_gcp_csv_export_with_covariance_columns(self):
        """Verifies USGS ISIS3 jigsaw control network CSV export specifications."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "test_control_network.csv"

            matches = [
                KeypointMatch(
                    ref_xy=(100.5, 200.25),
                    target_xy=(102.1, 199.8),
                    confidence=0.92,
                    residual_error=0.18,
                    sigma_x=0.22,
                    sigma_y=0.25,
                    cov_xy=0.015,
                    weight=4.5,
                ),
                KeypointMatch(
                    ref_xy=(300.0, 400.0),
                    target_xy=(301.5, 399.5),
                    confidence=0.85,
                    residual_error=0.32,
                    sigma_x=0.45,
                    sigma_y=0.48,
                    cov_xy=-0.02,
                    weight=2.1,
                ),
            ]

            PlanetaryRasterWriter.export_gcp_csv(matches, csv_path)

            assert csv_path.exists()
            lines = csv_path.read_text().strip().split("\n")

            # Check header
            expected_header = "gcp_id,pixel_ref,line_ref,pixel_tgt,line_tgt,geo_x,geo_y,residual_px,confidence,sigma_x,sigma_y,cov_xy,weight"
            assert lines[0] == expected_header

            # Check row 1
            row1 = lines[1].split(",")
            assert row1[0] == "0"
            assert float(row1[1]) == pytest.approx(100.5)
            assert float(row1[2]) == pytest.approx(200.25)
            assert float(row1[9]) == pytest.approx(0.22)   # sigma_x
            assert float(row1[10]) == pytest.approx(0.25)  # sigma_y
            assert float(row1[11]) == pytest.approx(0.015) # cov_xy
            assert float(row1[12]) == pytest.approx(4.5)   # weight
