"""Pydantic models for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ScanStatus(str, Enum):
    """Scan status enum."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanRequest(BaseModel):
    """Request to start a new scan."""

    path: str = Field(..., description="File or directory path to scan")


class ScanResponse(BaseModel):
    """Scan result response."""

    scan_id: str
    status: ScanStatus
    path: str
    threats_found: int = 0
    files_scanned: int = 0
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    threats: List[dict] = Field(default_factory=list)


class ScanListResponse(BaseModel):
    """Paginated list of scans."""

    scans: List[ScanResponse]
    total: int
    page: int
    page_size: int


class StatsOverview(BaseModel):
    """Dashboard overview statistics."""

    total_scans: int
    threats_found: int
    files_quarantined: int
    system_status: str  # "online" or "offline"
    last_update: Optional[datetime] = None


class RecentScan(BaseModel):
    """Recent scan summary."""

    scan_id: str
    path: str
    status: ScanStatus
    threats_found: int
    timestamp: datetime


class ThreatTimelinePoint(BaseModel):
    """Threat count for a specific date."""

    date: str
    threats: int


class SystemStatus(BaseModel):
    """ClamAV system status."""

    clamav_online: bool
    clamav_version: Optional[str] = None
    definitions_version: Optional[str] = None
    last_update: Optional[datetime] = None


class QuarantineFile(BaseModel):
    """Quarantined file information."""

    file_id: str
    original_path: str
    quarantine_path: str
    threat_name: str
    quarantine_date: datetime
    file_size: int


class QuarantineListResponse(BaseModel):
    """Paginated list of quarantined files."""

    files: List[QuarantineFile]
    total: int
    page: int
    page_size: int


class ConfigResponse(BaseModel):
    """Current configuration (sanitized)."""

    scanning: dict
    quarantine: dict
    clamav: dict  # Only safe fields, no credentials


class ConfigUpdateRequest(BaseModel):
    """Configuration update request."""

    scanning: Optional[dict] = None
    quarantine: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    clamav_connected: bool


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None
    code: str


class WSMessage(BaseModel):
    """WebSocket message format."""

    event_type: str  # "scan_progress", "threat_detected", "system_status"
    payload: dict
