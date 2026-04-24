from __future__ import annotations


class DefendError(Exception):
    """Base exception for expected operational failures."""


class ConfigValidationError(DefendError):
    """Raised when configuration is invalid or unreadable."""


class RuleValidationError(DefendError):
    """Raised when rules bundle schema or integrity checks fail."""


class ScanTargetError(DefendError):
    """Raised when scan target cannot be resolved safely."""


class QuarantineError(DefendError):
    """Raised when quarantine lifecycle operations fail."""
