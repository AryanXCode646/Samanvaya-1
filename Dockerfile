# ==============================================================================
# ISRO Chandrayaan-2 Planetary Remote Sensing Engine (SIH PS 26166)
# Multi-stage production container with GDAL, PROJ, Rasterio, and PyTorch
# ==============================================================================

FROM python:3.11-slim-bullseye AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GDAL_DATA=/usr/share/gdal \
    PROJ_LIB=/usr/share/proj

# 1. Install system geospatial libraries (GDAL, PROJ, GEOS, LibTIFF)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    gdal-bin \
    libproj-dev \
    libgeos-dev \
    libspatialindex-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Install Python dependencies with GDAL version matching system GDAL
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    numpy \
    scipy \
    sympy \
    astropy \
    matplotlib \
    opencv-python-headless \
    tifffile \
    pydantic \
    fastapi \
    uvicorn \
    streamlit \
    pytest

# Install PyTorch CPU and Kornia
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir kornia-rs && \
    pip install --no-cache-dir kornia --no-deps

# Install Rasterio using wheel
RUN pip install --no-cache-dir rasterio

# 3. Copy application codebase
COPY . /app

# 4. Install ch2_lunar_reg in editable mode
RUN pip install -e .

EXPOSE 8000 8501

# Default command launches FastAPI REST API
CMD ["python3", "-m", "ch2_lunar_reg.interfaces.cli", "serve", "--port", "8000"]
