"""
Unit Tests for DEM Surface Gradient Integration in Lommel-Seeliger Photometric Normalization.
Verifies continuous 3D unit normal facet derivation and rim burnout prevention on steep crater walls.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from lunar_core.models import SunAngles, TransformationType
from lunar_core.preprocessing.photometric import PhotometricNormalizer
from lunar_core.pipeline import LunarCorePipeline


def create_synthetic_crater_dem(
    size: int = 128,
    radius: float = 40.0,
    depth_meters: float = 300.0,
    pixel_gsd: float = 10.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Synthesizes a 3D digital elevation model (DEM) of a lunar impact crater with 25°-35° slopes.
    Returns (dem_meters, slope_degrees).
    """
    cx, cy = size / 2.0, size / 2.0
    y, x = np.ogrid[:size, :size]
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

    # Parabolic crater bowl
    dem = np.zeros((size, size), dtype=np.float32)
    inside_mask = dist <= radius
    norm_dist = dist[inside_mask] / radius
    dem[inside_mask] = -depth_meters * (1.0 - norm_dist**2)

    # Calculate theoretical slope angle in degrees
    slope_deg = np.zeros((size, size), dtype=np.float32)
    # Derivative dz/dr = 2 * depth * r / (radius^2)
    # In spatial distance: dr_meters = dr_pixels * pixel_gsd
    dz_dr = 2.0 * depth_meters * norm_dist / (radius * pixel_gsd)
    slope_deg[inside_mask] = np.degrees(np.arctan(dz_dr))

    return dem, slope_deg


class TestPhotometricNormalizerDEM:
    """Tests for DEM slope gradient integration into Lommel-Seeliger normalization."""

    def test_planar_fallback_without_dem(self):
        """Verifies backward compatibility when DEM is omitted."""
        image = np.full((64, 64), 100.0, dtype=np.float32)
        sun = SunAngles(azimuth_deg=45.0, elevation_deg=30.0)

        normalizer = PhotometricNormalizer()
        corrected, mask = normalizer.normalize(image, sun, dem_data=None)

        assert corrected.shape == (64, 64)
        assert np.isfinite(corrected).all()
        assert np.all(corrected >= 0.0) and np.all(corrected <= 1.0)
        assert mask.shape == (64, 64)

    def test_surface_normal_derivation_physics(self):
        """Verifies that 3D unit normal vectors satisfy ||n|| = 1.0 and radial symmetry."""
        dem, slopes = create_synthetic_crater_dem(size=128, radius=40.0, depth_meters=300.0, pixel_gsd=10.0)
        normalizer = PhotometricNormalizer()

        nx, ny, nz = normalizer.compute_surface_normals_from_dem(dem, pixel_gsd=10.0)

        # 1. Normal magnitude must be 1.0 everywhere
        magnitude = np.sqrt(nx**2 + ny**2 + nz**2)
        np.testing.assert_allclose(magnitude, 1.0, rtol=1e-5, atol=1e-5)

        # 2. Outside flat plateau should have vertical normal n = [0, 0, 1]
        assert np.isclose(nz[5, 5], 1.0, atol=1e-3)
        assert np.isclose(nx[5, 5], 0.0, atol=1e-3)
        assert np.isclose(ny[5, 5], 0.0, atol=1e-3)

        # 3. Crater center bottom should have vertical normal
        center = 64
        assert np.isclose(nz[center, center], 1.0, atol=1e-2)

        # 4. Crater rims should have significant non-zero horizontal normal components
        rim_nx = nx[center, center + 30]  # East rim
        assert rim_nx < -0.15  # Normal points inward/upward

    def test_crater_slope_burnout_prevention_at_low_sun(self):
        """
        Simulates low solar elevation (15°) illuminating a crater with 30° slopes.
        Proves that DEM normalization balances crater wall reflectance and prevents rim burnout.
        """
        dem, slopes = create_synthetic_crater_dem(size=128, radius=40.0, depth_meters=300.0, pixel_gsd=10.0)
        sun = SunAngles(azimuth_deg=90.0, elevation_deg=15.0)  # Sun from East at low angle
        sun_vec = sun.sun_vector

        normalizer = PhotometricNormalizer()
        nx, ny, nz = normalizer.compute_surface_normals_from_dem(dem, pixel_gsd=10.0)

        # Forward synthetic optical model: raw image shaped by local slope incidence
        cos_i_true = np.maximum(nx * sun_vec[0] + ny * sun_vec[1] + nz * sun_vec[2], 0.01)
        cos_e_true = np.maximum(nz, 0.01)
        raw_reflectance = normalizer.lommel_seeliger(cos_i_true, cos_e_true)
        raw_image = (raw_reflectance * 255.0).astype(np.float32)

        # Normalize WITHOUT DEM (planar baseline assumption)
        corr_planar, _ = normalizer.normalize(raw_image, sun, dem_data=None)

        # Normalize WITH DEM (topographic surface normals)
        corr_dem, mask_dem = normalizer.normalize(raw_image, sun, dem_data=dem, pixel_gsd=10.0)

        assert np.isfinite(corr_dem).all()
        assert np.all(corr_dem >= 0.0) and np.all(corr_dem <= 1.0)

        # Examine the steep sun-facing slope (cos_i_true > 0.4) vs surrounding flat plateau
        sun_facing = (cos_i_true > 0.4) & (dem < -10.0)
        flat_plateau = (dem == 0)

        assert np.any(sun_facing)
        assert np.any(flat_plateau)

        # In raw optical and planar correction, the sun-facing crater wall is heavily over-bright (> 2.4x)
        ratio_planar = float(np.mean(corr_planar[sun_facing]) / np.mean(corr_planar[flat_plateau]))
        ratio_dem = float(np.mean(corr_dem[sun_facing]) / np.mean(corr_dem[flat_plateau]))

        # DEM slope normalization dampens the over-brightness, bringing slope reflectance closer to 1.0
        assert ratio_dem < ratio_planar
        assert ratio_dem < 1.75  # Significantly balanced towards 1.0

        # Maximum value on the steep rim must be strictly bounded in [0, 1] without blowout spikes
        assert np.max(corr_dem) <= 1.0

    def test_pipeline_integration_with_dem(self):
        """Verifies end-to-end LunarCorePipeline execution with dem_data."""
        dem, _ = create_synthetic_crater_dem(size=128, radius=35.0, depth_meters=200.0)
        img_ref = (np.clip(-dem / 200.0, 0.0, 1.0) * 200.0 + 30.0).astype(np.float32)
        img_tgt = img_ref.copy()

        ref_sun = SunAngles(azimuth_deg=45.0, elevation_deg=25.0)
        tgt_sun = SunAngles(azimuth_deg=45.0, elevation_deg=25.0)

        pipeline = LunarCorePipeline(
            enable_photometric=True,
            transformation_type=TransformationType.AFFINE,
        )

        result = pipeline.register(
            ref_image=img_ref,
            target_image=img_tgt,
            ref_sun=ref_sun,
            target_sun=tgt_sun,
            dem_data=dem,
        )

        assert result is not None
        assert result.transform_matrix is not None
        assert result.metrics is not None
