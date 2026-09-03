"""
Streamlit Real-Time Verification & Inspection Dashboard.
ISRO Chandrayaan-2 Lunar Optical Image Registration (SIH PS 26166).

Interactive Visualizations:
1. Solar illumination controls & shadow reversal simulation.
2. Inlier tie-point vector overlay & spatial distribution inspection.
3. Interactive checkerboard blending for sub-pixel boundary continuity.
4. Phase Congruency & RIFT Maximum Index Map (MIM) feature representations.
5. Quantitative residual error distribution and ISRO < 0.4 px RMSE compliance audit.
"""

from __future__ import annotations

import streamlit as st
import numpy as np
import cv2
import matplotlib.pyplot as plt

from ch2_lunar_reg.domain.models import SunAngles, TransformationModel
from ch2_lunar_reg.application.pipeline import LunarRegistrationPipeline
from ch2_lunar_reg.infrastructure.synthetic_generator import LunarTerrainSimulator
from ch2_lunar_reg.domain.phase_congruency import PhaseCongruencyEngine


st.set_page_config(
    page_title="ISRO Chandrayaan-2 Lunar Registration Engine (SIH PS 26166)",
    page_icon="🌕",
    layout="wide",
)

st.title("🌕 ISRO Chandrayaan-2 Planetary Image Registration Framework")
st.caption("SIH PS 26166: Multi-modal, Sun angle and scale invariant image correspondence (OHRC, TMC-2, IIRS)")

# Sidebar Controls
st.sidebar.header("🛰️ Orbital Sensor & Solar Geometry")

preset = st.sidebar.selectbox(
    "Mission Scenario Preset",
    [
        "Extreme Shadow Reversal (Morning 60° vs Afternoon 240°)",
        "Grazing Low-Sun (15°) vs High Noon (60°)",
        "Cross-Track Stereo TMC-2 Triplet (Fore vs Aft)",
        "Custom Parameters",
    ]
)

if preset == "Extreme Shadow Reversal (Morning 60° vs Afternoon 240°)":
    ref_az, ref_el = 60.0, 25.0
    tgt_az, tgt_el = 240.0, 35.0
elif preset == "Grazing Low-Sun (15°) vs High Noon (60°)":
    ref_az, ref_el = 90.0, 15.0
    tgt_az, tgt_el = 90.0, 60.0
elif preset == "Cross-Track Stereo TMC-2 Triplet (Fore vs Aft)":
    ref_az, ref_el = 45.0, 30.0
    tgt_az, tgt_el = 50.0, 28.0
else:
    ref_az = st.sidebar.slider("Reference Sun Azimuth (°)", 0.0, 360.0, 60.0)
    ref_el = st.sidebar.slider("Reference Sun Elevation (°)", 5.0, 85.0, 25.0)
    tgt_az = st.sidebar.slider("Target Sun Azimuth (°)", 0.0, 360.0, 240.0)
    tgt_el = st.sidebar.slider("Target Sun Elevation (°)", 5.0, 85.0, 35.0)

st.sidebar.markdown("---")
st.sidebar.header("🔬 Algorithmic Pipeline Knobs")

enable_photometric = st.sidebar.checkbox("Lommel-Seeliger Photometric Normalization", value=True)
enable_anms = st.sidebar.checkbox("Adaptive Non-Maximal Suppression (ANMS)", value=True)
enable_subpixel = st.sidebar.checkbox("2D Quadratic Taylor Sub-Pixel Refinement", value=True)
model_choice = st.sidebar.selectbox("Transformation Model", ["AFFINE", "HOMOGRAPHY", "TPS"])
target_features = st.sidebar.slider("Feature Quota (Features)", 100, 800, 350, step=50)

# Simulate Lunar Scene
@st.cache_data(show_spinner=False)
def get_simulated_pair(ref_az, ref_el, tgt_az, tgt_el):
    sim = LunarTerrainSimulator(size=(384, 384), seed=42)
    sun_ref = SunAngles(azimuth_deg=ref_az, elevation_deg=ref_el)
    sun_tgt = SunAngles(azimuth_deg=tgt_az, elevation_deg=tgt_el)
    img_ref, img_tgt, true_affine, dem = sim.generate_registered_pair_with_ground_truth(
        sun_ref=sun_ref,
        sun_tgt=sun_tgt,
        true_translation=(12.0, -8.0),
        true_rotation_deg=3.5,
    )
    return img_ref, img_tgt, true_affine, dem, sun_ref, sun_tgt

img_ref, img_tgt, true_affine, dem, sun_ref, sun_tgt = get_simulated_pair(ref_az, ref_el, tgt_az, tgt_el)

# Run Pipeline
with st.spinner("Executing Multi-Modal Invariant Registration Pipeline..."):
    pipeline = LunarRegistrationPipeline(
        target_features=target_features,
        enable_photometric_norm=enable_photometric,
        enable_anms=enable_anms,
        enable_subpixel=enable_subpixel,
        transformation_model=TransformationModel(model_choice),
    )
    result = pipeline.register(
        ref_image=img_ref,
        target_image=img_tgt,
        ref_sun=sun_ref,
        target_sun=sun_tgt,
    )

