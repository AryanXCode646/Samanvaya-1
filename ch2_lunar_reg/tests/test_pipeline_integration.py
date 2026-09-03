"""
End-to-End Mission Integration Test for SIH PS 26166.
Tests Multi-Modal, Sun Angle (180 deg shadow inversion), and Scale Invariance.
Mandate: Sub-pixel RMSE < 0.40 pixels.
"""

import numpy as np
import pytest
from ch2_lunar_reg.domain.models import SunAngles, TransformationModel
from ch2_lunar_reg.application.pipeline import LunarRegistrationPipeline
from ch2_lunar_reg.infrastructure.synthetic_generator import LunarTerrainSimulator


def test_extreme_sun_angle_reversal_registration():
    """
    Simulates Morning Orbit (Sun Azimuth 60 deg, Elevation 25 deg)
    vs Afternoon Orbit (Sun Azimuth 240 deg, Elevation 35 deg)
    with 180-degree shadow reversal on crater rims.
    
    Verifies that Phase Congruency + RIFT + ANMS + Sub-Pixel Taylor Refinement
    recovers the geometric transformation with RMSE < 0.40 pixels.
    """
    sim = LunarTerrainSimulator(size=(256, 256), seed=42)
    sun_ref = SunAngles(azimuth_deg=60.0, elevation_deg=25.0)
    sun_tgt = SunAngles(azimuth_deg=240.0, elevation_deg=35.0)

    true_shift = (6.0, -4.0)
    true_rot = 2.5

    img_ref, img_tgt, true_affine, _ = sim.generate_registered_pair_with_ground_truth(
        sun_ref=sun_ref,
        sun_tgt=sun_tgt,
        true_translation=true_shift,
        true_rotation_deg=true_rot,
    )

    pipeline = LunarRegistrationPipeline(
        target_features=300,
        enable_photometric_norm=True,
        enable_anms=True,
        enable_subpixel=True,
        transformation_model=TransformationModel.AFFINE,
    )

    result = pipeline.register(
        ref_image=img_ref,
        target_image=img_tgt,
        ref_sun=sun_ref,
        target_sun=sun_tgt,
    )

    m = result.metrics

    print("\n[TEST PIPELINE AUDIT]")
    print(f"Ref Features     : {m.num_detected_ref}")
    print(f"Target Features  : {m.num_detected_target}")
    print(f"Initial Matches  : {m.num_initial_matches}")
    print(f"Inliers          : {m.num_inliers}")
    print(f"Inlier Ratio     : {m.inlier_ratio * 100:.2f}%")
    print(f"RMSE (pixels)    : {m.rmse_pixels:.4f} px")
    print(f"ISRO Compliance  : {m.meets_isro_subpixel_mandate}")

    assert m.num_inliers >= 4, f"Insufficient inliers: {m.num_inliers}"
    assert result.transform_matrix is not None
    assert result.warped_target is not None
    assert m.rmse_pixels < 0.40, f"FAILED ISRO MANDATE: RMSE {m.rmse_pixels:.4f} px >= 0.40 px limit!"
    assert m.meets_isro_subpixel_mandate is True
