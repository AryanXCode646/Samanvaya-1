"""
Command-Line Interface (CLI) for Chandrayaan-2 Lunar Image Registration.
ISRO SIH PS 26166 Mission Suite.
"""

from __future__ import annotations

import argparse
import json
import sys
import cv2
import numpy as np

from ch2_lunar_reg.domain.models import SunAngles, TransformationModel
from ch2_lunar_reg.application.pipeline import LunarRegistrationPipeline
from ch2_lunar_reg.infrastructure.synthetic_generator import LunarTerrainSimulator
from ch2_lunar_reg.infrastructure.raster_io import PlanetaryRasterDriver


def run_benchmark(args: argparse.Namespace) -> None:
    print("=" * 70)
    print("ISRO Chandrayaan-2 Planetary Image Registration Benchmark (SIH PS 26166)")
    print("Simulating extreme solar shadow inversion: Azimuth 60 deg vs 240 deg (180 deg delta)")
    print("=" * 70)

    sim = LunarTerrainSimulator(size=(384, 384), seed=args.seed)
    sun_ref = SunAngles(azimuth_deg=args.ref_azimuth, elevation_deg=args.ref_elevation)
    sun_tgt = SunAngles(azimuth_deg=args.tgt_azimuth, elevation_deg=args.tgt_elevation)

    img_ref, img_tgt, true_affine, _ = sim.generate_registered_pair_with_ground_truth(
        sun_ref=sun_ref,
        sun_tgt=sun_tgt,
        true_translation=(10.5, -7.2),
        true_rotation_deg=3.5,
    )

    pipeline = LunarRegistrationPipeline(
        target_features=400,
        enable_photometric_norm=True,
        enable_anms=not args.disable_anms,
        enable_subpixel=not args.disable_subpixel,
        transformation_model=TransformationModel(args.model),
    )

    result = pipeline.register(
        ref_image=img_ref,
        target_image=img_tgt,
        ref_sun=sun_ref,
        target_sun=sun_tgt,
    )

    m = result.metrics
    print("\n--- REGISTRATION PERFORMANCE REPORT ---")
    print(f"Features Detected (Ref / Tgt) : {m.num_detected_ref} / {m.num_detected_target}")
    print(f"Initial Matches (MNN + NNDR)   : {m.num_initial_matches}")
    print(f"Inlier Correspondences        : {m.num_inliers}")
    print(f"Inlier Ratio                  : {m.inlier_ratio * 100:.2f}%")
    print(f"Sub-Pixel RMSE (pixels)       : {m.rmse_pixels:.4f} px")
    print(f"Mean Residual Error           : {m.mean_residual_pixels:.4f} px")
    print(f"Spatial Coverage Score        : {m.spatial_coverage_score:.4f} (Uniform dispersion)")
    print(f"Total Processing Time         : {m.processing_time_ms:.2f} ms")
    print("-" * 70)
    
    if m.meets_isro_subpixel_mandate:
        print(">> ISRO MANDATE STATUS: [PASS] Target RMSE < 0.40 pixels successfully achieved!")
    else:
        print(">> ISRO MANDATE STATUS: [FAIL] RMSE exceeds 0.40 pixels.")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="ISRO Chandrayaan-2 Registration Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Benchmark subcommand
    bench = subparsers.add_parser("benchmark", help="Run synthetic multi-sun-angle benchmark")
    bench.add_argument("--ref-azimuth", type=float, default=60.0)
    bench.add_argument("--ref-elevation", type=float, default=25.0)
    bench.add_argument("--tgt-azimuth", type=float, default=240.0)
    bench.add_argument("--tgt-elevation", type=float, default=35.0)
    bench.add_argument("--seed", type=int, default=42)
    bench.add_argument("--model", type=str, default="AFFINE", choices=["AFFINE", "HOMOGRAPHY", "TPS"])
    bench.add_argument("--disable-anms", action="store_true")
    bench.add_argument("--disable-subpixel", action="store_true")

    # Serve subcommand
    serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    serve.add_argument("--host", type=str, default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8000)

    # Dashboard subcommand
    dash = subparsers.add_parser("dashboard", help="Launch Streamlit interactive inspection dashboard")
    dash.add_argument("--port", type=int, default=8501)

    args = parser.parse_args()

    if args.command == "benchmark":
        run_benchmark(args)
    elif args.command == "serve":
        import uvicorn
        from ch2_lunar_reg.interfaces.api import app
        uvicorn.run(app, host=args.host, port=args.port)
    elif args.command == "dashboard":
        import subprocess
        subprocess.run(["streamlit", "run", "ch2_lunar_reg/interfaces/dashboard.py", "--server.port", str(args.port)])


if __name__ == "__main__":
    main()
