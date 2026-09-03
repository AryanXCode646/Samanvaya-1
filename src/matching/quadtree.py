"""
src/matching/quadtree.py

Quad-Tree spatial distribution for Adaptive Non-Maximal Suppression (ANMS).
Ensures uniform distribution of keypoints across the image space, which is critical
for robust homography/affine estimation in low-contrast lunar imagery.
"""
from __future__ import annotations

import numpy as np
from typing import List, Tuple, Any

class QuadTreeANMS:
    """
    Quad-Tree based Adaptive Non-Maximal Suppression (ANMS).
    Recursively divides the image into a Quad-Tree and selects the strongest
    features within each spatial bin to guarantee uniform spatial coverage.
    """

    def __init__(self, max_points: int = 2000, grid_size: int = 8) -> None:
        """
        Parameters
        ----------
        max_points : int
            The maximum number of keypoints to retain after suppression.
        grid_size : int
            The base granularity of the grid (e.g., 8x8 blocks).
        """
        self.max_points = max_points
        self.grid_size = grid_size

    def distribute_keypoints(
        self, 
        keypoints: np.ndarray, 
        scores: np.ndarray, 
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Spatially distribute keypoints using a Quad-Tree structure.

        Parameters
        ----------
        keypoints : np.ndarray
            Array of shape (N, 2) containing (x, y) coordinates of keypoints.
        scores : np.ndarray
            Array of shape (N,) containing the strength/response of each keypoint.
        image_shape : Tuple[int, int]
            The shape of the original image (rows, cols).

        Returns
        -------
        np.ndarray
            Array of shape (M, 2) containing the filtered keypoints (M <= max_points).
        """
        if len(keypoints) == 0:
            return np.array([])
            
        if len(keypoints) <= self.max_points:
            # Sort by score descending and return
            idx = np.argsort(scores)[::-1]
            return keypoints[idx]

        height, width = image_shape
        
        # Determine the maximum depth of the quadtree based on the grid size
        # and requested max_points to ensure fine enough binning.
        node = self._build_quadtree(
            keypoints, scores, x_min=0, y_min=0, x_max=width, y_max=height
        )
        
        # Retrieve distributed points
        filtered_indices = []
        self._extract_points(node, filtered_indices, target_count=self.max_points)
        
        # If we didn't hit exactly max_points, we pad with the remaining strongest points
        if len(filtered_indices) < self.max_points:
            remaining_needed = self.max_points - len(filtered_indices)
            
            # Mask out already selected indices
            mask = np.ones(len(scores), dtype=bool)
            mask[filtered_indices] = False
            
            # Find the strongest remaining points
            remaining_indices = np.where(mask)[0]
            remaining_scores = scores[remaining_indices]
            
            sorted_rem_idx = np.argsort(remaining_scores)[::-1][:remaining_needed]
            filtered_indices.extend(remaining_indices[sorted_rem_idx])
            
        elif len(filtered_indices) > self.max_points:
            # Technically shouldn't happen with proper target_count balancing,
            # but safeguard just in case.
            filtered_indices = filtered_indices[:self.max_points]

        return keypoints[filtered_indices]

    def _build_quadtree(
        self, 
        pts: np.ndarray, 
        scores: np.ndarray, 
        x_min: float, 
        y_min: float, 
        x_max: float, 
        y_max: float,
        depth: int = 0
    ) -> dict:
        """
        Recursively construct the Quad-Tree over the keypoints.
        """
        # Node structure:
        # { 'is_leaf': bool, 'indices': list, 'children': list }
        
        # Filter points within this bounding box
        in_box = (
            (pts[:, 0] >= x_min) & (pts[:, 0] < x_max) &
            (pts[:, 1] >= y_min) & (pts[:, 1] < y_max)
        )
        indices = np.where(in_box)[0]
        
        # Stopping criteria: few points, or reached desired grid depth
        if len(indices) <= 1 or depth >= np.log2(self.grid_size):
            # Sort indices inside this leaf by score
            sorted_indices = indices[np.argsort(scores[indices])[::-1]]
            return {
                'is_leaf': True,
                'indices': sorted_indices.tolist(),
                'children': []
            }
            
        # Subdivide
        x_mid = (x_min + x_max) / 2.0
        y_mid = (y_min + y_max) / 2.0
        
        children = [
            self._build_quadtree(pts, scores, x_min, y_min, x_mid, y_mid, depth + 1),  # TL
            self._build_quadtree(pts, scores, x_mid, y_min, x_max, y_mid, depth + 1),  # TR
            self._build_quadtree(pts, scores, x_min, y_mid, x_mid, y_max, depth + 1),  # BL
            self._build_quadtree(pts, scores, x_mid, y_mid, x_max, y_max, depth + 1),  # BR
        ]
        
        return {
            'is_leaf': False,
            'indices': [],
            'children': children
        }
        
    def _extract_points(self, node: dict, output_list: List[int], target_count: int) -> None:
        """
        Recursively extract points from the quad tree in a round-robin fashion
        across all leaf nodes until target_count is reached.
        """
        # Collect all leaf lists
        leaf_lists = []
        
        def collect_leaves(n):
            if n['is_leaf']:
                if n['indices']:
                    leaf_lists.append(n['indices'])
            else:
                for c in n['children']:
                    collect_leaves(c)
                    
        collect_leaves(node)
        
        if not leaf_lists:
            return
            
        # Round-robin extraction from leaves
        added = 0
        pointers = [0] * len(leaf_lists)
        
        while added < target_count:
            progress = False
            for i, lst in enumerate(leaf_lists):
                if added >= target_count:
                    break
                if pointers[i] < len(lst):
                    output_list.append(lst[pointers[i]])
                    pointers[i] += 1
                    added += 1
                    progress = True
                    
            if not progress:
                # All leaves exhausted
                break
