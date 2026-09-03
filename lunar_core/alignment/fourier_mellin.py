"""
Fourier-Mellin Global Invariant Alignment (Rotation, Scale, Translation Decoupling).
"""

from __future__ import annotations

from typing import Tuple
import cv2
import numpy as np


class FourierMellinAligner:
    """
    Decouples global rotation and scaling from translation using Log-Polar Fourier spectra.
    """

    @staticmethod
    def _spectrum(img: np.ndarray) -> np.ndarray:
        h, w = img.shape
        win = cv2.createHanningWindow((w, h), cv2.CV_32F)
        f = np.fft.fft2(img.astype(np.float32) * win)
        f_shift = np.fft.fftshift(f)
        mag = np.log1p(np.abs(f_shift))
        return cv2.normalize(mag, None, 0.0, 1.0, cv2.NORM_MINMAX)

    @classmethod
    def estimate_coarse_similarity(
        cls,
        img_ref: np.ndarray,
        img_tgt: np.ndarray,
    ) -> Tuple[float, float, float, float, float]:
        """
        Estimates coarse similarity parameters:
            rotation_deg, scale, dx, dy, confidence
        """
        h, w = img_ref.shape
        if img_tgt.shape != (h, w):
            img_tgt = cv2.resize(img_tgt, (w, h), interpolation=cv2.INTER_LINEAR)

        mag_ref = cls._spectrum(img_ref)
        mag_tgt = cls._spectrum(img_tgt)

        center = (w / 2.0, h / 2.0)
        max_r = min(w, h) / 2.0
        flags = cv2.INTER_LINEAR + cv2.WARP_POLAR_LOG

        lp_ref = cv2.warpPolar(mag_ref, (w, h), center, max_r, flags)
        lp_tgt = cv2.warpPolar(mag_tgt, (w, h), center, max_r, flags)

        # Phase correlation on Log-Polar spectra
        shift, conf = cv2.phaseCorrelate(lp_ref, lp_tgt)
        d_log_r, d_theta_px = shift

        angle_deg = (d_theta_px / h) * 360.0
        angle_deg = (angle_deg + 180.0) % 360.0 - 180.0
        scale = np.exp(d_log_r / (w / np.log(max_r + 1e-6)))

        # Disambiguate theta vs theta + 180 deg using spatial phase correlation
        cand1 = (angle_deg + 180.0) % 360.0 - 180.0
        cand2 = (cand1 + 180.0) % 360.0
        if cand2 > 180.0:
            cand2 -= 360.0

        rot1 = cv2.getRotationMatrix2D(center, -cand1, 1.0 / (scale + 1e-6))
        derot1 = cv2.warpAffine(img_tgt, rot1, (w, h), flags=cv2.INTER_LINEAR)
        shift1, conf1 = cv2.phaseCorrelate(img_ref, derot1)

        rot2 = cv2.getRotationMatrix2D(center, -cand2, 1.0 / (scale + 1e-6))
        derot2 = cv2.warpAffine(img_tgt, rot2, (w, h), flags=cv2.INTER_LINEAR)
        shift2, conf2 = cv2.phaseCorrelate(img_ref, derot2)

        if conf2 > conf1:
            best_angle = cand2
            dx, dy = shift2
            trans_conf = conf2
        else:
            best_angle = cand1
            dx, dy = shift1
            trans_conf = conf1

        return float(best_angle), float(scale), float(dx), float(dy), float(conf * trans_conf)

