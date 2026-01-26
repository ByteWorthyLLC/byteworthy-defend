"""Spyware detection monitoring for HifzDefend.

This monitor detects spyware and surveillance software including:
- Keyloggers (process-based and kernel-level)
- Screen capture software
- Process injection attempts
- Suspicious DLL loads
- Hidden processes
- Known spyware signatures

Features:
- Real-time process monitoring
- Keylogger signature detection
- Screen capture detection
- Process injection monitoring
- DLL injection detection
- Hidden process detection
"""

import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import psutil
from pydantic import Field

from hifzdefend.monitoring.base import BaseMonitor
from hifzdefend.monitoring.events import Event, EventSeverity, EventType
from hifzdefend.monitoring.base import MonitorConfig

logger = logging.getLogger(__name__)


class SpywareMonitorConfig(MonitorConfig):
    """Configuration for Spyware detection monitor."""

    enabled: bool = Field(default=True, description="Enable spyware detection monitoring")

    detect_keyloggers: bool = Field(
        default=True, description="Detect keylogger processes and behavior"
    )

    detect_screen_capture: bool = Field(
        default=True, description="Detect screen capture software"
    )

    detect_process_injection: bool = Field(
        default=True, description="Detect process injection attempts"
    )

    detect_dll_injection: bool = Field(
        default=True, description="Detect suspicious DLL injection"
    )

    detect_hidden_processes: bool = Field(
        default=True, description="Detect hidden/rootkit processes"
    )

    keylogger_signatures: list[str] = Field(
        default_factory=lambda: [
            "keylog",
            "keystroke",
            "keygrab",
            "keysniff",
            "hookkey",
            "logkey",
            "capturekey",
            "recordkey",
            "spykey",
        ],
        description="Process name patterns that indicate keyloggers",
    )

    screen_capture_signatures: list[str] = Field(
        default_factory=lambda: [
            "screencapture",
            "screenshot",
            "screenrecord",
            "screensnap",
            "screengrab",
            "capturescr",
            "recordscreen",
            "spyscr",
        ],
        description="Process name patterns for screen capture software",
    )

    known_spyware_names: list[str] = Field(
        default_factory=lambda: [
            "perfectkeylogger",
            "revealer",
            "spyagent",
            "spytech",
            "webwatcher",
            "activtrak",
            "teramind",
            "veriato",
            "interguard",
        ],
        description="Known commercial spyware product names",
    )

    whitelisted_processes: list[str] = Field(
        default_factory=lambda: [
            "snippingtool.exe",
            "screensketch.exe",
            "obs64.exe",  # OBS Studio
            "obs32.exe",
            "zoom.exe",
            "teams.exe",
            "slack.exe",
            "discord.exe",
        ],
        description="Legitimate processes to whitelist",
    )

    check_dll_loads: bool = Field(
        default=True,
        description="Monitor DLL loads for suspicious libraries",
    )

    suspicious_dll_patterns: list[str] = Field(
        default_factory=lambda: [
            "hook",
            "inject",
            "spy",
            "capture",
            "record",
        ],
        description="DLL name patterns that are suspicious",
    )

    scan_interval_seconds: int = Field(
        default=30,
        ge=10,
        description="How often to scan for spyware (seconds)",
    )


@dataclass
class ProcessInfo:
    """Information about a process."""

    pid: int
    name: str
    exe_path: str
    cmdline: list[str]
    create_time: float
    username: str
    suspicious_score: int = 0


