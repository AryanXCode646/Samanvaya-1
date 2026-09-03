"""
Unit Tests for Log-Gabor Phase Congruency & RIFT Feature Extraction.
"""

import numpy as np
import pytest
from ch2_lunar_reg.domain.phase_congruency import (
    LogGaborFilterBank,
    PhaseCongruencyEngine,
    RIFTDescriptorExtractor,
)


def test_log_gabor_dc_component():
    """Verify that Log-Gabor kernels have strictly zero DC component."""
    bank = LogGaborFilterBank(num_scales=3, num_orientations=4)
    filters = bank.build_filters(64, 64)
    
    assert len(filters) == 4
    assert len(filters[0]) == 3
    
    for o in range(4):
        for s in range(3):
            kernel = filters[o][s]
            # Kernel at DC (0, 0) must be identically zero
            assert kernel[0, 0] == 0.0
            assert np.all(kernel >= 0.0)


def test_phase_congruency_invariance_to_contrast_inversion():
    """
    Core scientific mandate: Phase Congruency must detect crater boundaries
    even under contrast inversion (e.g., shadows vs illuminated slopes).
    """
    engine = PhaseCongruencyEngine(num_scales=3, num_orientations=4)
    
    # Synthetic edge: dark-to-light step
    img1 = np.zeros((64, 64), dtype=np.float32)
    img1[:, 32:] = 1.0
    
    # Inverse edge: light-to-dark step (contrast polarity flipped)
    img2 = 1.0 - img1
    
    pc1 = engine.compute(img1)
    pc2 = engine.compute(img2)
    
    # Peak of M_max should occur along the vertical boundary x=31..33 in both images
    col_response1 = np.mean(pc1.max_moment, axis=0)
    col_response2 = np.mean(pc2.max_moment, axis=0)
    
    peak_x1 = np.argmax(col_response1)
    peak_x2 = np.argmax(col_response2)
    
    assert abs(peak_x1 - peak_x2) <= 1, f"Peak mismatch: {peak_x1} vs {peak_x2}"


def test_rift_descriptor_shape_and_normalization():
    """Verify RIFT descriptor dimensions and unit-norm properties."""
    extractor = RIFTDescriptorExtractor(patch_size=32, spatial_bins=4, num_orientations=6)
    expected_dim = 4 * 4 * 6  # 96
    
    mim = np.random.randint(0, 6, size=(64, 64), dtype=np.uint8)
    kps = [(32.0, 32.0), (20.0, 20.0)]
    
    desc, valid_kps = extractor.compute_descriptors(mim, kps)
    
    assert desc.shape == (2, expected_dim)
    assert len(valid_kps) == 2
    # Verify L2 normalization
    norms = np.linalg.norm(desc, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3)
