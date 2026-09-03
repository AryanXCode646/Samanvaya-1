"""
Adaptive Non-Maximal Suppression (ANMS) & Grid-Based Uniform Spatial Allocator.
"""

from __future__ import annotations

from typing import List, Tuple
import numpy as np
from lunar_core.models import KeypointMatch


class SpatialUniformDistributor:
    """
    Suppresses feature clumping on high-relief crater edges and enforces uniform spatial allocation.
    """

    def __init__(self, grid_rows: int = 8, grid_cols: int = 8) -> None:
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols

    @staticmethod
    def anms_brown(
        keypoints: np.ndarray,
        responses: np.ndarray,
        target_count: int,
        c_robust: float = 0.9,
    ) -> np.ndarray:
        """
        Classic Brown et al. ANMS suppression radius formulation:
            r_i = min_{j: s_j > c_robust * s_i} ||x_i - x_j||_2
        """
        n = keypoints.shape[0]
        if n <= target_count:
            return np.arange(n)

        sorted_indices = np.argsort(-responses)
        sorted_kps = keypoints[sorted_indices]
        radii = np.full(n, np.inf, dtype=np.float32)

        for i in range(1, n):
            higher = sorted_kps[:i]
            dists = np.linalg.norm(higher - sorted_kps[i], axis=1)
            radii[i] = np.min(dists)

        top_by_radius = np.argsort(-radii)[:target_count]
        return sorted_indices[top_by_radius]

    def cap_grid_cells(
        self,
        matches: List[KeypointMatch],
        image_shape: Tuple[int, int],
        cap_per_cell: int = 4,
    ) -> List[KeypointMatch]:
        """
        Subdivides the scene into an 8x8 or 16x16 grid and caps top-confidence matches per cell.
        """
        if not matches:
            return []

        h, w = image_shape
        cell_h = h / self.grid_rows
        cell_w = w / self.grid_cols

        buckets: List[List[KeypointMatch]] = [[] for _ in range(self.grid_rows * self.grid_cols)]

        for m in matches:
            rx, ry = m.ref_xy
            gx = min(max(0, int(rx // cell_w)), self.grid_cols - 1)
            gy = min(max(0, int(ry // cell_h)), self.grid_rows - 1)
            idx = gy * self.grid_cols + gx
            buckets[idx].append(m)

        capped: List[KeypointMatch] = []
        for b in buckets:
            if not b:
                continue
            b_sorted = sorted(b, key=lambda match: match.confidence, reverse=True)
            capped.extend(b_sorted[:cap_per_cell])

        return capped
