"""
Photometric Normalization & Reflectance Correction for Lunar Regolith.
ISRO Chandrayaan-2 Planetary Pipeline (OHRC, TMC-2, IIRS).

Implements:
1. Lommel-Seeliger scattering model for low-albedo particulate planetary regolith.
2. Hapke-based isotropic/anisotropic lunar photometric correction.
3. McEwen / USGS lunar empirical photometric normalization.
4. Robust dynamic shadow & penumbra masking.
"""

from __future__ import annotations

from typing import Optional, Tuple
import numpy as np
from ch2_lunar_reg.domain.models import SunAngles


class LunarPhotometricNormalizer:
    """
    Photometric correction engine for planetary optical remote sensing.
    
    Standardizes lunar radiance to reference photometric angles:
        i_ref = 30 deg, e_ref = 0 deg, phase_ref = 30 deg
    """

    DEFAULT_REF_INCIDENCE_DEG = 30.0
    DEFAULT_REF_EMISSION_DEG = 0.0
    DEFAULT_REF_PHASE_DEG = 30.0
    LUNAR_ALBEDO_MARE = 0.08
    LUNAR_ALBEDO_HIGHLANDS = 0.16

    def __init__(
        self,
        ref_incidence_deg: float = DEFAULT_REF_INCIDENCE_DEG,
        ref_emission_deg: float = DEFAULT_REF_EMISSION_DEG,
        ref_phase_deg: float = DEFAULT_REF_PHASE_DEG,
        single_scattering_albedo: float = LUNAR_ALBEDO_HIGHLANDS,
        shadow_threshold_quantile: float = 0.03,
    ) -> None:
        self.ref_i = np.radians(ref_incidence_deg)
        self.ref_e = np.radians(ref_emission_deg)
        self.ref_phase = np.radians(ref_phase_deg)
        self.w = single_scattering_albedo
        self.shadow_quantile = shadow_threshold_quantile

    @staticmethod
    def lommel_seeliger(
        cos_i: np.ndarray,
        cos_e: np.ndarray,
        eps: float = 1e-6
    ) -> np.ndarray:
        """
        Lommel-Seeliger scattering law:
            R_LS = mu_0 / (mu_0 + mu) = cos(i) / (cos(i) + cos(e))
        
        Args:
            cos_i: Cosine of incidence angle (array or float)
            cos_e: Cosine of emission angle (array or float)
            eps: Epsilon to prevent division by zero in grazing illumination
            
        Returns:
            Dimensionless reflectance factor array
        """
        mu_0 = np.maximum(cos_i, 0.0)
        mu = np.maximum(cos_e, 0.0)
        denom = mu_0 + mu + eps
        return np.where(denom > eps, mu_0 / denom, 0.0)

    def hapke_isotropic(
        self,
        cos_i: np.ndarray,
        cos_e: np.ndarray,
        phase_rad: float,
        h_param: float = 0.06,
        b0_param: float = 1.0,
    ) -> np.ndarray:
        """
        Hapke (1981, 2002) bidirectional reflectance model for lunar surface.
        
        Args:
            cos_i: Cosine of incidence angle.
            cos_e: Cosine of emission angle.
            phase_rad: Phase angle in radians.
            h_param: Angular width of opposition surge.
            b0_param: Opposition surge amplitude.
        """
        mu_0 = np.maximum(cos_i, 1e-4)
        mu = np.maximum(cos_e, 1e-4)
        
        # Chandrasekhar H-function approximation: H(x) = (1 + 2x) / (1 + 2x * sqrt(1 - w))
        gamma = np.sqrt(np.maximum(1.0 - self.w, 1e-6))
        h_mu0 = (1.0 + 2.0 * mu_0) / (1.0 + 2.0 * mu_0 * gamma)
        h_mu = (1.0 + 2.0 * mu) / (1.0 + 2.0 * mu * gamma)
        
        # Shadow-hiding opposition effect B(g)
        b_phase = 1.0 + (b0_param / (1.0 + (1.0 / h_param) * np.tan(phase_rad / 2.0)))
        
        # Single particle phase function (isotropic P(g) = 1.0)
        p_phase = 1.0
        
        # Bidirectional reflectance:
        r = (self.w / (4.0 * np.pi)) * (mu_0 / (mu_0 + mu)) * (b_phase * p_phase + h_mu0 * h_mu - 1.0)
        return np.maximum(r, 0.0)

    def normalize_lommel_seeliger(
        self,
        image: np.ndarray,
        sun_angles: SunAngles,
        dem_slopes: Optional[Tuple[np.ndarray, np.ndarray]] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Normalizes lunar optical image against arbitrary solar elevation/azimuth.
        
        Args:
            image: 2D numpy array of digital numbers or calibrated radiance.
            sun_angles: SunAngles dataclass instance.
            dem_slopes: Optional (dz_dx, dz_dy) gradient from lunar DEM (e.g. TMC DEM or SLDEM2015).
            
        Returns:
            Tuple of (normalized_image, valid_mask)
        """
        img_norm = image.astype(np.float32)
        h, w = img_norm.shape
        
        # Solar geometry vectors
        sun_vec = sun_angles.sun_vector  # [sx, sy, sz]
        
        if dem_slopes is not None:
            dz_dx, dz_dy = dem_slopes
            # Normal vector n = [-dz_dx, -dz_dy, 1] / sqrt(1 + dz_dx^2 + dz_dy^2)
            denom = np.sqrt(1.0 + dz_dx**2 + dz_dy**2)
            nx = -dz_dx / denom
            ny = -dz_dy / denom
            nz = 1.0 / denom
            cos_i = nx * sun_vec[0] + ny * sun_vec[1] + nz * sun_vec[2]
            cos_e = nz  # Nadir spacecraft viewing vector v = [0, 0, 1]
        else:
            # Planar surface approximation: surface normal = [0, 0, 1]
            cos_i = np.full((h, w), np.maximum(sun_vec[2], 0.01), dtype=np.float32)
            cos_e = np.ones((h, w), dtype=np.float32)

        # Reference geometry reflectance
        ref_cos_i = np.cos(self.ref_i)
        ref_cos_e = np.cos(self.ref_e)
        ref_rls = self.lommel_seeliger(ref_cos_i, ref_cos_e)
        
        # Current acquisition reflectance
        acq_rls = self.lommel_seeliger(cos_i, cos_e)
        
        # Correction factor ratio
        corr_factor = np.where(acq_rls > 1e-4, ref_rls / np.maximum(acq_rls, 1e-4), 1.0)
        
        # Apply normalization
        corrected = img_norm * corr_factor
        
        # Shadow masking: identify unilluminated deep shadow craters
        shadow_thresh = np.quantile(img_norm, self.shadow_quantile)
        valid_mask = (img_norm > shadow_thresh) & (cos_i > 0.05)
        
        # Robust min-max scaling to [0, 1]
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

    @staticmethod
    def minnaert(
        cos_i: np.ndarray,
        cos_e: np.ndarray,
        k: float = 0.8,
        eps: float = 1e-6,
    ) -> np.ndarray:
        """
        Minnaert photometric scattering model for rough planetary surfaces:
            R_Minnaert = (cos i)^k * (cos e)^(k - 1)
        where k in [0.5, 1.0] is the limb-darkening exponent (default k=0.8 for lunar regolith).
        """
        mu_0 = np.maximum(cos_i, eps)
        mu = np.maximum(cos_e, eps)
        return np.maximum((mu_0 ** k) * (mu ** (k - 1.0)), 0.0)

    def normalize_minnaert(
        self,
        image: np.ndarray,
        sun_angles: SunAngles,
        k: float = 0.8,
        dem_slopes: Optional[Tuple[np.ndarray, np.ndarray]] = None,
        dem_data: Optional[np.ndarray] = None,
        pixel_gsd: float = 1.0,
        max_correction_factor: float = 5.0,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Topographic Illumination Correction via Minnaert photometric normalization.
        Suppresses harsh shadow boundaries and crater wall burnout across extreme sun angles.
        """
        img_norm = image.astype(np.float32)
        h, w = img_norm.shape
        sun_vec = sun_angles.sun_vector

        if dem_data is not None:
            # Derive local slope gradients using Sobel operators
            dem_f = dem_data.astype(np.float32)
            if dem_f.shape != (h, w):
                import cv2
                dem_f = cv2.resize(dem_f, (w, h), interpolation=cv2.INTER_LINEAR)
            scale = 8.0 * max(float(pixel_gsd), 1e-6)
            import cv2
            dz_dx = cv2.Sobel(dem_f, cv2.CV_32F, 1, 0, ksize=3) / scale
            dz_dy = cv2.Sobel(dem_f, cv2.CV_32F, 0, 1, ksize=3) / scale
            denom = np.sqrt(1.0 + dz_dx**2 + dz_dy**2)
            nx = -dz_dx / denom
            ny = -dz_dy / denom
            nz = 1.0 / denom
            cos_i = nx * sun_vec[0] + ny * sun_vec[1] + nz * sun_vec[2]
            cos_e = nz
        elif dem_slopes is not None:
            dz_dx, dz_dy = dem_slopes
            denom = np.sqrt(1.0 + dz_dx**2 + dz_dy**2)
            nx = -dz_dx / denom
            ny = -dz_dy / denom
            nz = 1.0 / denom
            cos_i = nx * sun_vec[0] + ny * sun_vec[1] + nz * sun_vec[2]
            cos_e = nz
        else:
            cos_i = np.full((h, w), np.maximum(sun_vec[2], 0.01), dtype=np.float32)
            cos_e = np.ones((h, w), dtype=np.float32)

        # Standard reference geometry
        ref_cos_i = np.cos(self.ref_i)
        ref_cos_e = np.cos(self.ref_e)
        ref_rm = self.minnaert(ref_cos_i, ref_cos_e, k=k)

        # Local acquisition reflectance
        safe_cos_i = np.maximum(cos_i, 0.005)
        safe_cos_e = np.maximum(cos_e, 0.005)
        acq_rm = self.minnaert(safe_cos_i, safe_cos_e, k=k)

        # Bounded correction factor
        corr = np.where(acq_rm > 1e-5, ref_rm / np.maximum(acq_rm, 1e-5), 1.0)
        corr = np.clip(corr, 0.1, max_correction_factor)
        corrected = img_norm * corr

        # Dynamic shadow masking
        shadow_thresh = np.quantile(img_norm, self.shadow_quantile)
        valid_mask = (img_norm > shadow_thresh) & (cos_i > 0.04)

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


class LunarContrastEqualizer:
    """
    Dynamic Contrast Equalization for Lunar Terrain Imagery.
    Combines:
    1. Multi-Scale Retinex (MSR) for dynamic range compression in deep crater shadows.
    2. Contrast Limited Adaptive Histogram Equalization (CLAHE) for local slope relief enhancement.
    """

    def __init__(
        self,
        retinex_sigmas: Tuple[float, ...] = (15.0, 80.0, 250.0),
        clahe_clip_limit: float = 2.5,
        clahe_tile_grid_size: Tuple[int, int] = (8, 8),
    ) -> None:
        self.sigmas = retinex_sigmas
        self.clahe_clip = clahe_clip_limit
        self.clahe_grid = clahe_tile_grid_size

    def multiscale_retinex(self, image: np.ndarray) -> np.ndarray:
        """
        Applies Multi-Scale Retinex:
            R_MSR = sum_n w_n [ ln(I) - ln(G_sigma * I) ]
        """
        img_float = np.maximum(image.astype(np.float32), 1e-4)
        log_img = np.log(img_float)
        msr = np.zeros_like(img_float)
        weight = 1.0 / len(self.sigmas)

        for sigma in self.sigmas:
            ksize = int(2 * np.ceil(2 * sigma) + 1)
            blurred = cv2.GaussianBlur(img_float, (ksize, ksize), sigma)
            blurred = np.maximum(blurred, 1e-4)
            msr += weight * (log_img - np.log(blurred))

        # Robust contrast stretching
        p2, p98 = np.percentile(msr, (2.0, 98.0))
        if p98 > p2:
            norm_msr = np.clip((msr - p2) / (p98 - p2), 0.0, 1.0)
        else:
            norm_msr = cv2.normalize(msr, None, 0.0, 1.0, cv2.NORM_MINMAX)
        return norm_msr.astype(np.float32)

    def apply_clahe(self, image: np.ndarray) -> np.ndarray:
        """
        Applies CLAHE on normalized image [0, 1].
        """
        uint8_img = (np.clip(image, 0.0, 1.0) * 255.0).astype(np.uint8)
        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip, tileGridSize=self.clahe_grid)
        enhanced = clahe.apply(uint8_img)
        return (enhanced.astype(np.float32) / 255.0)

    def equalize(self, image: np.ndarray, blend_ratio: float = 0.5) -> np.ndarray:
        """
        Blends MSR dynamic range compression with CLAHE local texture enhancement.
        """
        msr = self.multiscale_retinex(image)
        clahe = self.apply_clahe(msr)
        return np.clip(blend_ratio * clahe + (1.0 - blend_ratio) * msr, 0.0, 1.0)

