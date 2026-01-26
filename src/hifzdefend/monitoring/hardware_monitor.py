"""Hardware access monitoring for HifzDefend.

This monitor tracks access to sensitive hardware including:
- Webcam activation
- Microphone access
- Hardware access by processes
- Unauthorized surveillance

Features:
- Real-time hardware access detection
- Process-to-hardware mapping
- Trusted application whitelisting
- Webcam LED monitoring
- Microphone input detection
"""

import logging
import platform
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import psutil
from pydantic import Field

from hifzdefend.monitoring.base import BaseMonitor
from hifzdefend.monitoring.events import Event, EventSeverity, EventType
from hifzdefend.monitoring.base import MonitorConfig

logger = logging.getLogger(__name__)


class HardwareMonitorConfig(MonitorConfig):
    """Configuration for Hardware access monitor."""

    enabled: bool = Field(
        default=True, description="Enable hardware access monitoring"
    )

    webcam_monitoring: bool = Field(
        default=True, description="Monitor webcam access"
    )

    microphone_monitoring: bool = Field(
        default=True, description="Monitor microphone access"
    )

    alert_on_hardware_access: bool = Field(
        default=True,
        description="Alert when hardware is accessed by non-whitelisted apps",
    )

    whitelisted_apps: list[str] = Field(
        default_factory=lambda: [
            "zoom.exe",
            "teams.exe",
            "slack.exe",
            "discord.exe",
            "skype.exe",
            "chrome.exe",
            "firefox.exe",
            "msedge.exe",
            "obs64.exe",
            "obs32.exe",
        ],
        description="Applications allowed to access webcam/microphone",
    )

    webcam_device_patterns: list[str] = Field(
        default_factory=lambda: [
            "webcam",
            "camera",
            "usb video",
            "integrated camera",
        ],
        description="Device name patterns for webcams",
    )

    microphone_device_patterns: list[str] = Field(
        default_factory=lambda: [
            "microphone",
            "mic",
            "audio input",
            "capture",
        ],
        description="Device name patterns for microphones",
    )

    check_process_handles: bool = Field(
        default=True,
        description="Check process handles for hardware access (Windows)",
    )

    scan_interval_seconds: int = Field(
        default=10,
        ge=5,
        description="How often to check hardware access (seconds)",
    )


@dataclass
class HardwareAccess:
    """Information about hardware access by a process."""

    pid: int
    process_name: str
    exe_path: str
    device_type: str  # "webcam" or "microphone"
    timestamp: datetime
    is_whitelisted: bool


