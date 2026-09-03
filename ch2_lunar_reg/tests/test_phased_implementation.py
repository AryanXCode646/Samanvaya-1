"""
Automated Test Suite for Phased Implementation Plan (SIH PS 26166).

Phase 1: Environment & Photometric Normalization (Phase Congruency & Docker GDAL/PyTorch)
Phase 2: Coarse Multi-Scale Correlation & ROI Localization (Fourier-Mellin Log-Polar & GSD 20x)
Phase 3: Transformer Matcher & Grid-Based ANMS (LoFTR Cross-Attention & 8x8 / 16x16 Grid Capping)
"""

import os
from pathlib import Path
import numpy as np
import pytest

from ch2_lunar_reg.domain.models import SunAngles, KeypointMatch
from ch2_lunar_reg.domain.phase_congruency import PhaseCongruencyEngine
from ch2_lunar_reg.application.scale_space import (
    FourierMellinRegistrar,
    HierarchicalScaleSpaceRegistrar,
    RoiLocalizer,
)
from ch2_lunar_reg.application.spatial_allocator import GridSpatialAllocator
from ch2_lunar_reg.application.robust_matcher import LoFTRPlanetaryMatcher
from ch2_lunar_reg.infrastructure.synthetic_generator import LunarTerrainSimulator


# ==============================================================================
# PHASE 1 TESTS: Photometric Normalization & Phase Congruency
# ==============================================================================

def test_phase1_dockerfile_and_gdal_configuration():
    """Verify production Dockerfile exists and configures GDAL and PyTorch."""
    dockerfile = Path("Dockerfile")
    assert dockerfile.exists(), "Dockerfile must exist in workspace root"
    content = dockerfile.read_text()
    assert "libgdal-dev" in content or "gdal-bin" in content
    assert "torch" in content
    assert "rasterio" in content


def test_phase1_phase_congruency_illumination_invariance():
    """
    Verify Phase Congruency detects physical crater rims under opposite illumination
    where raw intensity correlation fails.
    """
    sim = LunarTerrainSimulator(size=(128, 128), seed=101)
    dem = sim.generate_dem(num_craters=10)
    
    # Morning Sun: 60 deg vs Afternoon Sun: 240 deg (180 deg opposite azimuth)
    img_morning = sim.render_optical_image(dem, SunAngles(azimuth_deg=60.0, elevation_deg=25.0))
    img_afternoon = sim.render_optical_image(dem, SunAngles(azimuth_deg=240.0, elevation_deg=35.0))
    
    # Raw intensity correlation between opposite sun orbits is poor/inverted
    raw_corr = np.corrcoef(img_morning.ravel(), img_afternoon.ravel())[0, 1]
    
    # Phase Congruency decomposition
    pc_engine = PhaseCongruencyEngine(num_scales=3, num_orientations=4)
    pc_morning = pc_engine.compute(img_morning)
    pc_afternoon = pc_engine.compute(img_afternoon)
    
    # Phase Congruency Maximum Moment maps M_max correlate strongly at physical rims
    pc_corr = np.corrcoef(pc_morning.max_moment.ravel(), pc_afternoon.max_moment.ravel())[0, 1]
    
    # Phase Congruency correlation must be significantly higher than raw intensity
    assert pc_corr > raw_corr, f"PC correlation ({pc_corr:.3f}) should exceed raw ({raw_corr:.3f})"
    assert pc_corr > 0.40, f"PC correlation across 180 deg sun reversal must be > 0.40 (got {pc_corr:.3f})"


# ==============================================================================
# PHASE 2 TESTS: Coarse Multi-Scale Correlation & ROI Localization
# ==============================================================================

def test_phase2_gsd_parsing_and_20x_downscaling():
    """
    Verify Ground Sampling Distance (GSD) ratio parsing:
    OHRC ~0.25m vs TMC-2 ~5.0m represents a 20x scale ratio.
    Anti-aliased decimation must produce clean downscaled imagery without aliasing.
    """
    ohrc_gsd = 0.25  # meters/pixel
    tmc2_gsd = 5.00  # meters/pixel
    
    # Simulated high-res OHRC patch: 320x320
    ohrc_img = np.random.uniform(0.1, 0.9, (320, 320)).astype(np.float32)
    # Coarser TMC-2 patch: 16x16
    tmc_img = np.random.uniform(0.1, 0.9, (16, 16)).astype(np.float32)
    
    registrar = HierarchicalScaleSpaceRegistrar()
    resampled_ohrc, resampled_tmc, ratio = registrar.resample_to_common_gsd(
        ohrc_img, ohrc_gsd, tmc_img, tmc2_gsd
    )
    
    assert np.isclose(ratio, 20.0, atol=1e-2)
    # Resampled OHRC should match target dimensions (320 / 20 = 16)
    assert resampled_ohrc.shape == (16, 16)


