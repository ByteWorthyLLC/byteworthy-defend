"""PowerShell Security Monitor.

This module monitors PowerShell activity for suspicious patterns including:
- Obfuscated commands (Base64 encoding, character substitution)
- Suspicious cmdlets (Invoke-Expression, DownloadString, etc.)
- Script block logging events (Windows Event Log 4104)
- Fileless malware patterns
- Encoded command execution

The monitor integrates with Windows Event Log to track PowerShell executions
and can detect common malware techniques like:
- PowerShell Empire
- Cobalt Strike beacons
- Fileless payload delivery
- Living-off-the-land binaries (LOLBins)

Note: Requires PowerShell Script Block Logging to be enabled in Windows.
"""

import asyncio
import base64
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import psutil
from pydantic import Field

from hifzdefend.monitoring.base import BaseMonitor, MonitorConfig
from hifzdefend.monitoring.event_bus import EventBus
from hifzdefend.monitoring.events import Event, EventSeverity, EventType

logger = logging.getLogger(__name__)


class PowerShellMonitorConfig(MonitorConfig):
    """Configuration for PowerShell Security monitor."""

    monitor_event_log: bool = Field(
        default=True, description="Monitor Windows Event Log for PowerShell events"
    )
    detect_obfuscation: bool = Field(
        default=True, description="Detect obfuscated PowerShell commands"
    )
    suspicious_cmdlets: list[str] = Field(
        default_factory=lambda: [
            "Invoke-Expression",
            "IEX",
            "DownloadString",
            "DownloadFile",
            "New-Object Net.WebClient",
            "Start-BitsTransfer",
            "Invoke-WebRequest",
            "Invoke-RestMethod",
            "Add-Type",
            "Start-Process",
            "New-Service",
            "Set-Service",
        ],
        description="List of suspicious PowerShell cmdlets",
    )
    whitelist_scripts: list[str] = Field(
        default_factory=list, description="Paths to trusted PowerShell scripts"
    )
    alert_on_encoded_command: bool = Field(
        default=True, description="Alert on -EncodedCommand usage"
    )
    alert_on_download: bool = Field(
        default=True, description="Alert on download operations"
    )
    alert_on_execution: bool = Field(
        default=True, description="Alert on code execution cmdlets"
    )
    monitor_running_processes: bool = Field(
        default=True, description="Monitor running PowerShell processes"
    )
    event_log_lookback_minutes: int = Field(
        default=5, description="How far back to look in Event Log (minutes)"
    )
    detect_mimikatz: bool = Field(
        default=True, description="Detect Mimikatz credential dumping patterns"
    )
    detect_empire: bool = Field(
        default=True, description="Detect PowerShell Empire patterns"
    )


