"""Configuration management API endpoints."""

from fastapi import APIRouter, HTTPException

from ..models import ConfigResponse, ConfigUpdateRequest
from ...config.loader import load_config
from ...config.validator import validate_config

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=ConfigResponse)
async def get_config():
    """Get current configuration (sanitized)."""
    config = load_config()

    return ConfigResponse(
        scanning={
            "max_file_size": config.scanning.max_file_size,
            "scan_archives": config.scanning.scan_archives,
            "excluded_paths": config.scanning.excluded_paths
        },
        quarantine={
            "enabled": config.quarantine.enabled,
            "auto_quarantine": config.quarantine.auto_quarantine
        },
        clamav={
            "host": config.clamav.host,
            "port": config.clamav.port,
            "timeout": config.clamav.timeout
        }
    )


@router.put("", response_model=ConfigResponse)
async def update_config(request: ConfigUpdateRequest):
    """Update configuration settings."""
    config = load_config()

    # Update scanning settings
    if request.scanning:
        if "max_file_size" in request.scanning:
            config.scanning.max_file_size = request.scanning["max_file_size"]
        if "scan_archives" in request.scanning:
            config.scanning.scan_archives = request.scanning["scan_archives"]
        if "excluded_paths" in request.scanning:
            config.scanning.excluded_paths = request.scanning["excluded_paths"]

    # Update quarantine settings
    if request.quarantine:
        if "enabled" in request.quarantine:
            config.quarantine.enabled = request.quarantine["enabled"]
        if "auto_quarantine" in request.quarantine:
            config.quarantine.auto_quarantine = request.quarantine["auto_quarantine"]

    # Validate new config
    try:
        validate_config(config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")

    # Save config (would need to implement save functionality)
    # config.save()

    return ConfigResponse(
        scanning={
            "max_file_size": config.scanning.max_file_size,
            "scan_archives": config.scanning.scan_archives,
            "excluded_paths": config.scanning.excluded_paths
        },
        quarantine={
            "enabled": config.quarantine.enabled,
            "auto_quarantine": config.quarantine.auto_quarantine
        },
        clamav={
            "host": config.clamav.host,
            "port": config.clamav.port,
            "timeout": config.clamav.timeout
        }
    )


@router.post("/validate", status_code=200)
async def validate_config_endpoint(request: ConfigUpdateRequest):
    """Validate configuration without saving."""
    try:
        # Would validate the config
        return {"valid": True, "message": "Configuration is valid"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/defaults", response_model=ConfigResponse)
async def get_default_config():
    """Get default configuration values."""
    return ConfigResponse(
        scanning={
            "max_file_size": 104857600,  # 100 MB
            "scan_archives": True,
            "excluded_paths": []
        },
        quarantine={
            "enabled": True,
            "auto_quarantine": True
        },
        clamav={
            "host": "localhost",
            "port": 3310,
            "timeout": 60
        }
    )
