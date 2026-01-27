"""Dashboard statistics API endpoints."""

from datetime import datetime
from typing import List

from fastapi import APIRouter

from ..models import RecentScan, ScanStatus, StatsOverview, SystemStatus, ThreatTimelinePoint
from ..storage import scan_storage
from ...core.scanner import ClamAVScanner
from ...config.loader import load_config

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=StatsOverview)
async def get_overview():
    """Get dashboard overview statistics."""
    stats = scan_storage.get_stats()

    # Check ClamAV status
    try:
        config = load_config()
        scanner = ClamAVScanner(
            host=config.clamav.host,
            port=config.clamav.port,
            timeout=5
        )
        scanner.ping()
        system_status = "online"
    except:
        system_status = "offline"

    # Get quarantine count (simplified - would integrate with actual quarantine)
    files_quarantined = 0

    return StatsOverview(
        total_scans=stats["total_scans"],
        threats_found=stats["threats_found"],
        files_quarantined=files_quarantined,
        system_status=system_status,
        last_update=datetime.now()
    )


@router.get("/recent-scans", response_model=List[RecentScan])
async def get_recent_scans(limit: int = 10):
    """Get recent scans."""
    scans = scan_storage.get_recent_scans(limit=limit)

    return [
        RecentScan(
            scan_id=scan["scan_id"],
            path=scan["path"],
            status=ScanStatus(scan["status"]),
            threats_found=scan["threats_found"],
            timestamp=datetime.fromisoformat(scan["start_time"])
        )
        for scan in scans
    ]


@router.get("/threats-timeline", response_model=List[ThreatTimelinePoint])
async def get_threats_timeline(days: int = 7):
    """Get threats detected over time."""
    timeline = scan_storage.get_threats_timeline(days=days)

    return [ThreatTimelinePoint(**point) for point in timeline]


@router.get("/system-status", response_model=SystemStatus)
async def get_system_status():
    """Get ClamAV system status."""
    try:
        config = load_config()
        scanner = ClamAVScanner(
            host=config.clamav.host,
            port=config.clamav.port,
            timeout=5
        )

        # Ping ClamAV
        scanner.ping()

        # Get version
        version = scanner.get_version()

        return SystemStatus(
            clamav_online=True,
            clamav_version=version,
            definitions_version=None,  # Would need to parse from ClamAV
            last_update=datetime.now()
        )
    except Exception as e:
        return SystemStatus(
            clamav_online=False,
            clamav_version=None,
            definitions_version=None,
            last_update=None
        )