def test_phase2_fourier_mellin_and_roi_localization():
    """
    Verify Fourier-Mellin log-polar correlation estimates initial planar rotation
    and scale, and RoiLocalizer projects and crops overlapping bounding ROI.
    """
    sim = LunarTerrainSimulator(size=(200, 200), seed=42)
    dem = sim.generate_dem(num_craters=8)
    sun = SunAngles(azimuth_deg=45.0, elevation_deg=30.0)
    base_img = sim.render_optical_image(dem, sun)
    
    localizer = RoiLocalizer(padding_pixels=8)
    roi_bundle = localizer.localize_and_crop(
        img_ref=base_img,
        img_tgt=base_img,
        ref_gsd=1.0,
        target_gsd=1.0,
    )
    
    assert roi_bundle.ref_roi.shape[0] > 50
    assert roi_bundle.ref_roi.shape[1] > 50
    assert roi_bundle.confidence > 0.50
    assert abs(roi_bundle.coarse_rotation_deg) < 5.0


# ==============================================================================
# PHASE 3 TESTS: Transformer Matcher & Grid-Based ANMS
# ==============================================================================

def test_phase3_loftr_dense_matcher_confidence_threshold():
    """
    Verify LoFTR detector-free dense matcher enforces cross-attention
    confidence threshold tau > 0.75.
    """
    ref_patch = np.random.uniform(0.2, 0.8, (64, 64)).astype(np.float32)
    tgt_patch = ref_patch.copy()  # Perfect correspondence
    
    matcher = LoFTRPlanetaryMatcher(temperature=0.08, confidence_threshold=0.75, grid_stride=8)
    matches = matcher.match_dense_patches(ref_patch, tgt_patch)
    
    assert len(matches) > 0, "LoFTR dense matcher should identify correspondences on identical patches"
    for m in matches:
        assert m.confidence >= 0.75, f"Confidence {m.confidence} below tau=0.75 threshold"


def test_phase3_grid_based_anms_equal_cell_capping():
    """
    Verify Grid-Based ANMS across 8x8 or 16x16 grid:
    Enforces equal cap of top-confidence correspondences per cell,
    preventing clumping on crater rims and distributing matches uniformly across the scene.
    """
    allocator = GridSpatialAllocator(grid_rows=8, grid_cols=8)
    image_shape = (256, 256)
    
    # Create 100 matches clustered in a single crater cell (e.g. cell at top-left: x in [10, 25], y in [10, 25])
    clustered_matches = [
        KeypointMatch(
            ref_xy=(np.random.uniform(10, 25), np.random.uniform(10, 25)),
            target_xy=(np.random.uniform(10, 25), np.random.uniform(10, 25)),
            confidence=0.95 - i * 0.001,
        )
        for i in range(100)
    ]
    
    # Create 30 matches spread across other grid cells
    sparse_matches = [
        KeypointMatch(
            ref_xy=(np.random.uniform(50, 240), np.random.uniform(50, 240)),
            target_xy=(np.random.uniform(50, 240), np.random.uniform(50, 240)),
            confidence=0.80,
        )
        for _ in range(30)
    ]
    
    all_matches = clustered_matches + sparse_matches
    cap_per_cell = 4
    
    capped = allocator.cap_matches_per_grid_cell(
        all_matches, image_shape=image_shape, cap_per_cell=cap_per_cell
    )
    
    # In the clustered cell (x in [0, 32], y in [0, 32]), at most `cap_per_cell` matches may remain!
    clump_remaining = [
        m for m in capped if m.ref_xy[0] < 32 and m.ref_xy[1] < 32
    ]
    assert len(clump_remaining) <= cap_per_cell, (
        f"Clumped crater cell has {len(clump_remaining)} matches, exceeding cap of {cap_per_cell}"
    )
    
    # Matches from sparse regions must be preserved
    sparse_remaining = [
        m for m in capped if m.ref_xy[0] >= 32 or m.ref_xy[1] >= 32
    ]
    assert len(sparse_remaining) > 0, "Sparse lunar terrain matches must be retained"
