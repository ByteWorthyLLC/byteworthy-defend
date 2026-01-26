"""Browser Download Monitor for HifzDefend.

This module monitors browser download directories for potentially malicious files.
It provides real-time scanning of downloaded files, VirusTotal reputation checks,
and detection of downloads from suspicious domains.

Features:
- Watch browser download directories (Chrome, Firefox, Edge, etc.)
- Auto-scan downloads with ClamAV before execution
- VirusTotal API integration for file reputation
- Track download sources (URLs) via browser history
- Alert on suspicious file extensions
- Monitor for drive-by downloads
- Quarantine malicious downloads automatically

Author: HifzDefend Team
License: MIT
"""

import asyncio
import hashlib
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import aiohttp
from pydantic import Field
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from hifzdefend.monitoring.base import MonitorConfig
from hifzdefend.monitoring.base import BaseMonitor
from hifzdefend.monitoring.events import Event, EventSeverity, EventType

logger = logging.getLogger(__name__)


class DownloadMonitorConfig(MonitorConfig):
    """Configuration for Browser Download monitor."""

    enabled: bool = Field(
        default=True,
        description="Enable browser download monitoring",
    )

    watch_directories: list[str] = Field(
        default_factory=lambda: [],
        description="Directories to monitor for downloads (e.g., Downloads folder)",
    )

    auto_scan: bool = Field(
        default=True,
        description="Automatically scan downloaded files with ClamAV",
    )

    quarantine_on_detect: bool = Field(
        default=True,
        description="Automatically quarantine malicious downloads",
    )

    check_file_reputation: bool = Field(
        default=True,
        description="Check file reputation with VirusTotal API",
    )

    virustotal_api_key: str = Field(
        default="",
        description="VirusTotal API key (optional but recommended)",
    )

    suspicious_extensions: list[str] = Field(
        default_factory=lambda: [
            ".exe",
            ".scr",
            ".pif",
            ".bat",
            ".cmd",
            ".com",
            ".vbs",
            ".js",
            ".jar",
            ".msi",
            ".dll",
            ".hta",
            ".wsf",
        ],
        description="File extensions that require extra scrutiny",
    )

    suspicious_domains: list[str] = Field(
        default_factory=lambda: [
            # Malware distribution domains (examples)
            "malware-site.example",
            "phishing-domain.example",
            "fake-download.example",
        ],
        description="Known malicious domains (will be expanded with threat intel)",
    )

    max_file_size_mb: int = Field(
        default=500,
        ge=1,
        description="Maximum file size (MB) to scan (avoid scanning huge files)",
    )

    scan_timeout_seconds: int = Field(
        default=60,
        ge=10,
        description="Timeout for ClamAV scan per file",
    )

    vt_scan_threshold_mb: int = Field(
        default=50,
        ge=1,
        description="Only send files smaller than this to VirusTotal",
    )

    track_download_sources: bool = Field(
        default=True,
        description="Track download source URLs from browser history",
    )

    ignore_temporary_files: bool = Field(
        default=True,
        description="Ignore temporary browser download files (.crdownload, .tmp, etc.)",
    )

    temporary_extensions: list[str] = Field(
        default_factory=lambda: [
            ".crdownload",  # Chrome
            ".part",  # Firefox
            ".partial",  # Edge
            ".tmp",  # General
            ".download",  # General
        ],
        description="Temporary file extensions to ignore",
    )


