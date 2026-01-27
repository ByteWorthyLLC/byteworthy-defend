"""
HifzDefend Service Layer

This module provides the service abstraction layer that decouples business logic
from the CLI and provides interfaces for the Windows service, system tray, and web API.
"""

from .engine import HifzDefendEngine
from .state import ServiceState, SystemStatus
from .events import ServiceEvent, EventEmitter

__all__ = [
    "HifzDefendEngine",
    "ServiceState",
    "SystemStatus",
    "ServiceEvent",
    "EventEmitter",
]
