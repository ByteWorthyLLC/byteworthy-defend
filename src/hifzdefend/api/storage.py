"""Scan history storage using JSON file."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import ScanResponse, ScanStatus


class ScanStorage:
    """Manages scan history storage."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize storage."""
        if storage_path is None:
            storage_path = Path.home() / "AppData" / "Local" / "HifzDefend" / "scans.json"

        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize file if it doesn't exist
        if not self.storage_path.exists():
            self._write_data({"scans": {}})

    def _read_data(self) -> dict:
        """Read data from storage file."""
        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"scans": {}}

    def _write_data(self, data: dict) -> None:
        """Write data to storage file."""
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def create_scan(self, path: str) -> str:
        """Create a new scan entry."""
        scan_id = str(uuid.uuid4())
        data = self._read_data()

        data["scans"][scan_id] = {
            "scan_id": scan_id,
            "status": ScanStatus.PENDING.value,
            "path": path,
            "threats_found": 0,
            "files_scanned": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "threats": []
        }

        self._write_data(data)
        return scan_id

    def update_scan(self, scan_id: str, **kwargs) -> None:
        """Update scan with new data."""
        data = self._read_data()

        if scan_id in data["scans"]:
            data["scans"][scan_id].update(kwargs)
            self._write_data(data)

    def get_scan(self, scan_id: str) -> Optional[Dict]:
        """Get scan by ID."""
        data = self._read_data()
        return data["scans"].get(scan_id)

    def list_scans(self, skip: int = 0, limit: int = 10) -> tuple[List[Dict], int]:
        """List scans with pagination."""
        data = self._read_data()
        scans = list(data["scans"].values())

        # Sort by start_time descending
        scans.sort(key=lambda x: x["start_time"], reverse=True)

        total = len(scans)
        paginated = scans[skip:skip + limit]

        return paginated, total

    def get_recent_scans(self, limit: int = 10) -> List[Dict]:
        """Get recent scans."""
        scans, _ = self.list_scans(skip=0, limit=limit)
        return scans

    def get_threats_timeline(self, days: int = 7) -> List[Dict]:
        """Get threats detected over time."""
        data = self._read_data()
        scans = data["scans"].values()

        # Group by date
        threats_by_date: Dict[str, int] = {}

        for scan in scans:
            start_time = datetime.fromisoformat(scan["start_time"])
            date_key = start_time.strftime("%Y-%m-%d")

            if date_key not in threats_by_date:
                threats_by_date[date_key] = 0

            threats_by_date[date_key] += scan["threats_found"]

        # Convert to list format
        timeline = [
            {"date": date, "threats": count}
            for date, count in sorted(threats_by_date.items())
        ]

        # Return last N days
        return timeline[-days:]

    def get_stats(self) -> Dict:
        """Get overall statistics."""
        data = self._read_data()
        scans = data["scans"].values()

        total_scans = len(scans)
        threats_found = sum(scan["threats_found"] for scan in scans)

        return {
            "total_scans": total_scans,
            "threats_found": threats_found
        }


# Global storage instance
scan_storage = ScanStorage()