class PowerShellMonitor(BaseMonitor):
    """Monitor PowerShell activity for security threats.

    This monitor detects:
    - Obfuscated PowerShell commands
    - Suspicious cmdlet usage
    - Encoded command execution
    - Download operations
    - Fileless malware patterns
    - Credential dumping (Mimikatz)
    - C2 frameworks (Empire, Cobalt Strike)
    """

    # Suspicious cmdlets that indicate potential malicious activity
    SUSPICIOUS_CMDLETS = {
        "Invoke-Expression": 70,  # Threat score
        "IEX": 70,
        "Invoke-Command": 60,
        "ICM": 60,
        "DownloadString": 80,
        "DownloadFile": 80,
        "New-Object Net.WebClient": 75,
        "Start-BitsTransfer": 75,
        "Invoke-WebRequest": 65,
        "IWR": 65,
        "Invoke-RestMethod": 65,
        "IRM": 65,
        "Add-Type": 70,
        "Start-Process": 50,
        "New-Service": 75,
        "Set-Service": 70,
        "Stop-Service": 65,
        "Remove-Item": 55,
        "Invoke-WmiMethod": 70,
        "Get-WmiObject": 60,
        "Register-ScheduledTask": 75,
        "Set-MpPreference": 85,  # Disabling Windows Defender
        "Add-MpPreference": 80,
    }

    # Obfuscation patterns (regex)
    OBFUSCATION_PATTERNS = {
        "base64_encoded": re.compile(
            r"-(?:enc(?:odedcommand)?|e)\s+([A-Za-z0-9+/=]{20,})", re.IGNORECASE
        ),
        "char_substitution": re.compile(r"\[char\]\d+", re.IGNORECASE),
        "string_concat": re.compile(r"['\"][\w\s]+['\"]\s*\+\s*['\"]", re.IGNORECASE),
        "backtick_obfuscation": re.compile(r"\w+`\w+", re.IGNORECASE),
        "format_string": re.compile(r"-f\s+['\"]", re.IGNORECASE),
        "compression": re.compile(
            r"IO\.Compression|DeflateStream|GZipStream", re.IGNORECASE
        ),
        "reflection": re.compile(
            r"System\.Reflection|GetMethod|Invoke\(", re.IGNORECASE
        ),
    }

    # Fileless malware patterns
    FILELESS_PATTERNS = {
        "mimikatz": re.compile(
            r"(?:mimikatz|sekurlsa|lsadump|kerberos::golden)", re.IGNORECASE
        ),
        "empire": re.compile(
            r"(?:powershell.*empire|system\.net\.webclient.*empire|invoke-empire)",
            re.IGNORECASE,
        ),
        "cobalt_strike": re.compile(
            r"(?:beacon|stageless|stager|\\x[0-9a-f]{2})", re.IGNORECASE
        ),
        "credential_dump": re.compile(
            r"(?:Get-Credential|ConvertFrom-SecureString|password|credential)",
            re.IGNORECASE,
        ),
        "process_injection": re.compile(
            r"(?:VirtualAlloc|WriteProcessMemory|CreateRemoteThread|NtCreateThreadEx)",
            re.IGNORECASE,
        ),
        "amsi_bypass": re.compile(
            r"(?:AmsiUtils|amsiInitFailed|Reflection\.Assembly.*Load)", re.IGNORECASE
        ),
    }

    # Download patterns
    DOWNLOAD_PATTERNS = {
        "webclient": re.compile(
            r"New-Object\s+(?:System\.)?Net\.WebClient", re.IGNORECASE
        ),
        "downloadstring": re.compile(r"DownloadString\s*\(", re.IGNORECASE),
        "downloadfile": re.compile(r"DownloadFile\s*\(", re.IGNORECASE),
        "bitstransfer": re.compile(r"Start-BitsTransfer", re.IGNORECASE),
        "webrequest": re.compile(r"Invoke-WebRequest", re.IGNORECASE),
        "restmethod": re.compile(r"Invoke-RestMethod", re.IGNORECASE),
    }

    def __init__(self, config: PowerShellMonitorConfig, event_bus: EventBus):
        """Initialize PowerShell monitor.

        Args:
            config: Monitor configuration
            event_bus: Event bus for publishing events
        """
        super().__init__(config, event_bus)
        self.config: PowerShellMonitorConfig = config
        self._monitored_pids: set[int] = set()
        self._last_event_log_check: datetime | None = None
        self._event_log_available = False
        self._check_event_log_availability()

    def _check_event_log_availability(self) -> None:
        """Check if Windows Event Log is available and accessible."""
        try:
            import win32evtlog  # type: ignore

            # Try to open PowerShell event log
            handle = win32evtlog.OpenEventLog(
                None, "Microsoft-Windows-PowerShell/Operational"
            )
            win32evtlog.CloseEventLog(handle)
            self._event_log_available = True
            logger.info("Windows Event Log access confirmed")
        except ImportError:
            logger.warning(
                "pywin32 not installed - Event Log monitoring disabled. "
                "Install with: pip install pywin32"
            )
            self._event_log_available = False
        except Exception as e:
            logger.warning(f"Event Log not accessible: {e}")
            self._event_log_available = False

    async def start(self) -> None:
        """Start the PowerShell monitor."""
        self._running = True
        self._last_event_log_check = datetime.now()
        logger.info(
            f"PowerShell monitor started (Event Log: {self._event_log_available})"
        )

    async def stop(self) -> None:
        """Stop the PowerShell monitor."""
        self._running = False
        logger.info("PowerShell monitor stopped")

    async def check(self) -> list[Event]:
        """Perform PowerShell security check.

        Returns:
            List of security events detected
        """
        events = []

        # Check running PowerShell processes
        if self.config.monitor_running_processes:
            events.extend(await self._check_running_processes())

        # Check Windows Event Log
        if self.config.monitor_event_log and self._event_log_available:
            events.extend(await self._check_event_log())

        return events

    async def _check_running_processes(self) -> list[Event]:
        """Check currently running PowerShell processes.

        Returns:
            List of events for suspicious PowerShell processes
        """
        events = []

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                name = proc.info["name"]
                if name and name.lower() in ["powershell.exe", "pwsh.exe"]:
                    pid = proc.info["pid"]

                    # Skip if already monitored
                    if pid in self._monitored_pids:
                        continue

                    self._monitored_pids.add(pid)

                    cmdline = proc.info["cmdline"]
                    if cmdline:
                        command = " ".join(cmdline)
                        event_list = await self._analyze_command(command, pid)
                        events.extend(event_list)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return events

    async def _check_event_log(self) -> list[Event]:
        """Check Windows Event Log for PowerShell script block logging.

        Returns:
            List of events from Event Log analysis
        """
        events = []

        try:
            import win32evtlog  # type: ignore
            import win32evtlogutil  # type: ignore

            # Open PowerShell Operational log
            hand = win32evtlog.OpenEventLog(
                None, "Microsoft-Windows-PowerShell/Operational"
            )

            # Calculate time window
            now = datetime.now()
            lookback = timedelta(minutes=self.config.event_log_lookback_minutes)
            cutoff_time = now - lookback

            # Read events
            flags = (
                win32evtlog.EVENTLOG_BACKWARDS_READ
                | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            )
            total = 0

            while True:
                evts = win32evtlog.ReadEventLog(hand, flags, 0)
                if not evts:
                    break

                for event in evts:
                    # Event ID 4104 = Script Block Logging
                    if event.EventID == 4104:
                        # Check event time
                        event_time = event.TimeGenerated.Format()
                        # Parse time (format: MM/DD/YY HH:MM:SS)
                        try:
                            evt_dt = datetime.strptime(event_time, "%m/%d/%y %H:%M:%S")
                            if evt_dt < cutoff_time:
                                # Stop reading - events are too old
                                win32evtlog.CloseEventLog(hand)
                                return events
                        except ValueError:
                            pass

                        # Extract script block text
                        script_block = str(event.StringInserts) if event.StringInserts else ""
                        if script_block:
                            event_list = await self._analyze_command(script_block, None)
                            events.extend(event_list)

                total += len(evts)
                if total > 1000:  # Safety limit
                    break

            win32evtlog.CloseEventLog(hand)

        except ImportError:
            logger.debug("pywin32 not available for Event Log monitoring")
        except Exception as e:
            logger.warning(f"Error reading Event Log: {e}")

        return events

    async def _analyze_command(
        self, command: str, pid: int | None
    ) -> list[Event]:
        """Analyze PowerShell command for suspicious patterns.

        Args:
            command: PowerShell command string
            pid: Process ID (None if from Event Log)

        Returns:
            List of events for detected threats
        """
        events = []

        # Skip whitelisted scripts
        if self._is_whitelisted(command):
            return events

        # Check for obfuscation
        if self.config.detect_obfuscation:
            obfuscation_events = self._check_obfuscation(command, pid)
            events.extend(obfuscation_events)

        # Check for suspicious cmdlets
        cmdlet_events = self._check_suspicious_cmdlets(command, pid)
        events.extend(cmdlet_events)

        # Check for download operations
        if self.config.alert_on_download:
            download_events = self._check_downloads(command, pid)
            events.extend(download_events)

        # Check for fileless malware patterns
        fileless_events = self._check_fileless_patterns(command, pid)
        events.extend(fileless_events)

        return events

    def _is_whitelisted(self, command: str) -> bool:
        """Check if command is from a whitelisted script.

        Args:
            command: PowerShell command

        Returns:
            True if whitelisted
        """
        for script_path in self.config.whitelist_scripts:
            if script_path.lower() in command.lower():
                return True
        return False

    def _check_obfuscation(self, command: str, pid: int | None) -> list[Event]:
        """Check for obfuscated PowerShell commands.

        Args:
            command: PowerShell command
            pid: Process ID

        Returns:
            List of obfuscation events
        """
        events = []

        for pattern_name, pattern_regex in self.OBFUSCATION_PATTERNS.items():
            if pattern_regex.search(command):
                # Special handling for Base64
                if pattern_name == "base64_encoded" and self.config.alert_on_encoded_command:
                    match = pattern_regex.search(command)
                    if match:
                        encoded_cmd = match.group(1)
                        decoded = self._decode_base64(encoded_cmd)

                        events.append(
                            Event(
                                event_type=EventType.SUSPICIOUS_ACTIVITY,
                                severity=EventSeverity.CRITICAL,
                                source_monitor=self.name,
                                threat_score=90,
                                description=f"PowerShell encoded command detected: {pattern_name}",
                                data={
                                    "pattern": pattern_name,
                                    "command": command[:200],
                                    "encoded": encoded_cmd[:100],
                                    "decoded": decoded[:200] if decoded else "Failed to decode",
                                    "pid": pid,
                                },
                            )
                        )
                else:
                    events.append(
                        Event(
                            event_type=EventType.SUSPICIOUS_ACTIVITY,
                            severity=EventSeverity.WARNING,
                            source_monitor=self.name,
                            threat_score=75,
                            description=f"PowerShell obfuscation detected: {pattern_name}",
                            data={
                                "pattern": pattern_name,
                                "command": command[:200],
                                "pid": pid,
                            },
                        )
                    )

        return events

    def _check_suspicious_cmdlets(self, command: str, pid: int | None) -> list[Event]:
        """Check for suspicious PowerShell cmdlets.

        Args:
            command: PowerShell command
            pid: Process ID

        Returns:
            List of cmdlet events
        """
        events = []

        for cmdlet, threat_score in self.SUSPICIOUS_CMDLETS.items():
            # Case-insensitive search
            if re.search(rf"\b{re.escape(cmdlet)}\b", command, re.IGNORECASE):
                # Determine severity based on threat score
                if threat_score >= 80:
                    severity = EventSeverity.CRITICAL
                elif threat_score >= 60:
                    severity = EventSeverity.WARNING
                else:
                    severity = EventSeverity.INFO

                events.append(
                    Event(
                        event_type=EventType.SUSPICIOUS_ACTIVITY,
                        severity=severity,
                        source_monitor=self.name,
                        threat_score=threat_score,
                        description=f"Suspicious PowerShell cmdlet: {cmdlet}",
                        data={
                            "cmdlet": cmdlet,
                            "command": command[:200],
                            "pid": pid,
                            "recommendation": "Review PowerShell command for malicious intent",
                        },
                    )
                )

        return events

    def _check_downloads(self, command: str, pid: int | None) -> list[Event]:
        """Check for download operations.

        Args:
            command: PowerShell command
            pid: Process ID

        Returns:
            List of download events
        """
        events = []

        for pattern_name, pattern_regex in self.DOWNLOAD_PATTERNS.items():
            if pattern_regex.search(command):
                events.append(
                    Event(
                        event_type=EventType.SUSPICIOUS_ACTIVITY,
                        severity=EventSeverity.WARNING,
                        source_monitor=self.name,
                        threat_score=80,
                        description=f"PowerShell download operation detected: {pattern_name}",
                        data={
                            "pattern": pattern_name,
                            "command": command[:200],
                            "pid": pid,
                            "recommendation": "Verify legitimacy of download operation",
                        },
                    )
                )

        return events

    def _check_fileless_patterns(self, command: str, pid: int | None) -> list[Event]:
        """Check for fileless malware patterns.

        Args:
            command: PowerShell command
            pid: Process ID

        Returns:
            List of fileless malware events
        """
        events = []

        for pattern_name, pattern_regex in self.FILELESS_PATTERNS.items():
            if pattern_regex.search(command):
                # All fileless patterns are critical
                threat_score = 95

                # Mimikatz and credential dumping are highest priority
                if pattern_name in ["mimikatz", "credential_dump"]:
                    threat_score = 98

                events.append(
                    Event(
                        event_type=EventType.SUSPICIOUS_ACTIVITY,
                        severity=EventSeverity.CRITICAL,
                        source_monitor=self.name,
                        threat_score=threat_score,
                        description=f"Fileless malware pattern detected: {pattern_name}",
                        data={
                            "pattern": pattern_name,
                            "command": command[:200],
                            "pid": pid,
                            "threat_type": "fileless_malware",
                            "recommendation": "Terminate process immediately and investigate",
                        },
                    )
                )

        return events

    def _decode_base64(self, encoded: str) -> str | None:
        """Decode Base64 PowerShell command.

        Args:
            encoded: Base64 encoded string

        Returns:
            Decoded string or None if decoding fails
        """
        try:
            # PowerShell uses UTF-16LE encoding
            decoded_bytes = base64.b64decode(encoded)
            decoded = decoded_bytes.decode("utf-16-le")
            return decoded
        except Exception:
            try:
                # Try UTF-8 as fallback
                decoded_bytes = base64.b64decode(encoded)
                decoded = decoded_bytes.decode("utf-8")
                return decoded
            except Exception:
                return None
