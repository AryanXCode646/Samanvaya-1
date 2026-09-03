"""
Hyperspectral Continuum Extraction and Dimensionality Reduction for Chandrayaan-2 IIRS.
Operates across 256 spectral channels (800 nm - 5000 nm).
"""

from __future__ import annotations

import logging
from typing import Optional, Sequence, Tuple, Union
import cv2
import numpy as np

logger = logging.getLogger("lunar_core.spectral")


class HyperspectralBandSelector:
    """
    Extracts radiometrically stable continuum bands and compresses multi-channel
    IIRS cubes into high-variance 2D structural edge maps for cross-modal registration.
    """

    # Typical IIRS operational parameters
    DEFAULT_MIN_WAVELENGTH_NM = 800.0
    DEFAULT_MAX_WAVELENGTH_NM = 5000.0
    DEFAULT_NUM_BANDS = 256

    # Optimal continuum reflectance window (least affected by lunar thermal emission)
    CONTINUUM_MIN_NM = 1000.0  # 1.0 µm
    CONTINUUM_MAX_NM = 1250.0  # 1.25 µm

    def __init__(
        self,
        wavelengths: Optional[Sequence[float]] = None,
        num_bands: int = 256,
        min_wavelength_nm: float = 800.0,
        max_wavelength_nm: float = 5000.0,
    ) -> None:
        """
        Args:
            wavelengths: Explicit array of band center wavelengths in nm or µm.
            num_bands: Total spectral channels (default 256 for IIRS).
            min_wavelength_nm: Lower spectral boundary in nm (800 nm).
            max_wavelength_nm: Upper spectral boundary in nm (5000 nm).
        """
        self.num_bands = num_bands
        if wavelengths is not None:
            wl_arr = np.asarray(wavelengths, dtype=np.float32)
            # If specified in micrometers (e.g. 0.8 - 5.0), convert to nanometers
            if np.max(wl_arr) < 50.0:
                wl_arr = wl_arr * 1000.0
            self.wavelengths = wl_arr
        else:
            self.wavelengths = np.linspace(
                min_wavelength_nm, max_wavelength_nm, num_bands, dtype=np.float32
            )

    def _standardize_cube_layout(self, cube: np.ndarray) -> np.ndarray:
        """
        Ensures cube layout is (bands, height, width).
        Accepts (bands, H, W) or (H, W, bands).
        """
        arr = np.asarray(cube, dtype=np.float32)
        if arr.ndim != 3:
            raise ValueError(f"Expected 3D hyperspectral cube, got shape {arr.shape}")

        num_wl = len(self.wavelengths)
        if arr.shape[0] == num_wl:
            return arr
        elif arr.shape[2] == num_wl:
            return np.transpose(arr, (2, 0, 1))
        elif arr.shape[1] == num_wl:
            return np.transpose(arr, (1, 0, 2))

        # Heuristic fallback if wavelengths length does not match exactly
        if arr.shape[0] == arr.shape[1] and arr.shape[2] != arr.shape[0]:
            # Square spatial dimensions (H, H, bands)
            return np.transpose(arr, (2, 0, 1))
        elif arr.shape[2] < arr.shape[0] and arr.shape[2] < arr.shape[1]:
            return np.transpose(arr, (2, 0, 1))

        return arr

    def get_band_indices_for_range(
        self,
        min_nm: float = 1000.0,
        max_nm: float = 1250.0,
    ) -> np.ndarray:
        """
        Returns channel indices falling within the specified wavelength range.
        """
        mask = (self.wavelengths >= min_nm) & (self.wavelengths <= max_nm)
        indices = np.where(mask)[0]
        if len(indices) == 0:
            # Fallback to the closest single band
            center_nm = 0.5 * (min_nm + max_nm)
            closest_idx = int(np.argmin(np.abs(self.wavelengths - center_nm)))
            return np.array([closest_idx], dtype=np.int64)
        return indices

    def extract_continuum_band(
        self,
        cube: np.ndarray,
        min_nm: float = 1000.0,
        max_nm: float = 1250.0,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Extracts continuum reflectance across the 1.0 - 1.25 µm window,
        where lunar thermal emission is negligible and optical contrast is optimal.

        Returns:
            2D float32 array (height, width) normalized to [0.0, 1.0].
        """
        c_cube = self._standardize_cube_layout(cube)
        indices = self.get_band_indices_for_range(min_nm, max_nm)

        # Slice continuum channels and compute mean reflectance
        selected_channels = c_cube[indices, :, :]
        continuum_2d = np.nanmean(selected_channels, axis=0)

        if not normalize:
            return continuum_2d

        # Percentile dynamic range normalization
        p1 = float(np.nanpercentile(continuum_2d, 1.0))
        p99 = float(np.nanpercentile(continuum_2d, 99.0))
        denom = max(p99 - p1, 1e-5)
        normalized = np.clip((continuum_2d - p1) / denom, 0.0, 1.0)
        return np.nan_to_num(normalized, nan=0.5).astype(np.float32)

    def extract_pca_structural_band(
        self,
        cube: np.ndarray,
        subsample_ratio: float = 1.0,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Compresses 256 spectral channels into a single structural 2D band
        along the first principal component (maximum spatial-spectral variance).

        Returns:
            2D float32 array (height, width) normalized to [0.0, 1.0].
        """
        c_cube = self._standardize_cube_layout(cube)
        num_bands, height, width = c_cube.shape

        # Reshape to (N_pixels, N_bands)
        flat_pixels = c_cube.reshape(num_bands, -1).T  # (H*W, bands)

        # Handle NaNs or Infs
        valid_mask = np.all(np.isfinite(flat_pixels), axis=1)
        if not np.any(valid_mask):
            return np.zeros((height, width), dtype=np.float32)

        pixels_clean = flat_pixels[valid_mask]

        # Mean centering
        mean_vec = np.mean(pixels_clean, axis=0, keepdims=True)
        centered = pixels_clean - mean_vec

        # Subsample rows for fast covariance computation if large
        if subsample_ratio < 1.0 and centered.shape[0] > 1000:
            step = int(1.0 / subsample_ratio)
            cov_matrix = np.cov(centered[::step], rowvar=False)
        else:
            cov_matrix = np.cov(centered, rowvar=False)

        # Compute eigen-decomposition of spectral covariance matrix (bands x bands)
        # For 256 bands, cov_matrix is 256x256, taking < 2ms to solve
        eig_vals, eig_vecs = np.linalg.eigh(cov_matrix)

        # First principal component is the eigenvector with the largest eigenvalue
        first_pc = eig_vecs[:, -1]

        # Project all pixels onto the first principal component
        full_centered = flat_pixels - mean_vec
        pc1_projection = np.dot(full_centered, first_pc)

        # Polarity correction: ensure positive correlation with mean brightness
        mean_spatial = np.nanmean(c_cube, axis=0).ravel()
        corr = np.corrcoef(pc1_projection[valid_mask], mean_spatial[valid_mask])[0, 1]
        if corr < 0:
            pc1_projection = -pc1_projection

        pc1_image = pc1_projection.reshape(height, width)

        if not normalize:
            return pc1_image.astype(np.float32)

        p1 = float(np.nanpercentile(pc1_image, 1.0))
        p99 = float(np.nanpercentile(pc1_image, 99.0))
        denom = max(p99 - p1, 1e-5)
        norm_pc1 = np.clip((pc1_image - p1) / denom, 0.0, 1.0)
        return np.nan_to_num(norm_pc1, nan=0.5).astype(np.float32)

    def extract_optimal_structural_band(
        self,
        cube: np.ndarray,
        method: str = "continuum",
    ) -> np.ndarray:
        """
        Dispatches band extraction via 'continuum' (1.0 - 1.25 µm) or 'pca'.
        """
        if method.lower() == "pca":
            return self.extract_pca_structural_band(cube)
        return self.extract_continuum_band(cube)
