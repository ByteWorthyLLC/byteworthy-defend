"""
Report generation and formatting.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..config.loader import ReportingConfig


class ScanReport:
    """Represents a scan report."""

    def __init__(self, scan_id: str, start_time: datetime):
        """
        Initialize scan report.

        Args:
            scan_id: Unique scan identifier
            start_time: Scan start time
        """
        self.scan_id = scan_id
        self.start_time = start_time
        self.end_time: Optional[datetime] = None
        self.scanned_files: list[str] = []
        self.threats_found: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.total_size: int = 0

    def add_scanned_file(self, file_path: str, file_size: int = 0) -> None:
        """Add a scanned file to the report."""
        self.scanned_files.append(file_path)
        self.total_size += file_size

    def add_threat(
        self,
        file_path: str,
        threat_name: str,
        file_hash: Optional[str] = None,
        quarantined: bool = False,
    ) -> None:
        """Add a detected threat to the report."""
        self.threats_found.append(
            {
                "file_path": file_path,
                "threat_name": threat_name,
                "file_hash": file_hash,
                "quarantined": quarantined,
                "detected_at": datetime.now().isoformat(),
            }
        )

    def add_error(self, file_path: str, error_message: str) -> None:
        """Add an error to the report."""
        self.errors.append({"file_path": file_path, "error": error_message})

    def complete(self) -> None:
        """Mark scan as complete."""
        self.end_time = datetime.now()

    @property
    def duration(self) -> float:
        """Get scan duration in seconds."""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    @property
    def files_scanned(self) -> int:
        """Get number of files scanned."""
        return len(self.scanned_files)

    @property
    def threats_count(self) -> int:
        """Get number of threats found."""
        return len(self.threats_found)

    @property
    def has_threats(self) -> bool:
        """Check if any threats were found."""
        return self.threats_count > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "scan_id": self.scan_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration,
            "files_scanned": self.files_scanned,
            "total_size_bytes": self.total_size,
            "threats_found": self.threats_count,
            "threats": self.threats_found,
            "errors": self.errors,
            "scanned_files": self.scanned_files,
        }

    def to_json(self) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def to_text(self) -> str:
        """Convert report to human-readable text."""
        lines = [
            "=" * 60,
            "HifzDefend Scan Report",
            "=" * 60,
            f"Scan ID: {self.scan_id}",
            f"Start Time: {self.start_time}",
            f"End Time: {self.end_time or 'In Progress'}",
            f"Duration: {self.duration:.2f} seconds",
            f"Files Scanned: {self.files_scanned}",
            f"Total Size: {self._format_size(self.total_size)}",
            f"Threats Found: {self.threats_count}",
            "",
        ]

        if self.has_threats:
            lines.append("THREATS DETECTED:")
            lines.append("-" * 60)
            for threat in self.threats_found:
                lines.append(f"File: {threat['file_path']}")
                lines.append(f"Threat: {threat['threat_name']}")
                if threat.get("file_hash"):
                    lines.append(f"Hash: {threat['file_hash']}")
                lines.append(f"Quarantined: {'Yes' if threat['quarantined'] else 'No'}")
                lines.append("")
        else:
            lines.append("No threats detected.")
            lines.append("")

        if self.errors:
            lines.append("ERRORS:")
            lines.append("-" * 60)
            for error in self.errors:
                lines.append(f"File: {error['file_path']}")
                lines.append(f"Error: {error['error']}")
                lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


def save_report(report: ScanReport, config: ReportingConfig) -> Path:
    """
    Save scan report to file.

    Args:
        report: Scan report to save
        config: Reporting configuration

    Returns:
        Path to saved report file
    """
    # Ensure report directory exists
    report_dir = config.report_dir_path
    report_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scan_report_{timestamp}_{report.scan_id}.{config.report_format}"
    report_path = report_dir / filename

    # Save report based on format
    if config.report_format == "json":
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report.to_json())
    elif config.report_format == "text":
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report.to_text())
    elif config.report_format == "html":
        # HTML format can be implemented later
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report.to_text())

    return report_path
