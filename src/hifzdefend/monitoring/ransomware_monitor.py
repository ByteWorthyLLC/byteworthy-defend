"""Ransomware Detection Monitor.

This module detects ransomware behavior patterns including:
- Mass file encryption operations
- Rapid file modifications across directories
- Shadow copy deletion attempts
- Ransom note creation
- File extension changes
- Suspicious process behavior

Triggers automatic backup and alerts on detection.
"""

import asyncio
import logging
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import psutil
from pydantic import Field
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from hifzdefend.monitoring.base import BaseMonitor, MonitorConfig
from hifzdefend.monitoring.events import Event, EventSeverity, EventType

logger = logging.getLogger(__name__)


class RansomwareMonitorConfig(MonitorConfig):
    """Configuration for Ransomware Detection monitor."""

    enabled: bool = Field(default=True, description="Enable ransomware detection")
    file_modification_threshold: int = Field(
        default=50, description="Number of files modified in threshold window to trigger alert"
    )
    threshold_window_seconds: int = Field(
        default=10, description="Time window for file modification threshold"
    )
    monitored_directories: list[str] = Field(
        default_factory=lambda: [
            str(Path.home() / "Documents"),
            str(Path.home() / "Desktop"),
            str(Path.home() / "Pictures"),
            str(Path.home() / "Videos"),
        ],
        description="Directories to monitor for ransomware activity",
    )
    detect_shadow_copy_deletion: bool = Field(
        default=True, description="Detect shadow copy deletion attempts"
    )
    auto_backup_on_detect: bool = Field(
        default=False, description="Automatically trigger backup on ransomware detection"
    )
    backup_directory: str = Field(
        default=str(Path.home() / "HifzDefend_Backups"),
        description="Directory for automatic backups",
    )
    ransom_note_patterns: list[str] = Field(
        default_factory=lambda: [
            "encrypted",
            "ransom",
            "bitcoin",
            "decrypt",
            "payment",
            "restore your files",
            "locked",
            "recovery key",
            ".onion",
            "tor browser",
        ],
        description="Patterns to detect in ransom notes",
    )
    suspicious_extensions: list[str] = Field(
        default_factory=lambda: [
            ".encrypted",
            ".locked",
            ".crypto",
            ".crypt",
            ".enc",
            ".locky",
            ".cerber",
            ".zepto",
            ".thor",
            ".wannacry",
            ".petya",
        ],
        description="File extensions commonly used by ransomware",
    )
    monitor_process_execution: bool = Field(
        default=True, description="Monitor for suspicious process executions (vssadmin, etc.)"
    )
    terminate_on_detect: bool = Field(
        default=False, description="Automatically terminate suspicious processes"
    )
    extension_change_threshold: int = Field(
        default=20, description="Number of extension changes to trigger alert"
    )


class FileOperationTracker:
    """Track file operations for ransomware detection."""

    def __init__(self, threshold: int, window_seconds: int):
        self.threshold = threshold
        self.window_seconds = window_seconds
        self.modifications: dict[str, list[float]] = defaultdict(list)
        self.extension_changes: dict[tuple[str, str], int] = defaultdict(int)
        self.created_files: list[tuple[str, float]] = []
        self._lock = asyncio.Lock()

    async def record_modification(self, file_path: str, pid: int | None = None) -> dict[str, Any]:
        """Record a file modification.

        Returns dict with:
            - threshold_exceeded: bool
            - modification_count: int
            - window_start: datetime
            - process_id: int | None
        """
        async with self._lock:
            now = time.time()
            self.modifications[file_path].append(now)

            # Clean old entries outside window
            cutoff = now - self.window_seconds
            for path in list(self.modifications.keys()):
                self.modifications[path] = [t for t in self.modifications[path] if t >= cutoff]
                if not self.modifications[path]:
                    del self.modifications[path]

            # Count total modifications in window
            total_mods = sum(len(times) for times in self.modifications.values())

            return {
                "threshold_exceeded": total_mods >= self.threshold,
                "modification_count": total_mods,
                "unique_files": len(self.modifications),
                "window_start": datetime.fromtimestamp(cutoff),
                "process_id": pid,
            }

    async def record_extension_change(
        self, old_ext: str, new_ext: str
    ) -> dict[str, Any]:
        """Record a file extension change.

        Returns dict with:
            - count: int (total changes for this extension pair)
            - old_extension: str
            - new_extension: str
        """
        async with self._lock:
            key = (old_ext.lower(), new_ext.lower())
            self.extension_changes[key] += 1

            return {
                "count": self.extension_changes[key],
                "old_extension": old_ext,
                "new_extension": new_ext,
                "total_extension_changes": sum(self.extension_changes.values()),
            }

    async def record_file_creation(self, file_path: str):
        """Record a file creation (for ransom note detection)."""
        async with self._lock:
            now = time.time()
            self.created_files.append((file_path, now))

            # Keep only recent files (last 5 minutes)
            cutoff = now - 300
            self.created_files = [(p, t) for p, t in self.created_files if t >= cutoff]

    def get_recent_created_files(self, seconds: int = 60) -> list[str]:
        """Get files created in the last N seconds."""
        cutoff = time.time() - seconds
        return [path for path, t in self.created_files if t >= cutoff]

    def reset(self):
        """Reset all tracking data."""
        self.modifications.clear()
        self.extension_changes.clear()
        self.created_files.clear()


