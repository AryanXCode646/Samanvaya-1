"""
src/features/phase_congruency.py

Mathematically rigorous implementation of Phase Congruency using a 2D Log-Gabor filter bank.
Designed for illumination-invariant feature extraction on lunar surfaces.
"""
from __future__ import annotations

import numpy as np
import scipy.fft as fft
from typing import Tuple, Dict, Any

class PhaseCongruencyEngine:
    """
    Computes Phase Congruency of an image using 2D Log-Gabor filters.
    Provides robust, sun-angle and illumination invariant edge and corner maps.
    
    References:
        Peter Kovesi, "Image Features from Phase Congruency", 
        Videre: Journal of Computer Vision Research, 1999.
    """

    def __init__(
        self,
        num_scales: int = 4,
        num_orientations: int = 6,
        min_wavelength: float = 3.0,
        mult: float = 2.0,
        sigma_on_f: float = 0.55,
        theta_sigma: float = 1.2,
        k: float = 2.0,
        cut_off: float = 0.5,
        g: float = 10.0,
        noise_method: int = -1
    ) -> None:
        """
        Initialize the Phase Congruency Engine.

        Parameters
        ----------
        num_scales : int
            Number of wavelet scales.
        num_orientations : int
            Number of filter orientations.
        min_wavelength : float
            Wavelength of the smallest scale filter.
        mult : float
            Scaling factor between successive filters.
        sigma_on_f : float
            Ratio of the standard deviation of the Gaussian describing the log Gabor 
            filter's transfer function in the frequency domain to the filter center frequency.
        theta_sigma : float
            Angular spread of the filter.
        k : float
            Number of standard deviations of the noise energy beyond the mean at 
            which we set the noise threshold point.
        cut_off : float
            The fractional measure of frequency spread below which phase congruency 
            values get penalized.
        g : float
            Factor used to control the sharpness of the transition in the sigmoid 
            function used to weight phase congruency.
        noise_method : int
            Parameter specifying method used to determine noise statistics.
            -1 indicates noise estimate is computed from the smallest scale filter response.
        """
        self.num_scales = num_scales
        self.num_orientations = num_orientations
        self.min_wavelength = min_wavelength
        self.mult = mult
        self.sigma_on_f = sigma_on_f
        self.theta_sigma = theta_sigma
        self.k = k
        self.cut_off = cut_off
        self.g = g
        self.noise_method = noise_method

    def compute(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute the Phase Congruency of a 2D grayscale image.

        Parameters
        ----------
        image : np.ndarray
            2D input image array.

        Returns
        -------
        pc : np.ndarray
            Maximum phase congruency across all orientations (edge map).
        or_map : np.ndarray
            Orientation map (angles in radians).
        ft : np.ndarray
            Feature type map (corners vs edges).
        T : np.ndarray
            Calculated noise threshold per orientation.
        """
        if image.ndim != 2:
            raise ValueError("Input image must be a 2D array.")
            
        rows, cols = image.shape
        image_fft = fft.fft2(image)
        
        # Grid setup for frequency domain
        y, x = np.mgrid[-rows//2:rows//2, -cols//2:cols//2]
        y = fft.ifftshift(y) / rows
        x = fft.ifftshift(x) / cols
        
        radius = np.sqrt(x**2 + y**2)
        radius[0, 0] = 1.0  # Avoid division by zero at origin
        theta = np.arctan2(-y, x)
        
        # Angular filters
        sintheta = np.sin(theta)
        costheta = np.cos(theta)
        
        # Precompute angular components
        angular_filters = []
        for o in range(self.num_orientations):
            angl = o * np.pi / self.num_orientations
            ds = sintheta * np.cos(angl) - costheta * np.sin(angl)
            dc = costheta * np.cos(angl) + sintheta * np.sin(angl)
            dtheta = np.abs(np.arctan2(ds, dc))
            angular_filters.append(np.exp((-dtheta**2) / (2 * self.theta_sigma**2)))
            
        # Precompute radial (scale) filters
        radial_filters = []
        for s in range(self.num_scales):
            wavelength = self.min_wavelength * (self.mult ** s)
            fo = 1.0 / wavelength
            r_filter = np.exp((-(np.log(radius / fo))**2) / (2 * np.log(self.sigma_on_f)**2))
            r_filter[0, 0] = 0.0
            radial_filters.append(r_filter)
            
        # Core computation arrays
        pc_orientations = np.zeros((self.num_orientations, rows, cols), dtype=np.float64)
        sum_E = np.zeros((rows, cols), dtype=np.float64)
        sum_O = np.zeros((rows, cols), dtype=np.float64)
        sum_An_An = np.zeros((rows, cols), dtype=np.float64)
        noise_thresholds = np.zeros(self.num_orientations, dtype=np.float64)
        
        energy_V = np.zeros((rows, cols), dtype=np.float64)
        energy_V_x = np.zeros((rows, cols), dtype=np.float64)
        energy_V_y = np.zeros((rows, cols), dtype=np.float64)

        for o in range(self.num_orientations):
            sum_An_o = np.zeros((rows, cols), dtype=np.float64)
            sum_E_o = np.zeros((rows, cols), dtype=np.float64)
            sum_O_o = np.zeros((rows, cols), dtype=np.float64)
            EO_responses = []

            for s in range(self.num_scales):
                filter_2d = radial_filters[s] * angular_filters[o]
                # Apply filter in frequency domain, transform back to spatial domain
                filtered_image_fft = image_fft * filter_2d
                EO = fft.ifft2(filtered_image_fft)
                EO_responses.append(EO)
                
                An = np.abs(EO)
                sum_An_o += An
                sum_E_o += np.real(EO)
                sum_O_o += np.imag(EO)
                
                # Smallest scale is used to estimate noise
                if s == 0:
                    tau = np.median(An) / np.sqrt(np.log(4))
                    noise_T = tau * np.sqrt(np.pi / 2)
                    noise_thresholds[o] = noise_T
            
            # Energy calculation for the current orientation
            Energy_o = np.sqrt(sum_E_o**2 + sum_O_o**2)
            
            # Noise thresholding
            T = noise_thresholds[o]
            noise_thresh = T + self.k * np.sqrt(np.clip((4 - np.pi) * (tau**2) / 2, 0, None))
            
            # Calculate phase congruency for this orientation
            # Subtract noise and apply sigmoid weighting (Frequency spread penalization)
            width = sum_An_o / (np.max(An) + 1e-6)  # Frequency spread approximation
            weight = 1.0 / (1.0 + np.exp(self.g * (self.cut_off - width)))
            
            pc_o = weight * np.maximum(Energy_o - noise_thresh, 0) / (sum_An_o + 1e-4)
            pc_orientations[o] = pc_o
            
            # Accumulate for features type (Corners vs Edges)
            angl = o * np.pi / self.num_orientations
            energy_V_x += pc_o * np.cos(2 * angl)
            energy_V_y += pc_o * np.sin(2 * angl)
            energy_V += pc_o

        # Calculate maximum PC across all orientations
        pc = np.max(pc_orientations, axis=0)
        
        # Calculate orientation map
        max_or_indices = np.argmax(pc_orientations, axis=0)
        or_map = max_or_indices * np.pi / self.num_orientations
        
        # Feature type (Cornerness vs Edge)
        # Ratio of min/max moments
        M_min = (energy_V - np.sqrt(energy_V_x**2 + energy_V_y**2)) / 2
        M_max = (energy_V + np.sqrt(energy_V_x**2 + energy_V_y**2)) / 2
        ft = M_min / (M_max + 1e-4)  # 1.0 = highly corner-like, 0.0 = highly edge-like

        return np.clip(pc, 0, 1), or_map, ft, noise_thresholds
