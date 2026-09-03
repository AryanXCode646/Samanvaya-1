"""
Unit Tests for Sub-Pixel Precision & 2D Quadratic Taylor-Series Refinement.
SIH PS 26166 Constraint: Target RMSE < 0.40 pixels.
"""

import numpy as np
import pytest
from ch2_lunar_reg.domain.models import KeypointMatch
from ch2_lunar_reg.application.subpixel_refiner import TaylorSubpixelRefiner


def test_quadratic_taylor_exact_paraboloid_fit():
    """
    Construct an exact continuous 2D concave paraboloid:
        f(x, y) = C - a*(x - x_true)^2 - b*(y - y_true)^2 - c*(x - x_true)*(y - y_true)
    with a true fractional sub-pixel peak at (x_true, y_true) = (0.28, -0.35).
    Sample the 3x3 discrete values and verify that Taylor refinement recovers
    (x_true, y_true) within 0.05 pixels.
    """
    true_dx = 0.28
    true_dy = -0.35
    
    # Paraboloid coefficients (concave maximum)
    a = 2.0
    b = 1.5
    c = 0.3
    c_const = 10.0
    
    patch_3x3 = np.zeros((3, 3), dtype=np.float64)
    for dy_idx, y_coord in enumerate([-1.0, 0.0, 1.0]):
        for dx_idx, x_coord in enumerate([-1.0, 0.0, 1.0]):
            val = c_const - a * (x_coord - true_dx)**2 - b * (y_coord - true_dy)**2 - c * (x_coord - true_dx) * (y_coord - true_dy)
            patch_3x3[dy_idx, dx_idx] = val
            
    refiner = TaylorSubpixelRefiner()
    fit = refiner.fit_quadratic_peak(patch_3x3)
    
    assert fit is not None, "Taylor fit failed on valid concave paraboloid"
    est_dx, est_dy, peak_val = fit
    
    err_x = abs(est_dx - true_dx)
    err_y = abs(est_dy - true_dy)
    residual = np.sqrt(err_x**2 + err_y**2)
    
    assert residual < 0.05, f"Sub-pixel error {residual:.4f} px exceeds 0.05 px bound!"
    assert residual < 0.40, f"Mandate check: Sub-pixel error must be < 0.40 px (got {residual:.4f})"


def test_taylor_rejects_saddle_points():
    """Verify that hyperbolic saddle points (det(H) < 0) are rejected."""
    # Saddle point: f(x, y) = x^2 - y^2
    patch = np.array([
        [ 0.0, -1.0,  0.0],
        [ 1.0,  0.0,  1.0],
        [ 0.0, -1.0,  0.0]
    ], dtype=np.float64)
    
    refiner = TaylorSubpixelRefiner()
    fit = refiner.fit_quadratic_peak(patch)
    assert fit is None, "Failed to reject saddle point surface"


def test_batch_subpixel_refiner():
    """Verify batch processing on KeypointMatch instances."""
    ref_img = np.random.uniform(0.2, 0.8, (128, 128)).astype(np.float32)
    # Target image with identical patch shifted by fractional offset
    tgt_img = ref_img.copy()
    
    matches = [
        KeypointMatch(ref_xy=(50.0, 50.0), target_xy=(50.0, 50.0), confidence=0.9),
        KeypointMatch(ref_xy=(60.0, 60.0), target_xy=(60.0, 60.0), confidence=0.85),
    ]
    
    refiner = TaylorSubpixelRefiner(patch_radius=8)
    refined = refiner.refine_matches_batch(matches, ref_img, tgt_img)
    
    assert len(refined) == len(matches)
    for m in refined:
        assert m.subpixel_refined is True
        # For identical images, subpixel delta should be approximately zero
        assert np.isclose(m.target_xy[0], m.ref_xy[0], atol=0.1)
        assert np.isclose(m.target_xy[1], m.ref_xy[1], atol=0.1)
