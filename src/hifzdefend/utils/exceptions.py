"""
Custom exceptions for HifzDefend.
"""


class HifzDefendError(Exception):
    """Base exception for all HifzDefend errors."""

    pass


class ConfigurationError(HifzDefendError):
    """Raised when configuration is invalid or cannot be loaded."""

    pass


class ScannerError(HifzDefendError):
    """Raised when scanner encounters an error."""

    pass


class ClamAVConnectionError(ScannerError):
    """Raised when cannot connect to ClamAV daemon."""

    pass


class ClamAVTimeoutError(ScannerError):
    """Raised when ClamAV operation times out."""

    pass


class QuarantineError(HifzDefendError):
    """Raised when quarantine operation fails."""

    pass


class ValidationError(HifzDefendError):
    """Raised when validation fails."""

    pass


class FileAccessError(HifzDefendError):
    """Raised when file access fails (permissions, not found, etc.)."""

    pass


class PathTraversalError(ValidationError):
    """Raised when path traversal attempt is detected."""

    pass
