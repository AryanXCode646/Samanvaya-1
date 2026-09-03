"""
Planetary Data Ingestion Driver (GDAL/Rasterio GeoTIFF and PDS4 Reader).
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Tuple, Union
import numpy as np
import rasterio

from lunar_core.models import GeoRaster, SensorModality, SunAngles


class PlanetaryRasterReader:
    """
    Reads planetary imagery from standard GeoTIFF formats and PDS4 product labels.
    """

    @staticmethod
    def read_geotiff(
        filepath: Union[str, Path],
        modality: SensorModality = SensorModality.SYNTHETIC,
        gsd_fallback: float = 1.0,
    ) -> GeoRaster:
        """
        Ingests georeferenced GeoTIFF raster and extracts spatial resolution and CRS.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"GeoTIFF file not found: {path}")

        with rasterio.open(str(path)) as src:
            data = src.read(1).astype(np.float32)
            transform = src.transform
            crs = str(src.crs) if src.crs else "IAU2000:30100"
            nodata = src.nodata

            # Pixel dimensions in meters from affine transform
            res_x = abs(transform[0])
            res_y = abs(transform[4])
            gsd = float((res_x + res_y) / 2.0) if (res_x > 0 and res_y > 0) else gsd_fallback

            # Read optional solar metadata tags
            tags = src.tags()
            sun_az = float(tags.get("SUN_AZIMUTH", 0.0))
            sun_el = float(tags.get("SUN_ELEVATION", 45.0))
            sun = SunAngles(azimuth_deg=sun_az, elevation_deg=sun_el) if "SUN_AZIMUTH" in tags else None

        return GeoRaster(
            data=data,
            modality=modality,
            gsd_meters=gsd,
            sun_angles=sun,
            transform=transform,
            crs=crs,
            nodata_val=nodata,
        )

    @staticmethod
    def parse_pds4_metadata(label_xml_path: Union[str, Path]) -> Tuple[SunAngles, float, SensorModality]:
        """
        Parses PDS4 XML label for Chandrayaan-2/LRO products:
        Extracts solar illumination angles, pixel resolution (GSD), and sensor modality.
        """
        tree = ET.parse(str(label_xml_path))
        root = tree.getroot()

        # Extract namespace if present
        ns = {"pds": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}

        # Default fallback values
        sun_az = 0.0
        sun_el = 45.0
        gsd = 1.0
        modality = SensorModality.SYNTHETIC

        # Search for solar geometry in PDS4 observation area
        az_node = root.find(".//pds:solar_azimuth_angle", ns) or root.find(".//solar_azimuth_angle")
        el_node = root.find(".//pds:solar_elevation_angle", ns) or root.find(".//solar_elevation_angle")
        gsd_node = root.find(".//pds:pixel_resolution", ns) or root.find(".//pixel_resolution")
        sensor_node = root.find(".//pds:instrument_id", ns) or root.find(".//instrument_id")

        if az_node is not None and az_node.text:
            sun_az = float(az_node.text)
        if el_node is not None and el_node.text:
            sun_el = float(el_node.text)
        if gsd_node is not None and gsd_node.text:
            gsd = float(gsd_node.text)

        if sensor_node is not None and sensor_node.text:
            s_name = sensor_node.text.upper()
            if "OHRC" in s_name:
                modality = SensorModality.OHRC
                gsd = gsd if gsd != 1.0 else 0.25
            elif "TMC" in s_name:
                modality = SensorModality.TMC2
                gsd = gsd if gsd != 1.0 else 5.0
            elif "IIRS" in s_name:
                modality = SensorModality.IIRS
                gsd = gsd if gsd != 1.0 else 80.0

        return SunAngles(azimuth_deg=sun_az, elevation_deg=sun_el), gsd, modality