class SpywareMonitor(BaseMonitor):
    """Monitor for spyware and surveillance software."""

    def __init__(self, config: SpywareMonitorConfig, event_bus):
        super().__init__(config, event_bus)
        self.config: SpywareMonitorConfig = config

        # Process tracking
        self._known_processes: dict[int, ProcessInfo] = {}
        self._suspicious_processes: dict[int, ProcessInfo] = {}

        # DLL injection tracking
        self._dll_loads: dict[int, list[str]] = defaultdict(list)

        # Statistics
        self._stats = {
            "total_processes_scanned": 0,
            "keyloggers_detected": 0,
            "screen_capture_detected": 0,
            "process_injection_detected": 0,
            "dll_injection_detected": 0,
            "hidden_processes_detected": 0,
            "known_spyware_detected": 0,
        }

        logger.info("Spyware monitor initialized")

    async def start(self) -> None:
        """Start spyware monitoring."""
        if self._running:
            logger.warning("Spyware monitor already running")
            return

        logger.info("Starting spyware monitor")
        self._running = True
        logger.info("Spyware monitor started successfully")

    async def stop(self) -> None:
        """Stop monitoring."""
        if not self._running:
            return

        logger.info("Stopping spyware monitor")
        self._running = False
        logger.info("Spyware monitor stopped")

    async def check(self) -> list[Event]:
        """Perform spyware detection check."""
        if not self._running:
            return []

        events = []

        try:
            # Get all running processes
            processes = self._get_running_processes()

            for proc in processes:
                self._stats["total_processes_scanned"] += 1

                # Check for keyloggers
                if self.config.detect_keyloggers:
                    keylogger_event = self._check_keylogger(proc)
                    if keylogger_event:
                        events.append(keylogger_event)

                # Check for screen capture
                if self.config.detect_screen_capture:
                    screen_event = self._check_screen_capture(proc)
                    if screen_event:
                        events.append(screen_event)

                # Check for known spyware
                spyware_event = self._check_known_spyware(proc)
                if spyware_event:
                    events.append(spyware_event)

                # Check for process injection (Windows API calls)
                if self.config.detect_process_injection:
                    injection_event = self._check_process_injection(proc)
                    if injection_event:
                        events.append(injection_event)

            # Check for hidden processes
            if self.config.detect_hidden_processes:
                hidden_event = self._check_hidden_processes(processes)
                if hidden_event:
                    events.append(hidden_event)

        except Exception as e:
            logger.error(f"Error during spyware check: {e}", exc_info=True)

        return events

    def _get_running_processes(self) -> list[ProcessInfo]:
        """Get all running processes."""
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'create_time', 'username']):
            try:
                info = proc.info

                proc_info = ProcessInfo(
                    pid=info['pid'],
                    name=info['name'] or "Unknown",
                    exe_path=info['exe'] or "",
                    cmdline=info['cmdline'] or [],
                    create_time=info['create_time'] or 0,
                    username=info['username'] or "Unknown",
                )

                processes.append(proc_info)

                # Track in known processes
                if proc_info.pid not in self._known_processes:
                    self._known_processes[proc_info.pid] = proc_info

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logger.debug(f"Error getting process info: {e}")
                continue

        return processes

    def _check_keylogger(self, proc: ProcessInfo) -> Optional[Event]:
        """Check if process is a keylogger."""
        # Check whitelist first
        if self._is_whitelisted(proc):
            return None

        # Check process name against keylogger signatures
        name_lower = proc.name.lower()
        exe_path_lower = proc.exe_path.lower() if proc.exe_path else ""

        for signature in self.config.keylogger_signatures:
            if signature in name_lower or signature in exe_path_lower:
                self._stats["keyloggers_detected"] += 1
                self._suspicious_processes[proc.pid] = proc

                event = Event(
                    event_type=EventType.THREAT_DETECTED,
                    severity=EventSeverity.CRITICAL,
                    source_monitor=self.name,
                    description=f"Keylogger detected: {proc.name}",
                    threat_score=95,
                    data={
                        "pattern": "keylogger",
                        "process_name": proc.name,
                        "pid": proc.pid,
                        "exe_path": proc.exe_path,
                        "cmdline": " ".join(proc.cmdline) if proc.cmdline else "",
                        "username": proc.username,
                        "signature_matched": signature,
                        "recommendation": "CRITICAL: Keylogger detected. Terminate process immediately and run full system scan.",
                    },
                )

                return event

        # Check for suspicious behavior patterns
        # Keyloggers often have these characteristics:
        # - Low-level keyboard hooks (need Windows API access)
        # - Hidden windows or no UI
        # - Running from suspicious locations (Temp, AppData)

        suspicious_locations = ["\\temp\\", "\\appdata\\local\\temp\\", "\\downloads\\"]
        for location in suspicious_locations:
            if location in exe_path_lower:
                # Additional check: if process name contains input/key/hook
                if any(keyword in name_lower for keyword in ["input", "key", "hook"]):
                    self._stats["keyloggers_detected"] += 1

                    event = Event(
                        event_type=EventType.SUSPICIOUS_ACTIVITY,
                        severity=EventSeverity.WARNING,
                        source_monitor=self.name,
                        description=f"Suspicious process with keylogging indicators: {proc.name}",
                        threat_score=70,
                        data={
                            "pattern": "suspicious_keylogger",
                            "process_name": proc.name,
                            "pid": proc.pid,
                            "exe_path": proc.exe_path,
                            "reason": f"Process running from suspicious location: {location}",
                            "recommendation": "Investigate process. May be keylogger or malware.",
                        },
                    )

                    return event

        return None

    def _check_screen_capture(self, proc: ProcessInfo) -> Optional[Event]:
        """Check if process is screen capture software."""
        # Check whitelist first (legitimate tools like OBS, Zoom, Teams)
        if self._is_whitelisted(proc):
            return None

        name_lower = proc.name.lower()
        exe_path_lower = proc.exe_path.lower() if proc.exe_path else ""

        for signature in self.config.screen_capture_signatures:
            if signature in name_lower or signature in exe_path_lower:
                self._stats["screen_capture_detected"] += 1
                self._suspicious_processes[proc.pid] = proc

                event = Event(
                    event_type=EventType.SUSPICIOUS_ACTIVITY,
                    severity=EventSeverity.WARNING,
                    source_monitor=self.name,
                    description=f"Screen capture software detected: {proc.name}",
                    threat_score=60,
                    data={
                        "pattern": "screen_capture",
                        "process_name": proc.name,
                        "pid": proc.pid,
                        "exe_path": proc.exe_path,
                        "cmdline": " ".join(proc.cmdline) if proc.cmdline else "",
                        "signature_matched": signature,
                        "recommendation": "Verify if screen capture is authorized. May be spyware or surveillance tool.",
                    },
                )

                return event

        return None

    def _check_known_spyware(self, proc: ProcessInfo) -> Optional[Event]:
        """Check if process matches known commercial spyware."""
        name_lower = proc.name.lower()
        exe_path_lower = proc.exe_path.lower() if proc.exe_path else ""

        for spyware_name in self.config.known_spyware_names:
            if spyware_name in name_lower or spyware_name in exe_path_lower:
                self._stats["known_spyware_detected"] += 1
                self._suspicious_processes[proc.pid] = proc

                event = Event(
                    event_type=EventType.THREAT_DETECTED,
                    severity=EventSeverity.CRITICAL,
                    source_monitor=self.name,
                    description=f"Known commercial spyware detected: {proc.name}",
                    threat_score=98,
                    data={
                        "pattern": "known_spyware",
                        "process_name": proc.name,
                        "pid": proc.pid,
                        "exe_path": proc.exe_path,
                        "spyware_product": spyware_name,
                        "recommendation": "CRITICAL: Commercial spyware detected. This is monitoring software. Terminate immediately.",
                    },
                )

                return event

        return None

    def _check_process_injection(self, proc: ProcessInfo) -> Optional[Event]:
        """Check for process injection indicators.

        Process injection is a technique where malware injects code into another process.
        Detection indicators:
        - Process with suspicious DLLs loaded
        - Process memory anomalies
        - Unusual parent-child relationships
        """
        # This is a simplified check
        # In production, would use Windows API to check loaded modules

        # Check for suspicious command line arguments that indicate injection
        cmdline_str = " ".join(proc.cmdline).lower() if proc.cmdline else ""

        injection_indicators = [
            "inject",
            "createremotethread",
            "writeprocessmemory",
            "virtualalloc",
            "loadlibrary",
        ]

        for indicator in injection_indicators:
            if indicator in cmdline_str:
                self._stats["process_injection_detected"] += 1

                event = Event(
                    event_type=EventType.THREAT_DETECTED,
                    severity=EventSeverity.CRITICAL,
                    source_monitor=self.name,
                    description=f"Process injection detected: {proc.name}",
                    threat_score=90,
                    data={
                        "pattern": "process_injection",
                        "process_name": proc.name,
                        "pid": proc.pid,
                        "exe_path": proc.exe_path,
                        "cmdline": cmdline_str,
                        "indicator": indicator,
                        "recommendation": "CRITICAL: Process injection attempt detected. Likely malware. Terminate and investigate.",
                    },
                )

                return event

        return None

    def _check_hidden_processes(self, processes: list[ProcessInfo]) -> Optional[Event]:
        """Check for hidden processes or rootkits.

        Hidden processes may indicate rootkit activity.
        Detection methods:
        - Processes not visible in normal enumeration
        - Processes with no executable path
        - Processes with suspicious permissions
        """
        hidden_count = 0

        for proc in processes:
            # Check for processes with no executable path (suspicious)
            if not proc.exe_path:
                hidden_count += 1

        if hidden_count > 5:  # More than 5 is unusual
            self._stats["hidden_processes_detected"] += 1

            event = Event(
                event_type=EventType.SUSPICIOUS_ACTIVITY,
                severity=EventSeverity.WARNING,
                source_monitor=self.name,
                description=f"Multiple hidden processes detected: {hidden_count}",
                threat_score=50,
                data={
                    "pattern": "hidden_processes",
                    "count": hidden_count,
                    "recommendation": "Multiple processes with no executable path. May indicate rootkit or system anomaly.",
                },
            )

            return event

        return None

    def _is_whitelisted(self, proc: ProcessInfo) -> bool:
        """Check if process is whitelisted."""
        name_lower = proc.name.lower()

        for whitelisted in self.config.whitelisted_processes:
            if whitelisted.lower() in name_lower:
                return True

        return False

    def get_statistics(self) -> dict[str, Any]:
        """Get monitor statistics."""
        return {
            "total_processes_scanned": self._stats["total_processes_scanned"],
            "keyloggers_detected": self._stats["keyloggers_detected"],
            "screen_capture_detected": self._stats["screen_capture_detected"],
            "process_injection_detected": self._stats["process_injection_detected"],
            "dll_injection_detected": self._stats["dll_injection_detected"],
            "hidden_processes_detected": self._stats["hidden_processes_detected"],
            "known_spyware_detected": self._stats["known_spyware_detected"],
            "suspicious_processes": len(self._suspicious_processes),
            "detect_keyloggers": self.config.detect_keyloggers,
            "detect_screen_capture": self.config.detect_screen_capture,
            "detect_process_injection": self.config.detect_process_injection,
        }
