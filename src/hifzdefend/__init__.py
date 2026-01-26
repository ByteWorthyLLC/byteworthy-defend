"""
HifzDefend - Custom Windows Antivirus Solution Based on ClamAV

حفظ (Hifz) - Protection/Preservation

Preserving Your Digital Safety
"""

__version__ = "0.1.0"
__author__ = "HifzDefend Team"
__license__ = "MIT"

from .config.loader import get_config, load_config
from .core.scanner import ClamAVScanner, ScanResult
from .core.engine import ScanEngine
from .utils.exceptions import (
    HifzDefendError,
    ConfigurationError,
    ScannerError,
    ClamAVConnectionError,
    QuarantineError,
)

__all__ = [
    "__version__",
    "get_config",
    "load_config",
    "ClamAVScanner",
    "ScanResult",
    "ScanEngine",
    "HifzDefendError",
    "ConfigurationError",
    "ScannerError",
    "ClamAVConnectionError",
    "QuarantineError",
]
