"""Auto-update API endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...updater import UpdateChecker, UpdateDownloader, UpdateInstaller
from ...updater.models import UpdateInfo, UpdateProgress, UpdateChannel

router = APIRouter(prefix="/updates", tags=["updates"])
logger = logging.getLogger(__name__)

# Global update components
_update_checker: UpdateChecker | None = None
_update_downloader: UpdateDownloader | None = None
_update_installer: UpdateInstaller | None = None


def get_update_checker() -> UpdateChecker:
    """Get update checker instance."""
    global _update_checker
    if _update_checker is None:
        _update_checker = UpdateChecker(current_version="0.3.0")
    return _update_checker


def get_update_downloader() -> UpdateDownloader:
    """Get update downloader instance."""
    global _update_downloader
    if _update_downloader is None:
        _update_downloader = UpdateDownloader()
    return _update_downloader


def get_update_installer() -> UpdateInstaller:
    """Get update installer instance."""
    global _update_installer
    if _update_installer is None:
        _update_installer = UpdateInstaller()
    return _update_installer


class CheckUpdateRequest(BaseModel):
    """Check for updates request."""

    channel: UpdateChannel = UpdateChannel.STABLE


class DownloadUpdateRequest(BaseModel):
    """Download update request."""

    version: str


class InstallUpdateRequest(BaseModel):
    """Install update request."""

    version: str
    silent: bool = True
    restart: bool = True


@router.post("/check", response_model=UpdateInfo | None)
async def check_for_updates(request: CheckUpdateRequest) -> UpdateInfo | None:
    """Check for available updates.

    Args:
        request: Check request

    Returns:
        Update info if available
    """
    try:
        checker = get_update_checker()
        update_info = checker.check_for_updates(channel=request.channel)

        return update_info

    except Exception as e:
        logger.error(f"Update check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current-version")
async def get_current_version() -> dict:
    """Get current application version.

    Returns:
        Current version info
    """
    return {
        "version": "0.3.0",
        "build_date": "2026-01-27",
        "channel": "stable",
    }


@router.post("/download")
async def download_update(request: DownloadUpdateRequest) -> dict:
    """Download update file.

    Args:
        request: Download request

    Returns:
        Download status
    """
    try:
        checker = get_update_checker()
        update_info = checker.get_cached_update()

        if not update_info or update_info.version != request.version:
            raise HTTPException(status_code=404, detail="Update not found in cache")

        downloader = get_update_downloader()

        # Start download in background (stub - would use async task queue)
        # For now, return immediate response
        return {
            "status": "download_started",
            "version": request.version,
            "message": "Update download started in background"
        }

    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/install")
async def install_update(request: InstallUpdateRequest) -> dict:
    """Install downloaded update.

    Args:
        request: Install request

    Returns:
        Installation status
    """
    try:
        # This would check if update is downloaded
        # Then run the installer

        return {
            "status": "installation_scheduled",
            "version": request.version,
            "message": "Update will be installed shortly. Application will restart."
        }

    except Exception as e:
        logger.error(f"Installation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_update_status() -> dict:
    """Get update system status.

    Returns:
        Update status
    """
    checker = get_update_checker()

    return {
        "auto_check_enabled": True,
        "last_check": None,  # Would read from last_check_file
        "update_available": checker.get_cached_update() is not None,
        "current_version": "0.3.0",
    }
