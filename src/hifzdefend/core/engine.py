"""
Scan engine orchestration and quarantine management.
"""

import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from .scanner import ClamAVScanner, ScanResult
from ..config.loader import HifzDefendConfig
from ..reporting.formatter import ScanReport
from ..utils.exceptions import QuarantineError, FileAccessError
from ..utils.helpers import calculate_file_hash


class QuarantineEntry:
    """Represents a quarantined file."""

    def __init__(
        self,
        quarantine_id: str,
        original_path: Path,
        quarantine_path: Path,
        threat_name: str,
        file_hash: str,
        quarantined_at: datetime,
    ):
        """Initialize quarantine entry."""
        self.quarantine_id = quarantine_id
        self.original_path = original_path
        self.quarantine_path = quarantine_path
        self.threat_name = threat_name
        self.file_hash = file_hash
        self.quarantined_at = quarantined_at

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "quarantine_id": self.quarantine_id,
            "original_path": str(self.original_path),
            "quarantine_path": str(self.quarantine_path),
            "threat_name": self.threat_name,
            "file_hash": self.file_hash,
            "quarantined_at": self.quarantined_at.isoformat(),
        }


class ScanEngine:
    """Main scan engine with quarantine functionality."""

    def __init__(self, config: HifzDefendConfig):
        """
        Initialize scan engine.

        Args:
            config: HifzDefend configuration
        """
        self.config = config
        self.scanner = ClamAVScanner(config.clamav)
        self.logger = logging.getLogger(__name__)

    def should_scan_file(self, file_path: Path) -> bool:
        """
        Check if file should be scanned based on configuration.

        Args:
            file_path: Path to file

        Returns:
            True if file should be scanned
        """
        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size > self.config.scanning.max_file_size:
                self.logger.debug(
                    f"Skipping {file_path}: exceeds max size "
                    f"({file_size} > {self.config.scanning.max_file_size})"
                )
                return False
        except OSError:
            return False

        # Check excluded paths
        file_str = str(file_path).lower()
        for excluded in self.config.scanning.excluded_paths:
            if file_str.startswith(excluded.lower()):
                self.logger.debug(f"Skipping {file_path}: in excluded path")
                return False

        # Check excluded extensions
        if file_path.suffix.lower() in self.config.scanning.excluded_extensions:
            self.logger.debug(f"Skipping {file_path}: excluded extension")
            return False

        return True

    def quarantine_file(
        self, file_path: Union[str, Path], threat_name: str
    ) -> QuarantineEntry:
        """
        Quarantine an infected file.

        Args:
            file_path: Path to infected file
            threat_name: Name of detected threat

        Returns:
            QuarantineEntry object

        Raises:
            QuarantineError: If quarantine fails
        """
        if not self.config.quarantine.enabled:
            raise QuarantineError("Quarantine is disabled in configuration")

        file_path = Path(file_path)

        if not file_path.exists():
            raise QuarantineError(f"File not found: {file_path}")

        try:
            # Generate quarantine ID
            quarantine_id = str(uuid.uuid4())

            # Calculate file hash before moving
            file_hash = calculate_file_hash(file_path)

            # Ensure quarantine directory exists
            quarantine_dir = self.config.quarantine.quarantine_dir_path
            quarantine_dir.mkdir(parents=True, exist_ok=True)

            # Create quarantine path with UUID
            quarantine_path = quarantine_dir / f"{quarantine_id}.quarantined"

            # Move file to quarantine
            shutil.move(str(file_path), str(quarantine_path))

            # Set read-only and remove execute permissions
            quarantine_path.chmod(0o444)

            self.logger.info(
                f"Quarantined {file_path} as {quarantine_id} "
                f"(threat: {threat_name})"
            )

            return QuarantineEntry(
                quarantine_id=quarantine_id,
                original_path=file_path,
                quarantine_path=quarantine_path,
                threat_name=threat_name,
                file_hash=file_hash,
                quarantined_at=datetime.now(),
            )

        except FileAccessError as e:
            raise QuarantineError(f"Failed to quarantine file: {e}")
        except Exception as e:
            raise QuarantineError(f"Quarantine error: {e}")

    def scan_path(
        self,
        path: Union[str, Path],
        report: Optional[ScanReport] = None,
    ) -> ScanReport:
        """
        Scan a file or directory.

        Args:
            path: Path to scan
            report: Optional existing report to update

        Returns:
            ScanReport object
        """
        path = Path(path)

        # Create report if not provided
        if report is None:
            scan_id = str(uuid.uuid4())[:8]
            report = ScanReport(scan_id, datetime.now())

        # Check if path exists
        if not path.exists():
            report.add_error(str(path), "Path not found")
            report.complete()
            return report

        # Scan file or directory
        if path.is_file():
            results = [self._scan_single_file(path)]
        elif path.is_dir():
            results = self._scan_directory(path)
        else:
            report.add_error(str(path), "Not a file or directory")
            report.complete()
            return report

        # Process results
        for result in results:
            if result.has_error:
                report.add_error(str(result.file_path), result.error)
            else:
                file_size = 0
                try:
                    file_size = result.file_path.stat().st_size
                except OSError:
                    pass

                report.add_scanned_file(str(result.file_path), file_size)

                if result.is_infected:
                    # Calculate file hash
                    try:
                        file_hash = calculate_file_hash(result.file_path)
                    except FileAccessError:
                        file_hash = None

                    # Auto-quarantine if enabled
                    quarantined = False
                    if self.config.quarantine.auto_quarantine:
                        try:
                            self.quarantine_file(
                                result.file_path, result.threat_name
                            )
                            quarantined = True
                        except QuarantineError as e:
                            self.logger.error(f"Auto-quarantine failed: {e}")

                    report.add_threat(
                        str(result.file_path),
                        result.threat_name,
                        file_hash=file_hash,
                        quarantined=quarantined,
                    )

        report.complete()
        return report

    def _scan_single_file(self, file_path: Path) -> ScanResult:
        """Scan a single file with filtering."""
        if not self.should_scan_file(file_path):
            return ScanResult(file_path, False)

        return self.scanner.scan_file(file_path)

    def _scan_directory(self, directory_path: Path) -> list[ScanResult]:
        """Scan directory with filtering."""
        results = []

        # Get files to scan
        if self.config.scanning.scan_recursively:
            files = list(directory_path.rglob("*"))
        else:
            files = list(directory_path.glob("*"))

        # Filter and scan files
        for file_path in files:
            if not file_path.is_file():
                continue

            if not self.should_scan_file(file_path):
                continue

            try:
                result = self.scanner.scan_file(file_path)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error scanning {file_path}: {e}")
                results.append(ScanResult(file_path, False, error=str(e)))

        return results

    def check_connection(self) -> bool:
        """
        Check connection to ClamAV daemon.

        Returns:
            True if connected, False otherwise
        """
        return self.scanner.ping()

    def get_version(self) -> Optional[str]:
        """
        Get ClamAV version.

        Returns:
            Version string or None
        """
        return self.scanner.get_version()

    def close(self) -> None:
        """Close scanner connection."""
        self.scanner.close()

    def __enter__(self) -> "ScanEngine":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
