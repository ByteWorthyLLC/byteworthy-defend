"""
Configuration API router.

Provides endpoints for configuration management.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ...service.engine import HifzDefendEngine
from ..dependencies import get_engine, authenticate
from ..models import ConfigUpdateRequest, ConfigUpdateResponse

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("", response_model=Dict[str, Any])
async def get_config(
    engine: HifzDefendEngine = Depends(get_engine),
) -> Dict[str, Any]:
    """
    Get current configuration.

    Returns:
        Current configuration dictionary
    """
    # Convert config to dictionary
    config = engine.config
    return {
        "clamav": {
            "host": config.clamav.host,
            "port": config.clamav.port,
            "timeout": config.clamav.timeout,
        },
        "scanning": {
            "max_file_size": config.scanning.max_file_size,
            "scan_archives": config.scanning.scan_archives,
            "scan_recursively": config.scanning.scan_recursively,
        },
        "monitoring": {
            "enabled": config.monitoring.enabled,
            "watch_paths": config.monitoring.watch_paths,
        },
        "quarantine": {
            "enabled": config.quarantine.enabled,
            "auto_quarantine": config.quarantine.auto_quarantine,
        },
    }


@router.put("", response_model=ConfigUpdateResponse)
async def update_config(
    request: ConfigUpdateRequest,
    engine: HifzDefendEngine = Depends(get_engine),
) -> ConfigUpdateResponse:
    """
    Update configuration.

    Args:
        request: Configuration update request

    Returns:
        Update result
    """
    try:
        result = engine.update_config(request.section, request.updates)
        return ConfigUpdateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exclusions")
async def get_exclusions(
    engine: HifzDefendEngine = Depends(get_engine),
) -> Dict[str, Any]:
    """
    Get scanning exclusions.

    Returns:
        Exclusions configuration
    """
    config = engine.config
    return {
        "excluded_paths": config.scanning.excluded_paths,
        "excluded_extensions": config.scanning.excluded_extensions,
    }


@router.post("/exclusions/paths")
async def add_excluded_path(
    path: str,
    engine: HifzDefendEngine = Depends(get_engine),
) -> Dict[str, Any]:
    """
    Add a path to exclusions.

    Args:
        path: Path to exclude from scans

    Returns:
        Updated exclusions
    """
    # TODO: Implement path exclusion management
    return {"success": True, "path": path}
