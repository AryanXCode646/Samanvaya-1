"""
src/core/exceptions.py

Domain-specific exceptions for Samanvaya to gracefully handle
algorithm failures, security violations, and data integrity errors.
"""

class SamanvayaError(Exception):
    """Base exception for all Samanvaya domain errors."""
    pass


class SecurityViolationError(SamanvayaError):
    """Raised when a security validation fails (e.g., path traversal, pixel bomb)."""
    pass


class RasterIngestionError(SamanvayaError):
    """Raised when a raster file cannot be parsed or loaded correctly."""
    pass


class RegistrationConvergenceError(SamanvayaError):
    """Raised when the alignment algorithm fails to converge."""
    pass


class OutlierRejectionError(SamanvayaError):
    """Raised when RANSAC/MAGSAC fails to find a valid inlier set."""
    pass


class HardwareAccelerationError(SamanvayaError):
    """Raised when CUDA/GPU fallback fails critically."""
    pass
