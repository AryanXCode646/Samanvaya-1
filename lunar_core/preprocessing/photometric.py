"""
Planetary Photometric Reflectance Normalizer (Lommel-Seeliger & Hapke).
"""

from __future__ import annotations

from typing import Tuple
import numpy as np
from lunar_core.models import SunAngles


class PhotometricNormalizer:
    """
    Normalizes optical lunar imagery against variable solar incidence, emission, and phase.
    """

    def __init__(self, ref_incidence_deg: float = 30.0, ref_emission_deg: float = 0.0) -> None:
        self.ref_i = np.radians(ref_incidence_deg)
        self.ref_e = np.radians(ref_emission_deg)

    @staticmethod
    def lommel_seeliger(cos_i: np.ndarray, cos_e: np.ndarray) -> np.ndarray:
        """
        Lommel-Seeliger scattering law for particulate planetary regolith:
            R_LS(i, e) = cos(i) / (cos(i) + cos(e))
        """
        denom = np.maximum(cos_i + cos_e, 1e-6)
        return np.maximum(cos_i, 0.0) / denom

    def normalize(
        self,
        image: np.ndarray,
        sun_angles: SunAngles,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Corrects image intensities to standard reference lighting geometry.
        """
        img_f = image.astype(np.float32)
        h, w = img_f.shape
        sun_vec = sun_angles.sun_vector

        cos_i = np.full((h, w), np.maximum(sun_vec[2], 0.01), dtype=np.float32)
        cos_e = np.ones((h, w), dtype=np.float32)

        ref_rls = self.lommel_seeliger(np.cos(self.ref_i), np.cos(self.ref_e))
        acq_rls = self.lommel_seeliger(cos_i, cos_e)

        corr = np.where(acq_rls > 1e-4, ref_rls / np.maximum(acq_rls, 1e-4), 1.0)
        corrected = img_f * corr

        shadow_thresh = np.quantile(img_f, 0.05)
        valid_mask = (img_f > shadow_thresh) & (cos_i > 0.05)

        valid_pixels = corrected[valid_mask]
        if len(valid_pixels) > 0:
            p2, p98 = np.percentile(valid_pixels, (2.0, 98.0))
            if p98 > p2:
                corrected = np.clip((corrected - p2) / (p98 - p2), 0.0, 1.0)
            else:
                corrected = np.clip(corrected, 0.0, 1.0)
        else:
            corrected = np.clip(corrected, 0.0, 1.0)

        return corrected, valid_mask