m = result.metrics

# Benchmark Cards
col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
col_m1.metric("RMSE (Sub-pixel)", f"{m.rmse_pixels:.3f} px", delta=f"{m.rmse_pixels - 0.4:.3f} vs 0.4 px", delta_color="inverse")
col_m2.metric("Total Matches", f"{m.num_initial_matches}")
col_m3.metric("Inlier Count", f"{m.num_inliers}")
col_m4.metric("Inlier Ratio (%)", f"{m.inlier_ratio * 100:.1f}%")
col_m5.metric("Spatial Uniformity", f"{m.spatial_uniformity_entropy:.2f} / 1.0")
col_m6.metric("Pipeline Latency", f"{m.processing_time_ms:.1f} ms")

if m.meets_isro_subpixel_mandate:
    st.success("🎯 **ISRO SIH PS 26166 Mandate Passed**: Sub-pixel RMSE < 0.40 pixels achieved under extreme illumination reversal.")
else:
    st.warning("⚠️ High geometric residual detected or insufficient inliers.")

# Main Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📸 Image Registration & Blending",
    "🔗 Interactive Vector Flow Field",
    "🌊 Phase Congruency & Retinex MSR",
    "📊 Residual Error Analytics",
    "🗺️ GIS & Photogrammetry Export",
])

