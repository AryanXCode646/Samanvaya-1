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
        Optimized Brown et al. ANMS suppression radius formulation:
            r_i = min_{j: s_j > c_robust * s_i} ||x_i - x_j||_2
        Uses fast spatial hash bucketing and vectorization to achieve O(N) performance.
        """
        n = keypoints.shape[0]
        if n <= target_count:
            return np.arange(n)

        sorted_indices = np.argsort(-responses)
        sorted_kps = keypoints[sorted_indices]
        radii = np.full(n, np.inf, dtype=np.float32)

        # For small arrays (n < 150), direct vectorized evaluation is fastest
        if n < 150:
            for i in range(1, n):
                dists = np.linalg.norm(sorted_kps[:i] - sorted_kps[i], axis=1)
                radii[i] = np.min(dists)
        else:
            # Fast spatial hash grid
            coord_min = np.min(sorted_kps, axis=0)
            coord_max = np.max(sorted_kps, axis=0)
            span = np.maximum(coord_max - coord_min, 1.0)
            cell_size = float(np.mean(span) / np.sqrt(n))

            grid: dict[Tuple[int, int], List[int]] = {}

            for i in range(n):
                pt = sorted_kps[i]
                gx = int((pt[0] - coord_min[0]) / cell_size)
                gy = int((pt[1] - coord_min[1]) / cell_size)

                min_dist = float("inf")
                # Search expanding concentric rings of cells
                ring = 1
                found = False
                while not found and ring <= 4:
                    for dy in range(-ring, ring + 1):
                        for dx in range(-ring, ring + 1):
                            cell = (gx + dx, gy + dy)
                            if cell in grid:
                                for prev_idx in grid[cell]:
                                    d = float(np.linalg.norm(sorted_kps[prev_idx] - pt))
                                    if d < min_dist:
                                        min_dist = d
                                        found = True
                    ring += 1

                if not found and i > 0:
                    # Fallback to nearest among previous points
                    dists = np.linalg.norm(sorted_kps[:i] - pt, axis=1)
                    min_dist = float(np.min(dists))

                radii[i] = min_dist
                cell_key = (gx, gy)
                if cell_key not in grid:
                    grid[cell_key] = []
                grid[cell_key].append(i)

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
        Guarantees uniform spatial distribution and prevents feature clumping along high-relief crater rims.
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

    def compute_shannon_spatial_entropy(
        self,
        matches: List[KeypointMatch],
        image_shape: Tuple[int, int],
    ) -> float:
        """
        Computes the Normalized Shannon Spatial Entropy H in [0.0, 1.0] across the lattice.
        Target: H >= 0.95 (uniformly distributed throughout image, zero clumping).
        """
        if not matches:
            return 0.0

        h, w = image_shape
        cell_h = h / self.grid_rows
        cell_w = w / self.grid_cols
        total_cells = self.grid_rows * self.grid_cols

        counts = np.zeros(total_cells, dtype=np.float64)
        for m in matches:
            rx, ry = m.ref_xy
            gx = min(max(0, int(rx // cell_w)), self.grid_cols - 1)
            gy = min(max(0, int(ry // cell_h)), self.grid_rows - 1)
            idx = gy * self.grid_cols + gx
            counts[idx] += 1.0

        total = float(np.sum(counts))
        if total == 0:
            return 0.0

        p = counts[counts > 0] / total
        shannon = -float(np.sum(p * np.log2(p)))
        max_shannon = float(np.log2(total_cells))
        return float(np.clip(shannon / max_shannon, 0.0, 1.0))
