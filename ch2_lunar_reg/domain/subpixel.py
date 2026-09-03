"""
O(1) Parabolic Taylor Sub-Pixel Refinement & Hessian Covariance Estimation.
ISRO Chandrayaan-2 Planetary Remote Sensing (SIH PS 26166).

Theoretical Formulation:
Continuous 2D bivariate quadratic patch:
    f(x, y) = a*x^2 + b*y^2 + c*x*y + d*x + e*y + f
around the integer grid center (0, 0) over a 3x3 local neighborhood.

Hessian matrix:
    H = [[2a,  c],
         [ c, 2b]]
Determinant:
    det(H) = 4*a*b - c^2

Strict Negative-Definite Validation:
    det(H) > 0, a < 0, b < 0
Guarantees a strict local maximum (concave paraboloid peak) and rejects hyperbolic
saddle points and local minima, achieving target RMSE < 0.40 pixels.

Inverse Hessian Covariance & Eigenvalue Decomposition:
    Sigma = (-H)^(-1) = 1/(4*a*b - c^2) * [[-2b,   c],
                                           [  c, -2a]]
    sigma_x = sqrt(Sigma_xx), sigma_y = sqrt(Sigma_yy)
    Eigenvalues (lambda_1, lambda_2) define principal uncertainty axes for confidence weighting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np


@dataclass
class SubpixelSurfaceFit:
    """
    Result of continuous 2D quadratic patch fitting.
    Supports backward-compatible tuple unpacking:
        dx, dy, peak_val = fit
    """
    dx: float
    dy: float
    peak_val: float
    sigma_x: float
    sigma_y: float
    cov_xy: float
    eigenvalues: Tuple[float, float]
    weight: float

    def __iter__(self):
        yield self.dx
        yield self.dy
        yield self.peak_val

    def as_tuple(self) -> Tuple[float, float, float, float, float, float, Tuple[float, float], float]:
        return (
            self.dx,
            self.dy,
            self.peak_val,
            self.sigma_x,
            self.sigma_y,
            self.cov_xy,
            self.eigenvalues,
            self.weight,
        )


def fit_quadratic_peak(patch_3x3: np.ndarray) -> Optional[SubpixelSurfaceFit]:
    r"""
    Fits an analytical 2D bivariate quadratic surface:
        f(x, y) = a*x^2 + b*y^2 + c*x*y + d*x + e*y + f
    around integer grid point (0, 0) over a 3x3 local neighborhood.

    Stationary point:
        dx* = (-2*b*d + c*e) / (4*a*b - c^2)
        dy* = (-2*a*e + c*d) / (4*a*b - c^2)

    Strict Validation:
        a < 0, b < 0, det(H) = 4*a*b - c^2 > 1e-7.
        Displacement bound: |dx*| <= 1.0, |dy*| <= 1.0.

    Covariance:
        Sigma = (-H)^(-1)
        Eigenvalues lambda_1 >= lambda_2 > 0 extracted for confidence weighting.

    Args:
        patch_3x3: 3x3 similarity surface with center at index [1, 1].

    Returns:
        SubpixelSurfaceFit or None if saddle point / degenerate.
    """
    if patch_3x3.shape != (3, 3):
        raise ValueError(f"Expected 3x3 patch, got shape {patch_3x3.shape}")

    # Discrete samples at row y in {-1, 0, +1}, col x in {-1, 0, +1}
    z00 = float(patch_3x3[1, 1])  # (0, 0)
    z_xp = float(patch_3x3[1, 2]) # (+1, 0)
    z_xm = float(patch_3x3[1, 0]) # (-1, 0)
    z_yp = float(patch_3x3[2, 1]) # (0, +1)
    z_ym = float(patch_3x3[0, 1]) # (0, -1)
    z_pp = float(patch_3x3[2, 2]) # (+1, +1)
    z_pm = float(patch_3x3[0, 2]) # (+1, -1)
    z_mp = float(patch_3x3[2, 0]) # (-1, +1)
    z_mm = float(patch_3x3[0, 0]) # (-1, -1)

    # 6-parameter analytical quadratic polynomial
    a = (z_xp - 2.0 * z00 + z_xm) / 2.0
    b = (z_yp - 2.0 * z00 + z_ym) / 2.0
    c = (z_pp - z_pm - z_mp + z_mm) / 4.0
    d = (z_xp - z_xm) / 2.0
    e = (z_yp - z_ym) / 2.0
    f = z00

    # Hessian Determinant det(H) = 4*a*b - c^2
    det_h = 4.0 * a * b - c**2

    # Negative-definite Hessian check (strict maximum):
    # det(H) > 0 and a < 0 and b < 0. Rejects saddle points and local minima.
    if det_h <= 1e-7 or a >= 0.0 or b >= 0.0:
        return None

    # Analytical sub-pixel peak (dx*, dy*)
    dx = (-2.0 * b * d + c * e) / det_h
    dy = (-2.0 * a * e + c * d) / det_h

    # Ensure peak remains within 1-pixel radius
    if abs(dx) > 1.0 or abs(dy) > 1.0:
        return None

    # Continuous peak value
    peak_val = a * dx**2 + b * dy**2 + c * dx * dy + d * dx + e * dy + f

    # Inverse negative Hessian Covariance Matrix:
    # Sigma = (-H)^(-1) = (1 / det_h) * [[-2b, c], [c, -2a]]
    sigma_xx = (-2.0 * b) / det_h
    sigma_yy = (-2.0 * a) / det_h
    cov_xy = c / det_h

    # Coordinate standard deviations
    sigma_x = float(np.sqrt(max(sigma_xx, 0.0)))
    sigma_y = float(np.sqrt(max(sigma_yy, 0.0)))

    # Eigenvalues of 2x2 covariance matrix Sigma
    # Trace T = sigma_xx + sigma_yy, Det D = 1 / det_h
    trace_cov = sigma_xx + sigma_yy
    det_cov = 1.0 / det_h
    discriminant = max(0.0, trace_cov**2 - 4.0 * det_cov)
    sqrt_disc = float(np.sqrt(discriminant))

    lambda_1 = float(0.5 * (trace_cov + sqrt_disc))
    lambda_2 = float(0.5 * (trace_cov - sqrt_disc))

    # Weight proportional to surface curvature
    weight = float(np.sqrt(det_h))

    return SubpixelSurfaceFit(
        dx=float(dx),
        dy=float(dy),
        peak_val=float(peak_val),
        sigma_x=sigma_x,
        sigma_y=sigma_y,
        cov_xy=float(cov_xy),
        eigenvalues=(lambda_1, lambda_2),
        weight=weight,
    )


def fit_quadratic_peaks_batch(patches_3x3: np.ndarray) -> List[Optional[SubpixelSurfaceFit]]:
    """
    Vectorized batch quadratic surface fitting for an array of N 3x3 patches.
    Shape: [N, 3, 3] -> List of N Optional[SubpixelSurfaceFit].
    Runs in vectorized O(1) per patch.
    """
    patches = np.asarray(patches_3x3, dtype=np.float64)
    if patches.ndim != 3 or patches.shape[1:] != (3, 3):
        raise ValueError(f"Expected array of shape (N, 3, 3), got {patches.shape}")

    n = patches.shape[0]
    if n == 0:
        return []

    z00 = patches[:, 1, 1]
    z_xp = patches[:, 1, 2]
    z_xm = patches[:, 1, 0]
    z_yp = patches[:, 2, 1]
    z_ym = patches[:, 0, 1]
    z_pp = patches[:, 2, 2]
    z_pm = patches[:, 0, 2]
    z_mp = patches[:, 2, 0]
    z_mm = patches[:, 0, 0]

    a = (z_xp - 2.0 * z00 + z_xm) / 2.0
    b = (z_yp - 2.0 * z00 + z_ym) / 2.0
    c = (z_pp - z_pm - z_mp + z_mm) / 4.0
    d = (z_xp - z_xm) / 2.0
    e = (z_yp - z_ym) / 2.0
    f = z00

    det_h = 4.0 * a * b - c**2
    valid = (det_h > 1e-7) & (a < 0.0) & (b < 0.0)

    safe_det = np.where(valid, det_h, 1.0)
    dx = (-2.0 * b * d + c * e) / safe_det
    dy = (-2.0 * a * e + c * d) / safe_det

    valid = valid & (np.abs(dx) <= 1.0) & (np.abs(dy) <= 1.0)

    results: List[Optional[SubpixelSurfaceFit]] = []
    for i in range(n):
        if not valid[i]:
            results.append(None)
            continue

        dxi = float(dx[i])
        dyi = float(dy[i])
        ai = float(a[i])
        bi = float(b[i])
        ci = float(c[i])
        di = float(d[i])
        ei = float(e[i])
        fi = float(f[i])
        deth_i = float(det_h[i])

        peak = ai * dxi**2 + bi * dyi**2 + ci * dxi * dyi + di * dxi + ei * dyi + fi
        s_xx = (-2.0 * bi) / deth_i
        s_yy = (-2.0 * ai) / deth_i
        cov_xy = ci / deth_i

        sx = float(np.sqrt(max(s_xx, 0.0)))
        sy = float(np.sqrt(max(s_yy, 0.0)))

        t = s_xx + s_yy
        disc = max(0.0, t**2 - 4.0 / deth_i)
        sq_disc = float(np.sqrt(disc))
        l1 = float(0.5 * (t + sq_disc))
        l2 = float(0.5 * (t - sq_disc))
        w = float(np.sqrt(deth_i))

        results.append(
            SubpixelSurfaceFit(
                dx=dxi,
                dy=dyi,
                peak_val=float(peak),
                sigma_x=sx,
                sigma_y=sy,
                cov_xy=float(cov_xy),
                eigenvalues=(l1, l2),
                weight=w,
            )
        )

    return results
