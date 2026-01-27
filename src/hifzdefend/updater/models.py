"""Update system data models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class UpdateChannel(str, Enum):
    """Update channels."""

    STABLE = "stable"
    BETA = "beta"
    ALPHA = "alpha"


class UpdateStatus(str, Enum):
    """Update status."""

    CHECKING = "checking"
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    READY = "ready"
    INSTALLING = "installing"
    COMPLETED = "completed"
    FAILED = "failed"
    UP_TO_DATE = "up_to_date"


class UpdateInfo(BaseModel):
    """Update information."""

    version: str = Field(..., description="Version number")
    release_date: datetime = Field(..., description="Release date")
    download_url: str = Field(..., description="Download URL")
    changelog: str = Field(..., description="Changelog text")
    size_bytes: int = Field(..., description="Download size in bytes")
    sha256: Optional[str] = Field(None, description="SHA256 checksum")
    is_critical: bool = Field(default=False, description="Critical security update")
    minimum_version: Optional[str] = Field(None, description="Minimum version required")


class UpdateProgress(BaseModel):
    """Update download/install progress."""

    status: UpdateStatus = Field(..., description="Current status")
    progress_percent: int = Field(default=0, description="Progress percentage")
    bytes_downloaded: int = Field(default=0, description="Bytes downloaded")
    bytes_total: int = Field(default=0, description="Total bytes")
    speed_bytes_per_sec: int = Field(default=0, description="Download speed")
    eta_seconds: Optional[int] = Field(None, description="Estimated time remaining")
    error: Optional[str] = Field(None, description="Error message if failed")


class UpdateSettings(BaseModel):
    """Update settings."""

    auto_check: bool = Field(default=True, description="Automatically check for updates")
    auto_download: bool = Field(default=True, description="Automatically download updates")
    auto_install: bool = Field(default=False, description="Automatically install updates")
    channel: UpdateChannel = Field(default=UpdateChannel.STABLE, description="Update channel")
    check_interval_hours: int = Field(default=24, description="Check interval in hours")
    notify_updates: bool = Field(default=True, description="Show update notifications")
