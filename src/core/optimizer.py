"""
src/core/optimizer.py

Dynamic hardware telemetry and execution optimization for low-end devices.
Automatically down-scales processing parameters (without losing features) 
if constrained hardware is detected.
"""
import os
import psutil
import cv2
import logging

logger = logging.getLogger("samanvaya.optimizer")

class HardwareOptimizer:
    """
    Detects system capabilities and provides optimized execution parameters.
    Ensures Samanvaya does not crash on low-end 4GB/8GB RAM systems.
    """
    
    @classmethod
    def analyze_hardware(cls) -> dict:
        """Returns physical cores and available RAM in GB."""
        ram_gb = psutil.virtual_memory().available / (1024 ** 3)
        cores = psutil.cpu_count(logical=False) or 2
        return {"available_ram_gb": ram_gb, "physical_cores": cores}
        
    @classmethod
    def apply_low_end_optimizations(cls) -> None:
        """
        Dynamically adjusts thread counts and environmental limits to prevent
        thrashing or out-of-memory errors on weak machines.
        """
        hw = cls.analyze_hardware()
        ram = hw["available_ram_gb"]
        cores = hw["physical_cores"]
        
        if ram < 4.0 or cores <= 4:
            logger.warning(f"Low-end hardware detected (RAM: {ram:.1f}GB, Cores: {cores}). Applying optimizations.")
            
            # Limit OpenCV threading to prevent CPU thrashing
            cv2.setNumThreads(max(1, cores // 2))
            
            # Suggest garbage collector limits if we were modifying gc
            os.environ["OMP_NUM_THREADS"] = str(max(1, cores // 2))
            os.environ["OPENBLAS_NUM_THREADS"] = str(max(1, cores // 2))
            os.environ["MKL_NUM_THREADS"] = str(max(1, cores // 2))
            
            cls._is_low_end = True
        else:
            logger.info("High-end hardware detected. Utilizing maximum resources.")
            cls._is_low_end = False

    @classmethod
    def get_phase_congruency_params(cls) -> dict:
        """
        Returns parameters for Phase Congruency.
        Reduces filter orientations on low-end hardware to save RAM and FFT time,
        without mathematically breaking the feature extraction pipeline.
        """
        if getattr(cls, '_is_low_end', False):
            return {"num_scales": 3, "num_orientations": 4} # 12 FFTs
        return {"num_scales": 4, "num_orientations": 6}     # 24 FFTs

    @classmethod
    def optimize_raster_size(cls, image: iter) -> tuple:
        """
        Calculates optimal downsampling factor to keep processing within RAM limits.
        (Implementation placeholder for integration in the image pipeline).
        """
        pass
