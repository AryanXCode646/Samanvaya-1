"""
Differentiable Planetary Computer Vision Operators (PyTorch & Kornia).
ISRO Chandrayaan-2 Registration Pipeline.

Enables:
1. GPU/CPU differentiable spatial grid warping.
2. Differentiable multi-scale structural similarity (SSIM) and PSNR.
3. Sub-pixel differentiable photometric loss functions.
"""

from __future__ import annotations

from typing import Tuple
import numpy as np
import torch
import kornia
import kornia.geometry.transform as K_geo
import kornia.metrics as K_metrics
import kornia.filters as K_filters


class DifferentiablePlanetaryOps:
    """
    Bridge between NumPy raster representations and PyTorch/Kornia differentiable ops.
    """

    @staticmethod
    def to_torch_tensor(img: np.ndarray, device: str = "cpu") -> torch.Tensor:
        """Converts 2D [H, W] or 3D [H, W, C] numpy image to [1, 1, H, W] float32 torch tensor."""
        if img.ndim == 2:
            t = torch.from_numpy(img).unsqueeze(0).unsqueeze(0).float()
        elif img.ndim == 3:
            t = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0).float()
        else:
            raise ValueError(f"Unsupported image dimensions: {img.ndim}")
        return t.to(device)

    @staticmethod
    def to_numpy(tensor: torch.Tensor) -> np.ndarray:
        """Converts [1, 1, H, W] or [1, C, H, W] torch tensor back to 2D numpy array."""
        t = tensor.detach().cpu().squeeze()
        return t.numpy()

    @classmethod
    def differentiable_affine_warp(
        cls,
        image: np.ndarray,
        affine_matrix_2x3: np.ndarray,
        output_size: Tuple[int, int],
        device: str = "cpu",
    ) -> np.ndarray:
        """
        Differentiable bilinear affine warping using Kornia.
        
        Args:
            image: 2D numpy array.
            affine_matrix_2x3: [2, 3] affine transformation.
            output_size: (height, width).
            device: torch device ('cpu' or 'cuda').
        """
        tensor = cls.to_torch_tensor(image, device)
        mat_tensor = torch.from_numpy(affine_matrix_2x3).unsqueeze(0).float().to(device)
        
        warped_tensor = K_geo.warp_affine(
            tensor,
            mat_tensor,
            dsize=output_size,
            mode="bilinear",
            padding_mode="zeros",
        )
        return cls.to_numpy(warped_tensor)

    @classmethod
    def compute_ssim_score(
        cls,
        img1: np.ndarray,
        img2: np.ndarray,
        window_size: int = 11,
        device: str = "cpu",
    ) -> float:
        """
        Computes Structural Similarity Index Measure (SSIM) between registered images.
        """
        t1 = cls.to_torch_tensor(img1, device)
        t2 = cls.to_torch_tensor(img2, device)
        
        ssim_val = K_metrics.ssim(t1, t2, window_size=window_size)
        return float(ssim_val.mean().item())

    @classmethod
    def compute_psnr_score(
        cls,
        img1: np.ndarray,
        img2: np.ndarray,
        max_val: float = 1.0,
        device: str = "cpu",
    ) -> float:
        """
        Computes Peak Signal-to-Noise Ratio (PSNR) in decibels.
        """
        t1 = cls.to_torch_tensor(img1, device)
        t2 = cls.to_torch_tensor(img2, device)
        
        psnr_val = K_metrics.psnr(t1, t2, max_val=max_val)
        return float(psnr_val.item())
