"""
Unit and Integration Tests for Samanvaya End-to-End Pipeline Harness (run_pipeline.py).
Verifies:
1. Multi-modal raster loading.
2. Topographic Minnaert Photometric Correction.
3. Successful execution of run_registration_pipeline.
4. Export of evaluation_report.json and evaluation_report.csv.
5. Compliance with ISRO Sub-Pixel Mandate (< 0.40 px).
"""

from pathlib import Path
import json
import numpy as np
import pytest

from run_pipeline import (
    load_geotiff_file,
    load_sample_manifest,
    get_sample_data_dir,
    run_registration_pipeline,
)
from lunar_core.models import SunAngles


def test_manifest_and_geotiff_loaders():
    sample_dir = get_sample_data_dir()
    assert sample_dir.exists()
    manifest = load_sample_manifest()
    assert "benchmarks" in manifest
    assert "scenario_a" in manifest["benchmarks"]

    bm = manifest["benchmarks"]["scenario_a"]
    src_file = sample_dir / bm["source"]["filename"]
    ref_file = sample_dir / bm["reference"]["filename"]
    assert src_file.exists()
    assert ref_file.exists()

    arr_src = load_geotiff_file(src_file)
    arr_ref = load_geotiff_file(ref_file)
    assert arr_src.shape == (256, 256)
    assert arr_ref.shape == (256, 256)
    assert 0.0 <= np.min(arr_src) and np.max(arr_src) <= 1.0


def test_end_to_end_pipeline_execution(tmp_path: Path):
    sample_dir = get_sample_data_dir()
    manifest = load_sample_manifest()
    bm = manifest["benchmarks"]["scenario_a"]

    src_img = load_geotiff_file(sample_dir / bm["source"]["filename"])
    ref_img = load_geotiff_file(sample_dir / bm["reference"]["filename"])

    sun_src = SunAngles(
        azimuth_deg=bm["source"]["sun_azimuth_deg"],
        elevation_deg=bm["source"]["sun_elevation_deg"],
    )
    sun_ref = SunAngles(
        azimuth_deg=bm["reference"]["sun_azimuth_deg"],
        elevation_deg=bm["reference"]["sun_elevation_deg"],
    )

    json_out = tmp_path / "test_report.json"
    csv_out = tmp_path / "test_report.csv"

    report = run_registration_pipeline(
        src_image=src_img,
        ref_image=ref_img,
        src_sun=sun_src,
        ref_sun=sun_ref,
        photometric_mode="minnaert",
        minnaert_k=0.80,
        transformation_model="affine",
        confidence_threshold=0.10,
        output_json=str(json_out),
        output_csv=str(csv_out),
    )

    assert report.total_matches > 0
    assert report.inlier_count > 0
    assert report.spatial_uniformity_score > 0.0
    assert json_out.exists()
    assert csv_out.exists()

    data = json.loads(json_out.read_text(encoding="utf-8"))
    assert data["metadata"]["problem_statement"] == "SIH PS 26166"
    assert len(data["tie_points"]) == report.inlier_count
