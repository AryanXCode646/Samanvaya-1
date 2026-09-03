"""
Unit Tests for Thin-Plate Splines (TPS) & Robust Geometric Solvers.
"""

import numpy as np
import pytest
from ch2_lunar_reg.domain.transformation import (
    GeometricTransformationSolver,
    ThinPlateSplineTransformer,
)
from ch2_lunar_reg.domain.models import TransformationModel


def test_thin_plate_spline_exact_interpolation():
    """Verify TPS interpolates control landmarks with minimal residual."""
    src = np.array([
        [10.0, 10.0],
        [90.0, 10.0],
        [10.0, 90.0],
        [90.0, 90.0],
        [50.0, 50.0],
    ], dtype=np.float32)
    
    # Introduce non-linear deformation at center
    dst = src.copy()
    dst[4] += [4.5, -3.2]
    
    tps = ThinPlateSplineTransformer(regularization=1e-6)
    tps.fit(src, dst)
    
    pred = tps.transform_points(src)
    residuals = np.linalg.norm(pred - dst, axis=1)
    
    # TPS must reproduce control points within numerical tolerance
    assert np.all(residuals < 0.1), f"TPS landmark error too large: {residuals}"


def test_affine_solver_accuracy():
    """Verify affine solver on synthetic 2D rotation + translation."""
    src = np.array([
        [20.0, 30.0],
        [120.0, 40.0],
        [50.0, 180.0],
        [150.0, 160.0],
    ], dtype=np.float32)
    
    # Rotation 5 deg + translation (10, -5)
    angle = np.radians(5.0)
    cos_a, sin_a = np.cos(angle), np.sin(angle)
    rot = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
    dst = (src @ rot.T) + np.array([10.0, -5.0])
    
    matrix = GeometricTransformationSolver.estimate_affine(src, dst)
    src_h = np.hstack([src, np.ones((4, 1))])
    pred = src_h @ matrix.T
    
    err = np.linalg.norm(pred - dst, axis=1)
    assert np.all(err < 0.1)