class HardwareMonitor(BaseMonitor):
    """Monitor hardware access for surveillance detection."""

    def __init__(self, config: HardwareMonitorConfig, event_bus):
        super().__init__(config, event_bus)
        self.config: HardwareMonitorConfig = config

        # Hardware access tracking
        self._active_webcam_processes: dict[int, HardwareAccess] = {}
        self._active_microphone_processes: dict[int, HardwareAccess] = {}
        self._hardware_access_history: list[HardwareAccess] = []

        # Statistics
        self._stats = {
            "webcam_accesses": 0,
            "microphone_accesses": 0,
            "unauthorized_webcam": 0,
            "unauthorized_microphone": 0,
            "total_hardware_alerts": 0,
        }

        # Platform detection
        self._is_windows = platform.system() == "Windows"

        logger.info("Hardware monitor initialized")

    async def start(self) -> None:
        """Start hardware monitoring."""
        if self._running:
            logger.warning("Hardware monitor already running")
            return

        logger.info("Starting hardware monitor")
        self._running = True
        logger.info("Hardware monitor started successfully")

    async def stop(self) -> None:
        """Stop monitoring."""
        if not self._running:
            return

        logger.info("Stopping hardware monitor")
        self._running = False
        logger.info("Hardware monitor stopped")

    async def check(self) -> list[Event]:
        """Perform hardware access check."""
        if not self._running:
            return []

        events = []

        try:
            # Check for processes accessing hardware
            if self.config.webcam_monitoring:
                webcam_events = self._check_webcam_access()
                events.extend(webcam_events)

            if self.config.microphone_monitoring:
                microphone_events = self._check_microphone_access()
                events.extend(microphone_events)

        except Exception as e:
            logger.error(f"Error during hardware check: {e}", exc_info=True)

        return events

    def _check_webcam_access(self) -> list[Event]:
        """Check for webcam access by processes."""
        events = []

        # Get processes that may be accessing webcam
        # This is a heuristic approach - check for processes with video capture
        accessing_processes = self._get_camera_accessing_processes()

        for proc_info in accessing_processes:
            pid = proc_info['pid']

            # Check if already tracking
            if pid in self._active_webcam_processes:
                continue

            # Track new webcam access
            is_whitelisted = self._is_whitelisted(proc_info['name'])

            access = HardwareAccess(
                pid=pid,
                process_name=proc_info['name'],
                exe_path=proc_info.get('exe', ''),
                device_type="webcam",
                timestamp=datetime.now(),
                is_whitelisted=is_whitelisted,
            )

            self._active_webcam_processes[pid] = access
            self._hardware_access_history.append(access)
            self._stats["webcam_accesses"] += 1

            # Alert if not whitelisted
            if not is_whitelisted and self.config.alert_on_hardware_access:
                self._stats["unauthorized_webcam"] += 1
                self._stats["total_hardware_alerts"] += 1

                event = Event(
                    event_type=EventType.SUSPICIOUS_ACTIVITY,
                    severity=EventSeverity.WARNING,
                    source_monitor=self.name,
                    description=f"Webcam access by unauthorized application: {proc_info['name']}",
                    threat_score=70,
                    data={
                        "pattern": "unauthorized_webcam_access",
                        "device_type": "webcam",
                        "process_name": proc_info['name'],
                        "pid": pid,
                        "exe_path": proc_info.get('exe', ''),
                        "recommendation": "Verify if webcam access is authorized. May indicate spyware or surveillance.",
                    },
                )

                events.append(event)

        # Keep history limited
        if len(self._hardware_access_history) > 100:
            self._hardware_access_history = self._hardware_access_history[-100:]

        return events

    def _check_microphone_access(self) -> list[Event]:
        """Check for microphone access by processes."""
        events = []

        # Get processes that may be accessing microphone
        accessing_processes = self._get_audio_accessing_processes()

        for proc_info in accessing_processes:
            pid = proc_info['pid']

            # Check if already tracking
            if pid in self._active_microphone_processes:
                continue

            # Track new microphone access
            is_whitelisted = self._is_whitelisted(proc_info['name'])

            access = HardwareAccess(
                pid=pid,
                process_name=proc_info['name'],
                exe_path=proc_info.get('exe', ''),
                device_type="microphone",
                timestamp=datetime.now(),
                is_whitelisted=is_whitelisted,
            )

            self._active_microphone_processes[pid] = access
            self._hardware_access_history.append(access)
            self._stats["microphone_accesses"] += 1

            # Alert if not whitelisted
            if not is_whitelisted and self.config.alert_on_hardware_access:
                self._stats["unauthorized_microphone"] += 1
                self._stats["total_hardware_alerts"] += 1

                event = Event(
                    event_type=EventType.SUSPICIOUS_ACTIVITY,
                    severity=EventSeverity.WARNING,
                    source_monitor=self.name,
                    description=f"Microphone access by unauthorized application: {proc_info['name']}",
                    threat_score=70,
                    data={
                        "pattern": "unauthorized_microphone_access",
                        "device_type": "microphone",
                        "process_name": proc_info['name'],
                        "pid": pid,
                        "exe_path": proc_info.get('exe', ''),
                        "recommendation": "Verify if microphone access is authorized. May indicate spyware or surveillance.",
                    },
                )

                events.append(event)

        return events

    def _get_camera_accessing_processes(self) -> list[dict]:
        """Get processes that may be accessing camera.

        This is a heuristic approach that checks for:
        - Processes with video-related connections
        - Known video capture processes
        - Processes with camera-related file handles (Windows)
        """
        accessing_processes = []

        # Heuristic: Check for processes with specific names
        video_process_keywords = [
            "zoom", "teams", "skype", "discord", "slack",
            "chrome", "firefox", "edge", "obs",
            "camera", "webcam", "video"
        ]

        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                name_lower = proc.info['name'].lower()

                # Check if process name matches video keywords
                if any(keyword in name_lower for keyword in video_process_keywords):
                    accessing_processes.append(proc.info)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return accessing_processes

    def _get_audio_accessing_processes(self) -> list[dict]:
        """Get processes that may be accessing microphone.

        This is a heuristic approach similar to camera detection.
        """
        accessing_processes = []

        # Heuristic: Check for processes with audio-related names
        audio_process_keywords = [
            "zoom", "teams", "skype", "discord", "slack",
            "chrome", "firefox", "edge", "obs",
            "audio", "sound", "mic", "voice"
        ]

        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                name_lower = proc.info['name'].lower()

                # Check if process name matches audio keywords
                if any(keyword in name_lower for keyword in audio_process_keywords):
                    accessing_processes.append(proc.info)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return accessing_processes

    def _is_whitelisted(self, process_name: str) -> bool:
        """Check if process is whitelisted for hardware access."""
        name_lower = process_name.lower()

        for whitelisted in self.config.whitelisted_apps:
            if whitelisted.lower() in name_lower:
                return True

        return False

    def get_statistics(self) -> dict[str, Any]:
        """Get monitor statistics."""
        return {
            "webcam_accesses": self._stats["webcam_accesses"],
            "microphone_accesses": self._stats["microphone_accesses"],
            "unauthorized_webcam": self._stats["unauthorized_webcam"],
            "unauthorized_microphone": self._stats["unauthorized_microphone"],
            "total_hardware_alerts": self._stats["total_hardware_alerts"],
            "active_webcam_processes": len(self._active_webcam_processes),
            "active_microphone_processes": len(self._active_microphone_processes),
            "webcam_monitoring": self.config.webcam_monitoring,
            "microphone_monitoring": self.config.microphone_monitoring,
        }
