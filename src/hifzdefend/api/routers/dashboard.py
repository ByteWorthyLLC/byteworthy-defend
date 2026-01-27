"""
Dashboard API router.

Provides endpoints for dashboard statistics and overview data.
"""

from fastapi import APIRouter, Depends
from typing import List

from ...service.engine import HifzDefendEngine
from ..dependencies import get_engine, authenticate
from ..models import DashboardStats, ScanHistoryItem, ThreatInfo, ResourceUsage

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    engine: HifzDefendEngine = Depends(get_engine),
) -> DashboardStats:
    """
    Get dashboard statistics.

    Returns comprehensive statistics for the dashboard including:
    - Protection status
    - Monitor states
    - Threat counts
    - Recent scans and threats
    - System resource usage
    """
    status = engine.get_system_status()
    recent_scans = engine.get_scan_history(limit=5)
    recent_threats = engine.get_recent_threats(limit=5)

    return DashboardStats(
        protection_enabled=(status["protection_status"] == "enabled"),
        monitors_active=status["monitors"]["active"],
        monitors_total=status["monitors"]["total"],
        threats_today=status["threats"]["today"],
        threats_week=status["threats"]["week"],
        threats_total=status["threats"]["total"],
        recent_scans=[ScanHistoryItem(**scan) for scan in recent_scans],
        recent_threats=[ThreatInfo(**threat) for threat in recent_threats],
        system_resources=ResourceUsage(
            cpu_usage=status["resources"]["cpu_usage"],
            memory_usage=status["resources"]["memory_usage"],
        ),
    )
