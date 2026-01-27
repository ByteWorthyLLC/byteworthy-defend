"""License data models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class LicenseType(str, Enum):
    """License types."""

    TRIAL = "trial"
    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class LicenseStatus(str, Enum):
    """License status."""

    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class License(BaseModel):
    """License model."""

    license_key: str = Field(..., description="License key")
    license_type: LicenseType = Field(..., description="License type")
    status: LicenseStatus = Field(default=LicenseStatus.ACTIVE)

    # Customer information
    customer_email: str = Field(..., description="Customer email")
    customer_name: Optional[str] = Field(None, description="Customer name")
    company_name: Optional[str] = Field(None, description="Company name")

    # Dates
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    activated_at: Optional[datetime] = Field(None, description="First activation date")

    # Hardware binding
    hardware_id: Optional[str] = Field(None, description="Bound hardware ID")
    max_activations: int = Field(default=1, description="Maximum concurrent activations")
    activation_count: int = Field(default=0, description="Current activation count")

    # Features
    max_scans_per_day: Optional[int] = Field(None, description="Daily scan limit")
    ai_enabled: bool = Field(default=True, description="AI analysis enabled")
    real_time_protection: bool = Field(default=True, description="Real-time protection")
    cloud_backup: bool = Field(default=False, description="Cloud quarantine backup")
    priority_support: bool = Field(default=False, description="Priority support access")

    # Metadata
    notes: Optional[str] = Field(None, description="Internal notes")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    class Config:
        """Pydantic config."""

        use_enum_values = True


class LicenseActivation(BaseModel):
    """License activation request."""

    license_key: str = Field(..., description="License key to activate")
    hardware_id: str = Field(..., description="Hardware fingerprint")
    device_name: Optional[str] = Field(None, description="Device name")


class LicenseValidation(BaseModel):
    """License validation response."""

    valid: bool = Field(..., description="Whether license is valid")
    license: Optional[License] = Field(None, description="License details if valid")
    error: Optional[str] = Field(None, description="Error message if invalid")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
