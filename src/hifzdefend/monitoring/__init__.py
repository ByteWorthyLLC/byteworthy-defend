"""HifzDefend Monitoring System.

This module provides the event-driven monitoring architecture for HifzDefend.
All security monitors publish events to a central EventBus for threat detection
and response coordination.

Example:
    ```python
    from hifzdefend.monitoring import (
        MonitorManager,
        EventBus,
        BaseMonitor,
        Event,
        EventType,
        EventSeverity,
    )

    # Create event bus and manager
    event_bus = EventBus()
    manager = MonitorManager(event_bus)

    # Register monitors
    manager.register_monitor(MyMonitor(config, event_bus))

    # Start monitoring
    await manager.start_all()
    ```
"""

from .base import BaseMonitor, MonitorConfig, MonitorStatus
from .event_bus import EventBus, get_event_bus
from .events import (
    DockerSecurityEvent,
    Event,
    EventSeverity,
    EventType,
    FileEvent,
    HardwareEvent,
    MonitoringEvent,
    NetworkEvent,
    PackageSecurityEvent,
    PowerShellEvent,
    PrivacyEvent,
    ProcessEvent,
    RegistryEvent,
    ThreatDetectedEvent,
)
from .manager import MonitorManager

__all__ = [
    # Core classes
    "BaseMonitor",
    "MonitorConfig",
    "MonitorStatus",
    "MonitorManager",
    "EventBus",
    "get_event_bus",
    # Event classes
    "Event",
    "EventType",
    "EventSeverity",
    "ThreatDetectedEvent",
    "ProcessEvent",
    "FileEvent",
    "NetworkEvent",
    "RegistryEvent",
    "HardwareEvent",
    "PackageSecurityEvent",
    "DockerSecurityEvent",
    "PowerShellEvent",
    "PrivacyEvent",
    "MonitoringEvent",
]
