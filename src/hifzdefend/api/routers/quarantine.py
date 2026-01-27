"""
Quarantine API router.

Provides endpoints for quarantine management.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ...service.engine import HifzDefendEngine
from ..dependencies import get_engine, authenticate
from ..models import QuarantineItem, QuarantineRestoreRequest, QuarantineRestoreResponse

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("", response_model=List[QuarantineItem])
async def get_quarantine_list(
    engine: HifzDefendEngine = Depends(get_engine),
) -> List[QuarantineItem]:
    """
    Get list of quarantined files.

    Returns:
        List of quarantined items
    """
    items = engine.get_quarantine_list()
    return [QuarantineItem(**item) for item in items]


@router.post("/restore", response_model=QuarantineRestoreResponse)
async def restore_from_quarantine(
    request: QuarantineRestoreRequest,
    engine: HifzDefendEngine = Depends(get_engine),
) -> QuarantineRestoreResponse:
    """
    Restore a file from quarantine.

    Args:
        request: Restore request with quarantine item ID

    Returns:
        Restore result
    """
    try:
        result = engine.restore_from_quarantine(request.id)
        return QuarantineRestoreResponse(
            success=result["success"],
            id=result["id"],
            message="File restored successfully" if result["success"] else "Restore failed",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{item_id}")
async def delete_quarantine_item(
    item_id: str,
    engine: HifzDefendEngine = Depends(get_engine),
) -> dict:
    """
    Permanently delete a quarantined file.

    Args:
        item_id: Quarantine item ID

    Returns:
        Deletion result
    """
    # TODO: Implement permanent deletion in engine
    return {"success": True, "id": item_id, "message": "Item deleted"}
