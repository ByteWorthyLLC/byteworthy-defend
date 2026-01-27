"""
Pydantic models for API request and response schemas.

These models ensure type safety and automatic validation for all API endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ============================================================================
# System Status Models
# ============================================================================


class ResourceUsage(BaseModel):
    """System resource usage."""

    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")


class MonitorStats(BaseModel):
    """Monitor statistics."""

    active: int = Field(..., description="Number of active monitors")
    total: int = Field(..., description="Total number of monitors")


class ThreatStats(BaseModel):
    """Threat statistics."""

    today: int = Field(..., description="Threats detected today")
    week: int = Field(..., description="Threats detected this week")
    total: int = Field(..., description="Total threats detected")


class SystemStatusResponse(BaseModel):
    """System status response."""

    protection_status: str = Field(..., description="Protection status")
    monitors: MonitorStats
    threats: ThreatStats
    last_scan: Optional[datetime] = Field(None, description="Last scan timestamp")
    last_update: Optional[datetime] = Field(None, description="Last update timestamp")
    resources: ResourceUsage


# ============================================================================
# Monitor Models
# ============================================================================


class MonitorStatus(BaseModel):
    """Monitor status information."""

    id: str = Field(..., description="Monitor identifier")
    name: str = Field(..., description="Monitor name")
    status: str = Field(..., description="Monitor status")
    enabled: bool = Field(..., description="Whether monitor is enabled")
    event_count: int = Field(..., description="Number of events detected")
    last_event: Optional[datetime] = Field(None, description="Last event timestamp")
    error_message: Optional[str] = Field(None, description="Error message if any")


class MonitorToggleRequest(BaseModel):
    """Request to toggle monitor."""

    enabled: bool = Field(..., description="Whether to enable the monitor")


class MonitorToggleResponse(BaseModel):
    """Monitor toggle response."""

    id: str = Field(..., description="Monitor identifier")
    enabled: bool = Field(..., description="New enabled state")
    status: str = Field(..., description="New status")


class MonitorHealthResponse(BaseModel):
    """Monitor health check response."""

    healthy: bool = Field(..., description="Whether all monitors are healthy")
    manager_running: bool = Field(..., description="Whether manager is running")
    total_monitors: int = Field(..., description="Total number of monitors")
    running_monitors: int = Field(..., description="Number of running monitors")
    unhealthy_monitors: int = Field(..., description="Number of unhealthy monitors")
    monitors: List[Dict[str, Any]] = Field(default_factory=list, description="Individual monitor health")


class MonitorActionResponse(BaseModel):
    """Generic monitor action response."""

    id: str = Field(..., description="Monitor identifier")
    status: str = Field(..., description="New status")


# ============================================================================
# Scan Models
# ============================================================================


class ScanRequest(BaseModel):
    """Scan request."""

    path: str = Field(..., description="Path to scan")
    recursive: bool = Field(True, description="Whether to scan recursively")


class ThreatDetail(BaseModel):
    """Detected threat details."""

    name: str = Field(..., description="Threat name")
    path: str = Field(..., description="File path")
    quarantined: bool = Field(False, description="Whether file was quarantined")


class ScanResponse(BaseModel):
    """Scan response."""

    scan_id: str = Field(..., description="Scan identifier")
    path: str = Field(..., description="Scanned path")
    files_scanned: int = Field(..., description="Number of files scanned")
    threats_found: int = Field(..., description="Number of threats found")
    threats: List[ThreatDetail] = Field(default_factory=list)
    status: str = Field(..., description="Scan status")


class ScanHistoryItem(BaseModel):
    """Scan history item."""

    id: str = Field(..., description="Scan identifier")
    path: str = Field(..., description="Scanned path")
    started_at: datetime = Field(..., description="Scan start time")
    completed_at: Optional[datetime] = Field(None, description="Scan completion time")
    status: str = Field(..., description="Scan status")
    files_scanned: int = Field(..., description="Files scanned")
    threats_found: int = Field(..., description="Threats found")


# ============================================================================
# Quarantine Models
# ============================================================================


class QuarantineItem(BaseModel):
    """Quarantined file information."""

    id: str = Field(..., description="Quarantine item ID")
    original_path: str = Field(..., description="Original file path")
    threat_name: str = Field(..., description="Threat name")
    quarantined_at: datetime = Field(..., description="Quarantine timestamp")
    size: int = Field(..., description="File size in bytes")


class QuarantineRestoreRequest(BaseModel):
    """Request to restore from quarantine."""

    id: str = Field(..., description="Quarantine item ID to restore")


class QuarantineRestoreResponse(BaseModel):
    """Quarantine restore response."""

    success: bool = Field(..., description="Whether restore was successful")
    id: str = Field(..., description="Quarantine item ID")
    message: Optional[str] = Field(None, description="Result message")


# ============================================================================
# Threat Models
# ============================================================================


class ThreatInfo(BaseModel):
    """Threat information."""

    id: str = Field(..., description="Threat identifier")
    name: str = Field(..., description="Threat name")
    severity: str = Field(..., description="Threat severity level")
    detected_at: datetime = Field(..., description="Detection timestamp")
    path: str = Field(..., description="File path")
    quarantined: bool = Field(..., description="Whether file was quarantined")
    description: Optional[str] = Field(None, description="Threat description")


# ============================================================================
# Configuration Models
# ============================================================================


class ConfigUpdateRequest(BaseModel):
    """Configuration update request."""

    section: str = Field(..., description="Configuration section")
    updates: Dict[str, Any] = Field(..., description="Updates to apply")


class ConfigUpdateResponse(BaseModel):
    """Configuration update response."""

    success: bool = Field(..., description="Whether update was successful")
    section: str = Field(..., description="Updated section")
    updates: Dict[str, Any] = Field(..., description="Applied updates")


# ============================================================================
# AI Models
# ============================================================================


class AIQueryRequest(BaseModel):
    """AI query request."""

    query: str = Field(..., description="Natural language query")
    context: Optional[str] = Field(None, description="Additional context")


class AIQueryResponse(BaseModel):
    """AI query response."""

    query: str = Field(..., description="Original query")
    response: str = Field(..., description="AI-generated response")
    sources: List[str] = Field(default_factory=list, description="Source references")
    cost: Optional[float] = Field(None, description="Query cost in USD")


class ScriptAnalyzeRequest(BaseModel):
    """Script analysis request."""

    content: str = Field(..., description="Script content to analyze")
    file_type: Optional[str] = Field(None, description="Script file type")
    filename: Optional[str] = Field(None, description="Script filename")


class ScriptAnalyzeResponse(BaseModel):
    """Script analysis response."""

    threat_level: str = Field(..., description="Threat level assessment")
    confidence: float = Field(..., description="Confidence score")
    analysis: str = Field(..., description="Detailed analysis")
    recommendations: List[str] = Field(default_factory=list)
    cost: Optional[float] = Field(None, description="Analysis cost in USD")


# ============================================================================
# Dashboard Models
# ============================================================================


class DashboardStats(BaseModel):
    """Dashboard statistics."""

    protection_enabled: bool
    monitors_active: int
    monitors_total: int
    threats_today: int
    threats_week: int
    threats_total: int
    recent_scans: List[ScanHistoryItem]
    recent_threats: List[ThreatInfo]
    system_resources: ResourceUsage


# ============================================================================
# WebSocket Models
# ============================================================================


class WebSocketMessage(BaseModel):
    """WebSocket message format."""

    type: str = Field(..., description="Message type")
    timestamp: datetime = Field(..., description="Message timestamp")
    data: Dict[str, Any] = Field(..., description="Message data")
    priority: int = Field(0, description="Message priority (0-3)")
