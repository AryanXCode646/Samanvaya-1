"""
Phase Congruency & RIFT (Radiation-variation Insensitive Feature Transform)
ISRO Chandrayaan-2 Planetary Optical & Hyperspectral Registration.

Theoretical Foundation:
- Morrone & Owens Local Energy Model: Features are perceived at points of maximum
  phase congruency across spatial frequencies, invariant to contrast and illumination.
- Kovesi's 2D Log-Gabor filter bank in frequency domain.
- Maximum and Minimum Moment maps for edge and corner detection.
- RIFT Maximum Index Map (MIM) and radiation-invariant patch descriptors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import cv2
import numpy as np


@dataclass
class PhaseCongruencyOutput:
    """
    Output representations from multi-scale Log-Gabor phase congruency analysis.
    """
    phase_congruency: np.ndarray       # Total PC map [0, 1]
    max_moment: np.ndarray             # M_max: highly localized edge feature map
    min_moment: np.ndarray             # M_min: robust corner feature map
    orientation_max_idx: np.ndarray    # Maximum Index Map (MIM) for RIFT
    feature_energy: np.ndarray         # Local energy magnitude map


class LogGaborFilterBank:
    """
    2D Log-Gabor wavelet filter bank constructed in frequency space.
    Eliminates DC component entirely, preventing low-frequency illumination bias.
    Fully vectorized with precomputed frequency grids (u, v, radius, theta).
    """

    def __init__(
        self,
        num_scales: int = 4,
        num_orientations: int = 6,
        min_wavelength: float = 3.0,
        mult: float = 2.1,
        sigma_on_f: float = 0.55,
        d_theta_on_sigma: float = 1.2,
    ) -> None:
        self.num_scales = num_scales
        self.num_orientations = num_orientations
        self.min_wavelength = min_wavelength
        self.mult = mult
        self.sigma_on_f = sigma_on_f
        self.d_theta_on_sigma = d_theta_on_sigma
        self._filter_cache: dict = {}
        self._tensor_filter_cache: dict = {}
        self._grid_cache: dict = {}

    def get_frequency_grids(
        self, rows: int, cols: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Retrieves or caches precomputed frequency coordinate grids: (u, v, radius, theta).
        """
        cache_key = (rows, cols)
        if cache_key in self._grid_cache:
            return self._grid_cache[cache_key]

        u = np.linspace(-0.5, 0.5, cols, endpoint=False, dtype=np.float32)
        v = np.linspace(-0.5, 0.5, rows, endpoint=False, dtype=np.float32)
        x, y = np.meshgrid(u, v)

        # FFT shift to align DC at (0, 0)
        x = np.fft.ifftshift(x)
        y = np.fft.ifftshift(y)

        radius = np.sqrt(x**2 + y**2).astype(np.float32)
        theta = np.arctan2(-y, x).astype(np.float32)
        radius[0, 0] = 1.0  # Avoid log(0) singularity at DC

        grids = (x, y, radius, theta)
        self._grid_cache[cache_key] = grids
        return grids

    def build_filters_tensor(self, rows: int, cols: int) -> np.ndarray:
        """
        Constructs vectorized 4D frequency-domain Log-Gabor kernels of shape [num_orientations, num_scales, rows, cols].
        Precomputes and caches frequency grids and kernels for O(1) repeated evaluation with zero Python loops.
        """
        cache_key = (rows, cols)
        if cache_key in self._tensor_filter_cache:
            return self._tensor_filter_cache[cache_key]

        _, _, radius, theta = self.get_frequency_grids(rows, cols)

        theta_sigma = float(np.pi / self.num_orientations / self.d_theta_on_sigma)

        # Vectorized angular spread filter across all orientations: shape [O, rows, cols]
        ang = (
            np.arange(self.num_orientations, dtype=np.float32)
            * (np.pi / self.num_orientations)
        ).reshape(-1, 1, 1)

        diff_theta1 = np.abs(theta[None, :, :] - ang)
        diff_theta1 = np.minimum(diff_theta1, 2.0 * np.pi - diff_theta1)

        diff_theta2 = np.abs(theta[None, :, :] - (ang + np.pi))
        diff_theta2 = np.minimum(diff_theta2, 2.0 * np.pi - diff_theta2)

        diff_theta = np.minimum(diff_theta1, diff_theta2)
        spread = np.exp(-(diff_theta**2) / (2.0 * theta_sigma**2)).astype(np.float32)

        # Vectorized radial Log-Gabor filter across all scales: shape [S, rows, cols]
        s_idx = np.arange(self.num_scales, dtype=np.float32).reshape(-1, 1, 1)
        wavelength = (self.min_wavelength * (self.mult**s_idx)).astype(np.float32)
        f0 = 1.0 / wavelength

        log_rad = np.log(radius[None, :, :] / f0)
        radial = np.exp(
            -(log_rad**2) / (2.0 * (np.log(self.sigma_on_f)) ** 2)
        ).astype(np.float32)
        radial[:, 0, 0] = 0.0  # Zero DC component across all scales

        # 4D filter bank: [O, S, rows, cols] via tensor broadcasting
        filters_4d = (spread[:, None, :, :] * radial[None, :, :, :]).astype(np.float32)

        self._tensor_filter_cache[cache_key] = filters_4d
        return filters_4d

    def build_filters(self, rows: int, cols: int) -> List[List[np.ndarray]]:
        """
        Constructs 2D frequency-domain Log-Gabor kernels of dimensions (rows, cols).
        Maintains backward compatibility returning List[List[np.ndarray]].
        """
        cache_key = (rows, cols)
        if cache_key in self._filter_cache:
            return self._filter_cache[cache_key]

        tensor_filters = self.build_filters_tensor(rows, cols)
        filters: List[List[np.ndarray]] = [
            [tensor_filters[o, s] for s in range(self.num_scales)]
            for o in range(self.num_orientations)
        ]
        self._filter_cache[cache_key] = filters
        return filters