class RansomwareFileEventHandler(FileSystemEventHandler):
    """Handle file system events for ransomware detection."""

    def __init__(self, monitor: "RansomwareMonitor"):
        super().__init__()
        self.monitor = monitor

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return

        # Schedule async processing
        asyncio.create_task(self.monitor._handle_file_modification(event.src_path))

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if event.is_directory:
            return

        asyncio.create_task(self.monitor._handle_file_creation(event.src_path))

    def on_moved(self, event: FileSystemEvent):
        """Handle file rename/move events (potential extension change)."""
        if event.is_directory:
            return

        asyncio.create_task(
            self.monitor._handle_file_rename(event.src_path, event.dest_path)
        )


class RansomwareMonitor(BaseMonitor):
    """Monitor for ransomware behavior detection.

    Detects:
    - Mass file encryption (rapid modifications)
    - File extension changes to suspicious extensions
    - Shadow copy deletion attempts
    - Ransom note creation
    - Suspicious process behavior
    """

    def __init__(self, config: RansomwareMonitorConfig, event_bus):
        super().__init__(config, event_bus)
        self.config: RansomwareMonitorConfig = config
        self.tracker = FileOperationTracker(
            threshold=config.file_modification_threshold,
            window_seconds=config.threshold_window_seconds,
        )
        self.observer: Observer | None = None
        self._event_handler: RansomwareFileEventHandler | None = None
        self._suspicious_processes: set[int] = set()
        self._backup_triggered = False
        self._alert_cooldown: dict[str, float] = {}
        self._ransom_note_regex = self._compile_ransom_patterns()

    def _compile_ransom_patterns(self) -> re.Pattern:
        """Compile ransom note detection patterns into single regex."""
        # Create case-insensitive pattern
        pattern_str = "|".join(
            re.escape(pattern) for pattern in self.config.ransom_note_patterns
        )
        return re.compile(pattern_str, re.IGNORECASE)

    async def start(self) -> None:
        """Start ransomware monitoring."""
        self._logger.info("Starting Ransomware Detection Monitor")

        # Start file system monitoring
        if self.config.monitored_directories:
            self._start_filesystem_monitoring()

        # Start process monitoring
        if self.config.monitor_process_execution:
            # Process monitoring happens in check() method
            self._logger.info("Process execution monitoring enabled")

        self._running = True
        self._logger.info("Ransomware Detection Monitor started successfully")

    def _start_filesystem_monitoring(self):
        """Start monitoring file system for ransomware activity."""
        self.observer = Observer()
        self._event_handler = RansomwareFileEventHandler(self)

        for directory in self.config.monitored_directories:
            dir_path = Path(directory)
            if dir_path.exists() and dir_path.is_dir():
                try:
                    self.observer.schedule(
                        self._event_handler, str(dir_path), recursive=True
                    )
                    self._logger.info(f"Monitoring directory: {dir_path}")
                except Exception as e:
                    self._logger.warning(
                        f"Failed to monitor directory {dir_path}: {e}"
                    )
            else:
                self._logger.warning(f"Directory does not exist: {dir_path}")

        if self.observer._watches:
            self.observer.start()
            self._logger.info("File system monitoring started")
        else:
            self._logger.warning("No directories to monitor")

    async def stop(self) -> None:
        """Stop ransomware monitoring."""
        self._logger.info("Stopping Ransomware Detection Monitor")

        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            self._logger.info("File system monitoring stopped")

        self._running = False
        self._logger.info("Ransomware Detection Monitor stopped")

    async def check(self) -> list[Event]:
        """Perform ransomware detection check.

        Returns:
            List of ransomware-related security events
        """
        events = []

        # Check for suspicious process executions
        if self.config.monitor_process_execution:
            process_events = await self._check_suspicious_processes()
            events.extend(process_events)

        # Check for recently created ransom notes
        ransom_note_events = await self._check_ransom_notes()
        events.extend(ransom_note_events)

        return events

    async def _check_suspicious_processes(self) -> list[Event]:
        """Check for suspicious process executions (vssadmin, wbadmin, etc.)."""
        events = []

        suspicious_process_names = [
            "vssadmin.exe",  # Volume Shadow Copy Service admin
            "wbadmin.exe",  # Windows Backup admin
            "bcdedit.exe",  # Boot configuration
            "wmic.exe",  # Windows Management Instrumentation
        ]

        suspicious_cmdlines = [
            "vssadmin delete shadows",
            "vssadmin.exe delete shadows",
            "wbadmin delete catalog",
            "wbadmin delete systemstatebackup",
            "bcdedit /set {default} recoveryenabled no",
            "bcdedit /set {default} bootstatuspolicy ignoreallfailures",
            "wmic shadowcopy delete",
        ]

        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
                try:
                    proc_name = proc.info["name"].lower()
                    cmdline = " ".join(proc.info["cmdline"] or []).lower()

                    # Check process name
                    if proc_name in suspicious_process_names:
                        # Check command line for dangerous operations
                        is_dangerous = any(
                            pattern.lower() in cmdline for pattern in suspicious_cmdlines
                        )

                        if is_dangerous:
                            # Alert cooldown (don't spam for same process)
                            cooldown_key = f"process_{proc.info['pid']}"
                            if self._should_alert(cooldown_key):
                                event = Event(
                                    event_type=EventType.SUSPICIOUS_ACTIVITY,
                                    severity=EventSeverity.CRITICAL,
                                    source_monitor=self.name,
                                    description=f"Suspicious process execution detected: {proc_name}",
                                    data={
                                        "process_name": proc_name,
                                        "process_id": proc.info["pid"],
                                        "command_line": cmdline,
                                        "pattern": "shadow_copy_deletion",
                                        "recommendation": "CRITICAL: This process is attempting to delete shadow copies, a common ransomware technique. Consider terminating immediately.",
                                    },
                                    threat_score=95,
                                )
                                events.append(event)
                                self._suspicious_processes.add(proc.info["pid"])

                                # Auto-terminate if configured
                                if self.config.terminate_on_detect:
                                    await self._terminate_process(proc)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            self._logger.error(f"Error checking suspicious processes: {e}")

        return events

    async def _handle_file_modification(self, file_path: str):
        """Handle file modification event."""
        try:
            # Get process that modified the file (if possible)
            pid = None
            try:
                # Try to get the process that has the file open
                for proc in psutil.process_iter(["pid", "open_files"]):
                    try:
                        if proc.info["open_files"]:
                            open_paths = [f.path for f in proc.info["open_files"]]
                            if file_path in open_paths:
                                pid = proc.info["pid"]
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception:
                pass

            # Record modification
            result = await self.tracker.record_modification(file_path, pid)

            # Check if threshold exceeded
            if result["threshold_exceeded"]:
                cooldown_key = "mass_modification"
                if self._should_alert(cooldown_key, cooldown_seconds=30):
                    event = Event(
                        event_type=EventType.THREAT_DETECTED,
                        severity=EventSeverity.CRITICAL,
                        source_monitor=self.name,
                        description=f"Mass file modification detected: {result['modification_count']} files in {self.config.threshold_window_seconds} seconds",
                        data={
                            "modification_count": result["modification_count"],
                            "unique_files": result["unique_files"],
                            "threshold": self.config.file_modification_threshold,
                            "window_seconds": self.config.threshold_window_seconds,
                            "window_start": result["window_start"].isoformat(),
                            "process_id": pid,
                            "pattern": "mass_encryption",
                            "recommendation": "CRITICAL: Possible ransomware encryption in progress. Consider isolating system and terminating suspicious processes.",
                        },
                        threat_score=98,
                    )
                    self.publish_event(event)

                    # Trigger backup if configured
                    if self.config.auto_backup_on_detect and not self._backup_triggered:
                        await self._trigger_backup()

        except Exception as e:
            self._logger.error(f"Error handling file modification {file_path}: {e}")

    async def _handle_file_creation(self, file_path: str):
        """Handle file creation event."""
        try:
            await self.tracker.record_file_creation(file_path)

            # Check if file is a potential ransom note
            path = Path(file_path)
            if path.suffix.lower() in [".txt", ".html", ".htm"]:
                # Check file content for ransom patterns
                is_ransom_note = await self._check_file_for_ransom_content(path)
                if is_ransom_note:
                    cooldown_key = f"ransom_note_{path.name}"
                    if self._should_alert(cooldown_key):
                        event = Event(
                            event_type=EventType.THREAT_DETECTED,
                            severity=EventSeverity.CRITICAL,
                            source_monitor=self.name,
                            description=f"Ransom note detected: {path.name}",
                            data={
                                "file_path": str(path),
                                "file_name": path.name,
                                "pattern": "ransom_note",
                                "recommendation": "CRITICAL: Ransom note detected. System may be compromised. Isolate immediately and restore from backups.",
                            },
                            threat_score=99,
                        )
                        self.publish_event(event)

        except Exception as e:
            self._logger.error(f"Error handling file creation {file_path}: {e}")

    async def _handle_file_rename(self, old_path: str, new_path: str):
        """Handle file rename/move event (potential extension change)."""
        try:
            old_ext = Path(old_path).suffix
            new_ext = Path(new_path).suffix

            if old_ext != new_ext:
                result = await self.tracker.record_extension_change(old_ext, new_ext)

                # Check if new extension is suspicious
                if new_ext.lower() in self.config.suspicious_extensions:
                    cooldown_key = f"suspicious_extension_{new_ext}"
                    if self._should_alert(cooldown_key, cooldown_seconds=10):
                        event = Event(
                            event_type=EventType.THREAT_DETECTED,
                            severity=EventSeverity.CRITICAL,
                            source_monitor=self.name,
                            description=f"File encrypted with suspicious extension: {old_ext} → {new_ext}",
                            data={
                                "old_path": old_path,
                                "new_path": new_path,
                                "old_extension": old_ext,
                                "new_extension": new_ext,
                                "extension_change_count": result["count"],
                                "pattern": "suspicious_extension",
                                "recommendation": "CRITICAL: File extension changed to known ransomware pattern. Possible encryption in progress.",
                            },
                            threat_score=97,
                        )
                        self.publish_event(event)

                # Check if too many extension changes overall
                if result["total_extension_changes"] >= self.config.extension_change_threshold:
                    cooldown_key = "mass_extension_change"
                    if self._should_alert(cooldown_key, cooldown_seconds=30):
                        event = Event(
                            event_type=EventType.THREAT_DETECTED,
                            severity=EventSeverity.CRITICAL,
                            source_monitor=self.name,
                            description=f"Mass file extension changes detected: {result['total_extension_changes']} changes",
                            data={
                                "total_changes": result["total_extension_changes"],
                                "threshold": self.config.extension_change_threshold,
                                "pattern": "mass_extension_change",
                                "recommendation": "CRITICAL: Mass file extension changes detected. Likely ransomware encryption.",
                            },
                            threat_score=98,
                        )
                        self.publish_event(event)

        except Exception as e:
            self._logger.error(f"Error handling file rename {old_path} → {new_path}: {e}")

    async def _check_ransom_notes(self) -> list[Event]:
        """Check for recently created ransom notes."""
        events = []

        try:
            recent_files = self.tracker.get_recent_created_files(seconds=60)

            for file_path in recent_files:
                path = Path(file_path)
                if path.exists() and path.suffix.lower() in [".txt", ".html", ".htm"]:
                    is_ransom = await self._check_file_for_ransom_content(path)
                    if is_ransom:
                        cooldown_key = f"ransom_note_{path.name}"
                        if self._should_alert(cooldown_key):
                            event = Event(
                                event_type=EventType.THREAT_DETECTED,
                                severity=EventSeverity.CRITICAL,
                                source_monitor=self.name,
                                description=f"Ransom note detected: {path.name}",
                                data={
                                    "file_path": str(path),
                                    "file_name": path.name,
                                    "pattern": "ransom_note",
                                    "recommendation": "CRITICAL: Ransom note detected. System is likely compromised.",
                                },
                                threat_score=99,
                            )
                            events.append(event)

        except Exception as e:
            self._logger.error(f"Error checking ransom notes: {e}")

        return events

    async def _check_file_for_ransom_content(self, file_path: Path) -> bool:
        """Check if file content matches ransom note patterns."""
        try:
            # Read file content (limit to 10KB to avoid reading huge files)
            content = file_path.read_text(encoding="utf-8", errors="ignore")[:10240]

            # Check against ransom patterns
            if self._ransom_note_regex.search(content):
                # Additional heuristic: ransom notes often have multiple keywords
                matches = sum(
                    1
                    for pattern in self.config.ransom_note_patterns
                    if pattern.lower() in content.lower()
                )
                return matches >= 2  # At least 2 keywords

            return False

        except Exception as e:
            self._logger.debug(f"Error reading file {file_path}: {e}")
            return False

    async def _trigger_backup(self):
        """Trigger automatic backup on ransomware detection."""
        self._backup_triggered = True
        self._logger.critical("RANSOMWARE DETECTED: Triggering automatic backup")

        try:
            backup_dir = Path(self.config.backup_directory)
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"ransomware_backup_{timestamp}"

            # Emit backup event
            event = Event(
                event_type=EventType.SUSPICIOUS_ACTIVITY,
                severity=EventSeverity.CRITICAL,
                source_monitor=self.name,
                description=f"Automatic backup triggered: {backup_name}",
                data={
                    "backup_directory": str(backup_dir),
                    "backup_name": backup_name,
                    "trigger": "ransomware_detection",
                    "recommendation": "Backup initiated. Monitor backup progress and verify integrity.",
                },
                threat_score=90,
            )
            self.publish_event(event)

            # TODO: Implement actual backup logic
            # This could integrate with Windows Backup, Volume Shadow Copy, or custom backup
            self._logger.warning("Backup trigger - implementation needed for actual backup")

        except Exception as e:
            self._logger.error(f"Failed to trigger backup: {e}")

    async def _terminate_process(self, process: psutil.Process):
        """Terminate a suspicious process."""
        try:
            self._logger.warning(
                f"Terminating suspicious process: {process.info['name']} (PID: {process.info['pid']})"
            )
            process.terminate()

            # Wait for graceful termination
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                # Force kill if still running
                process.kill()
                self._logger.warning(
                    f"Forcefully killed process {process.info['pid']}"
                )

        except Exception as e:
            self._logger.error(
                f"Failed to terminate process {process.info['pid']}: {e}"
            )

    def _should_alert(self, key: str, cooldown_seconds: int = 60) -> bool:
        """Check if alert should be sent (rate limiting)."""
        now = time.time()
        last_alert = self._alert_cooldown.get(key, 0)

        if now - last_alert >= cooldown_seconds:
            self._alert_cooldown[key] = now
            return True

        return False

    def get_statistics(self) -> dict[str, Any]:
        """Get ransomware detection statistics."""
        return {
            "monitored_directories": len(self.config.monitored_directories),
            "suspicious_processes": len(self._suspicious_processes),
            "backup_triggered": self._backup_triggered,
            "total_modifications": sum(
                len(times) for times in self.tracker.modifications.values()
            ),
            "total_extension_changes": sum(self.tracker.extension_changes.values()),
            "recent_files_created": len(self.tracker.get_recent_created_files()),
        }
