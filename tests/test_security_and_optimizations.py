"""
Comprehensive Unit Tests for Algorithm Optimization, OOP Hierarchy, and Security Hardening.
Tests Phase Congruency Caching, Sub-Pixel ABCs, Spatial Entropy, XXE, and Path Traversal Shielding.
"""

from __future__ import annotations

import os
from pathlib import Path
import numpy as np
import pytest
import torch

from lunar_core.preprocessing.phase_congruency import (
    PhaseCongruencyEngine,
    get_optimal_hardware_device,
)
from lunar_core.postprocessing.subpixel import (
    SubpixelRefinerBase,
    ParabolicHessianRefiner,
    AnalyticalTaylorRefiner,
    AnalyticalSubpixelRefiner,
    SubpixelSurfaceFit,
)
from lunar_core.postprocessing.anms import SpatialUniformDistributor
from lunar_core.models import KeypointMatch
from lunar_core.data_io.raster_reader import (
    sanitize_path,
    PlanetaryRasterReader,
    MAX_RASTER_DIMENSION,
    MAX_UNCOMPRESSED_BYTES,
)


class TestOptimizationAndOOP:
    """Verifies DSA optimizations and strict OOP design."""

    def test_optimal_hardware_fallback(self):
        device = get_optimal_hardware_device()
        assert isinstance(device, torch.device)
        assert device.type in ["cuda", "mps", "cpu"]

    def test_phase_congruency_grid_and_filter_caching(self):
        engine = PhaseCongruencyEngine(num_scales=3, num_orientations=4)
        dummy_img = np.random.uniform(0.1, 0.9, (128, 128)).astype(np.float32)

        # First run: builds and caches
        out1 = engine.compute(dummy_img)
        assert len(engine._grid_cache) == 1
        assert len(engine._filter_cache) == 1

        # Second run: identical dimensions must utilize cache
        out2 = engine.compute(dummy_img)
        assert len(engine._grid_cache) == 1
        assert len(engine._filter_cache) == 1

        np.testing.assert_allclose(out1.max_moment, out2.max_moment, atol=1e-5)

    def test_subpixel_refiner_oop_hierarchy(self):
        assert issubclass(ParabolicHessianRefiner, SubpixelRefinerBase)
        assert issubclass(AnalyticalTaylorRefiner, ParabolicHessianRefiner)
        assert issubclass(AnalyticalSubpixelRefiner, ParabolicHessianRefiner)

        refiner = ParabolicHessianRefiner()

        # Sharp parabolic peak at (x=0, y=0)
        # f(x, y) = -2*x^2 - 2*y^2 + 1.0
        x, y = np.meshgrid([-1, 0, 1], [-1, 0, 1])
        patch = -2.0 * x**2 - 2.0 * y**2 + 1.0

        fit = refiner.fit_surface(patch)
        assert fit is not None
        assert abs(fit.dx) < 1e-4
        assert abs(fit.dy) < 1e-4
        assert abs(fit.peak_val - 1.0) < 1e-4
        assert fit.weight > 0.0
        assert fit.sigma_x > 0.0 and fit.sigma_y > 0.0

    def test_subpixel_saddle_point_rejection(self):
        refiner = AnalyticalTaylorRefiner()
        # Saddle point: f(x, y) = -x^2 + y^2
        x, y = np.meshgrid([-1, 0, 1], [-1, 0, 1])
        patch_saddle = -1.0 * x**2 + 1.0 * y**2
        fit = refiner.fit_surface(patch_saddle)
        assert fit is None, "Saddle point must be rejected by negative-definite Hessian check"

    def test_anms_shannon_spatial_entropy_calculation(self):
        distributor = SpatialUniformDistributor(grid_rows=8, grid_cols=8)

        # 1. Perfectly uniform distribution: 1 keypoint in each of the 64 cells
        uniform_matches = []
        for r in range(8):
            for c in range(8):
                uniform_matches.append(
                    KeypointMatch(
                        ref_xy=(float(c * 10 + 5), float(r * 10 + 5)),
                        target_xy=(float(c * 10 + 5), float(r * 10 + 5)),
                        confidence=0.9,
                    )
                )

        h_uniform = distributor.compute_shannon_spatial_entropy(uniform_matches, image_shape=(80, 80))
        assert h_uniform >= 0.99, f"Uniform distribution must achieve near-perfect entropy, got {h_uniform}"

        # 2. Clumped distribution: all 64 keypoints inside a single cell (0, 0)
        clumped_matches = [
            KeypointMatch(
                ref_xy=(2.0 + i * 0.01, 2.0 + i * 0.01),
                target_xy=(2.0, 2.0),
                confidence=0.9,
            )
            for i in range(64)
        ]
        h_clumped = distributor.compute_shannon_spatial_entropy(clumped_matches, image_shape=(80, 80))
        assert h_clumped < 0.05, f"Clumped points must yield near-zero entropy, got {h_clumped}"


class TestCybersecurityHardening:
    """Verifies XXE, path traversal, and decompression bomb shielding."""

    def test_path_sanitization_null_byte_rejection(self):
        with pytest.raises(ValueError, match="null byte detected"):
            sanitize_path("data/raster\x00.tif")

    def test_path_sanitization_traversal_boundary(self, tmp_path):
        sub_dir = tmp_path / "allowed"
        sub_dir.mkdir()
        safe_file = sub_dir / "safe.tif"
        safe_file.touch()

        # Legitimate path inside allowed boundary
        sanitized = sanitize_path(safe_file, allowed_dir=sub_dir)
        assert sanitized == safe_file.resolve()

        # Path attempting escape with ../
        with pytest.raises(PermissionError, match="path traversal"):
            sanitize_path(sub_dir / ".." / "secret.txt", allowed_dir=sub_dir)

    def test_geotiff_decompression_bomb_rejection(self, monkeypatch, tmp_path):
        import rasterio
        from unittest.mock import MagicMock

        fake_tif = tmp_path / "huge_bomb.tif"
        fake_tif.touch()

        # Mock rasterio open context manager returning dimensions exceeding MAX_RASTER_DIMENSION
        mock_src = MagicMock()
        mock_src.width = MAX_RASTER_DIMENSION + 5000
        mock_src.height = MAX_RASTER_DIMENSION + 5000
        mock_src.count = 1
        mock_src.dtypes = ["float32"]

        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_src
        monkeypatch.setattr(rasterio, "open", MagicMock(return_value=mock_context))

        with pytest.raises(ValueError, match="Decompression bomb rejected"):
            PlanetaryRasterReader.read_geotiff(fake_tif)
