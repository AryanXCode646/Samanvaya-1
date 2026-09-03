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
        self._grid_cache: dict = {}

    def build_filters(self, rows: int, cols: int) -> List[List[np.ndarray]]:
        """
        Constructs 2D frequency-domain Log-Gabor kernels of dimensions (rows, cols).
        Caches precomputed frequency grids and kernels for O(1) repeated evaluation.
        """
        cache_key = (rows, cols)
        if cache_key in self._filter_cache:
            return self._filter_cache[cache_key]

        if cache_key in self._grid_cache:
            radius, theta = self._grid_cache[cache_key]
        else:
            # Frequency grid [-0.5, 0.5]
            u1 = np.linspace(-0.5, 0.5, cols, endpoint=False)
            u2 = np.linspace(-0.5, 0.5, rows, endpoint=False)
            x, y = np.meshgrid(u1, u2)
            
            # FFT shift to align DC at (0, 0)
            x = np.fft.ifftshift(x)
            y = np.fft.ifftshift(y)
            
            radius = np.sqrt(x**2 + y**2)
            theta = np.arctan2(-y, x)
            radius[0, 0] = 1.0  # Avoid log(0) singularity at DC
            self._grid_cache[cache_key] = (radius, theta)
        
        theta_sigma = np.pi / self.num_orientations / self.d_theta_on_sigma
        
        filters: List[List[np.ndarray]] = []
        for o in range(self.num_orientations):
            ang = o * np.pi / self.num_orientations
            # Angular spread filter (Gaussian in angle space)
            diff_theta1 = np.abs(theta - ang)
            diff_theta1 = np.minimum(diff_theta1, 2.0 * np.pi - diff_theta1)
            
            diff_theta2 = np.abs(theta - (ang + np.pi))
            diff_theta2 = np.minimum(diff_theta2, 2.0 * np.pi - diff_theta2)
            
            diff_theta = np.minimum(diff_theta1, diff_theta2)
            spread = np.exp(-(diff_theta**2) / (2.0 * theta_sigma**2))
            
            scale_filters: List[np.ndarray] = []
            for s in range(self.num_scales):
                wavelength = self.min_wavelength * (self.mult ** s)
                f0 = 1.0 / wavelength
                
                # Radial Log-Gabor filter
                log_rad = np.log(radius / f0)
                radial = np.exp(-(log_rad**2) / (2.0 * (np.log(self.sigma_on_f))**2))
                radial[0, 0] = 0.0  # Zero DC component
                
                filt = (radial * spread).astype(np.float32)
                scale_filters.append(filt)
            filters.append(scale_filters)
            
        self._filter_cache[cache_key] = filters
        return filters


class PhaseCongruencyEngine:
    """
    Computes illumination-invariant Phase Congruency and RIFT moment representations.
    Crucial for handling extreme shadow reversals on lunar crater rims.
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
        Executes Log-Gabor phase congruency decomposition.
        
        Args:
            image: 2D grayscale image (float32, [0, 1]).
            
        Returns:
            PhaseCongruencyOutput dataclass containing PC, M_max, M_min, and MIM.
        """
        img = image.astype(np.float32)
        h, w = img.shape
        fft_img = np.fft.fft2(img)
        
        filters = self.filter_bank.build_filters(h, w)
        num_orient = self.filter_bank.num_orientations
        num_scales = self.filter_bank.num_scales
        
        eo: List[List[np.ndarray]] = []
        amp: List[List[np.ndarray]] = []
        orientation_energy: List[np.ndarray] = []
        sum_amplitude = np.zeros((h, w), dtype=np.float32)
        
        for o in range(num_orient):
            eo_scale: List[np.ndarray] = []
            amp_scale: List[np.ndarray] = []
            sum_e = np.zeros((h, w), dtype=np.float32)
            sum_o = np.zeros((h, w), dtype=np.float32)
            
            for s in range(num_scales):
                kernel = filters[o][s]
                # Inverse FFT of bandpassed spectrum gives analytic signal (even + j*odd)
                analytic = np.fft.ifft2(fft_img * kernel)
                e_val = np.real(analytic).astype(np.float32)
                o_val = np.imag(analytic).astype(np.float32)
                
                a_val = np.sqrt(e_val**2 + o_val**2)
                eo_scale.append(analytic)
                amp_scale.append(a_val)
                sum_amplitude += a_val
                
                sum_e += e_val
                sum_o += o_val
                
            eo.append(eo_scale)
            amp.append(amp_scale)
            # Local energy at orientation o
            e_mag = np.sqrt(sum_e**2 + sum_o**2)
            orientation_energy.append(e_mag)
            
        # Rayleigh noise estimation from smallest scale responses (Kovesi noise model)
        total_energy = np.zeros((h, w), dtype=np.float32)
        pc_orientation: List[np.ndarray] = []
        
        for o in range(num_orient):
            e_mag = orientation_energy[o]
            # Smallest scale amplitude for noise estimate
            smallest_scale_amp = amp[o][0]
            tau = np.median(smallest_scale_amp) / np.sqrt(np.log(4.0))
            noise_thresh = self.k_noise * tau
            
            # Thresholded energy
            thresholded_e = np.maximum(e_mag - noise_thresh, 0.0)
            total_energy += thresholded_e
            pc_orientation.append(thresholded_e)
            
        eps = 1e-4
        pc_total = total_energy / (sum_amplitude + eps)
        pc_total = np.clip(pc_total, 0.0, 1.0)
        
        # Kovesi Moment Analysis for M_max and M_min
        # Moments of phase congruency determine orientation and anisotropy of feature
        cov_x2 = np.zeros((h, w), dtype=np.float32)
        cov_y2 = np.zeros((h, w), dtype=np.float32)
        cov_xy = np.zeros((h, w), dtype=np.float32)
        
        for o in range(num_orient):
            angle = o * np.pi / num_orient
            p = pc_orientation[o]
            px = p * np.cos(angle)
            py = p * np.sin(angle)
            cov_x2 += px**2
            cov_y2 += py**2
            cov_xy += px * py
            
        cov_x2 /= (num_orient / 2.0)
        cov_y2 /= (num_orient / 2.0)
        cov_xy = 2.0 * cov_xy / (num_orient / 2.0)
        
        term = np.sqrt(cov_xy**2 + (cov_x2 - cov_y2)**2 + 1e-8)
        m_max = 0.5 * (cov_y2 + cov_x2 + term)
        m_min = 0.5 * (cov_y2 + cov_x2 - term)
        
        # Normalize moments to [0, 1]
        m_max = np.clip(m_max / (np.max(m_max) + eps), 0.0, 1.0)
        m_min = np.clip(m_min / (np.max(m_min) + eps), 0.0, 1.0)
        
        # Maximum Index Map (MIM) for RIFT descriptor
        # Stack orientation energies and find argmax orientation per pixel
        energy_stack = np.stack(orientation_energy, axis=0)  # [num_orient, h, w]
        mim = np.argmax(energy_stack, axis=0).astype(np.uint8)
        
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
