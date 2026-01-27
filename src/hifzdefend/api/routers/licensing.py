"""License management API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr

from ...licensing import LicenseManager, LicenseActivation
from ...licensing.hardware import HardwareFingerprint
from ..dependencies import get_license_manager

router = APIRouter(prefix="/licensing", tags=["licensing"])


class ActivateRequest(BaseModel):
    """License activation request."""

    license_key: str


class LicenseInfoResponse(BaseModel):
    """License information response."""

    status: str
    license_type: str | None = None
    customer_email: str | None = None
    expires_at: str | None = None
    features: dict | None = None
    error: str | None = None
    warnings: list[str] = []


@router.get("/info", response_model=LicenseInfoResponse)
async def get_license_info(manager: LicenseManager = Depends(get_license_manager)) -> LicenseInfoResponse:
    """Get current license information."""
    info = manager.get_license_info()
    return LicenseInfoResponse(**info)


@router.post("/activate")
async def activate_license(
    request: ActivateRequest,
    manager: LicenseManager = Depends(get_license_manager)
) -> dict:
    """Activate a license key.

    Args:
        request: Activation request
        manager: License manager

    Returns:
        Activation result
    """
    # Get hardware fingerprint
    hardware_id = HardwareFingerprint.get_fingerprint()
    device_name = HardwareFingerprint.get_device_name()

    activation = LicenseActivation(
        license_key=request.license_key,
        hardware_id=hardware_id,
        device_name=device_name
    )

    validation = manager.activate_license(activation)

    if not validation.valid:
        raise HTTPException(
            status_code=400,
            detail=validation.error or "License activation failed"
        )

    return {
        "success": True,
        "message": "License activated successfully",
        "license_type": validation.license.license_type,
        "expires_at": validation.license.expires_at.isoformat() if validation.license.expires_at else None,
        "warnings": validation.warnings,
    }


@router.post("/deactivate")
async def deactivate_license(manager: LicenseManager = Depends(get_license_manager)) -> dict:
    """Deactivate current license."""
    success = manager.deactivate_license()

    if not success:
        raise HTTPException(status_code=404, detail="No active license to deactivate")

    return {
        "success": True,
        "message": "License deactivated successfully"
    }


@router.get("/hardware-id")
async def get_hardware_id() -> dict:
    """Get hardware fingerprint for this device."""
    return {
        "hardware_id": HardwareFingerprint.get_fingerprint(),
        "device_name": HardwareFingerprint.get_device_name(),
    }


@router.get("/check")
async def check_license(manager: LicenseManager = Depends(get_license_manager)) -> dict:
    """Quick license validity check."""
    is_valid = manager.is_licensed()

    return {
        "valid": is_valid,
        "status": "active" if is_valid else "unlicensed",
    }
