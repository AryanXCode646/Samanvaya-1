"""
Planetary Geometric Transformation & Surface Warping Models.
ISRO Chandrayaan-2 Image Processing Core.

Supports:
1. Rigid (Euclidean), Similarity, Affine, and Projective (Homography) transforms.
2. 2D Thin-Plate Splines (TPS) with Tikhonov regularization for non-rigid lunar topography.
3. Sub-pixel forward and backward coordinate mapping.
"""

from __future__ import annotations

from typing import Optional, Tuple
import cv2
import numpy as np
from ch2_lunar_reg.domain.models import TransformationModel


class ThinPlateSplineTransformer:
    r"""
    2D Thin-Plate Spline (TPS) transformation engine for non-rigid lunar terrain registration.
    Models localized elevation parallax and non-linear sensor scan distortions.
    
    Energy minimization formulation:
        E(f) = sum_i ||v_i - f(p_i)||^2 + lambda * \iint [ (f_xx)^2 + 2(f_xy)^2 + (f_yy)^2 ] dx dy
    """

    def __init__(self, regularization: float = 1e-4) -> None:
        self.regularization = regularization
        self.source_pts: Optional[np.ndarray] = None
        self.weights: Optional[np.ndarray] = None
        self.affine_coeffs: Optional[np.ndarray] = None

    @staticmethod
    def _radial_basis(r: np.ndarray) -> np.ndarray:
        """TPS biharmonic radial basis function: U(r) = r^2 * ln(r^2) = 2*r^2*ln(r)."""
        mask = r > 1e-8
        u = np.zeros_like(r)
        u[mask] = (r[mask] ** 2) * np.log(r[mask] ** 2)
        return u

    def fit(self, source_pts: np.ndarray, target_pts: np.ndarray) -> None:
        """
        Solves TPS linear system for weights and affine coefficients.
        
        Args:
            source_pts: [N, 2] coordinates (x, y) in source frame.
            target_pts: [N, 2] coordinates (x, y) in target frame.
        """
        n = source_pts.shape[0]
        if n < 4:
            raise ValueError(f"TPS requires at least 4 control points, got {n}")
            
        self.source_pts = source_pts.astype(np.float64)
        targets = target_pts.astype(np.float64)
        
        # Pairwise Euclidean distances
        diff = self.source_pts[:, np.newaxis, :] - self.source_pts[np.newaxis, :, :]  # [N, N, 2]
        dist = np.linalg.norm(diff, axis=-1)  # [N, N]
        
        k_matrix = self._radial_basis(dist)  # [N, N]
        k_matrix += self.regularization * np.eye(n)
        
        # Linear polynomial matrix P: [N, 3] with [1, x, y]
        p_matrix = np.hstack([np.ones((n, 1), dtype=np.float64), self.source_pts])
        
        # Build block matrix:
        # [ K + lambda*I   P ] [ W ]   [ V ]
        # [      P^T       0 ] [ A ] = [ 0 ]
        top = np.hstack([k_matrix, p_matrix])
        bottom = np.hstack([p_matrix.T, np.zeros((3, 3), dtype=np.float64)])
        system_matrix = np.vstack([top, bottom])  # [N+3, N+3]
        
        rhs = np.vstack([targets, np.zeros((3, 2), dtype=np.float64)])  # [N+3, 2]
        
        # Solve regularized system
        solution = np.linalg.lstsq(system_matrix, rhs, rcond=None)[0]
        self.weights = solution[:n, :]        # [N, 2]
        self.affine_coeffs = solution[n:, :]  # [3, 2]

    def transform_points(self, points: np.ndarray) -> np.ndarray:
        """
        Applies fitted TPS warp to arbitrary 2D query points.
        
        Args:
            points: [M, 2] coordinates (x, y).
            
        Returns:
            Warped coordinates [M, 2].
        """
        if self.source_pts is None or self.weights is None or self.affine_coeffs is None:
            raise RuntimeError("TPS model is not fitted yet.")
            
        pts = points.astype(np.float64)
        m = pts.shape[0]
        
        # Distance from query points to all landmark source points
        diff = pts[:, np.newaxis, :] - self.source_pts[np.newaxis, :, :]  # [M, N, 2]
        dist = np.linalg.norm(diff, axis=-1)  # [M, N]
        u_matrix = self._radial_basis(dist)   # [M, N]
        
        # Polynomial part: [M, 3] * [3, 2]
        p_matrix = np.hstack([np.ones((m, 1), dtype=np.float64), pts])
        affine_part = p_matrix @ self.affine_coeffs
        
        # Non-linear part: [M, N] * [N, 2]
        non_linear_part = u_matrix @ self.weights
        
        return (affine_part + non_linear_part).astype(np.float32)

    def warp_image(
        self,
        image: np.ndarray,
        output_shape: Tuple[int, int],
        order: int = 1,
    ) -> np.ndarray:
        """
        Warps source image into target coordinates using inverse mapping.
        
        Args:
            image: 2D array of source image.
            output_shape: (height, width) of target canvas.
            order: Interpolation order (1 = bilinear, 3 = bicubic).
        """
        out_h, out_w = output_shape
        # Create destination grid
        grid_x, grid_y = np.meshgrid(np.arange(out_w), np.arange(out_h))
        dest_coords = np.column_stack([grid_x.ravel(), grid_y.ravel()])
        
        # Inverse mapping: fit TPS from target -> source
        # Note: here points transform forward; for inverse warp we sample coordinates
        source_coords = self.transform_points(dest_coords)
        
        map_x = source_coords[:, 0].reshape(out_h, out_w).astype(np.float32)
        map_y = source_coords[:, 1].reshape(out_h, out_w).astype(np.float32)
        
        interp = cv2.INTER_LINEAR if order == 1 else cv2.INTER_CUBIC
        warped = cv2.remap(image, map_x, map_y, interpolation=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        return warped


class GeometricTransformationSolver:
    """
    Solves parametric and non-parametric coordinate transformations.
    """

    @staticmethod
    def estimate_affine(source_pts: np.ndarray, target_pts: np.ndarray) -> np.ndarray:
        """Estimates optimal 2x3 affine transformation matrix using Least Squares."""
        matrix, _ = cv2.estimateAffine2D(
            source_pts, target_pts, method=cv2.LMEDS
        )
        if matrix is None:
            # Fallback least squares
            src_homo = np.hstack([source_pts, np.ones((source_pts.shape[0], 1))])
            res, _, _, _ = np.linalg.lstsq(src_homo, target_pts, rcond=None)
            matrix = res.T
        return matrix.astype(np.float64)

    @staticmethod
    def estimate_homography(source_pts: np.ndarray, target_pts: np.ndarray) -> np.ndarray:
        """Estimates 3x3 projective homography matrix."""
        h_matrix, _ = cv2.findHomography(source_pts, target_pts, method=0)
        if h_matrix is None:
            h_matrix = np.eye(3, dtype=np.float64)
        return h_matrix.astype(np.float64)

    @staticmethod
    def warp_image(
        image: np.ndarray,
        matrix: np.ndarray,
        model: TransformationModel,
        output_shape: Tuple[int, int],
    ) -> np.ndarray:
        """
        Warps image using the solved geometric transformation.
        """
        h, w = output_shape
        if model in [TransformationModel.RIGID, TransformationModel.SIMILARITY, TransformationModel.AFFINE]:
            m2x3 = matrix[:2, :3].astype(np.float32)
            return cv2.warpAffine(image, m2x3, (w, h), flags=cv2.INTER_LINEAR)
        elif model == TransformationModel.HOMOGRAPHY:
            return cv2.warpPerspective(image, matrix.astype(np.float32), (w, h), flags=cv2.INTER_LINEAR)
        else:
            raise ValueError(f"Use ThinPlateSplineTransformer.warp_image for {model}")