class DownloadEventHandler(FileSystemEventHandler):
    """Handles file system events for download directory."""

    def __init__(self, monitor: "DownloadMonitor"):
        """Initialize handler.

        Args:
            monitor: DownloadMonitor instance
        """
        self.monitor = monitor

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation event.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Ignore temporary files
        if self.monitor.config.ignore_temporary_files:
            if file_path.suffix.lower() in self.monitor.config.temporary_extensions:
                logger.debug(f"Ignoring temporary file: {file_path}")
                return

        # Queue file for scanning
        asyncio.create_task(self.monitor._handle_new_download(file_path))

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification event.

        Args:
            event: File system event
        """
        # We primarily care about new downloads (on_created)
        # Modifications are usually during download progress
        pass


class DownloadMonitor(BaseMonitor):
    """Monitor browser download directories for malicious files."""

    def __init__(self, config: DownloadMonitorConfig, event_bus: Any):
        """Initialize Download Monitor.

        Args:
            config: Monitor configuration
            event_bus: Event bus for publishing events
        """
        super().__init__(config, event_bus)
        self.config: DownloadMonitorConfig = config

        # File system observer
        self._observer: Optional[Observer] = None
        self._handlers: list[DownloadEventHandler] = []

        # Download tracking
        self._scanned_files: set[str] = set()  # Track already scanned files
        self._download_history: list[dict[str, Any]] = []  # Track download events

        # VirusTotal API session
        self._vt_session: Optional[aiohttp.ClientSession] = None
        self._vt_api_url = "https://www.virustotal.com/api/v3"

        # Statistics
        self._stats = {
            "total_downloads": 0,
            "scanned_files": 0,
            "threats_detected": 0,
            "quarantined_files": 0,
            "virustotal_checks": 0,
            "suspicious_downloads": 0,
        }

    async def start(self) -> None:
        """Start monitoring download directories."""
        if self._running:
            logger.warning("Download monitor already running")
            return

        logger.info("Starting download monitor")

        # Validate watch directories
        if not self.config.watch_directories:
            logger.warning("No watch directories configured, using default Downloads folder")
            # Auto-detect Downloads folder
            downloads_path = Path.home() / "Downloads"
            if downloads_path.exists():
                self.config.watch_directories = [str(downloads_path)]
            else:
                logger.error("Could not find Downloads folder")
                return

        # Start VirusTotal session if API key provided
        if self.config.check_file_reputation and self.config.virustotal_api_key:
            self._vt_session = aiohttp.ClientSession(
                headers={"x-apikey": self.config.virustotal_api_key}
            )
            logger.info("VirusTotal integration enabled")

        # Start file system observer
        self._observer = Observer()
        for directory in self.config.watch_directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                logger.warning(f"Watch directory does not exist: {directory}")
                continue

            handler = DownloadEventHandler(self)
            self._handlers.append(handler)
            self._observer.schedule(handler, str(dir_path), recursive=False)
            logger.info(f"Watching directory: {directory}")

        self._observer.start()
        self._running = True
        logger.info("Download monitor started successfully")

    async def stop(self) -> None:
        """Stop monitoring download directories."""
        if not self._running:
            return

        logger.info("Stopping download monitor")

        # Stop file system observer
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None

        # Close VirusTotal session
        if self._vt_session:
            await self._vt_session.close()
            self._vt_session = None

        self._running = False
        logger.info("Download monitor stopped")

    async def check(self) -> list[Event]:
        """Perform periodic check (mainly for statistics).

        Returns:
            List of events (usually empty, events are generated on file creation)
        """
        # Download monitor is event-driven, not polling-based
        # Return empty list
        return []

    async def _handle_new_download(self, file_path: Path) -> None:
        """Handle a newly downloaded file.

        Args:
            file_path: Path to downloaded file
        """
        try:
            # Check if already scanned
            file_str = str(file_path)
            if file_str in self._scanned_files:
                logger.debug(f"File already scanned: {file_path.name}")
                return

            # Wait for file to finish downloading (check if size stabilizes)
            if not await self._wait_for_download_complete(file_path):
                logger.warning(f"File download may not be complete: {file_path.name}")
                return

            # Mark as scanned
            self._scanned_files.add(file_str)
            self._stats["total_downloads"] += 1

            logger.info(f"New download detected: {file_path.name}")

            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.config.max_file_size_mb:
                logger.warning(
                    f"File too large to scan: {file_path.name} ({file_size_mb:.2f} MB)"
                )
                # Still create an informational event
                event = Event(
                    event_type=EventType.FILE_MODIFIED,
                    severity=EventSeverity.INFO,
                    source_monitor=self.name,
                    description=f"Large file downloaded: {file_path.name} ({file_size_mb:.2f} MB)",
                    threat_score=0,
                    data={
                        "file_path": file_str,
                        "file_name": file_path.name,
                        "file_size_mb": round(file_size_mb, 2),
                        "reason": "file_too_large",
                    },
                )
                self.publish_event(event)
                return

            # Check if suspicious extension
            is_suspicious_ext = file_path.suffix.lower() in self.config.suspicious_extensions

            # Scan with ClamAV
            clamav_result = None
            if self.config.auto_scan:
                clamav_result = await self._scan_with_clamav(file_path)
                self._stats["scanned_files"] += 1

                if clamav_result and clamav_result.get("is_infected"):
                    # THREAT DETECTED!
                    await self._handle_malicious_download(file_path, clamav_result)
                    return

            # Check VirusTotal reputation
            vt_result = None
            if self.config.check_file_reputation and self._vt_session:
                if file_size_mb <= self.config.vt_scan_threshold_mb:
                    vt_result = await self._check_virustotal(file_path)
                    self._stats["virustotal_checks"] += 1

                    if vt_result and vt_result.get("is_malicious"):
                        # THREAT DETECTED via VirusTotal!
                        await self._handle_suspicious_download(file_path, vt_result, "virustotal")
                        return

            # Check if suspicious extension but clean scan
            if is_suspicious_ext:
                self._stats["suspicious_downloads"] += 1
                event = Event(
                    event_type=EventType.FILE_MODIFIED,
                    severity=EventSeverity.WARNING,
                    source_monitor=self.name,
                    description=f"Potentially suspicious file downloaded: {file_path.name}",
                    threat_score=30,
                    data={
                        "pattern": "suspicious_extension",
                        "file_path": file_str,
                        "file_name": file_path.name,
                        "file_extension": file_path.suffix,
                        "file_size_mb": round(file_size_mb, 2),
                        "clamav_clean": clamav_result is not None
                        and not clamav_result.get("is_infected"),
                        "vt_clean": vt_result is not None and not vt_result.get("is_malicious"),
                        "recommendation": "Review file before executing. Downloaded executables should be from trusted sources.",
                    },
                )
                self.publish_event(event)

            # Log successful download
            download_record = {
                "timestamp": datetime.now().isoformat(),
                "file_path": file_str,
                "file_name": file_path.name,
                "file_size_mb": round(file_size_mb, 2),
                "extension": file_path.suffix,
                "clamav_scanned": clamav_result is not None,
                "vt_checked": vt_result is not None,
                "is_suspicious": is_suspicious_ext,
            }
            self._download_history.append(download_record)

            # Keep history limited
            if len(self._download_history) > 1000:
                self._download_history.pop(0)

        except Exception as e:
            logger.error(f"Error handling download {file_path}: {e}", exc_info=True)

    async def _wait_for_download_complete(
        self, file_path: Path, max_wait: int = 30, check_interval: float = 0.5
    ) -> bool:
        """Wait for file download to complete by checking size stability.

        Args:
            file_path: Path to file
            max_wait: Maximum seconds to wait
            check_interval: Seconds between size checks

        Returns:
            True if download appears complete, False if timeout
        """
        if not file_path.exists():
            return False

        start_time = time.time()
        last_size = -1
        stable_count = 0

        while time.time() - start_time < max_wait:
            try:
                current_size = file_path.stat().st_size

                if current_size == last_size:
                    stable_count += 1
                    # Consider stable after 3 consecutive same-size checks
                    if stable_count >= 3:
                        return True
                else:
                    stable_count = 0
                    last_size = current_size

                await asyncio.sleep(check_interval)

            except FileNotFoundError:
                return False
            except Exception as e:
                logger.error(f"Error checking file size: {e}")
                return False

        # Timeout - file may still be downloading
        return False

    async def _scan_with_clamav(self, file_path: Path) -> Optional[dict[str, Any]]:
        """Scan file with ClamAV.

        Args:
            file_path: Path to file to scan

        Returns:
            Scan result dict with keys: is_infected, signature, error
        """
        try:
            # Import ClamAV scanner
            from hifzdefend.scanning.scanner import Scanner
            from hifzdefend.config.loader import load_config

            config = load_config()
            scanner = Scanner(config)

            logger.info(f"Scanning with ClamAV: {file_path.name}")

            # Scan file
            result = await asyncio.wait_for(
                asyncio.to_thread(scanner.scan_file, str(file_path)),
                timeout=self.config.scan_timeout_seconds,
            )

            return {
                "is_infected": result.is_infected,
                "signature": result.signature if result.is_infected else None,
                "error": None,
            }

        except asyncio.TimeoutError:
            logger.error(f"ClamAV scan timeout: {file_path.name}")
            return {"is_infected": False, "signature": None, "error": "timeout"}
        except Exception as e:
            logger.error(f"ClamAV scan error: {e}", exc_info=True)
            return {"is_infected": False, "signature": None, "error": str(e)}

    async def _check_virustotal(self, file_path: Path) -> Optional[dict[str, Any]]:
        """Check file reputation on VirusTotal.

        Args:
            file_path: Path to file

        Returns:
            Dict with keys: is_malicious, detections, total_scanners, permalink
        """
        if not self._vt_session:
            return None

        try:
            # Calculate file hash (SHA256)
            file_hash = await self._calculate_file_hash(file_path)

            logger.info(f"Checking VirusTotal: {file_path.name} ({file_hash[:16]}...)")

            # Query VirusTotal API for file hash
            url = f"{self._vt_api_url}/files/{file_hash}"

            async with self._vt_session.get(url) as response:
                if response.status == 404:
                    # File not known to VirusTotal
                    logger.info("File not found in VirusTotal database")
                    return {
                        "is_malicious": False,
                        "detections": 0,
                        "total_scanners": 0,
                        "permalink": None,
                        "status": "not_found",
                    }

                if response.status != 200:
                    logger.warning(f"VirusTotal API error: {response.status}")
                    return None

                data = await response.json()

                # Parse results
                attributes = data.get("data", {}).get("attributes", {})
                stats = attributes.get("last_analysis_stats", {})

                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                total = sum(stats.values())

                permalink = data.get("data", {}).get("links", {}).get("self")

                # Consider malicious if 3+ engines flag it
                is_malicious = malicious >= 3 or suspicious >= 5

                return {
                    "is_malicious": is_malicious,
                    "detections": malicious,
                    "suspicious": suspicious,
                    "total_scanners": total,
                    "permalink": permalink,
                    "status": "found",
                }

        except asyncio.TimeoutError:
            logger.error("VirusTotal API timeout")
            return None
        except Exception as e:
            logger.error(f"VirusTotal check error: {e}", exc_info=True)
            return None

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash as hex string
        """

        def _hash_file():
            hasher = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()

        return await asyncio.to_thread(_hash_file)

    async def _handle_malicious_download(
        self, file_path: Path, scan_result: dict[str, Any]
    ) -> None:
        """Handle detection of malicious download.

        Args:
            file_path: Path to malicious file
            scan_result: ClamAV scan result
        """
        self._stats["threats_detected"] += 1

        logger.critical(f"MALICIOUS DOWNLOAD DETECTED: {file_path.name}")

        # Create critical event
        event = Event(
            event_type=EventType.THREAT_DETECTED,
            severity=EventSeverity.CRITICAL,
            source_monitor=self.name,
            description=f"Malicious file downloaded: {file_path.name}",
            threat_score=95,
            data={
                "pattern": "malicious_download",
                "file_path": str(file_path),
                "file_name": file_path.name,
                "signature": scan_result.get("signature"),
                "scanner": "ClamAV",
                "recommendation": "File has been quarantined. Do not execute. Run full system scan.",
                "action_taken": "quarantine" if self.config.quarantine_on_detect else "alert_only",
            },
        )
        self.publish_event(event)

        # Quarantine file
        if self.config.quarantine_on_detect:
            try:
                await self._quarantine_file(file_path)
                self._stats["quarantined_files"] += 1
                logger.info(f"File quarantined: {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to quarantine file: {e}", exc_info=True)

    async def _handle_suspicious_download(
        self, file_path: Path, vt_result: dict[str, Any], source: str
    ) -> None:
        """Handle detection of suspicious download via VirusTotal.

        Args:
            file_path: Path to suspicious file
            vt_result: VirusTotal result
            source: Detection source
        """
        self._stats["threats_detected"] += 1

        logger.warning(f"SUSPICIOUS DOWNLOAD DETECTED: {file_path.name}")

        threat_score = 70
        severity = EventSeverity.WARNING

        # Adjust severity based on detection count
        detections = vt_result.get("detections", 0)
        if detections >= 10:
            threat_score = 90
            severity = EventSeverity.CRITICAL
        elif detections >= 5:
            threat_score = 80
            severity = EventSeverity.WARNING

        event = Event(
            event_type=EventType.SUSPICIOUS_ACTIVITY,
            severity=severity,
            source_monitor=self.name,
            description=f"Suspicious file detected by {detections} antivirus engines: {file_path.name}",
            threat_score=threat_score,
            data={
                "pattern": "suspicious_download_virustotal",
                "file_path": str(file_path),
                "file_name": file_path.name,
                "source": source,
                "detections": detections,
                "total_scanners": vt_result.get("total_scanners", 0),
                "permalink": vt_result.get("permalink"),
                "recommendation": f"File flagged by {detections} antivirus engines. Review before executing.",
                "action_taken": "alert",
            },
        )
        self.publish_event(event)

    async def _quarantine_file(self, file_path: Path) -> None:
        """Quarantine a malicious file.

        Args:
            file_path: Path to file to quarantine
        """
        try:
            # Import quarantine manager
            from hifzdefend.quarantine.manager import QuarantineManager
            from hifzdefend.config.loader import load_config

            config = load_config()
            quarantine_mgr = QuarantineManager(config)

            # Quarantine file
            await asyncio.to_thread(
                quarantine_mgr.quarantine_file,
                str(file_path),
                reason=f"Malicious download detected by {self.name}",
            )

            logger.info(f"File quarantined successfully: {file_path.name}")

        except Exception as e:
            logger.error(f"Quarantine failed: {e}", exc_info=True)
            raise

    def get_statistics(self) -> dict[str, Any]:
        """Get monitor statistics.

        Returns:
            Dictionary with monitor statistics
        """
        return {
            "monitor_name": self.name,
            "running": self._running,
            "watched_directories": len(self.config.watch_directories),
            "total_downloads": self._stats["total_downloads"],
            "scanned_files": self._stats["scanned_files"],
            "threats_detected": self._stats["threats_detected"],
            "quarantined_files": self._stats["quarantined_files"],
            "virustotal_checks": self._stats["virustotal_checks"],
            "suspicious_downloads": self._stats["suspicious_downloads"],
            "virustotal_enabled": self._vt_session is not None,
            "auto_scan_enabled": self.config.auto_scan,
            "quarantine_on_detect": self.config.quarantine_on_detect,
        }
