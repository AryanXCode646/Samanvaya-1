"""
Scale-Space Resampling and ROI Localization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
import cv2
import numpy as np

from lunar_core.alignment.fourier_mellin import FourierMellinAligner


@dataclass
class RoiBundle:
    ref_roi: np.ndarray
    target_roi: np.ndarray
    ref_bbox: Tuple[int, int, int, int]  # (xmin, ymin, xmax, ymax)
    coarse_rotation_deg: float
    coarse_scale: float
    coarse_translation: Tuple[float, float]
    confidence: float


class ScaleSpaceLocalizer:
    """
    Downsamples disparate sensor resolutions (e.g. 20x for OHRC vs TMC-2) and extracts overlapping ROIs.
    """

    @staticmethod
    def resample_to_common_gsd(
        ref_img: np.ndarray,
        ref_gsd: float,
        tgt_img: np.ndarray,
        tgt_gsd: float,
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Anti-alias resamples the finer resolution image to match the coarser image GSD.
        """
        ratio = tgt_gsd / ref_gsd
        if np.isclose(ratio, 1.0, atol=1e-2):
            return ref_img.copy(), tgt_img.copy(), 1.0

        if ratio > 1.0:
            sigma = max(0.5, (ratio - 1.0) * 0.5)
            ksize = int(2 * np.ceil(2 * sigma) + 1)
            blurred = cv2.GaussianBlur(ref_img, (ksize, ksize), sigma)
            new_w = max(16, int(round(ref_img.shape[1] / ratio)))
            new_h = max(16, int(round(ref_img.shape[0] / ratio)))
            resampled = cv2.resize(blurred, (new_w, new_h), interpolation=cv2.INTER_AREA)
            return resampled, tgt_img.copy(), ratio
        else:
            inv_ratio = 1.0 / ratio
            sigma = max(0.5, (inv_ratio - 1.0) * 0.5)
            ksize = int(2 * np.ceil(2 * sigma) + 1)
            blurred = cv2.GaussianBlur(tgt_img, (ksize, ksize), sigma)
            new_w = max(16, int(round(tgt_img.shape[1] / inv_ratio)))
            new_h = max(16, int(round(tgt_img.shape[0] / inv_ratio)))
            resampled = cv2.resize(blurred, (new_w, new_h), interpolation=cv2.INTER_AREA)
            return ref_img.copy(), resampled, ratio

    @classmethod
    def extract_coarse_roi(
        cls,
        img_ref: np.ndarray,
        img_tgt: np.ndarray,
        ref_gsd: float = 1.0,
        tgt_gsd: float = 1.0,
        padding: int = 16,
    ) -> RoiBundle:
        ref_comm, tgt_comm, scale_ratio = cls.resample_to_common_gsd(img_ref, ref_gsd, img_tgt, tgt_gsd)
        rot_deg, scale_est, dx, dy, conf = FourierMellinAligner.estimate_coarse_similarity(ref_comm, tgt_comm)

        h_ref, w_ref = ref_comm.shape
        center = (tgt_comm.shape[1] / 2.0, tgt_comm.shape[0] / 2.0)
        rot_mat = cv2.getRotationMatrix2D(center, -rot_deg, 1.0 / (scale_est + 1e-6))
        rot_mat[0, 2] += dx
        rot_mat[1, 2] += dy

        aligned_tgt = cv2.warpAffine(tgt_comm, rot_mat, (w_ref, h_ref), flags=cv2.INTER_LINEAR)
        mask = (ref_comm > 0).astype(np.uint8) & (aligned_tgt > 0).astype(np.uint8)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            x, y, w, h = cv2.boundingRect(np.vstack(contours))
            xmin, ymin = max(0, x - padding), max(0, y - padding)
            xmax, ymax = min(w_ref, x + w + padding), min(h_ref, y + h + padding)
        else:
            xmin, ymin, xmax, ymax = 0, 0, w_ref, h_ref

        return RoiBundle(
            ref_roi=ref_comm[ymin:ymax, xmin:xmax],
            target_roi=aligned_tgt[ymin:ymax, xmin:xmax],
            ref_bbox=(xmin, ymin, xmax, ymax),
            coarse_rotation_deg=rot_deg,
            coarse_scale=scale_est * scale_ratio,
            coarse_translation=(dx, dy),
            confidence=conf,
        )