class PhaseCongruencyEngine:
    """
    Computes illumination-invariant Phase Congruency and RIFT moment representations.
    Crucial for handling extreme shadow reversals on lunar crater rims.
    Vectorized O(N log N) execution with zero explicit Python loops across scales and orientations.
    """

    def __init__(
        self,
        num_scales: int = 4,
        num_orientations: int = 6,
        min_wavelength: float = 3.0,
        mult: float = 2.1,
        k_noise_threshold: float = 2.0,
    ) -> None:
        self.filter_bank = LogGaborFilterBank(
            num_scales=num_scales,
            num_orientations=num_orientations,
            min_wavelength=min_wavelength,
            mult=mult,
        )
        self.k_noise = k_noise_threshold

    def compute(self, image: np.ndarray) -> PhaseCongruencyOutput:
        """
        Executes fully vectorized Log-Gabor phase congruency decomposition.
        
        Args:
            image: 2D grayscale image (float32, [0, 1]).
            
        Returns:
            PhaseCongruencyOutput dataclass containing PC, M_max, M_min, and MIM.
        """
        img = image.astype(np.float32)
        h, w = img.shape
        fft_img = np.fft.fft2(img)

        # 4D filter bank: [num_orientations, num_scales, h, w]
        filters_tensor = self.filter_bank.build_filters_tensor(h, w)
        num_orient = self.filter_bank.num_orientations

        # Batched spectral filtering: [O, S, H, W]
        filtered_spectra = fft_img[None, None, :, :] * filters_tensor

        # Vectorized 2D inverse FFT across all orientations and scales simultaneously - O(N log N)
        analytic = np.fft.ifft2(filtered_spectra, axes=(-2, -1))
        e_val = np.real(analytic).astype(np.float32)
        o_val = np.imag(analytic).astype(np.float32)

        amp = np.sqrt(e_val**2 + o_val**2)
        sum_amplitude = np.sum(amp, axis=(0, 1))

        # Local energy per orientation: [O, H, W]
        sum_e = np.sum(e_val, axis=1)
        sum_o = np.sum(o_val, axis=1)
        orientation_energy = np.sqrt(sum_e**2 + sum_o**2)

        # Rayleigh noise estimation from smallest scale responses (Kovesi noise model)
        smallest_scale_amp = amp[:, 0, :, :]
        tau = np.median(smallest_scale_amp, axis=(-2, -1), keepdims=True) / np.sqrt(np.log(4.0))
        noise_thresh = self.k_noise * tau

        # Thresholded energy per orientation
        thresholded_e = np.maximum(orientation_energy - noise_thresh, 0.0)
        total_energy = np.sum(thresholded_e, axis=0)

        eps = 1e-4
        pc_total = np.clip(total_energy / (sum_amplitude + eps), 0.0, 1.0)

        # Vectorized Kovesi Moment Analysis for M_max and M_min
        angles = (
            np.arange(num_orient, dtype=np.float32) * (np.pi / num_orient)
        ).reshape(-1, 1, 1)
        px = thresholded_e * np.cos(angles)
        py = thresholded_e * np.sin(angles)

        cov_x2 = np.sum(px**2, axis=0) / (num_orient / 2.0)
        cov_y2 = np.sum(py**2, axis=0) / (num_orient / 2.0)
        cov_xy = 2.0 * np.sum(px * py, axis=0) / (num_orient / 2.0)

        term = np.sqrt(cov_xy**2 + (cov_x2 - cov_y2)**2 + 1e-8)
        m_max = 0.5 * (cov_y2 + cov_x2 + term)
        m_min = 0.5 * (cov_y2 + cov_x2 - term)

        # Normalize moments to [0, 1]
        m_max = np.clip(m_max / (np.max(m_max) + eps), 0.0, 1.0)
        m_min = np.clip(m_min / (np.max(m_min) + eps), 0.0, 1.0)

        # Maximum Index Map (MIM) for RIFT descriptor
        mim = np.argmax(orientation_energy, axis=0).astype(np.uint8)

        return PhaseCongruencyOutput(
            phase_congruency=pc_total,
            max_moment=m_max,
            min_moment=m_min,
            orientation_max_idx=mim,
            feature_energy=total_energy,
        )


