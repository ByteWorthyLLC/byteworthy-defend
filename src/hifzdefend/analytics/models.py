"""Analytics data models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Analytics event types."""

    # Application events
    APP_STARTED = "app_started"
    APP_STOPPED = "app_stopped"
    APP_UPDATED = "app_updated"

    # Scan events
    SCAN_STARTED = "scan_started"
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"
    THREAT_DETECTED = "threat_detected"

    # Protection events
    REALTIME_ENABLED = "realtime_enabled"
    REALTIME_DISABLED = "realtime_disabled"
    FILE_BLOCKED = "file_blocked"
    FILE_QUARANTINED = "file_quarantined"

    # AI events
    AI_ANALYSIS = "ai_analysis"
    AI_QUERY = "ai_query"

    # User events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    LICENSE_ACTIVATED = "license_activated"
    PURCHASE_COMPLETED = "purchase_completed"

    # Feature usage
    FEATURE_USED = "feature_used"
    SETTING_CHANGED = "setting_changed"


class AnalyticsEvent(BaseModel):
    """Analytics event."""

    event_type: EventType = Field(..., description="Event type")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Event properties
    properties: dict = Field(default_factory=dict, description="Event properties")

    # User context (anonymized)
    user_id: Optional[str] = Field(None, description="Anonymized user ID")
    session_id: Optional[str] = Field(None, description="Session ID")

    # System context
    app_version: str = Field(default="0.3.0")
    os_version: Optional[str] = Field(None)
    license_type: Optional[str] = Field(None)


class AnalyticsSettings(BaseModel):
    """Analytics settings."""

    enabled: bool = Field(default=True, description="Enable analytics")
    anonymize: bool = Field(default=True, description="Anonymize user data")
    send_crash_reports: bool = Field(default=True, description="Send crash reports")
    send_usage_stats: bool = Field(default=True, description="Send usage statistics")
    send_performance_data: bool = Field(default=False, description="Send performance data")


class UsageStats(BaseModel):
    """Usage statistics."""

    total_scans: int = Field(default=0)
    threats_detected: int = Field(default=0)
    files_quarantined: int = Field(default=0)
    ai_analyses: int = Field(default=0)
    uptime_hours: float = Field(default=0.0)
    last_scan: Optional[datetime] = None
    realtime_enabled: bool = Field(default=False)
