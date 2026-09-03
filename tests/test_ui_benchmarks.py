"""
Unit Tests for Pre-Bundled Planetary Test Pairs and Streamlit Benchmark Presets.
Verifies raster file existence, manifest integrity, coordinate referencing, and pipeline execution.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest
import rasterio

from lunar_core.ui.app import get_sample_data_dir, load_sample_manifest, load_geotiff_file
from lunar_core.alignment.dense_matcher import DenseLoFTRMatcher


class TestPlanetaryBenchmarkAssets:
    """Tests integrity of cached mission benchmark datasets."""

    def test_sample_data_directory_and_manifest(self):
        sample_dir = get_sample_data_dir()
        assert sample_dir.exists(), f"Sample data dir not found at {sample_dir}"

        manifest = load_sample_manifest()
        assert "benchmarks" in manifest
        assert "scenario_a" in manifest["benchmarks"]
        assert "scenario_b" in manifest["benchmarks"]
        assert "scenario_c" in manifest["benchmarks"]

    def test_scenario_a_ohrc_apollo11_geotiff(self):
        sample_dir = get_sample_data_dir()
        manifest = load_sample_manifest()
        bm = manifest["benchmarks"]["scenario_a"]

        src_path = sample_dir / bm["source"]["filename"]
        ref_path = sample_dir / bm["reference"]["filename"]

        assert src_path.exists()
        assert ref_path.exists()

        # Check rasterio metadata
        with rasterio.open(src_path) as src:
            assert src.count == 1
            assert src.shape == (256, 256)
            assert src.crs is not None

        with rasterio.open(ref_path) as ref:
            assert ref.count == 1
            assert ref.shape == (256, 256)
            assert ref.crs is not None

        # Check normalized data reading
        arr_src = load_geotiff_file(src_path)
        arr_ref = load_geotiff_file(ref_path)
        assert arr_src.shape == (256, 256)
        assert arr_ref.shape == (256, 256)
        assert np.min(arr_src) >= 0.0 and np.max(arr_src) <= 1.0

    def test_scenario_b_tmc2_stereo_baseline(self):
        sample_dir = get_sample_data_dir()
        manifest = load_sample_manifest()
        bm = manifest["benchmarks"]["scenario_b"]

        src_path = sample_dir / bm["source"]["filename"]
        ref_path = sample_dir / bm["reference"]["filename"]

        assert src_path.exists()
        assert ref_path.exists()

        arr_src = load_geotiff_file(src_path)
        arr_ref = load_geotiff_file(ref_path)
        assert arr_src.shape == (256, 256)
        assert arr_ref.shape == (256, 256)

    def test_scenario_c_extreme_lighting_pair(self):
        sample_dir = get_sample_data_dir()
        manifest = load_sample_manifest()
        bm = manifest["benchmarks"]["scenario_c"]

        src_path = sample_dir / bm["source"]["filename"]
        ref_path = sample_dir / bm["reference"]["filename"]

        assert src_path.exists()
        assert ref_path.exists()

        arr_src = load_geotiff_file(src_path)
        arr_ref = load_geotiff_file(ref_path)
        assert arr_src.shape == (256, 256)
        assert arr_ref.shape == (256, 256)

    def test_end_to_end_matching_on_benchmark_scenario_a(self):
        """Verifies that LoFTR finds correspondences on Scenario A (OHRC vs LRO NAC)."""
        sample_dir = get_sample_data_dir()
        manifest = load_sample_manifest()
        bm = manifest["benchmarks"]["scenario_a"]

        arr_src = load_geotiff_file(sample_dir / bm["source"]["filename"])
        arr_ref = load_geotiff_file(sample_dir / bm["reference"]["filename"])

        matcher = DenseLoFTRMatcher(
            pretrained="outdoor",
            confidence_threshold=0.10,
            grid_bins=8,
            cap_per_cell=4,
        )

        inliers, H, inlier_mask = matcher.match(arr_src, arr_ref)
        assert len(inliers) > 0, "LoFTR failed to match Scenario A GeoTIFF pair"
        if H is not None:
            assert H.shape == (3, 3)
            assert inlier_mask is not None and np.sum(inlier_mask) > 0
