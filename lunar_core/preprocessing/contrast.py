"""
Dynamic Contrast Equalization (Multi-Scale Retinex & CLAHE).
"""

from __future__ import annotations

from typing import Tuple
import cv2
import numpy as np


class DynamicContrastEqualizer:
    """
    Compresses dynamic range across shadowed craters and enhances subtle mare contrast.
    """

    def __init__(
        self,
        retinex_sigmas: Tuple[float, ...] = (15.0, 80.0, 250.0),
        clahe_clip_limit: float = 2.5,
        clahe_grid_size: Tuple[int, int] = (8, 8),
    ) -> None:
        self.sigmas = retinex_sigmas
        self.clahe_clip = clahe_clip_limit
        self.clahe_grid = clahe_grid_size

    def multiscale_retinex(self, image: np.ndarray) -> np.ndarray:
        """
        R_MSR = sum_n w_n * [ ln(I) - ln(G_sigma * I) ]
        """
        img_f = np.maximum(image.astype(np.float32), 1e-4)
        log_i = np.log(img_f)
        msr = np.zeros_like(img_f)
        weight = 1.0 / len(self.sigmas)

        for sigma in self.sigmas:
            ksize = int(2 * np.ceil(2 * sigma) + 1)
            blurred = cv2.GaussianBlur(img_f, (ksize, ksize), sigma)
            blurred = np.maximum(blurred, 1e-4)
            msr += weight * (log_i - np.log(blurred))

        p2, p98 = np.percentile(msr, (2.0, 98.0))
        if p98 > p2:
            return np.clip((msr - p2) / (p98 - p2), 0.0, 1.0).astype(np.float32)
        return cv2.normalize(msr, None, 0.0, 1.0, cv2.NORM_MINMAX).astype(np.float32)

    def apply_clahe(self, image: np.ndarray) -> np.ndarray:
        """
        Contrast Limited Adaptive Histogram Equalization.
        """
        uint8_img = (np.clip(image, 0.0, 1.0) * 255.0).astype(np.uint8)
        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip, tileGridSize=self.clahe_grid)
        enhanced = clahe.apply(uint8_img)
        return (enhanced.astype(np.float32) / 255.0)

    def process(self, image: np.ndarray, blend: float = 0.5) -> np.ndarray:
        """
        Blends Multi-Scale Retinex dynamic range compression with CLAHE local textures.
        """
        msr = self.multiscale_retinex(image)
        clahe = self.apply_clahe(msr)
        return np.clip(blend * clahe + (1.0 - blend) * msr, 0.0, 1.0)
