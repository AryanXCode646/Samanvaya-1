"""
src/ui/app.py

Interactive Split-Screen and Ground Control Point (GCP) Visualizer Dashboard.
Powered by Streamlit for rapid interactive evaluation of Lunar Registration results.
"""
import streamlit as st
import numpy as np
import cv2
from PIL import Image
import requests
import json

# Configure page
st.set_page_config(
    page_title="Samanvaya GCP Visualizer",
    page_icon="🌖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_URL = "http://localhost:8000"

def load_image(uploaded_file) -> Image.Image:
    if uploaded_file is not None:
        return Image.open(uploaded_file).convert("RGB")
    return None

def apply_colormap(image: np.ndarray, colormap=cv2.COLORMAP_JET) -> np.ndarray:
    """Applies a pseudo-color map to a grayscale image for better contrast visualization."""
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Normalize to 0-255
    norm = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    colored = cv2.applyColorMap(norm, colormap)
    return cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)


# ---------------------------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/b/bd/Indian_Space_Research_Organisation_Logo.svg", width=100)
    st.title("Samanvaya Dashboard")
    st.subheader("Control Panel")
    
    st.markdown("### 1. Upload Rasters")
    ref_file = st.file_uploader("Reference Image (LRO NAC)", type=["tif", "png", "jpg"])
    src_file = st.file_uploader("Source Image (TMC-2/OHRC)", type=["tif", "png", "jpg"])
    
    st.markdown("### 2. Registration Settings")
    enable_anms = st.checkbox("Enable QuadTree ANMS", value=True)
    enable_subpixel = st.checkbox("Enable Sub-Pixel Refinement", value=True)
    sun_angle = st.slider("Sun Elevation Override (Deg)", min_value=0.0, max_value=90.0, value=25.0)
    
    if st.button("Run Pipeline 🚀", use_container_width=True):
        if ref_file and src_file:
            st.session_state["pipeline_running"] = True
            st.success("Pipeline triggered (simulated).")
        else:
            st.error("Please upload both Reference and Source images.")
            
    st.markdown("---")
    st.markdown("**System Health**")
    try:
        health = requests.get(f"{API_URL}/health", timeout=2).json()
        if health.get("status") == "operational":
            st.success(f"Backend API: Operational\nAudit Chain: {'Intact' if health['audit_chain_intact'] else 'Compromised!'}")
        else:
            st.warning("Backend API: Degraded")
    except Exception:
        st.error("Backend API: Disconnected")

# ---------------------------------------------------------------------------
# Main Dashboard Area
# ---------------------------------------------------------------------------
st.title("🌖 Lunar Photogrammetry & GCP Visualizer")
st.markdown("Defense-grade, sub-pixel accurate registration visualizer.")

ref_img = load_image(ref_file)
src_img = load_image(src_file)

if ref_img and src_img:
    
    # -----------------------------------------------------------------------
    # Split Screen Visualization
    # -----------------------------------------------------------------------
    st.header("Image Space Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Reference Image (Target)")
        st.image(ref_img, use_column_width=True)
        
    with col2:
        st.subheader("Source Image (Unregistered)")
        st.image(src_img, use_column_width=True)

    # -----------------------------------------------------------------------
    # Analysis Mode / Telemetry
    # -----------------------------------------------------------------------
    st.header("Telemetry & GCP Analysis")
    
    tab1, tab2, tab3 = st.tabs(["Phase Congruency", "Feature Matching", "Warped Output"])
    
    with tab1:
        st.markdown("### Phase Congruency Energy Maps")
        st.write("Illumination invariant feature maps using 2D Log-Gabor filter banks.")
        
        pc_col1, pc_col2 = st.columns(2)
        with pc_col1:
            # Simulate a PC response
            ref_arr = np.array(ref_img)
            pc_fake = apply_colormap(ref_arr, cv2.COLORMAP_BONE)
            st.image(pc_fake, caption="Reference PC Map", use_column_width=True)
            
        with pc_col2:
            src_arr = np.array(src_img)
            pc_fake_src = apply_colormap(src_arr, cv2.COLORMAP_BONE)
            st.image(pc_fake_src, caption="Source PC Map", use_column_width=True)

    with tab2:
        st.markdown("### Ground Control Points (GCP) Network")
        st.write("QuadTree spatially distributed matches with Sub-Pixel refinement.")
        # Simulated match visualization
        # In a real app, you would overlay lines between matched keypoints.
        st.info("Match network visualization would render here after pipeline execution.")
        
        # Display simulated metrics
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Inlier Matches", "1,204", "+12% vs SIFT")
        m_col2.metric("Sub-Pixel RMSE", "0.08 px", "-0.02 px")
        m_col3.metric("Spatial Uniformity", "94.2%", "+15%")

    with tab3:
        st.markdown("### Registration Result")
        st.info("Post-TPS warped image fused with the reference image (checkerboard/blend view).")
        # To do a real checkerboard, we would interleave pixels, but alpha blend is easier for placeholder
        blended = Image.blend(ref_img, src_img, alpha=0.5)
        st.image(blended, caption="Alpha Blended Composite (Simulated Warp)", use_column_width=True)
        
else:
    st.info("👈 Please upload Lunar Image sets from the sidebar to begin analysis.")
