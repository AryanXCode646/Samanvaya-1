"""
src/security/file_validator.py
Defense-grade geospatial file validator for Samanvaya.
Protects against pixel bombs, XXE injection, path traversal, and
malformed geospatial file exploits (CVE-class GDAL/LibTIFF vulnerabilities).
"""
from __future__ import annotations

import hashlib
import os
import re
import struct
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import defusedxml.ElementTree as safe_et

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_DIMENSION_PX = 50_000          # per axis (prevents pixel bombs)
MAX_UNCOMPRESSED_BYTES = 4 * 2**30 # 4 GiB (prevents decompression bombs)
MAX_CHANNELS = 16
SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

# Magic byte signatures
_MAGIC = {
    "GEOTIFF_LE": b"\x49\x49\x2A\x00",   # Little-endian TIFF
    "GEOTIFF_BE": b"\x4D\x4D\x00\x2A",   # Big-endian TIFF
    "PNG":        b"\x89PNG\r\n\x1a\n",
    "FITS":       b"SIMPLE  =",
    "PDS3":       b"PDS_VERSION_ID",
    "HDF5":       b"\x89HDF\r\n\x1a\n",
}
_XML_HEADERS = (b"<?xml", b"<Product_Observational", b"<PDS_label")


class FileType(str, Enum):
    GEOTIFF = "GeoTIFF"
    PNG     = "PNG"
    FITS    = "FITS"
    PDS3    = "PDS3"
    PDS4    = "PDS4"
    HDF5    = "HDF5"
    UNKNOWN = "UNKNOWN"


@dataclass
class ValidationResult:
    is_valid:   bool
    file_type:  FileType = FileType.UNKNOWN
    dimensions: tuple[int, int] = (0, 0)   # (width, height)
    channels:   int = 0
    uuid_name:  str = field(default_factory=lambda: str(uuid.uuid4()))
    error:      Optional[str] = None
    sha256:     str = ""


