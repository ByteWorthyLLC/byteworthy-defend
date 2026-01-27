"""Scan management API endpoints."""

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from ..models import ScanListResponse, ScanRequest, ScanResponse, ScanStatus
from ..storage import scan_storage
from ...core.scanner import ClamAVScanner
from ...config.loader import load_config

router = APIRouter(prefix="/scans", tags=["scans"])

# Active scans tracking
active_scans = {}


async def run_scan_task(scan_id: str, path: str):
    """Background task to run scan."""
    try:
        # Update status to running
        scan_storage.update_scan(
            scan_id,
            status=ScanStatus.RUNNING.value
        )

        # Load config and create scanner
        config = load_config()
        scanner = ClamAVScanner(
            host=config.clamav.host,
            port=config.clamav.port,
            timeout=config.clamav.timeout
        )

        # Run scan
        start_time = datetime.now()
        result = scanner.scan_path(path)
        end_time = datetime.now()

        duration = (end_time - start_time).total_seconds()

        # Extract threats
        threats = []
        for file_path, scan_result in result.items():
            if scan_result["status"] == "FOUND":
                threats.append({
                    "file": file_path,
                    "threat": scan_result.get("threat", "Unknown")
                })

        # Update scan with results
        scan_storage.update_scan(
            scan_id,
            status=ScanStatus.COMPLETED.value,
            threats_found=len(threats),
            files_scanned=len(result),
            end_time=end_time.isoformat(),
            duration_seconds=duration,
            threats=threats
        )

    except Exception as e:
        # Mark as failed
        scan_storage.update_scan(
            scan_id,
            status=ScanStatus.FAILED.value,
            end_time=datetime.now().isoformat()
        )
        raise

    finally:
        # Remove from active scans
        if scan_id in active_scans:
            del active_scans[scan_id]


@router.post("", response_model=ScanResponse, status_code=201)
async def create_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks
):
    """Start a new scan."""
    # Create scan entry
    scan_id = scan_storage.create_scan(request.path)

    # Add to active scans
    active_scans[scan_id] = {"path": request.path, "task": None}

    # Start background scan
    background_tasks.add_task(run_scan_task, scan_id, request.path)

    # Return initial scan response
    scan_data = scan_storage.get_scan(scan_id)
    return ScanResponse(**scan_data)


@router.get("", response_model=ScanListResponse)
async def list_scans(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """List all scans with pagination."""
    skip = (page - 1) * page_size
    scans, total = scan_storage.list_scans(skip=skip, limit=page_size)

    return ScanListResponse(
        scans=[ScanResponse(**scan) for scan in scans],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str):
    """Get scan details and results."""
    scan_data = scan_storage.get_scan(scan_id)

    if not scan_data:
        raise HTTPException(status_code=404, detail="Scan not found")

    return ScanResponse(**scan_data)


@router.delete("/{scan_id}", status_code=204)
async def cancel_scan(scan_id: str):
    """Cancel a running scan."""
    scan_data = scan_storage.get_scan(scan_id)

    if not scan_data:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan_data["status"] not in [ScanStatus.PENDING.value, ScanStatus.RUNNING.value]:
        raise HTTPException(status_code=400, detail="Scan is not running")

    # Update status to cancelled
    scan_storage.update_scan(
        scan_id,
        status=ScanStatus.CANCELLED.value,
        end_time=datetime.now().isoformat()
    )

    # Remove from active scans
    if scan_id in active_scans:
        del active_scans[scan_id]

    return None
