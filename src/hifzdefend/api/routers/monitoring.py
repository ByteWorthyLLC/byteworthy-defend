"""
Monitoring API router.

Provides endpoints for monitor management and status.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ...service.engine import HifzDefendEngine
from ..dependencies import get_engine, authenticate
from ..models import (
    MonitorStatus,
    MonitorToggleRequest,
    MonitorToggleResponse,
    MonitorHealthResponse,
    MonitorActionResponse,
)

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("", response_model=List[MonitorStatus])
async def get_monitors(
    engine: HifzDefendEngine = Depends(get_engine),
) -> List[MonitorStatus]:
    """
    Get status of all monitors.

    Returns:
        List of monitor statuses
    """
    monitors = engine.get_monitors_status()
    return [MonitorStatus(**m) for m in monitors]


@router.get("/{monitor_id}", response_model=MonitorStatus)
async def get_monitor(
    monitor_id: str,
    engine: HifzDefendEngine = Depends(get_engine),
) -> MonitorStatus:
    """
    Get status of a specific monitor.

    Args:
        monitor_id: Monitor identifier

    Returns:
        Monitor status
    """
    monitor = engine.state.get_monitor_state(monitor_id)
    if monitor is None:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return MonitorStatus(
        id=monitor.id,
        name=monitor.name,
        status=monitor.status.value,
        enabled=monitor.enabled,
        event_count=monitor.event_count,
        last_event=monitor.last_event,
        error_message=monitor.error_message,
    )


@router.post("/{monitor_id}/toggle", response_model=MonitorToggleResponse)
async def toggle_monitor(
    monitor_id: str,
    request: MonitorToggleRequest,
    engine: HifzDefendEngine = Depends(get_engine),
) -> MonitorToggleResponse:
    """
    Enable or disable a monitor.

    Args:
        monitor_id: Monitor identifier
        request: Toggle request with enabled state

    Returns:
        Updated monitor status
    """
    try:
        result = engine.toggle_monitor(monitor_id, request.enabled)
        return MonitorToggleResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{monitor_id}/pause", response_model=MonitorActionResponse)
async def pause_monitor(
    monitor_id: str,
    engine: HifzDefendEngine = Depends(get_engine),
) -> MonitorActionResponse:
    """
    Pause a monitor (stops checks but keeps it running).

    Args:
        monitor_id: Monitor identifier

    Returns:
        Updated monitor status
    """
    try:
        result = engine.pause_monitor(monitor_id)
        return MonitorActionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{monitor_id}/resume", response_model=MonitorActionResponse)
async def resume_monitor(
    monitor_id: str,
    engine: HifzDefendEngine = Depends(get_engine),
) -> MonitorActionResponse:
    """
    Resume a paused monitor.

    Args:
        monitor_id: Monitor identifier

    Returns:
        Updated monitor status
    """
    try:
        result = engine.resume_monitor(monitor_id)
        return MonitorActionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{monitor_id}/restart", response_model=MonitorActionResponse)
async def restart_monitor(
    monitor_id: str,
    engine: HifzDefendEngine = Depends(get_engine),
) -> MonitorActionResponse:
    """
    Restart a monitor (stop then start).

    Args:
        monitor_id: Monitor identifier

    Returns:
        Updated monitor status
    """
    try:
        result = engine.restart_monitor(monitor_id)
        return MonitorActionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=MonitorHealthResponse)
async def get_monitor_health(
    engine: HifzDefendEngine = Depends(get_engine),
) -> MonitorHealthResponse:
    """
    Get health status of all monitors.

    Returns:
        Health check results
    """
    health = engine.get_monitor_health()
    return MonitorHealthResponse(**health)
