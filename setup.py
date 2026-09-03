from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="samanvaya",
    version="1.0.0",
    author="Ashish Singh Bora",
    author_email="mr.ashishsinghbora@gmail.com",
    description="Industry-Grade Lunar Optical Image Registration Framework (ISRO Chandrayaan-2 SIH PS 26166)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ashishsinghbora/Samanvaya",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Image Processing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "torch>=2.0.0",
        "kornia>=0.7.0",
        "opencv-contrib-python>=4.8.0",
        "rasterio>=1.3.0",
        "scipy>=1.10.0",
        "streamlit>=1.30.0",
        "numpy>=1.24.0",
        "matplotlib>=3.7.0",
        "pydantic>=2.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "defusedxml>=0.7.1",
    ],
    entry_points={
        "console_scripts": [
            "samanvaya=lunar_core.cli:main",
        ],
    },
)
