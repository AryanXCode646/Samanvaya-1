"""
USGS ISIS3 jigsaw-Compatible Ground Control Point (GCP) & Control Network Exporter.
ISRO Chandrayaan-2 Lunar Optical Image Registration Framework (SIH PS 26166).

Interoperability Standards:
Formats verified tie-points into USGS ISIS3 (Integrated Software for Imagers and
Spectrometers) jigsaw-compatible control networks (cnet) and GCP CSV tables.
Includes:
- Sub-pixel image coordinates (Sample=X, Line=Y).
- Continuous inverse Hessian covariance uncertainties (SigmaX, SigmaY, CovXY).
- Planetary curvature confidence weights.
- Geodetic projection metadata (IAU2000:30100 Lunar Spheroid R=1737400.0 m).
- Ground residual errors in pixels.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np

from lunar_core.models import GeoRaster, KeypointMatch, SensorModality
from lunar_core.data_io.raster_reader import sanitize_path


class IsisGcpExporter:
    """
    Exports registered lunar correspondences to USGS ISIS3 `jigsaw` bundle-adjustment
    format and standard Ground Control Point (GCP) control network tables.
    """

    DEFAULT_BODY_NAME = "MOON"
    DEFAULT_SPHEROID_RADIUS_M = 1737400.0  # IAU 2000 Moon radius
    DEFAULT_CRS = "IAU2000:30100"

    def __init__(
        self,
        ref_image_id: str = "REFERENCE_ORBITAL",
        target_image_id: str = "TARGET_ORBITAL",
        target_body: str = DEFAULT_BODY_NAME,
        crs: str = DEFAULT_CRS,
        one_based_indexing: bool = True,
    ) -> None:
        """
        Args:
            ref_image_id: Serial or product ID for reference image in ISIS3 cnet.
            target_image_id: Serial or product ID for target image in ISIS3 cnet.
            target_body: Target planetary body name (default 'MOON').
            crs: Coordinate reference system identifier.
            one_based_indexing: ISIS3 uses 1-based (Sample, Line) image coordinates.
        """
        self.ref_image_id = ref_image_id
        self.target_image_id = target_image_id
        self.target_body = target_body
        self.crs = crs
        self.one_based_indexing = one_based_indexing

    def _format_coord(self, coord: float) -> float:
        """Applies 1-based indexing for USGS ISIS standard if enabled."""
        offset = 1.0 if self.one_based_indexing else 0.0
        return round(float(coord + offset), 4)

    def export_pairwise_csv(
        self,
        matches: Sequence[KeypointMatch],
        output_path: Optional[Union[str, Path]] = None,
        ref_raster: Optional[GeoRaster] = None,
        target_raster: Optional[GeoRaster] = None,
    ) -> str:
        """
        Exports tie-points as a clean tabular GCP CSV compatible with ISIS3 jigsaw / qnet.
        
        Columns:
            PointId, PointType, RefSample, RefLine, TgtSample, TgtLine,
            SigmaX_px, SigmaY_px, CovXY, Weight, Residual_px, Confidence,
            RefLon, RefLat, TgtLon, TgtLat
        """
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        # Write ISIS3 Metadata Header
        writer.writerow(["# USGS ISIS3 Jigsaw-Compatible Ground Control Network (cnet)"])
        writer.writerow([f"# Software: Samanvaya ISRO Chandrayaan-2 Registration Framework (SIH PS 26166)"])
        writer.writerow([f"# Target Body: {self.target_body} (Mean Radius: {self.DEFAULT_SPHEROID_RADIUS_M} m)"])
        writer.writerow([f"# Coordinate Reference System: {self.crs}"])
        writer.writerow([f"# Reference Product: {self.ref_image_id}"])
        writer.writerow([f"# Target Product: {self.target_image_id}"])
        writer.writerow([f"# Total Inlier Control Points: {len(matches)}"])
        writer.writerow([f"# One-Based Indexing: {self.one_based_indexing}"])

        # Table Column Headers
        headers = [
            "PointId",
            "PointType",
            "RefSample",
            "RefLine",
            "TgtSample",
            "TgtLine",
            "SigmaX_px",
            "SigmaY_px",
            "CovXY",
            "Weight",
            "Residual_px",
            "Confidence",
        ]

        has_geo = ref_raster is not None and ref_raster.transform is not None
        if has_geo:
            headers.extend(["RefLongitude_deg", "RefLatitude_deg"])

        writer.writerow(headers)

        for idx, m in enumerate(matches, start=1):
            pid = f"GCP_{idx:05d}"
            pt_type = "TiePoint" if m.residual_error is not None else "Free"

            rx = self._format_coord(m.ref_xy[0])
            ry = self._format_coord(m.ref_xy[1])
            tx = self._format_coord(m.target_xy[0])
            ty = self._format_coord(m.target_xy[1])

            sig_x = round(float(m.sigma_x), 5) if m.sigma_x is not None else 0.20000
            sig_y = round(float(m.sigma_y), 5) if m.sigma_y is not None else 0.20000
            cov_xy = round(float(m.cov_xy), 5) if m.cov_xy is not None else 0.00000
            wt = round(float(m.weight), 4) if m.weight is not None else 1.0000
            res = round(float(m.residual_error), 4) if m.residual_error is not None else 0.0000
            conf = round(float(m.confidence), 4)

            row = [pid, pt_type, rx, ry, tx, ty, sig_x, sig_y, cov_xy, wt, res, conf]

            if has_geo and ref_raster and ref_raster.transform:
                try:
                    # Affine mapping: x_geo = a*col + b*row + c, y_geo = d*col + e*row + f
                    geo_x, geo_y = ref_raster.transform * (m.ref_xy[0], m.ref_xy[1])
                    row.extend([round(geo_x, 6), round(geo_y, 6)])
                except Exception:
                    row.extend(["N/A", "N/A"])

            writer.writerow(row)

        csv_content = buffer.getvalue()

        if output_path is not None:
            out_file = sanitize_path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(csv_content, encoding="utf-8")

        return csv_content

    def export_isis_measure_csv(
        self,
        matches: Sequence[KeypointMatch],
        output_path: Optional[Union[str, Path]] = None,
    ) -> str:
        """
        Exports in official ISIS3 `cnet2csv` measure record structure:
        Each tie-point is represented by one row per image measurement.
        """
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        writer.writerow(["# ISIS3 Jigsaw Multi-Measure Control Network"])
        writer.writerow([
            "PointId",
            "SerialNumber",
            "MeasureType",
            "Sample",
            "Line",
            "SampleResidual",
            "LineResidual",
            "Weight",
            "SigmaX",
            "SigmaY",
        ])

        for idx, m in enumerate(matches, start=1):
            pid = f"PT_{idx:05d}"
            rx = self._format_coord(m.ref_xy[0])
            ry = self._format_coord(m.ref_xy[1])
            tx = self._format_coord(m.target_xy[0])
            ty = self._format_coord(m.target_xy[1])

            sx = round(float(m.sigma_x), 5) if m.sigma_x is not None else 0.2
            sy = round(float(m.sigma_y), 5) if m.sigma_y is not None else 0.2
            wt = round(float(m.weight), 4) if m.weight is not None else 1.0

            # Reference measure
            writer.writerow([pid, self.ref_image_id, "Candidate", rx, ry, 0.0, 0.0, wt, sx, sy])
            # Target measure
            res = round(float(m.residual_error), 4) if m.residual_error is not None else 0.0
            writer.writerow([pid, self.target_image_id, "Registered", tx, ty, res, res, wt, sx, sy])

        content = buffer.getvalue()
        if output_path is not None:
            out_file = sanitize_path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(content, encoding="utf-8")

        return content
