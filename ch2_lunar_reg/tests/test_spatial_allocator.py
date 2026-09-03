"""
Unit Tests for Spatial Keypoint Allocators & Clumping Suppression (ANMS).
"""

import numpy as np
import pytest
from ch2_lunar_reg.application.spatial_allocator import (
    AdaptiveNonMaximalSuppression,
    GridSpatialAllocator,
)


def test_anms_suppression_of_dense_crater_rim():
    """
    Simulate a tight cluster of 100 features along a single crater rim,
    and 20 sparsely distributed features across the lunar mare.
    Verify that ANMS rejects clumping and preserves sparse features.
    """
    rng = np.random.RandomState(42)
    
    # 100 clustered points along a 10px circular rim at center (100, 100)
    angles = np.linspace(0, 2*np.pi, 100)
    rim_x = 100.0 + 10.0 * np.cos(angles) + rng.normal(0, 0.5, 100)
    rim_y = 100.0 + 10.0 * np.sin(angles) + rng.normal(0, 0.5, 100)
    rim_kps = np.column_stack([rim_x, rim_y])
    rim_resp = rng.uniform(0.8, 1.0, 100)  # Very high response
    
    # 20 points spread across 256x256 image
    sparse_x = rng.uniform(10, 240, 20)
    sparse_y = rng.uniform(10, 240, 20)
    sparse_kps = np.column_stack([sparse_x, sparse_y])
    sparse_resp = rng.uniform(0.3, 0.6, 20)  # Moderate response
    
    all_kps = np.vstack([rim_kps, sparse_kps])
    all_resp = np.concatenate([rim_resp, sparse_resp])
    
    anms = AdaptiveNonMaximalSuppression(robust_coefficient=0.9)
    selected_idx = anms.suppress(all_kps, all_resp, target_count=30)
    
    assert len(selected_idx) == 30
    
    # Out of 30 selected points, ANMS must pick a significant portion of sparse points
    # rather than clumping all 30 points onto the single crater rim
    sparse_indices = set(range(100, 120))
    selected_sparse = [idx for idx in selected_idx if idx in sparse_indices]
    assert len(selected_sparse) >= 5, f"ANMS failed to retain sparse features: {len(selected_sparse)}"


def test_grid_allocator_spatial_coverage():
    """Verify that GridSpatialAllocator populates all occupied tiles."""
    kps = np.random.uniform(0, 200, (500, 2))
    resp = np.random.uniform(0.1, 1.0, 500)
    
    allocator = GridSpatialAllocator(grid_rows=5, grid_cols=5)
    selected = allocator.allocate(kps, resp, (200, 200), total_target_count=50)
    
    assert len(selected) == 50
    coverage = allocator.compute_spatial_coverage(kps[selected], (200, 200), grid_bins=5)
    # High coverage score across the 25 bins
    assert coverage >= 0.70
