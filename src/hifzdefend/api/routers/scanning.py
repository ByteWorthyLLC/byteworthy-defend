"""
Scanning API router.

Provides endpoints for triggering scans and retrieving scan history.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ...service.engine import HifzDefendEngine
from ..dependencies import get_engine, authenticate
from ..models import ScanRequest, ScanResponse, ScanHistoryItem

router = APIRouter(dependencies=[Depends(authenticate)])


@router.post("", response_model=ScanResponse)
async def trigger_scan(
    request: ScanRequest,
    engine: HifzDefendEngine = Depends(get_engine),
) -> ScanResponse:
    """
    Trigger a new scan.

    Args:
        request: Scan request with path and options

    Returns:
        Scan results
    """
    try:
        result = engine.scan_path(
            path=request.path,
            recursive=request.recursive,
        )
        return ScanResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[ScanHistoryItem])
async def get_scan_history(
    limit: int = 20,
    engine: HifzDefendEngine = Depends(get_engine),
) -> List[ScanHistoryItem]:
    """
    Get scan history.

    Args:
        limit: Maximum number of scans to return

    Returns:
        List of historical scan results
    """
    history = engine.get_scan_history(limit=limit)
    return [ScanHistoryItem(**item) for item in history]


@router.get("/active", response_model=List[ScanResponse])
async def get_active_scans(
    engine: HifzDefendEngine = Depends(get_engine),
) -> List[ScanResponse]:
    """
    Get currently active scans.

    Returns:
        List of active scan operations
    """
    active = engine.state.get_active_scans()
    return [
        ScanResponse(
            scan_id=scan.id,
            path=scan.path,
            files_scanned=scan.files_scanned,
            threats_found=scan.threats_found,
            threats=[],
            status=scan.status,
        )
        for scan in active
    ]