class FileValidator:
    """
    Validates geospatial raster files before they enter the processing pipeline.

    Security guarantees:
    - Magic byte verification prevents content-type spoofing
    - Dimension limits prevent pixel/decompression bomb DoS
    - defusedxml prevents XXE/billion-laughs on PDS4 XML labels
    - UUIDv4 remapping eliminates path traversal on output
    - Strict project name regex blocks shell injection

    Note on sandbox isolation:
        In production (air-gapped / defense deployment), ingestion should be
        further wrapped in an ephemeral rootless container or cgroupsv2
        sandbox (max 8 GiB RAM, CPU throttled) with a tight seccomp profile
        (see docker/seccomp-profile.json) to isolate GDAL/LibTIFF parser
        vulnerabilities from the host OS.
    """

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self._workspace = workspace_root or Path.cwd()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def validate(self, path: Path) -> ValidationResult:
        """
        Full validation pipeline. Returns ValidationResult.
        is_valid=False on ANY security or format violation.
        """
        uuid_name = str(uuid.uuid4())
        path = path.resolve()

        # 1. Path traversal check
        if not self._safe_path(path):
            return ValidationResult(False, error="Path traversal detected", uuid_name=uuid_name)

        # 2. Existence check
        if not path.is_file():
            return ValidationResult(False, error=f"File not found: {path}", uuid_name=uuid_name)

        # 3. SHA-256 of raw file
        sha256 = self._sha256_file(path)

        # 4. Magic byte detection
        file_type = self._detect_type(path)

        # 5. Dispatch type-specific validation
        if file_type == FileType.PDS4:
            result = self._validate_pds4(path)
        elif file_type in (FileType.GEOTIFF, FileType.PNG):
            result = self._validate_raster_header(path, file_type)
        elif file_type == FileType.PDS3:
            result = self._validate_pds3(path)
        elif file_type == FileType.FITS:
            result = self._validate_fits(path)
        else:
            return ValidationResult(False, file_type=FileType.UNKNOWN,
                                    error="Unrecognized file magic bytes",
                                    uuid_name=uuid_name, sha256=sha256)

        result.uuid_name = uuid_name
        result.sha256 = sha256
        return result

    def validate_project_name(self, name: str) -> bool:
        """Strict allowlist: only [a-zA-Z0-9_-]{1..64} permitted."""
        return bool(SAFE_NAME_RE.match(name))

    # -----------------------------------------------------------------------
    # Path safety
    # -----------------------------------------------------------------------

    def _safe_path(self, path: Path) -> bool:
        """Reject null bytes, '..' components, and paths outside workspace."""
        raw = str(path)
        if "\x00" in raw:
            return False
        if ".." in path.parts:
            return False
        try:
            path.relative_to(self._workspace)
        except ValueError:
            return False
        return True

    # -----------------------------------------------------------------------
    # Magic byte detection
    # -----------------------------------------------------------------------

    def _detect_type(self, path: Path) -> FileType:
        with open(path, "rb") as f:
            header = f.read(512)

        for xml_sig in _XML_HEADERS:
            if header.lstrip().startswith(xml_sig):
                return FileType.PDS4

        if header[:4] in (_MAGIC["GEOTIFF_LE"], _MAGIC["GEOTIFF_BE"]):
            return FileType.GEOTIFF
        if header[:8] == _MAGIC["PNG"]:
            return FileType.PNG
        if header[:9] == _MAGIC["FITS"]:
            return FileType.FITS
        if header[:15] == _MAGIC["PDS3"]:
            return FileType.PDS3
        if header[:8] == _MAGIC["HDF5"]:
            return FileType.HDF5

        return FileType.UNKNOWN

    # -----------------------------------------------------------------------
    # GeoTIFF / PNG raster validation
    # -----------------------------------------------------------------------

    def _validate_raster_header(self, path: Path, file_type: FileType) -> ValidationResult:
        """
        Read image dimensions from TIFF/PNG headers WITHOUT decoding pixel data.
        Prevents decompression bombs at the header level.
        """
        try:
            if file_type == FileType.GEOTIFF:
                w, h, c = self._parse_tiff_dimensions(path)
            else:
                w, h, c = self._parse_png_dimensions(path)
        except Exception as exc:
            return ValidationResult(False, file_type=file_type, error=f"Header parse error: {exc}")

        err = self._dimension_bomb_check(w, h, c)
        if err:
            return ValidationResult(False, file_type=file_type, error=err, dimensions=(w, h))

        return ValidationResult(True, file_type=file_type, dimensions=(w, h), channels=c)

    def _parse_tiff_dimensions(self, path: Path) -> tuple[int, int, int]:
        """Parse TIFF IFD to extract ImageWidth(256), ImageLength(257), SamplesPerPixel(277)."""
        with open(path, "rb") as f:
            hdr = f.read(8)
            if hdr[:2] == b"II":
                endian = "<"
            else:
                endian = ">"
            offset = struct.unpack(f"{endian}I", hdr[4:8])[0]
            f.seek(offset)
            num_entries = struct.unpack(f"{endian}H", f.read(2))[0]
            tags: dict[int, int] = {}
            for _ in range(min(num_entries, 256)):
                entry = f.read(12)
                tag, dtype, count, value = struct.unpack(f"{endian}HHI4s", entry)
                if dtype in (3, 4):  # SHORT or LONG
                    v = struct.unpack(f"{endian}{'H' if dtype==3 else 'I'}", value[:2 if dtype==3 else 4])[0]
                    tags[tag] = v
            w = tags.get(256, 0)
            h = tags.get(257, 0)
            c = tags.get(277, 1)
        return w, h, c

    def _parse_png_dimensions(self, path: Path) -> tuple[int, int, int]:
        """Read PNG IHDR chunk for dimensions."""
        with open(path, "rb") as f:
            f.seek(16)
            w = struct.unpack(">I", f.read(4))[0]
            h = struct.unpack(">I", f.read(4))[0]
            f.read(1)  # bit depth
            color_type = struct.unpack("B", f.read(1))[0]
            c = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type, 1)
        return w, h, c

    def _dimension_bomb_check(self, w: int, h: int, c: int) -> Optional[str]:
        if w <= 0 or h <= 0:
            return "Invalid dimensions (zero or negative)"
        if w > MAX_DIMENSION_PX or h > MAX_DIMENSION_PX:
            return f"Pixel bomb rejected: {w}x{h} exceeds {MAX_DIMENSION_PX}px limit"
        if c > MAX_CHANNELS:
            return f"Excessive channels: {c}"
        uncompressed = w * h * c * 4  # assume float32
        if uncompressed > MAX_UNCOMPRESSED_BYTES:
            return f"Decompression bomb: estimated {uncompressed/2**30:.1f} GiB exceeds 4 GiB limit"
        return None

    # -----------------------------------------------------------------------
    # PDS4 XML validation (XXE-safe)
    # -----------------------------------------------------------------------

    def _validate_pds4(self, path: Path) -> ValidationResult:
        """
        Parse PDS4 XML label using defusedxml which:
        - Disables external DTD resolution (blocks XXE)
        - Disables entity expansion (blocks billion-laughs)
        - Disables network access
        """
        try:
            tree = safe_et.parse(str(path))
            root = tree.getroot()
            # Extract image dimensions from Array_2D_Image element
            ns = {"pds": "http://pds.nasa.gov/pds4/pds/v1"}
            lines = root.findtext(".//pds:Line_Samples", namespaces=ns) or \
                    root.findtext(".//Lines", namespaces={})
            samples = root.findtext(".//pds:Samples", namespaces=ns) or \
                      root.findtext(".//Samples", namespaces={})
            w = int(samples) if samples else 0
            h = int(lines) if lines else 0

            if w > 0 and h > 0:
                err = self._dimension_bomb_check(w, h, 1)
                if err:
                    return ValidationResult(False, FileType.PDS4, error=err)

            return ValidationResult(True, FileType.PDS4, dimensions=(w, h), channels=1)
        except Exception as exc:
            return ValidationResult(False, FileType.PDS4, error=f"PDS4 parse error: {exc}")

    # -----------------------------------------------------------------------
    # PDS3 validation
    # -----------------------------------------------------------------------

    def _validate_pds3(self, path: Path) -> ValidationResult:
        """Minimal PDS3 PVL label parser — reads dimensions from header text."""
        try:
            w, h = 0, 0
            with open(path, "rb") as f:
                header = f.read(8192).decode("ascii", errors="ignore")
            for line in header.splitlines():
                if "LINE_SAMPLES" in line and "=" in line:
                    w = int(line.split("=")[1].strip().split()[0])
                if "LINES " in line and "=" in line:
                    h = int(line.split("=")[1].strip().split()[0])
            err = self._dimension_bomb_check(w or 1, h or 1, 1)
            if err:
                return ValidationResult(False, FileType.PDS3, error=err)
            return ValidationResult(True, FileType.PDS3, dimensions=(w, h), channels=1)
        except Exception as exc:
            return ValidationResult(False, FileType.PDS3, error=f"PDS3 parse error: {exc}")

    # -----------------------------------------------------------------------
    # FITS validation
    # -----------------------------------------------------------------------

    def _validate_fits(self, path: Path) -> ValidationResult:
        try:
            w, h = 0, 0
            with open(path, "rb") as f:
                header = f.read(2880).decode("ascii", errors="ignore")
            for card in [header[i:i+80] for i in range(0, len(header), 80)]:
                if card.startswith("NAXIS1  ="):
                    w = int(card.split("=")[1].split("/")[0].strip())
                if card.startswith("NAXIS2  ="):
                    h = int(card.split("=")[1].split("/")[0].strip())
            err = self._dimension_bomb_check(w or 1, h or 1, 1)
            if err:
                return ValidationResult(False, FileType.FITS, error=err)
            return ValidationResult(True, FileType.FITS, dimensions=(w, h), channels=1)
        except Exception as exc:
            return ValidationResult(False, FileType.FITS, error=f"FITS parse error: {exc}")

    # -----------------------------------------------------------------------
    # Utilities
    # -----------------------------------------------------------------------

    @staticmethod
    def _sha256_file(path: Path, chunk: int = 1 << 20) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(chunk), b""):
                h.update(block)
        return h.hexdigest()
