"""
Hierarchical Scale-Space & Coarse-to-Fine Registration Orchestrator.
ISRO Chandrayaan-2 Planetary Remote Sensing (OHRC, TMC-2, IIRS, LRO NAC).

Handles massive resolution ratios (e.g. 0.25m OHRC vs 5m TMC-2: 20x ratio;
5m TMC-2 vs 80m IIRS: 16x ratio; OHRC vs IIRS: up to 320x ratio).

Architecture:
1. Physical GSD-based Anti-Aliased Nyquist decimation.
2. Hierarchical Gaussian Scale-Space Pyramids with scale step octaves.
3. Coarse Stage: Phase Correlation / Fourier-Mellin transform for global shift/rotation.
4. Fine Stage: Guided multi-scale local feature matching with scale propagation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import cv2
import numpy as np


class ScaleSpacePyramid:
    """
    Constructs an anti-aliased Gaussian scale-space pyramid.
    Applies Gaussian low-pass filtering before subsampling to prevent aliasing.
    """

    def __init__(self, num_levels: int = 4, scale_factor: float = 2.0) -> None:
        self.num_levels = num_levels
        self.scale_factor = scale_factor

    def build_pyramid(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Builds image pyramid from fine (level 0) to coarse (level N-1).
        """
        pyramid = [image.astype(np.float32)]
        current = image.astype(np.float32)

        for _ in range(1, self.num_levels):
            # Compute Nyquist anti-aliasing sigma
            sigma = max(0.5, (self.scale_factor - 1.0) * 0.6)
            ksize = int(2 * np.ceil(2 * sigma) + 1)
            blurred = cv2.GaussianBlur(current, (ksize, ksize), sigma)
            
            new_w = max(16, int(round(current.shape[1] / self.scale_factor)))
            new_h = max(16, int(round(current.shape[0] / self.scale_factor)))
            downsampled = cv2.resize(blurred, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            pyramid.append(downsampled)
            current = downsampled

        return pyramid


class PhaseCorrelationEstimator:
    """
    Computes global translational shift between images using frequency-domain Phase Correlation.
    In frequency space:
        Q = (F1 * F2*) / |F1 * F2*|
        Inverse FFT of Q yields a sharp peak at (delta_x, delta_y).
    """

    @staticmethod
    def estimate_translation(img1: np.ndarray, img2: np.ndarray) -> Tuple[float, float, float]:
        """
        Estimates translation (dx, dy) and cross-correlation response peak.
        
        Args:
            img1: 2D reference image.
            img2: 2D target image of same dimensions.
            
        Returns:
            Tuple of (dx, dy, response)
        """
        h, w = img1.shape
        if img2.shape != (h, w):
            img2 = cv2.resize(img2, (w, h), interpolation=cv2.INTER_LINEAR)

        # Apply Hanning window to reduce spectral leakage at boundaries
        win = cv2.createHanningWindow((w, h), cv2.CV_32F)
        f1 = cv2.dft(img1.astype(np.float32) * win, flags=cv2.DFT_COMPLEX_OUTPUT)
        f2 = cv2.dft(img2.astype(np.float32) * win, flags=cv2.DFT_COMPLEX_OUTPUT)

        # Cross power spectrum
        f2_conj = np.zeros_like(f2)
        f2_conj[:, :, 0] = f2[:, :, 0]
        f2_conj[:, :, 1] = -f2[:, :, 1]

        # Complex multiplication: (a+ib)(c-id) = (ac+bd) + i(bc-ad)
        real = f1[:, :, 0] * f2_conj[:, :, 0] - f1[:, :, 1] * f2_conj[:, :, 1]
        imag = f1[:, :, 0] * f2_conj[:, :, 1] + f1[:, :, 1] * f2_conj[:, :, 0]
        mag = np.sqrt(real**2 + imag**2) + 1e-7

        cps = np.zeros_like(f1)
        cps[:, :, 0] = real / mag
        cps[:, :, 1] = imag / mag

        # Inverse DFT
        corr = cv2.idft(cps, flags=cv2.DFT_SCALE | cv2.DFT_REAL_OUTPUT)
        
        # Shift zero-frequency component to center
        corr = np.fft.fftshift(corr)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(corr)
        peak_x, peak_y = max_loc

        # Translation relative to center
        center_x = w // 2
        center_y = h // 2
        dx = float(peak_x - center_x)
        dy = float(peak_y - center_y)

        return dx, dy, float(max_val)


class HierarchicalScaleSpaceRegistrar:
    """
    Orchestrates coarse-to-fine multi-resolution image alignment.
    Bridges high resolution ratios (OHRC ~0.25m vs TMC ~5m vs IIRS ~80m).
    """

    def __init__(
        self,
        pyramid_levels: int = 4,
        scale_step: float = 2.0,
    ) -> None:
        self.pyramid_builder = ScaleSpacePyramid(num_levels=pyramid_levels, scale_factor=scale_step)
        self.phase_correlator = PhaseCorrelationEstimator()

    def resample_to_common_gsd(
        self,
        ref_img: np.ndarray,
        ref_gsd: float,
        target_img: np.ndarray,
        target_gsd: float,
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Anti-alias resamples higher-resolution image to match the coarser ground resolution.
        
        Args:
            ref_img: Reference image.
            ref_gsd: GSD in meters/pixel (e.g. 0.25m for OHRC).
            target_img: Target image.
            target_gsd: GSD in meters/pixel (e.g. 5.0m for TMC).
            
        Returns:
            Tuple of (resampled_ref, resampled_target, scale_ratio)
        """
        scale_ratio = target_gsd / ref_gsd
        
        if np.isclose(scale_ratio, 1.0, atol=1e-2):
            return ref_img.copy(), target_img.copy(), 1.0

        if scale_ratio > 1.0:
            # Reference image is finer (e.g. OHRC 0.25m vs TMC 5m -> ratio 20)
            # Decimate reference image
            sigma = max(0.5, (scale_ratio - 1.0) * 0.5)
            ksize = int(2 * np.ceil(2 * sigma) + 1)
            blurred = cv2.GaussianBlur(ref_img, (ksize, ksize), sigma)
            new_w = max(16, int(round(ref_img.shape[1] / scale_ratio)))
            new_h = max(16, int(round(ref_img.shape[0] / scale_ratio)))
            resampled_ref = cv2.resize(blurred, (new_w, new_h), interpolation=cv2.INTER_AREA)
            return resampled_ref, target_img.copy(), scale_ratio
        else:
            # Target image is finer
            inv_ratio = 1.0 / scale_ratio
            sigma = max(0.5, (inv_ratio - 1.0) * 0.5)
            ksize = int(2 * np.ceil(2 * sigma) + 1)
            blurred = cv2.GaussianBlur(target_img, (ksize, ksize), sigma)
            new_w = max(16, int(round(target_img.shape[1] / inv_ratio)))
            new_h = max(16, int(round(target_img.shape[0] / inv_ratio)))
            resampled_target = cv2.resize(blurred, (new_w, new_h), interpolation=cv2.INTER_AREA)
            return ref_img.copy(), resampled_target, scale_ratio


class FourierMellinRegistrar:
    """
    Fourier-Mellin Phase Correlation for rotation and scale invariant global alignment.
    Decouples rotation and scale by operating on Log-Polar transformed magnitude spectra.
    """

    @staticmethod
    def _magnitude_spectrum(img: np.ndarray) -> np.ndarray:
        h, w = img.shape
        win = cv2.createHanningWindow((w, h), cv2.CV_32F)
        f = np.fft.fft2(img.astype(np.float32) * win)
        f_shift = np.fft.fftshift(f)
        mag = np.log1p(np.abs(f_shift))
        return cv2.normalize(mag, None, 0.0, 1.0, cv2.NORM_MINMAX)

    @classmethod
    def estimate_similarity_parameters(
        cls,
        img_ref: np.ndarray,
        img_tgt: np.ndarray,
    ) -> Tuple[float, float, float, float, float]:
        """
        Estimates global rotation angle (degrees), scale factor, and translation (dx, dy).
        
        Returns:
            Tuple of (rotation_deg, scale, dx, dy, confidence)
        """
        h, w = img_ref.shape
        if img_tgt.shape != (h, w):
            img_tgt = cv2.resize(img_tgt, (w, h), interpolation=cv2.INTER_LINEAR)

        # 1. Compute shifted Fourier magnitude spectra
        mag1 = cls._magnitude_spectrum(img_ref)
        mag2 = cls._magnitude_spectrum(img_tgt)

        # 2. Resample magnitude spectra to log-polar coordinates
        center = (w / 2.0, h / 2.0)
        max_radius = min(w, h) / 2.0
        flags = cv2.INTER_LINEAR + cv2.WARP_POLAR_LOG

        lp1 = cv2.warpPolar(mag1, (w, h), center, max_radius, flags)
        lp2 = cv2.warpPolar(mag2, (w, h), center, max_radius, flags)

        # 3. Phase correlation on log-polar spectra
        correlator = PhaseCorrelationEstimator()
        d_log_r, d_theta_px, conf = correlator.estimate_translation(lp1, lp2)

        # Convert pixel shifts to rotation angle and scale
        angle_deg = (d_theta_px / h) * 360.0
        # Wrap angle to [-180, 180]
        angle_deg = (angle_deg + 180.0) % 360.0 - 180.0
        
        # Scale: max_radius is mapped logarithmically across width
        scale_est = np.exp(d_log_r / (w / np.log(max_radius + 1e-6)))

        # 4. Correct for estimated rotation and scale, then estimate (dx, dy)
        rot_mat = cv2.getRotationMatrix2D(center, -angle_deg, 1.0 / (scale_est + 1e-6))
        derotated_tgt = cv2.warpAffine(img_tgt, rot_mat, (w, h), flags=cv2.INTER_LINEAR)
        dx, dy, trans_conf = correlator.estimate_translation(img_ref, derotated_tgt)

        return float(angle_deg), float(scale_est), float(dx), float(dy), float(conf * trans_conf)


@dataclass
class RoiCropResult:
    """
    Cropped Region-of-Interest (ROI) data bundle for fine deep matching.
    """
    ref_roi: np.ndarray
    target_aligned: np.ndarray
    ref_bbox: Tuple[int, int, int, int]  # (xmin, ymin, xmax, ymax)
    coarse_rotation_deg: float
    coarse_scale: float
    coarse_translation: Tuple[float, float]
    confidence: float


class RoiLocalizer:
    """
    Projects target imagery footprint onto reference space after coarse Fourier-Mellin
    registration and extracts aligned overlapping Region-of-Interest (ROI) patches.
    """

    def __init__(self, padding_pixels: int = 16) -> None:
        self.padding = padding_pixels
        self.fm_registrar = FourierMellinRegistrar()

    def localize_and_crop(
        self,
        img_ref: np.ndarray,
        img_tgt: np.ndarray,
        ref_gsd: float = 1.0,
        target_gsd: float = 1.0,
    ) -> RoiCropResult:
        """
        Executes GSD decimation, Fourier-Mellin global similarity solve, and ROI cropping.
        """
        # Step 1: Decimate to common ground resolution
        registrar = HierarchicalScaleSpaceRegistrar()
        ref_common, tgt_common, scale_ratio = registrar.resample_to_common_gsd(
            img_ref, ref_gsd, img_tgt, target_gsd
        )

        # Step 2: Fourier-Mellin log-polar correlation for coarse (theta, scale, dx, dy)
        rot_deg, scale_est, dx, dy, conf = self.fm_registrar.estimate_similarity_parameters(
            ref_common, tgt_common
        )

        h_ref, w_ref = ref_common.shape
        h_tgt, w_tgt = tgt_common.shape

        # Step 3: Align target using estimated similarity transform
        center = (w_tgt / 2.0, h_tgt / 2.0)
        rot_mat = cv2.getRotationMatrix2D(center, -rot_deg, 1.0 / (scale_est + 1e-6))
        rot_mat[0, 2] += dx
        rot_mat[1, 2] += dy

        aligned_tgt = cv2.warpAffine(
            tgt_common, rot_mat, (w_ref, h_ref), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0
        )

        # Step 4: Compute valid intersection ROI
        mask_ref = (ref_common > 0).astype(np.uint8)
        mask_tgt = (aligned_tgt > 0).astype(np.uint8)
        intersection = mask_ref & mask_tgt

        contours, _ = cv2.findContours(intersection, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            x, y, w, h = cv2.boundingRect(np.vstack(contours))
            xmin = max(0, x - self.padding)
            ymin = max(0, y - self.padding)
            xmax = min(w_ref, x + w + self.padding)
            ymax = min(h_ref, y + h + self.padding)
        else:
            xmin, ymin, xmax, ymax = 0, 0, w_ref, h_ref

        ref_roi = ref_common[ymin:ymax, xmin:xmax]
        tgt_roi = aligned_tgt[ymin:ymax, xmin:xmax]

        return RoiCropResult(
            ref_roi=ref_roi,
            target_aligned=tgt_roi,
            ref_bbox=(xmin, ymin, xmax, ymax),
            coarse_rotation_deg=rot_deg,
            coarse_scale=scale_est * scale_ratio,
            coarse_translation=(dx, dy),
            confidence=conf,
        )


