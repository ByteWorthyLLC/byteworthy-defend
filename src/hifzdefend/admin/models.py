"""Pydantic models for admin operations."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AdminActionType(str, Enum):
    """Admin action type enum."""

    LICENSE_CREATED = "license_created"
    LICENSE_REVOKED = "license_revoked"
    LICENSE_EXTENDED = "license_extended"
    TICKET_ASSIGNED = "ticket_assigned"
    TICKET_CLOSED = "ticket_closed"
    TICKET_STATUS_CHANGED = "ticket_status_changed"
    TICKET_PRIORITY_CHANGED = "ticket_priority_changed"
    USER_CREATED = "user_created"
    USER_DISABLED = "user_disabled"


class AdminAction(BaseModel):
    """Admin action log entry."""

    id: int
    admin_id: str
    action: AdminActionType
    resource_type: str
    resource_id: str
    details: Optional[Dict] = None
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class LicenseExtend(BaseModel):
    """Extend license expiration."""

    days: int = Field(..., ge=1, le=3650, description="Number of days to extend")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for extension")


class LicenseRevoke(BaseModel):
    """Revoke a license."""

    reason: str = Field(..., min_length=10, max_length=500, description="Reason for revocation")


class TicketAssignment(BaseModel):
    """Assign ticket to agent."""

    agent_id: str = Field(..., description="Agent user ID")


class AdminStats(BaseModel):
    """Admin dashboard statistics."""

    total_customers: int = 0
    total_licenses: int = 0
    active_subscriptions: int = 0
    mrr: float = 0.0  # Monthly Recurring Revenue
    arr: float = 0.0  # Annual Recurring Revenue
    trial_conversion_rate: float = 0.0  # Percentage (0-100)
    open_tickets_count: int = 0
    tickets_by_priority: Dict[str, int] = {}
    recent_signups_7d: int = 0
    recent_purchases_7d: int = 0
    recent_revenue_7d: float = 0.0

    model_config = {
        "from_attributes": True,
    }


class RecentSignup(BaseModel):
    """Recent signup entry."""

    email: str
    full_name: Optional[str]
    license_type: str
    created_at: datetime


class RecentPurchase(BaseModel):
    """Recent purchase entry."""

    email: str
    license_type: str
    amount: float
    created_at: datetime
