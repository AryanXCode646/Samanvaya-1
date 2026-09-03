"""
Geospatial Raster Drivers & Planetary Data Access (GDAL / Rasterio).
ISRO Chandrayaan-2 Planetary Remote Sensing Architecture.

Handles:
1. GeoTIFF / PDS4 / ISIS3 image ingestion.
2. Lunar Coordinate Reference Systems (IAU2000:30100 Moon sphere).
3. Export of registered rasters with updated Affine geotransform.
4. Export of Ground Control Points (GCPs) for ISIS3/SPICE bundle adjustment.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Tuple, Union
import numpy as np
import rasterio
from rasterio.transform import Affine, from_origin
from rasterio.control import GroundControlPoint

from ch2_lunar_reg.domain.models import GeoRaster, KeypointMatch, SensorModality, SunAngles
from lunar_core.data_io.raster_reader import sanitize_path


class PlanetaryRasterDriver:
    """
    Geospatial I/O adapter using Rasterio / GDAL for planetary imagery.
    """

    LUNAR_CRS_WKT = (
        'GEOGCS["Moon 2000",'
        'DATUM["D_Moon_2000",'
        'SPHEROID["Moon_2000_IAU_IAG",1737400.0,0.0]],'
        'PRIMEM["Reference_Meridian",0.0],'
        'UNIT["Degree",0.0174532925199433]]'
    )

    @classmethod
    def read_georaster(
        cls,
        filepath: Union[str, Path],
        modality: SensorModality = SensorModality.TMC2_NADIR,
        sun_angles: Optional[SunAngles] = None,
    ) -> GeoRaster:
        """
        Reads planetary GeoTIFF with full geospatial spatial reference.
        Enforces decompression bomb prevention limits before reading.
        """
        clean_path = sanitize_path(filepath)
        path_str = str(clean_path)
        with rasterio.open(path_str) as src:
            if src.width > 30000 or src.height > 30000:
                raise ValueError(f"Raster dimensions ({src.width}x{src.height}) exceed maximum threshold (30000x30000)")
            itemsize = np.dtype(src.dtypes[0]).itemsize if src.dtypes else 4
            if src.width * src.height * src.count * itemsize > 4 * 1024**3:
                raise MemoryError("Raster buffer exceeds 4GB safety limit")

            data = src.read(1).astype(np.float32)
            transform = src.transform
            crs_str = src.crs.to_string() if src.crs else cls.LUNAR_CRS_WKT
            nodata = src.nodata

            # Estimate GSD in meters (if projected or approximate degree to meters on Moon)
            # Lunar radius = 1737.4 km -> 1 deg latitude ~ 30.323 km
            if src.crs and src.crs.is_projected:
                gsd = float(abs(transform.a))
            else:
                deg_to_m = (np.pi / 180.0) * 1737400.0
                gsd = float(abs(transform.a) * deg_to_m)

        if sun_angles is None:
            # Default mid-elevation solar geometry if not in header
            sun_angles = SunAngles(azimuth_deg=65.0, elevation_deg=35.0)

        return GeoRaster(
            data=data,
            modality=modality,
            gsd_meters=gsd,
            sun_angles=sun_angles,
            transform=transform,
            crs=crs_str,
            nodata_val=nodata,
        )

    @classmethod
    def write_georaster(
        cls,
        output_path: Union[str, Path],
        data: np.ndarray,
        reference_raster: GeoRaster,
        updated_transform: Optional[Affine] = None,
    ) -> None:
        """
        Exports registered lunar image as a standard GeoTIFF.
        """
        clean_out = sanitize_path(output_path)
        os.makedirs(clean_out.parent, exist_ok=True)
        h, w = data.shape
        trans = updated_transform if updated_transform is not None else reference_raster.transform
        if trans is None:
            trans = from_origin(0.0, 0.0, reference_raster.gsd_meters, reference_raster.gsd_meters)

        profile = {
            "driver": "GTiff",
            "dtype": "float32",
            "nodata": reference_raster.nodata_val if reference_raster.nodata_val is not None else -9999.0,
            "width": w,
            "height": h,
            "count": 1,
            "crs": reference_raster.crs,
            "transform": trans,
            "compress": "lzw",
        }

        with rasterio.open(str(clean_out), "w", **profile) as dst:
            dst.write(data.astype(np.float32), 1)

    @staticmethod
    def export_isis_gcp_csv(
        matches: List[KeypointMatch],
        ref_transform: Affine,
        csv_filepath: Union[str, Path],
    ) -> None:
        """
        Exports tie-points as a USGS ISIS3 jigsaw-compatible GCP CSV file.
        """
        clean_csv = sanitize_path(csv_filepath)
        os.makedirs(clean_csv.parent, exist_ok=True)
        lines = ["gcp_id,pixel_ref,line_ref,pixel_tgt,line_tgt,geo_x,geo_y,residual_px\n"]
        for idx, m in enumerate(matches):
            rx, ry = m.ref_xy
            tx, ty = m.target_xy
            geo_x, geo_y = ref_transform * (rx, ry)
            res = m.residual_error if m.residual_error is not None else 0.0
            lines.append(f"{idx},{rx:.4f},{ry:.4f},{tx:.4f},{ty:.4f},{geo_x:.6f},{geo_y:.6f},{res:.4f}\n")

        with open(str(clean_csv), "w") as f:
            f.writelines(lines)

    @staticmethod
    def export_vector_field_geojson(
        matches: List[KeypointMatch],
        ref_transform: Affine,
        geojson_filepath: Union[str, Path],
    ) -> None:
        """
        Exports displacement vector field as standard GeoJSON features for QGIS / ArcGIS.
        """
        import json
        clean_json = sanitize_path(geojson_filepath)
        os.makedirs(clean_json.parent, exist_ok=True)

        features = []
        for idx, m in enumerate(matches):
            rx, ry = m.ref_xy
            tx, ty = m.target_xy
            geo_x_ref, geo_y_ref = ref_transform * (rx, ry)
            geo_x_tgt, geo_y_tgt = ref_transform * (tx, ty)
            dx = tx - rx
            dy = ty - ry
            res = m.residual_error if m.residual_error is not None else 0.0

            feat = {
                "type": "Feature",
                "id": idx,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [float(geo_x_ref), float(geo_y_ref)],
                        [float(geo_x_tgt), float(geo_y_tgt)],
                    ],
                },
                "properties": {
                    "gcp_id": idx,
                    "dx_pixels": float(dx),
                    "dy_pixels": float(dy),
                    "displacement_magnitude": float(np.sqrt(dx**2 + dy**2)),
                    "subpixel_residual_error": float(res),
                    "confidence": float(m.confidence),
                },
            }
            features.append(feat)

        geojson_doc = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features,
        }

        with open(str(geojson_filepath), "w") as f:
            json.dump(geojson_doc, f, indent=2)

