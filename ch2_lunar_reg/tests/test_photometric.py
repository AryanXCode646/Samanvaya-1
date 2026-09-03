"""
Unit Tests for Photometric Normalization & Lunar Reflectance Models.
"""

import numpy as np
import pytest
from ch2_lunar_reg.domain.models import SunAngles
from ch2_lunar_reg.domain.photometric import LunarPhotometricNormalizer


def test_lommel_seeliger_properties():
    """Verify physical properties of the Lommel-Seeliger scattering function."""
    cos_i = np.array([1.0, 0.866, 0.5, 0.1, 0.0])
    cos_e = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    
    rls = LunarPhotometricNormalizer.lommel_seeliger(cos_i, cos_e)
    
    # At normal incidence & emission (i=0, e=0): R_LS = 1 / (1 + 1) = 0.5
    assert np.isclose(rls[0], 0.5, atol=1e-3)
    # Reflectance must decrease monotonically with increasing incidence angle
    assert np.all(np.diff(rls[:4]) < 0)
    # Grazing angle must yield zero or near zero
    assert rls[-1] == 0.0


def test_hapke_model():
    """Verify Hapke bidirectional reflectance model."""
    normalizer = LunarPhotometricNormalizer()
    cos_i = np.array([0.8])
    cos_e = np.array([1.0])
    phase_rad = np.radians(30.0)
    
    r = normalizer.hapke_isotropic(cos_i, cos_e, phase_rad)
    assert r.shape == (1,)
    assert r[0] > 0.0
    assert not np.isnan(r[0])


def test_photometric_normalization_pipeline():
    """Verify radiometric normalization on simulated image with solar geometry."""
    normalizer = LunarPhotometricNormalizer()
    synthetic_img = np.full((64, 64), 0.25, dtype=np.float32)
    # Add an artificial shadow patch
    synthetic_img[0:10, 0:10] = 0.005
    
    sun = SunAngles(azimuth_deg=75.0, elevation_deg=30.0)
    norm_img, valid_mask = normalizer.normalize_lommel_seeliger(synthetic_img, sun)
    
    assert norm_img.shape == (64, 64)
    assert valid_mask.shape == (64, 64)
    assert np.all(norm_img >= 0.0) and np.all(norm_img <= 1.0)
    # Deep shadow patch should be marked invalid
    assert not valid_mask[2, 2]
