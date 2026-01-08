"""
Custom exception classes for the GPS data collection service.
"""
from typing import Optional, Dict, Any


class GPSDataCollectionError(Exception):
    """Base exception for GPS data collection service."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class GPSProviderError(GPSDataCollectionError):
    """Raised when GPS provider API fails."""
    pass


class GPSProviderTimeout(GPSProviderError):
    """Raised when GPS provider request times out."""
    pass


class GPSProviderAuthenticationError(GPSProviderError):
    """Raised when GPS provider authentication fails."""
    pass


class DataNormalizationError(GPSDataCollectionError):
    """Raised when data normalization/transformation fails."""
    pass


class RepositoryError(GPSDataCollectionError):
    """Raised when database operations fail."""
    pass


class JobExecutionError(GPSDataCollectionError):
    """Raised when scheduled job execution fails."""
    pass


class ConfigurationError(GPSDataCollectionError):
    """Raised when configuration is invalid or missing."""
    pass


class VehicleNotFoundError(GPSDataCollectionError):
    """Raised when vehicle data is not found."""
    pass
