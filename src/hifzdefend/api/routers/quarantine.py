"""Quarantine management API endpoints."""

import os
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Query

from ..models import QuarantineFile, QuarantineListResponse

router = APIRouter(prefix="/quarantine", tags=["quarantine"])


def get_quarantine_dir() -> Path:
    """Get quarantine directory path."""
    return Path.home() / "AppData" / "Local" / "HifzDefend" / "quarantine"


def list_quarantined_files() -> List[QuarantineFile]:
    """List all quarantined files."""
    quarantine_dir = get_quarantine_dir()

    if not quarantine_dir.exists():
        return []

    files = []

    for file_path in quarantine_dir.rglob("*"):
        if file_path.is_file():
            # Parse metadata from filename or metadata file
            # Format: original_hash_threatname.quarantine
            file_id = file_path.stem

            stat = file_path.stat()

            files.append(QuarantineFile(
                file_id=file_id,
                original_path=str(file_path),  # Would store original path separately
                quarantine_path=str(file_path),
                threat_name="Unknown",  # Would parse from metadata
                quarantine_date=datetime.fromtimestamp(stat.st_ctime),
                file_size=stat.st_size
            ))

    return files


@router.get("", response_model=QuarantineListResponse)
async def list_quarantine(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """List all quarantined files with pagination."""
    files = list_quarantined_files()

    # Sort by quarantine date descending
    files.sort(key=lambda x: x.quarantine_date, reverse=True)

    total = len(files)
    skip = (page - 1) * page_size
    paginated = files[skip:skip + page_size]

    return QuarantineListResponse(
        files=paginated,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{file_id}", response_model=QuarantineFile)
async def get_quarantine_file(file_id: str):
    """Get quarantine file details."""
    files = list_quarantined_files()

    for file in files:
        if file.file_id == file_id:
            return file

    raise HTTPException(status_code=404, detail="Quarantined file not found")


@router.post("/{file_id}/restore", status_code=200)
async def restore_file(file_id: str):
    """Restore file to original location."""
    files = list_quarantined_files()

    file_to_restore = None
    for file in files:
        if file.file_id == file_id:
            file_to_restore = file
            break

    if not file_to_restore:
        raise HTTPException(status_code=404, detail="Quarantined file not found")

    # TODO: Implement actual restore logic
    # Would need to store original path metadata and restore to that location

    return {"message": "File restore not yet implemented", "file_id": file_id}


@router.delete("/{file_id}", status_code=204)
async def delete_quarantine_file(file_id: str):
    """Permanently delete quarantined file."""
    files = list_quarantined_files()

    file_to_delete = None
    for file in files:
        if file.file_id == file_id:
            file_to_delete = file
            break

    if not file_to_delete:
        raise HTTPException(status_code=404, detail="Quarantined file not found")

    # Delete the file
    try:
        os.remove(file_to_delete.quarantine_path)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

    return None