with tab1:
    col_img1, col_img2, col_img3 = st.columns(3)
    col_img1.subheader("Reference Image (Morning Sun)")
    col_img1.image(img_ref, clamp=True, use_container_width=True, caption=f"Sun Az: {ref_az}°, El: {ref_el}°")
    
    col_img2.subheader("Target Image (Afternoon Sun)")
    col_img2.image(img_tgt, clamp=True, use_container_width=True, caption=f"Sun Az: {tgt_az}°, El: {tgt_el}° (Shadow Inverted)")
    
    col_img3.subheader("Registered & Warped Result")
    if result.warped_target is not None:
        col_img3.image(result.warped_target, clamp=True, use_container_width=True, caption="Aligned to Reference Frame")
    else:
        col_img3.error("Transformation could not be computed.")

    st.markdown("### 🎚️ 50/50 Split-Swipe Comparison")
    st.caption("Slide to wipe across Reference (Left) and Aligned Target (Right) to visually confirm sub-pixel alignment along crater boundaries.")
    if result.warped_target is not None:
        split_pct = st.slider("Split-Swipe Divider Position (%)", 0, 100, 50)
        h, w = img_ref.shape
        split_col = int((split_pct / 100.0) * w)
        split_view = np.zeros_like(img_ref)
        split_view[:, :split_col] = img_ref[:, :split_col]
        split_view[:, split_col:] = result.warped_target[:, split_col:]
        # Draw red separator line
        split_rgb = cv2.cvtColor((split_view * 255).astype(np.uint8), cv2.COLOR_GRAY2RGB)
        if 0 <= split_col < w:
            split_rgb[:, split_col, :] = [255, 30, 30]
        st.image(split_rgb, use_container_width=True, caption=f"Left: Reference Frame | Right: Registered Target (Split at {split_pct}%)")

    st.markdown("### 🏁 Checkerboard Blending Inspection")
    st.caption("Alternating spatial tiles verify seamless crater rim boundaries and crater wall continuity.")
    if result.warped_target is not None:
        checker_size = st.slider("Checkerboard Tile Size (pixels)", 16, 64, 32, step=8)
        h, w = img_ref.shape
        checker = np.zeros_like(img_ref)
        for y in range(0, h, checker_size):
            for x in range(0, w, checker_size):
                if ((x // checker_size) + (y // checker_size)) % 2 == 0:
                    checker[y:y+checker_size, x:x+checker_size] = img_ref[y:y+checker_size, x:x+checker_size]
                else:
                    checker[y:y+checker_size, x:x+checker_size] = result.warped_target[y:y+checker_size, x:x+checker_size]
        st.image(checker, clamp=True, use_container_width=True)

with tab2:
    st.subheader("Interactive Vector Flow Field (Match Directions & Magnitudes)")
    st.caption("Visualizes displacement vector field $(\Delta x, \Delta y)$ with color-coded magnitude and angular orientation.")
    
    if result.inliers:
        rx_list = np.array([m.ref_xy[0] for m in result.inliers])
        ry_list = np.array([m.ref_xy[1] for m in result.inliers])
        dx_list = np.array([m.target_xy[0] - m.ref_xy[0] for m in result.inliers])
        dy_list = np.array([m.target_xy[1] - m.ref_xy[1] for m in result.inliers])
        magnitudes = np.sqrt(dx_list**2 + dy_list**2)
        angles_deg = np.degrees(np.arctan2(dy_list, dx_list))

        fig, ax = plt.subplots(figsize=(10, 8))
        ax.imshow(img_ref, cmap="gray")
        
        # Quiver plot with color mapping to magnitude
        q = ax.quiver(
            rx_list, ry_list, dx_list, dy_list,
            magnitudes,
            cmap="autumn",
            angles="xy",
            scale_units="xy",
            scale=1.0,
            width=0.005,
            headwidth=4,
            headlength=5,
        )
        cbar = plt.colorbar(q, ax=ax, shrink=0.7)
        cbar.set_label("Displacement Magnitude (pixels)")
        
        ax.scatter(rx_list, ry_list, c="lime", s=20, edgecolors="black", linewidths=0.5, label="Ref Tie-Points")
        ax.set_title(f"USAC-MAGSAC++ Vector Flow Field ({len(result.inliers)} Inlier Vectors)")
        ax.legend(loc="upper right")
        ax.axis("off")
        st.pyplot(fig)

        # Vector Field Analytics Summary
        c_v1, c_v2, c_v3 = st.columns(3)
        c_v1.metric("Mean Displacement", f"{np.mean(magnitudes):.2f} px")
        c_v2.metric("Max Displacement", f"{np.max(magnitudes):.2f} px")
        c_v3.metric("Mean Flow Direction", f"{np.mean(angles_deg):.1f}°")
    else:
        st.warning("No inliers detected for vector flow field.")


with tab3:
    st.subheader("Phase Congruency Moments & Multiscale Retinex")
    pc_engine = PhaseCongruencyEngine(num_scales=4, num_orientations=6)
    pc_out = pc_engine.compute(img_ref)
    
    from ch2_lunar_reg.domain.photometric import LunarContrastEqualizer
    retinex = LunarContrastEqualizer()
    msr_img = retinex.equalize(img_ref)

    col_pc1, col_pc2, col_pc3 = st.columns(3)
    col_pc1.image(pc_out.phase_congruency, clamp=True, use_container_width=True, caption="Total Phase Congruency (PC)")
    col_pc2.image(pc_out.max_moment, clamp=True, use_container_width=True, caption="Maximum Moment (M_max - Invariant Crater Edges)")
    col_pc3.image(msr_img, clamp=True, use_container_width=True, caption="Multiscale Retinex (MSR) Dynamic Range Compression")

with tab4:
    st.subheader("Sub-Pixel Geometric Residual Distribution")
    if result.inliers:
        residuals = [m.residual_error for m in result.inliers if m.residual_error is not None]
        fig_hist, ax_hist = plt.subplots(figsize=(8, 4))
        ax_hist.hist(residuals, bins=25, color="royalblue", edgecolor="black", alpha=0.8)
        ax_hist.axvline(0.40, color="crimson", linestyle="--", linewidth=2, label="ISRO Mandate Limit (0.4 px)")
        ax_hist.axvline(m.rmse_pixels, color="green", linestyle="-", linewidth=2, label=f"Measured RMSE ({m.rmse_pixels:.3f} px)")
        ax_hist.set_xlabel("Geometric Residual Error (pixels)")
        ax_hist.set_ylabel("Number of Matches")
        ax_hist.set_title("Sub-Pixel Accuracy Distribution")
        ax_hist.legend()
        st.pyplot(fig_hist)
    else:
        st.info("No inliers available for residual analytics.")

with tab5:
    st.subheader("Planetary GIS & Photogrammetry Export")
    st.markdown("Export ground-truth tie-points and displacement vector fields for **QGIS**, **ArcGIS Pro**, or **USGS ISIS3 Jigsaw**.")

    from rasterio.transform import from_origin
    ref_transform = from_origin(0.0, 0.0, 1.0, 1.0)
    
    # Generate CSV GCP data
    gcp_lines = ["gcp_id,pixel_ref,line_ref,pixel_tgt,line_tgt,residual_px,confidence\n"]
    for idx, m in enumerate(result.inliers):
        rx, ry = m.ref_xy
        tx, ty = m.target_xy
        res = m.residual_error if m.residual_error is not None else 0.0
        gcp_lines.append(f"{idx},{rx:.4f},{ry:.4f},{tx:.4f},{ty:.4f},{res:.4f},{m.confidence:.4f}\n")
    gcp_csv = "".join(gcp_lines)

    # Generate GeoJSON Vector Field
    import json
    features = []
    for idx, m in enumerate(result.inliers):
        rx, ry = m.ref_xy
        tx, ty = m.target_xy
        features.append({
            "type": "Feature",
            "id": idx,
            "geometry": {
                "type": "LineString",
                "coordinates": [[float(rx), float(ry)], [float(tx), float(ty)]]
            },
            "properties": {
                "gcp_id": idx,
                "dx": float(tx - rx),
                "dy": float(ty - ry),
                "residual_px": float(m.residual_error if m.residual_error is not None else 0.0)
            }
        })
    geojson_str = json.dumps({"type": "FeatureCollection", "features": features}, indent=2)

    col_exp1, col_exp2 = st.columns(2)
    col_exp1.download_button(
        label="📥 Download Ground Control Points (GCPs CSV)",
        data=gcp_csv,
        file_name="ch2_inlier_gcps.csv",
        mime="text/csv",
    )
    col_exp2.download_button(
        label="📥 Download Displacement Vectors (GeoJSON)",
        data=geojson_str,
        file_name="ch2_vector_field.geojson",
        mime="application/geo+json",
    )

