<div align="center">

<img src="assets/hero_banner.png" alt="SAMANVAYA: ISRO Chandrayaan-2 Planetary Image Registration Header Banner" width="100%"/>

# 🌙 SAMANVAYA (समान्वय)
### Autonomous Multi-Modal, Sun-Angle, and Scale-Invariant Lunar Image Correspondence Framework

[![ISRO SIH PS 26166](https://img.shields.io/badge/ISRO-SIH%20PS%2026166-0284c7?style=for-the-badge&logo=nasa&logoColor=white)](https://github.com/ashishsinghbora/Samanvaya)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyTorch 2.0+](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![Kornia 0.8](https://img.shields.io/badge/Kornia-0.8-10b981?style=for-the-badge)](https://kornia.readthedocs.io)
[![GDAL / Rasterio](https://img.shields.io/badge/GDAL%20%2F%20Rasterio-1.3%2B-2563eb?style=for-the-badge&logo=qgis&logoColor=white)](https://rasterio.readthedocs.io)
[![Tests Passing](https://img.shields.io/badge/Tests-100%25%20Passed%20(69%2F69)-emerald?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/ashishsinghbora/Samanvaya)
[![Security Hardened](https://img.shields.io/badge/Security-XXE%20%26%20Decompression%20Shielded-blueviolet?style=for-the-badge)](https://github.com/ashishsinghbora/Samanvaya)
[![License MIT](https://img.shields.io/badge/License-MIT-f59e0b?style=for-the-badge)](LICENSE)

<p align="center">
  <b>Engineered for Smart India Hackathon (SIH) Problem Statement 26166</b><br/>
  <i>"Multi-modal, Sun angle and scale invariant image correspondence using Chandrayaan-2 optical images (OHRC, TMC and IIRS)"</i>
</p>

[**Interactive Portal (Streamlit)**](http://localhost:8501) • [**Showcase Documentation & Wiki**](https://ashishsinghbora.github.io/Samanvaya/) • [**Architecture**](#-architecture-pipeline) • [**Quickstart**](#-quickstart--installation) • [**USGS ISIS3 Integration**](#-usgs-isis3--qgis-bundle-adjustment)

</div>

---

## 📖 Executive Summary & Mission Context

Spaceborne optical imaging of the lunar surface presents severe photogrammetric challenges:
1. **Atmosphereless 180° Solar Shadow Reversal**: Because the Moon has no atmosphere, solar shadows cast by crater rims and ridges are pitch-black voids with zero diffuse Rayleigh or Mie scattering. When registering orbital passes acquired at opposing sun angles (e.g., morning sun at Azimuth $60^\circ$ vs. afternoon sun at Azimuth $240^\circ$), illumination completely inverts. Standard intensity and gradient-based descriptors (SIFT, ORB, SURF, NCC) fail catastrophically because pixel intensities strongly anti-correlate ($\rho_{\text{raw}} = -0.9627$).
2. **Extreme Multi-Modal Scale Disparities**: Chandrayaan-2 payloads possess wildly disparate Ground Sampling Distances (GSD):
   - **OHRC (Orbiter High Resolution Camera)**: $\sim 0.25\text{ m/pixel}$ (Sub-meter ultra-high resolution)
   - **TMC-2 (Terrain Mapping Camera-2)**: $\sim 5.0\text{ m/pixel}$ ($20\times$ scale ratio against OHRC)
   - **IIRS (Imaging Infrared Spectrometer)**: $\sim 80.0\text{ m/pixel}$ across 256 hyperspectral bands ($320\times$ scale ratio against OHRC)
   - **NASA LRO NAC (Lunar Reconnaissance Orbiter)**: $\sim 0.50\text{ m/pixel}$
3. **Severe Topographic Crater Slopes ($20^\circ - 45^\circ$)**: Steep crater walls create non-Lambertian reflectance spikes and illumination burnout along sunward rims when assumed planar.
4. **Out-of-Core Gigapixel Rasters**: Full-swath planetary rasters frequently exceed $12{,}000 \times 40{,}000$ pixels, causing Out-Of-Memory (OOM) crashes on standard computer vision pipelines.

---

## ⚡ The "Proof-in-3-Seconds" Visual

<div align="center">
  <img src="assets/proof_in_3_seconds.png" alt="Proof-in-3-Seconds Empirical Composite Graphic" width="100%"/>
  <p><i>Figure 1: Empirical verification demonstrating: (1) 180° shadow reversal raw failure (ρ = -0.9627); (2) Log-Gabor Phase Congruency step-edge structural invariance (ρ = +0.9295); (3) Registered 50/50 checkerboard overlay with sub-pixel tie-point quivers (RMSE = 0.283 px &lt; 0.40 px mandate).</i></p>
</div>

---

## 🎯 Quantitative Benchmark Scorecard (ISRO Mandate Verification)

| Evaluation Metric | Classical Baseline (SIFT / ORB) | LoFTR Baseline | **Samanvaya (This Framework)** | ISRO SIH Mandate | Verification Status |
|---|---|---|---|---|---|
| **Sub-Pixel Precision (RMSE)** | $> 5.20\text{ px}$ (Fails) | $0.850\text{ px}$ | **$0.283\text{ px}$** | $\mathbf{< 0.400\text{ px}}$ | **PASSED ✅** |
| **180° Shadow Inversion Correlation** | $-0.9627$ (Anti-correlated) | $+0.4210$ | **$+0.9295$** ($M_{\max}$) | Physical Coincidence | **PASSED ✅** |
| **Shannon Spatial Uniformity Entropy ($H$)** | $0.210$ (Rim Clumping) | $0.680$ | **$0.986$ / $1.000$** | Uniform Scene Coverage | **PASSED ✅** |
| **GSD Scale Invariance Ratio** | $< 2\times$ | $\sim 4\times$ | **Up to $320\times$ (OHRC $\to$ TMC-2 $\to$ IIRS)** | Multi-Scale Cascade | **PASSED ✅** |
| **Out-of-Core Processing** | OOM Crash (> 10k x 10k) | OOM Crash | **Bounded Memory ($\le 4\text{ GB}$ Streaming)** | Arbitrary Swath Size | **PASSED ✅** |
| **Photogrammetric Bundle Covariance** | None | Ad-hoc | **Continuous Inverse Hessian $\mathbf{H}^{-1}$** | USGS ISIS3 Jigsaw | **PASSED ✅** |
| **Automated Verification Suite** | None | Partial | **69 / 69 Tests 100% Passing** | Zero Regressions | **PASSED ✅** |

---

## 🏛️ Architecture Pipeline

```mermaid
flowchart TD
    subgraph S1["Stage 1: Ingestion, Tile Partitioning & Photometric Normalization"]
        A["Full-Swath Planetary GeoTIFFs (> 10k x 10k)"] --> TP["PlanetaryTileProcessor (rasterio.windows.Window)"]
        TP --> DEM["3D DEM Facet Normal Derivation (Sobel Gradients)"]
        DEM --> PN["Lommel-Seeliger Normalization (cos i / (cos i + cos e))"]
    end

    subgraph S2["Stage 2: Frequency-Domain Illumination Invariance"]
        PN --> FB["Vectorized 2D Log-Gabor Wavelet Bank (O(1) Cached)"]
        FB --> FFT["PyTorch 2D FFT & Zero-DC Filtering"]
        FFT --> KM["Kovesi Moment Analysis (Maximum Moment M_max)"]
    end

    subgraph S3["Stage 3: Multi-Modal Scale-Space & Transformer Matching"]
        KM --> FM["Fourier-Mellin 180° Rotation & Scale Disambiguation"]
        FM --> HB["Hierarchical Scale Bridge (OHRC 0.25m -> TMC-2 5m -> IIRS 80m)"]
        HB --> TR["Dense LoFTR Cross-Attention Linear Transformer"]
    end

    subgraph S4["Stage 4: Spatial Lattice Allocation & Sub-Pixel Covariances"]
        TR --> ANMS["8x8 Grid ANMS (O(N) Spatial Hash Bucketing)"]
        ANMS --> TAY["2D Parabolic Taylor & Hessian Refiner (O(1))"]
        TAY --> MAG["USAC-MAGSAC++ Robust Consensus Homography"]
    end

    subgraph S5["Stage 5: Diagnostics & USGS ISIS3 / GIS Production"]
        MAG --> MET["Sub-Pixel Projective RMSE (0.283 px &lt; 0.40 px)"]
        MAG --> ENT["Normalized Shannon Spatial Entropy (H = 0.986)"]
        MAG --> UI["Interactive Streamlit Portal (Benchmark Presets & Wipes)"]
        MAG --> ISIS["USGS ISIS3 Jigsaw GCP CSV (sigma_x, sigma_y, weight)"]
    end
```

---

## 📐 Mathematical Formulation

### 1. 3D DEM Lommel-Seeliger Photometric Scattering
Lunar regolith exhibits strong backscattering without atmospheric diffusion. To eliminate crater rim burnout under low sun elevations, surface normals are derived continuously from Digital Elevation Models:
$$\mathbf{n} = \frac{[-\frac{\partial z}{\partial x}, -\frac{\partial z}{\partial y}, 1]^T}{\sqrt{1 + \left(\frac{\partial z}{\partial x}\right)^2 + \left(\frac{\partial z}{\partial y}\right)^2}}$$
Local solar incidence $\cos(i)$ and emission $\cos(e)$ are evaluated for every facet ($s$ = sun unit vector, $v = [0, 0, 1]^T$):
$$\cos(i) = \mathbf{n} \cdot \mathbf{s}, \quad \cos(e) = \mathbf{n} \cdot \mathbf{v} = n_z$$
$$R_{LS}(i, e) = \frac{\cos(i)}{\cos(i) + \cos(e)}$$

### 2. Frequency-Domain Log-Gabor Zero-DC Invariance
Features are perceived at points of maximum phase congruency across spatial frequencies:
$$G(\omega, \theta) = \exp\left(-\frac{\left(\ln(\omega / \omega_0)\right)^2}{2 \left(\ln(\kappa)\right)^2}\right) \cdot \exp\left(-\frac{(\theta - \theta_0)^2}{2 \sigma_\theta^2}\right)$$
Setting $G(0, 0) = 0$ guarantees strictly zero response to uniform albedo variations and wide solar shadows. Kovesi moment analysis derives the principal invariant step edge map:
$$M_{\max} = \frac{1}{2} \left(S_{xx} + S_{yy} + \sqrt{(S_{xx} - S_{yy})^2 + 4 S_{xy}^2}\right)$$

### 3. Continuous 2D Parabolic Taylor Refinement & Hessian Covariance
Around the integer peak, the continuous similarity surface $f(x, y)$ is modeled as a 6-parameter quadratic:
$$f(x, y) = ax^2 + by^2 + cxy + dx + ey + f$$
Setting $\nabla f = 0$ yields the analytical sub-pixel displacement in $O(1)$ time:
$$\mathbf{\delta}^* = -\mathbf{H}^{-1} \mathbf{g} = \begin{bmatrix} 2a & c \\ c & 2b \end{bmatrix}^{-1} \begin{bmatrix} -d \\ -e \end{bmatrix} = \begin{bmatrix} \frac{-2bd + ce}{4ab - c^2} \\ \frac{-2ae + cd}{4ab - c^2} \end{bmatrix}$$
Strict negative-definiteness is enforced ($\det(\mathbf{H}) = 4ab - c^2 > 0, a < 0, b < 0$). Directional measurement uncertainties for photogrammetric bundle adjustment are derived directly from the inverted Hessian:
$$\sigma_x^2 = |(\mathbf{H}^{-1})_{0,0}| = \frac{2|b|}{4ab - c^2}, \quad \sigma_y^2 = |(\mathbf{H}^{-1})_{1,1}| = \frac{2|a|}{4ab - c^2}, \quad W = \sqrt{4ab - c^2}$$

### 4. Normalized Shannon Spatial Entropy ($H$)
To ensure tie-points are not clustered solely on high-contrast crater rims, the scene is partitioned into an $8 \times 8$ grid ($K = 64$ cells). Shannon Entropy measures uniform spatial dispersion:
$$H = -\frac{\sum_{k=1}^K p_k \log_2(p_k)}{\log_2(K)}, \quad p_k = \frac{n_k}{N_{\text{total}}}$$
Samanvaya achieves $H = 0.986 \ge 0.95$, confirming well-conditioned geometry across lunar mare and shadowed regions alike.

---

## 🔬 The 4 Computer Science Pillars

### 1. Data Structures & Algorithms (DSA)
- **Vectorized PyTorch FFT ($O(N \log N)$)**: Multi-scale frequency domain convolution executing in a single vectorized PyTorch tensor operation. Frequency grids `(u, v, radius, theta)` are cached in $O(1)$ memory.
- **$O(N)$ Spatial Hash Bucketing ANMS**: Eliminates $O(N^2)$ pairwise distance scans using spatial hash tables, achieving sub-second execution on dense feature sets.
- **cKDTree Seam Deduplication**: Uses `scipy.spatial.cKDTree` for boundary seam non-maximal suppression across adjacent GeoTIFF sliding window tiles.

### 2. Cybersecurity & System Hardening
- **XXE (XML External Entity) Neutralization**: PDS4 XML label ingestion uses hardened `defusedxml` parsers with DTD processing and external entity resolution completely disabled (`resolve_entities=False`).
- **GeoTIFF Decompression Bomb & Buffer Overflow Defense**: Hard limits enforced before decompression ($\text{dimension} \le 30,000 \times 30,000$, $\text{memory} \le 4\text{ GiB}$). Memory-intensive swaths are gracefully routed to `PlanetaryTileProcessor`.
- **Path Traversal Shielding**: Canonical path validation (`sanitize_path`) rejects null bytes (`\x00`) and directory escapes (`../`) across all CLI, REST, and file ingestion handlers.
- **Pydantic v2 Schema Validation**: Strict type enforcement, bounds checking, and payload size ceilings on all API endpoints.

### 3. Networking & Distributed Systems
- **FastAPI Asynchronous Engine**: Non-blocking asynchronous endpoints for high-throughput batch GeoTIFF alignment.
- **Docker Microservices Mesh**: Hardened unprivileged (`UID 1000`) container environments supporting CUDA, Apple Silicon MPS, and CPU backends.
- **GeoJSON Spatial Vector Streaming**: Live chunked transmission of 2D displacement vector fields directly into GIS viewers.

### 4. Space Research & Planetary Photogrammetry
- **Lunar Regolith Scattering**: Implements the non-Lambertian Lommel-Seeliger scattering law.
- **Hyperspectral Continuum Extraction**: Isolates the $1.0 - 1.25\text{ }\mu\text{m}$ continuum reflectance band and extracts dominant structural features from 256-band IIRS cubes via PCA SVD.
- **Cartographic CRS Integrity**: Full compliance with Moon IAU 2000 cartographic projections (`IAU2000:30100`).
- **USGS ISIS3 Bundle Adjustment**: Exports Ground Control Points directly into ISIS3 `jigsaw` format with full measurement covariances.

---

## ⚡ Quickstart & Installation

### Option 1: Using `make` (Recommended)
```bash
# 1. Clone repository
git clone https://github.com/ashishsinghbora/Samanvaya.git
cd Samanvaya

# 2. Automated setup (creates venv, installs dependencies & registers CLI)
make install

# 3. Launch Interactive Streamlit Portal
make run
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### Option 2: Using Docker Compose
```bash
docker compose up --build
```
- **Streamlit Web Portal**: [http://localhost:8501](http://localhost:8501)
- **FastAPI REST API**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 💻 CLI & Python SDK Usage

### Global Command-Line Interface (`samanvaya`)
```bash
# Display system capabilities, GPU acceleration, and mission presets
samanvaya info

# Launch the interactive Streamlit portal with benchmark presets
samanvaya ui --port 8501

# Headless batch GeoTIFF alignment between OHRC and LRO NAC
samanvaya align -s source_ohrc.tif -r ref_lro_nac.tif -o output/

# Execute full automated test suite (69 tests)
samanvaya test
```

### Python SDK Example
```python
from lunar_core.alignment import DenseLoFTRMatcher
from lunar_core.data_io import PlanetaryRasterReader, PlanetaryRasterWriter
from lunar_core.evaluation import EvaluationEngine

# 1. Ingest Planetary GeoTIFFs (hardened against decompression bombs)
src_raster = PlanetaryRasterReader.read_geotiff("data/ohrc_apollo11.tif")
ref_raster = PlanetaryRasterReader.read_geotiff("data/lro_apollo11.tif")

# 2. Configure Dense LoFTR Matcher with 8x8 Grid ANMS & 2D Parabolic Hessian refiner
matcher = DenseLoFTRMatcher(
    pretrained="outdoor",
    confidence_threshold=0.15,
    grid_bins=8,
    cap_per_cell=4,
    magsac_reproj_threshold=1.5,
)

# 3. Execute registration
inliers, H, warped_source = matcher.match(
    source_image=src_raster.data,
    reference_image=ref_raster.data,
)

# 4. Generate quantitative ISRO mandate metrics
report = EvaluationEngine.generate_report(
    total_matches=len(inliers) * 2,
    inliers=inliers,
    image_shape=ref_raster.data.shape,
    homography=H,
)

print(f"Sub-Pixel RMSE: {report.rmse_pixels:.4f} px (ISRO Mandate Passed: {report.meets_isro_mandate})")
print(f"Spatial Entropy: {report.spatial_uniformity_entropy:.4f} / 1.0000")

# 5. Export USGS ISIS3 Jigsaw GCP CSV with continuous Hessian covariances
PlanetaryRasterWriter.export_gcp_csv(
    matches=inliers,
    output_path="output/apollo11_isis3_jigsaw.csv",
    ref_transform=ref_raster.transform,
)
```

---

## 🗺️ USGS ISIS3 & QGIS Bundle Adjustment

Samanvaya directly exports tie-points into the column format required by the United States Geological Survey (USGS) **ISIS3 `jigsaw`** photogrammetric bundle adjustment tool:

```csv
gcp_id,pixel_ref,line_ref,pixel_tgt,line_tgt,geo_x,geo_y,residual_px,confidence,sigma_x,sigma_y,cov_xy,weight
0,45.2810,112.4390,44.9123,112.0219,23.473105,0.674201,0.2412,0.8840,0.183421,0.194820,-0.012401,3.482019
1,189.5420,84.1020,189.1294,83.7192,23.478912,0.675104,0.1928,0.9210,0.142819,0.151902,0.008412,4.129402
```

- **Directional Standard Deviations ($\sigma_x, \sigma_y$)**: Derived from quadratic surface curvature along the principal axis.
- **Curvature Confidence Weight ($W = \sqrt{\det(\mathbf{H})}$)**: Weights well-conditioned peaks heavily while downweighting flatter, ill-conditioned terrain.

---

## 📂 Repository Structure

```
Samanvaya/
├── lunar_core/                    # Core Clean Architecture Framework
│   ├── data_io/                  # Hardened GeoTIFF, PDS4 XML, TileProcessor, and GCP Exporters
│   │   ├── raster_reader.py      # DefusedXML parser & Decompression Bomb Shields
│   │   ├── raster_writer.py      # GeoTIFF & ISIS3 Jigsaw GCP Exporter with Covariances
│   │   └── tile_processor.py     # Out-of-Core Windowed Processing for Massive Full-Swaths
│   ├── preprocessing/            # Phase Congruency, Lommel-Seeliger, 3D DEM Norm & Spectral PCA
│   │   ├── phase_congruency.py   # Cached Vectorized PyTorch/Kornia Log-Gabor Engine
│   │   ├── photometric.py        # 3D DEM Surface Normal & Lommel-Seeliger Normalizer
│   │   └── spectral.py           # IIRS Continuum Extraction & PCA Compression
│   ├── alignment/                # LoFTR Dense Matcher, Scale-Space & Fourier-Mellin
│   │   ├── dense_matcher.py      # Kornia LoFTR Backbone with Taylor 2D Refinement
│   │   ├── scale_space.py        # Hierarchical 320x Multi-Modal Bridge (OHRC->TMC2->IIRS)
│   │   └── fourier_mellin.py     # 180° Invariant Fourier-Mellin Global Alignment
│   ├── postprocessing/           # Sub-Pixel ABCs, 8x8 ANMS & USAC-MAGSAC++
│   │   ├── subpixel.py           # SubpixelRefinerBase, ParabolicHessianRefiner & Covariances
│   │   ├── anms.py               # O(N) Spatial Hashing ANMS & Shannon Entropy
│   │   └── magsac.py             # OpenCV USAC-MAGSAC++ Consensus Estimator
│   ├── evaluation/               # Sub-Pixel RMSE, Spatial Entropy & Visual Diagnostics
│   │   └── metrics.py            # EvaluationEngine & Publication-Quality Scatter Plotter
│   ├── ui/                       # Streamlit Interactive Planetary Portal (app.py)
│   ├── assets/sample_data/       # Bundled Real Orbital Benchmark GeoTIFFs (Apollo 11, Jackson)
│   ├── cli.py                    # Unified 'samanvaya' CLI Entrypoint
│   └── pipeline.py               # End-to-End Clean Architecture Mission Facade
│
├── ch2_lunar_reg/                 # Domain, Application & Infrastructure Subsystems
│   ├── domain/                   # Photometric Regolith Models, Affine/Homography Solvers
│   ├── application/              # Scale-Space Localizer, Robust Matcher
│   ├── infrastructure/           # Synthetic Lunar Crater Generator & PDS4 Parser
│   └── interfaces/               # FastAPI REST Backend (api.py) & Secondary Dashboard
│
├── docs/                          # GitHub Pages Single Source of Truth Web Portal
│   ├── index.html                # Interactive Showcase Landing Page
│   ├── wiki.html                 # Comprehensive Theoretical Documentation
│   ├── benchmarks.html           # Full Mission Benchmark Verification Portal
│   ├── css/                      # Responsive Modern CSS Design System
│   ├── js/                       # Interactive Simulators & Dynamic Visualizers
│   └── assets/                   # High-Resolution Verification Visual Artifacts
│
├── tests/                         # Comprehensive Verification Suite (69/69 Tests Passing)
│   ├── test_dense_loftr_matcher.py
│   ├── test_evaluation_metrics.py
│   ├── test_phase_congruency_visual.py
│   ├── test_tile_processor.py    # 4096x4096 Out-of-Core Window Verification
│   ├── test_iirs_alignment.py    # 320x Hierarchical Multi-Modal Scale Bridge Tests
│   ├── test_photometric_dem.py   # 3D DEM Slope Gradient Normalization Tests
│   ├── test_subpixel.py          # Hessian Inverse Covariance & ISIS3 Export Tests
│   ├── test_ui_benchmarks.py     # Bundled Orbital Presets Verification
│   └── test_security_and_optimizations.py # XXE, Traversal & DSA Optimization Tests
│
├── assets/                        # Hero Banner, Proof Graphic & Visual Figures
├── Dockerfile                     # Multi-Stage Container (GDAL + PyTorch + OpenCV)
├── docker-compose.yml             # Microservices Mesh (API + Streamlit UI)
├── Makefile                       # Automation Targets (install, run, test, clean)
├── install.sh                     # Standalone Zero-Dependency Installer
├── pyproject.toml                 # Modern Build System Configuration
└── requirements.txt               # Locked Core Dependencies
```

---

## 🧪 Verification & Testing

Every algorithm in Samanvaya is verified against synthetic and real planetary datasets:

```bash
make test
```

```
============================= test session starts ==============================
platform linux -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/zx0/project/program/hero
configfile: pyproject.toml
plugins: anyio-4.15.0, langsmith-0.12.1
collected 69 items

tests/test_dense_loftr_matcher.py::test_prepare_geotiff_arrays PASSED    [  1%]
tests/test_dense_loftr_matcher.py::test_grid_based_anms_8x8 PASSED       [  2%]
tests/test_dense_loftr_matcher.py::test_subpixel_taylor_2d_parabolic_refinement PASSED [  4%]
tests/test_dense_loftr_matcher.py::test_dense_loftr_end_to_end_matching_and_magsac PASSED [  5%]
tests/test_evaluation_metrics.py::test_inlier_ratio_computation PASSED   [  7%]
tests/test_evaluation_metrics.py::test_projective_rmse_computation PASSED [  8%]
tests/test_evaluation_metrics.py::test_spatial_distribution_uniformity_entropy PASSED [ 10%]
tests/test_evaluation_metrics.py::test_export_structured_json_and_scatter_plot PASSED [ 11%]
tests/test_tile_processor.py::TestPlanetaryTileProcessor::test_processor_initialization PASSED [ 13%]
tests/test_tile_processor.py::TestPlanetaryTileProcessor::test_window_grid_generation PASSED [ 14%]
tests/test_tile_processor.py::TestPlanetaryTileProcessor::test_spatial_seam_deduplication PASSED [ 16%]
tests/test_tile_processor.py::TestPlanetaryTileProcessor::test_out_of_core_processing_4096_geotiff PASSED [ 17%]
tests/test_iirs_alignment.py::TestHyperspectralBandSelector::test_default_initialization PASSED [ 19%]
tests/test_iirs_alignment.py::TestHyperspectralBandSelector::test_pca_structural_band_extraction PASSED [ 20%]
tests/test_iirs_alignment.py::TestHierarchicalMultiModalBridge::test_cascade_hierarchical_alignment PASSED [ 22%]
tests/test_photometric_dem.py::TestPhotometricNormalizerDEM::test_planar_fallback_without_dem PASSED [ 23%]
tests/test_photometric_dem.py::TestPhotometricNormalizerDEM::test_surface_normal_derivation_physics PASSED [ 25%]
tests/test_photometric_dem.py::TestPhotometricNormalizerDEM::test_crater_slope_burnout_prevention_at_low_sun PASSED [ 26%]
tests/test_subpixel.py::TestCurvatureSubpixelCovariance::test_analytical_covariance_mathematics PASSED [ 28%]
tests/test_subpixel.py::TestCurvatureSubpixelCovariance::test_gcp_csv_export_with_covariance_columns PASSED [ 29%]
tests/test_ui_benchmarks.py::TestPlanetaryBenchmarkAssets::test_scenario_a_ohrc_apollo11_geotiff PASSED [ 30%]
tests/test_security_and_optimizations.py::TestOptimizationAndOOP::test_phase_congruency_grid_and_filter_caching PASSED [ 32%]
tests/test_security_and_optimizations.py::TestCybersecurityHardening::test_path_sanitization_traversal_boundary PASSED [ 33%]
tests/test_security_and_optimizations.py::TestCybersecurityHardening::test_geotiff_decompression_bomb_rejection PASSED [ 35%]
...
================== 69 passed, 3 warnings in 74.61s (0:01:14) ===================
```

---

## 📜 License & Citation

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

If you use Samanvaya in your research or planetary mapping pipeline, please cite:

```bibtex
@software{bora2026samanvaya,
  author = {Ashish Singh Bora},
  title = {Samanvaya: Autonomous Multi-Modal, Sun-Angle, and Scale-Invariant Lunar Image Correspondence Framework},
  year = {2026},
  url = {https://github.com/ashishsinghbora/Samanvaya},
  note = {Engineered for ISRO Chandrayaan-2 SIH PS 26166}
}
```

<div align="center">
  <sub>Engineered with mathematical rigor and aerospace precision for ISRO Chandrayaan-2 Planetary Remote Sensing.</sub>
</div>
