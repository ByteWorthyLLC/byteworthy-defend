"""
Application state management for HifzDefend service.

This module manages the runtime state of the HifzDefend service, including
protection status, monitor states, scan history, and threat information.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from threading import Lock


class ProtectionStatus(str, Enum):
    """Protection status enumeration."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    PAUSED = "paused"
    ERROR = "error"


class MonitorStatus(str, Enum):
    """Monitor status enumeration."""

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    DISABLED = "disabled"


class ThreatSeverity(str, Enum):
    """Threat severity levels."""

    BENIGN = "benign"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    CRITICAL = "critical"


@dataclass
class MonitorState:
    """State information for a single monitor."""

    id: str
    name: str
    status: MonitorStatus
    enabled: bool
    last_event: Optional[datetime] = None
    event_count: int = 0
    error_message: Optional[str] = None


@dataclass
class ScanResult:
    """Scan result information."""

    id: str
    path: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"
    threats_found: int = 0
    files_scanned: int = 0
    threats: List[Dict] = field(default_factory=list)


@dataclass
class ThreatInfo:
    """Threat information."""

    id: str
    name: str
    severity: ThreatSeverity
    detected_at: datetime
    path: str
    quarantined: bool = False
    description: Optional[str] = None


@dataclass
class SystemStatus:
    """Overall system status."""

    protection_status: ProtectionStatus
    monitors_active: int
    monitors_total: int
    threats_today: int
    threats_week: int
    threats_total: int
    last_scan: Optional[datetime] = None
    last_update: Optional[datetime] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0


class ServiceState:
    """
    Centralized application state manager.

    This class maintains the runtime state of the HifzDefend service and provides
    thread-safe access to state information for all components.
    """

    def __init__(self) -> None:
        """Initialize service state."""
        self._lock = Lock()
        self._protection_status = ProtectionStatus.DISABLED
        self._monitors: Dict[str, MonitorState] = {}
        self._active_scans: Dict[str, ScanResult] = {}
        self._recent_threats: List[ThreatInfo] = []
        self._scan_history: List[ScanResult] = []
        self._started_at: Optional[datetime] = None

    @property
    def protection_status(self) -> ProtectionStatus:
        """Get current protection status."""
        with self._lock:
            return self._protection_status

    @protection_status.setter
    def protection_status(self, status: ProtectionStatus) -> None:
        """Set protection status."""
        with self._lock:
            self._protection_status = status

    def start_service(self) -> None:
        """Mark service as started."""
        with self._lock:
            self._started_at = datetime.now()
            self._protection_status = ProtectionStatus.ENABLED

    def stop_service(self) -> None:
        """Mark service as stopped."""
        with self._lock:
            self._protection_status = ProtectionStatus.DISABLED

    def register_monitor(self, monitor_id: str, name: str, enabled: bool = True) -> None:
        """Register a monitor."""
        with self._lock:
            self._monitors[monitor_id] = MonitorState(
                id=monitor_id,
                name=name,
                status=MonitorStatus.STOPPED,
                enabled=enabled,
            )

    def update_monitor_status(
        self, monitor_id: str, status: MonitorStatus, error: Optional[str] = None
    ) -> None:
        """Update monitor status."""
        with self._lock:
            if monitor_id in self._monitors:
                self._monitors[monitor_id].status = status
                self._monitors[monitor_id].error_message = error
                if status == MonitorStatus.RUNNING:
                    self._monitors[monitor_id].last_event = datetime.now()

    def increment_monitor_events(self, monitor_id: str) -> None:
        """Increment event count for a monitor."""
        with self._lock:
            if monitor_id in self._monitors:
                self._monitors[monitor_id].event_count += 1
                self._monitors[monitor_id].last_event = datetime.now()

    def get_monitor_state(self, monitor_id: str) -> Optional[MonitorState]:
        """Get state of a specific monitor."""
        with self._lock:
            return self._monitors.get(monitor_id)

    def get_all_monitors(self) -> List[MonitorState]:
        """Get all monitor states."""
        with self._lock:
            return list(self._monitors.values())

    def add_threat(self, threat: ThreatInfo) -> None:
        """Add a detected threat."""
        with self._lock:
            self._recent_threats.insert(0, threat)
            # Keep only last 100 threats in memory
            if len(self._recent_threats) > 100:
                self._recent_threats = self._recent_threats[:100]

    def get_recent_threats(self, limit: int = 10) -> List[ThreatInfo]:
        """Get recent threats."""
        with self._lock:
            return self._recent_threats[:limit]

    def start_scan(self, scan_id: str, path: str) -> None:
        """Register a new scan."""
        with self._lock:
            self._active_scans[scan_id] = ScanResult(
                id=scan_id,
                path=path,
                started_at=datetime.now(),
            )

    def update_scan_progress(
        self, scan_id: str, files_scanned: int, threats_found: int
    ) -> None:
        """Update scan progress."""
        with self._lock:
            if scan_id in self._active_scans:
                self._active_scans[scan_id].files_scanned = files_scanned
                self._active_scans[scan_id].threats_found = threats_found

    def complete_scan(self, scan_id: str, threats: List[Dict]) -> None:
        """Mark scan as completed."""
        with self._lock:
            if scan_id in self._active_scans:
                scan = self._active_scans[scan_id]
                scan.completed_at = datetime.now()
                scan.status = "completed"
                scan.threats = threats
                # Move to history
                self._scan_history.insert(0, scan)
                if len(self._scan_history) > 50:
                    self._scan_history = self._scan_history[:50]
                # Remove from active
                del self._active_scans[scan_id]

    def get_active_scans(self) -> List[ScanResult]:
        """Get all active scans."""
        with self._lock:
            return list(self._active_scans.values())

    def get_scan_history(self, limit: int = 20) -> List[ScanResult]:
        """Get scan history."""
        with self._lock:
            return self._scan_history[:limit]

    def get_system_status(self) -> SystemStatus:
        """Get overall system status."""
        with self._lock:
            monitors_active = sum(
                1 for m in self._monitors.values() if m.status == MonitorStatus.RUNNING
            )
            monitors_total = len(self._monitors)

            # Count threats by time period
            now = datetime.now()
            threats_today = sum(
                1
                for t in self._recent_threats
                if (now - t.detected_at).days == 0
            )
            threats_week = sum(
                1
                for t in self._recent_threats
                if (now - t.detected_at).days <= 7
            )

            last_scan = None
            if self._scan_history:
                last_scan = self._scan_history[0].completed_at

            return SystemStatus(
                protection_status=self._protection_status,
                monitors_active=monitors_active,
                monitors_total=monitors_total,
                threats_today=threats_today,
                threats_week=threats_week,
                threats_total=len(self._recent_threats),
                last_scan=last_scan,
            )
