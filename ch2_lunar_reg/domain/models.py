"""
ISRO Chandrayaan-2 Planetary Data Processing Pipeline - Domain Models
Smart India Hackathon (SIH) PS 26166: Multi-modal, Sun angle & scale invariant registration.

Enterprise Domain Entities, Value Objects, and Mathematical Representations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class SensorModality(str, Enum):
    """Chandrayaan-2 and lunar orbital optical sensor modalities."""
    OHRC = "CH2_OHRC"          # ~0.25 m/pixel high-resolution panchromatic
    TMC2_NADIR = "CH2_TMC2_NADIR"  # ~5.0 m/pixel terrain mapping camera (nadir)
    TMC2_FORE = "CH2_TMC2_FORE"    # +26 deg fore stereo
    TMC2_AFT = "CH2_TMC2_AFT"      # -26 deg aft stereo
    IIRS = "CH2_IIRS"          # ~80 m/pixel hyperspectral (0.8 - 5.0 um)
    LRO_NAC = "LRO_NAC"        # ~0.5 m/pixel Narrow Angle Camera (benchmarking)
    SYNTHETIC = "SYNTHETIC"    # High-fidelity simulated lunar terrain


class TransformationModel(str, Enum):
    """Geometric transformation models for lunar surface correspondence."""
    RIGID = "RIGID"                     # Translation + Rotation (3 DOF)
    SIMILARITY = "SIMILARITY"           # Translation + Rotation + Uniform Scale (4 DOF)
    AFFINE = "AFFINE"                   # Affine 2D (6 DOF)
    HOMOGRAPHY = "HOMOGRAPHY"           # Perspective Projective (8 DOF)
    THIN_PLATE_SPLINE = "TPS"          # Non-rigid 2D Thin-Plate Splines


@dataclass(frozen=True)
class SunAngles:
    """
    Solar illumination geometry angles for planetary surface photometric normalization.
    
    Attributes:
        azimuth_deg: Solar azimuth angle in degrees [0, 360), measured from North.
        elevation_deg: Solar elevation angle above local lunar horizon [-90, +90].
        incidence_deg: Angle between solar incident vector and surface normal [0, 90].
        emission_deg: Angle between spacecraft line-of-sight vector and surface normal [0, 90].
        phase_deg: Solar phase angle (angle between sun and camera vectors) [0, 180].
    """
    azimuth_deg: float
    elevation_deg: float
    incidence_deg: Optional[float] = None
    emission_deg: Optional[float] = None
    phase_deg: Optional[float] = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.azimuth_deg <= 360.0):
            raise ValueError(f"Azimuth must be in [0, 360], got {self.azimuth_deg}")
        if not (-90.0 <= self.elevation_deg <= 90.0):
            raise ValueError(f"Elevation must be in [-90, 90], got {self.elevation_deg}")

    @property
    def sun_vector(self) -> np.ndarray:
        """Normalized 3D Cartesian unit vector pointing toward the Sun."""
        az_rad = np.radians(self.azimuth_deg)
        el_rad = np.radians(self.elevation_deg)
        return np.array([
            np.cos(el_rad) * np.sin(az_rad),  # East (X)
            np.cos(el_rad) * np.cos(az_rad),  # North (Y)
            np.sin(el_rad)                    # Zenith (Z)
        ], dtype=np.float64)


@dataclass
class GeoRaster:
    """
    Georeferenced planetary raster entity with metadata and physical parameters.
    
    Attributes:
        data: 2D or 3D NumPy array of radiance or digital numbers (float32).
        modality: Orbital sensor modality.
        gsd_meters: Ground Sampling Distance in meters per pixel.
        sun_angles: Solar geometry at image acquisition epoch.
        transform: Affine geotransform tuple (c, a, b, f, d, e) or rasterio.Affine.
        crs: Coordinate Reference System (e.g., 'IAU2000:30100' for Moon).
        nodata_val: Pixel value designated as nodata/invalid.
    """
    data: np.ndarray
    modality: SensorModality
    gsd_meters: float
    sun_angles: SunAngles
    transform: Optional[Any] = None
    crs: str = "IAU2000:30100"  # Lunar sphere IAU 2000
    nodata_val: Optional[float] = None

    def __post_init__(self) -> None:
        if self.data.ndim == 2:
            self.height, self.width = self.data.shape
        elif self.data.ndim == 3:
            self.height, self.width = self.data.shape[1], self.data.shape[2]
        else:
            raise ValueError(f"Raster data must be 2D or 3D, got ndim={self.data.ndim}")
        if self.gsd_meters <= 0.0:
            raise ValueError(f"GSD must be positive, got {self.gsd_meters}")


@dataclass
class KeypointMatch:
    """
    A single point-to-point correspondence between reference and target lunar imagery.
    
    Attributes:
        ref_xy: Coordinates (x, y) in reference image (sub-pixel float).
        target_xy: Coordinates (x, y) in target image (sub-pixel float).
        confidence: Normalized match confidence / descriptor distance metric [0, 1].
        subpixel_refined: Whether coordinates were refined via quadratic Taylor series.
        residual_error: Geometric residual error post-transformation (in pixels).
    """
    ref_xy: Tuple[float, float]
    target_xy: Tuple[float, float]
    confidence: float
    subpixel_refined: bool = False
    residual_error: Optional[float] = None


@dataclass
class RegistrationMetrics:
    """
    Quantitative performance metrics for registered lunar imagery.
    """
    num_detected_ref: int
    num_detected_target: int
    num_initial_matches: int
    num_inliers: int
    inlier_ratio: float
    rmse_pixels: float
    mean_residual_pixels: float
    max_residual_pixels: float
    spatial_coverage_score: float  # [0, 1] measure of uniform spatial distribution
    spatial_uniformity_entropy: float = 0.0  # [0, 1] Normalized Shannon Spatial Entropy Index
    processing_time_ms: float = 0.0

    @property
    def meets_isro_subpixel_mandate(self) -> bool:
        """ISRO SIH constraint: Sub-pixel precision with target RMSE < 0.4 pixels."""
        return self.rmse_pixels < 0.40 and self.num_inliers >= 4


@dataclass
class RegistrationResult:
    """
    Complete output bundle of the multi-phase lunar image registration pipeline.
    """
    transformation_model: TransformationModel
    transform_matrix: Optional[np.ndarray]
    matches: List[KeypointMatch]
    inliers: List[KeypointMatch]
    metrics: RegistrationMetrics
    warped_target: Optional[np.ndarray] = None
    tps_source_pts: Optional[np.ndarray] = None
    tps_target_pts: Optional[np.ndarray] = None