class RIFTDescriptorExtractor:
    """
    Extracts Radiation-variation Insensitive Feature Transform (RIFT) descriptors.
    Uses Maximum Index Map (MIM) circular convolution patches to achieve
    absolute sun angle, shadow reversal, and sensor modality invariance.
    """

    def __init__(
        self,
        patch_size: int = 48,
        spatial_bins: int = 4,
        num_orientations: int = 6,
    ) -> None:
        self.patch_size = patch_size
        self.spatial_bins = spatial_bins
        self.num_orientations = num_orientations
        self.bin_size = patch_size // spatial_bins
        self.descriptor_dim = spatial_bins * spatial_bins * num_orientations

    def compute_descriptors(
        self,
        mim: np.ndarray,
        keypoints: List[Tuple[float, float]],
    ) -> Tuple[np.ndarray, List[Tuple[float, float]]]:
        """
        Computes normalized RIFT descriptors for given (x, y) keypoints.
        
        Args:
            mim: Maximum Index Map from PhaseCongruencyEngine.
            keypoints: List of (x, y) coordinates.
            
        Returns:
            Tuple of (descriptors: [N, descriptor_dim], valid_keypoints)
        """
        h, w = mim.shape
        half = self.patch_size // 2
        descriptors: List[np.ndarray] = []
        valid_kps: List[Tuple[float, float]] = []
        
        for (x, y) in keypoints:
            ix, iy = int(round(x)), int(round(y))
            if (ix - half < 0 or ix + half >= w or
                iy - half < 0 or iy + half >= h):
                continue
                
            patch = mim[iy - half : iy + half, ix - half : ix + half]
            desc = np.zeros((self.spatial_bins, self.spatial_bins, self.num_orientations), dtype=np.float32)
            
            for by in range(self.spatial_bins):
                for bx in range(self.spatial_bins):
                    cell = patch[
                        by * self.bin_size : (by + 1) * self.bin_size,
                        bx * self.bin_size : (bx + 1) * self.bin_size
                    ]
                    # Compute histogram of orientations in this spatial bin
                    hist, _ = np.histogram(cell, bins=self.num_orientations, range=(0, self.num_orientations))
                    desc[by, bx, :] = hist
                    
            flat_desc = desc.flatten()
            norm = np.linalg.norm(flat_desc) + 1e-7
            flat_desc /= norm
            
            # Non-linear thresholding & re-normalization (similar to SIFT saturation clipping)
            flat_desc = np.minimum(flat_desc, 0.2)
            flat_desc /= (np.linalg.norm(flat_desc) + 1e-7)
            
            descriptors.append(flat_desc)
            valid_kps.append((x, y))
            
        if len(descriptors) == 0:
            return np.empty((0, self.descriptor_dim), dtype=np.float32), []
            
        return np.array(descriptors, dtype=np.float32), valid_kps
