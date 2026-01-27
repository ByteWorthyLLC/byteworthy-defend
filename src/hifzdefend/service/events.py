"""
Event system for HifzDefend service.

This module provides an event emission system that allows the service to notify
UI components (system tray, web dashboard) about state changes and important events.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types."""

    # Service events
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    SERVICE_ERROR = "service_error"

    # Monitor events
    MONITOR_STARTED = "monitor_started"
    MONITOR_STOPPED = "monitor_stopped"
    MONITOR_ERROR = "monitor_error"
    MONITOR_EVENT = "monitor_event"

    # Scan events
    SCAN_STARTED = "scan_started"
    SCAN_PROGRESS = "scan_progress"
    SCAN_COMPLETED = "scan_completed"
    SCAN_ERROR = "scan_error"

    # Threat events
    THREAT_DETECTED = "threat_detected"
    THREAT_QUARANTINED = "threat_quarantined"
    THREAT_REMOVED = "threat_removed"

    # Configuration events
    CONFIG_CHANGED = "config_changed"

    # Update events
    DEFINITIONS_UPDATED = "definitions_updated"
    UPDATE_AVAILABLE = "update_available"


@dataclass
class ServiceEvent:
    """
    Service event data structure.

    Events are emitted by the service and can be consumed by multiple subscribers
    (system tray, web dashboard via WebSocket, logging, etc.).
    """

    type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    priority: int = 0  # 0=low, 1=normal, 2=high, 3=critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "priority": self.priority,
        }


class EventEmitter:
    """
    Event emitter for the HifzDefend service.

    This class manages event subscriptions and dispatches events to all
    registered handlers. It's thread-safe and supports multiple subscribers.
    """

    def __init__(self) -> None:
        """Initialize event emitter."""
        self._lock = Lock()
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._global_handlers: List[Callable] = []
        self._event_history: List[ServiceEvent] = []
        self._max_history = 100

    def subscribe(
        self, event_type: Optional[EventType], handler: Callable[[ServiceEvent], None]
    ) -> None:
        """
        Subscribe to events.

        Args:
            event_type: Specific event type to subscribe to, or None for all events
            handler: Callback function that receives ServiceEvent objects
        """
        with self._lock:
            if event_type is None:
                # Global handler for all events
                self._global_handlers.append(handler)
                logger.debug(f"Registered global event handler: {handler.__name__}")
            else:
                # Specific event type handler
                if event_type not in self._handlers:
                    self._handlers[event_type] = []
                self._handlers[event_type].append(handler)
                logger.debug(
                    f"Registered handler for {event_type.value}: {handler.__name__}"
                )

    def unsubscribe(
        self, event_type: Optional[EventType], handler: Callable[[ServiceEvent], None]
    ) -> None:
        """
        Unsubscribe from events.

        Args:
            event_type: Event type to unsubscribe from, or None for global handler
            handler: Handler to remove
        """
        with self._lock:
            try:
                if event_type is None:
                    self._global_handlers.remove(handler)
                elif event_type in self._handlers:
                    self._handlers[event_type].remove(handler)
                logger.debug(f"Unregistered event handler: {handler.__name__}")
            except ValueError:
                logger.warning(f"Handler not found for unsubscribe: {handler.__name__}")

    def emit(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        priority: int = 0,
    ) -> None:
        """
        Emit an event to all subscribed handlers.

        Args:
            event_type: Type of event
            data: Event data
            priority: Event priority (0-3)
        """
        event = ServiceEvent(
            type=event_type,
            timestamp=datetime.now(),
            data=data,
            priority=priority,
        )

        # Store in history
        with self._lock:
            self._event_history.insert(0, event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[: self._max_history]

            # Get handlers to call (copy to avoid lock during callback)
            handlers = []
            if event_type in self._handlers:
                handlers.extend(self._handlers[event_type])
            handlers.extend(self._global_handlers)

        # Call handlers outside of lock to avoid deadlocks
        logger.debug(f"Emitting event: {event_type.value} to {len(handlers)} handlers")
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler {handler.__name__}: {e}", exc_info=True
                )

    def emit_service_started(self) -> None:
        """Emit service started event."""
        self.emit(
            EventType.SERVICE_STARTED,
            {"message": "HifzDefend service started"},
            priority=1,
        )

    def emit_service_stopped(self) -> None:
        """Emit service stopped event."""
        self.emit(
            EventType.SERVICE_STOPPED,
            {"message": "HifzDefend service stopped"},
            priority=1,
        )

    def emit_monitor_started(self, monitor_id: str, monitor_name: str) -> None:
        """Emit monitor started event."""
        self.emit(
            EventType.MONITOR_STARTED,
            {"monitor_id": monitor_id, "monitor_name": monitor_name},
            priority=0,
        )

    def emit_monitor_stopped(self, monitor_id: str, monitor_name: str) -> None:
        """Emit monitor stopped event."""
        self.emit(
            EventType.MONITOR_STOPPED,
            {"monitor_id": monitor_id, "monitor_name": monitor_name},
            priority=0,
        )

    def emit_threat_detected(
        self,
        threat_id: str,
        threat_name: str,
        path: str,
        severity: str,
    ) -> None:
        """Emit threat detected event."""
        self.emit(
            EventType.THREAT_DETECTED,
            {
                "threat_id": threat_id,
                "threat_name": threat_name,
                "path": path,
                "severity": severity,
            },
            priority=3 if severity == "critical" else 2,
        )

    def emit_scan_started(self, scan_id: str, path: str) -> None:
        """Emit scan started event."""
        self.emit(
            EventType.SCAN_STARTED,
            {"scan_id": scan_id, "path": path},
            priority=1,
        )

    def emit_scan_progress(
        self, scan_id: str, files_scanned: int, threats_found: int
    ) -> None:
        """Emit scan progress event."""
        self.emit(
            EventType.SCAN_PROGRESS,
            {
                "scan_id": scan_id,
                "files_scanned": files_scanned,
                "threats_found": threats_found,
            },
            priority=0,
        )

    def emit_scan_completed(
        self, scan_id: str, files_scanned: int, threats_found: int
    ) -> None:
        """Emit scan completed event."""
        self.emit(
            EventType.SCAN_COMPLETED,
            {
                "scan_id": scan_id,
                "files_scanned": files_scanned,
                "threats_found": threats_found,
            },
            priority=1,
        )

    def emit_config_changed(self, section: str, changes: Dict[str, Any]) -> None:
        """Emit configuration changed event."""
        self.emit(
            EventType.CONFIG_CHANGED,
            {"section": section, "changes": changes},
            priority=1,
        )

    def get_event_history(self, limit: int = 20) -> List[ServiceEvent]:
        """
        Get recent event history.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        with self._lock:
            return self._event_history[:limit]

    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._event_history.clear()
