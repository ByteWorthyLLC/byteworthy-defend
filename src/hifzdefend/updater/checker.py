"""Update checker - checks for new versions."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import json
import re

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..core.config import get_app_data_dir
from .models import UpdateInfo, UpdateChannel

logger = logging.getLogger(__name__)


class UpdateChecker:
    """Check for application updates."""

    def __init__(
        self,
        current_version: str,
        github_repo: str = "byteworthy/Hafz-Defend",
        data_dir: Optional[Path] = None
    ):
        """Initialize update checker.

        Args:
            current_version: Current application version
            github_repo: GitHub repository (owner/repo)
            data_dir: Directory for update data storage
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests package required. Run: pip install requests")

        self.current_version = current_version
        self.github_repo = github_repo
        self.data_dir = data_dir or get_app_data_dir() / "updates"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.cache_file = self.data_dir / "update_cache.json"
        self.last_check_file = self.data_dir / "last_check.txt"

    def check_for_updates(self, channel: UpdateChannel = UpdateChannel.STABLE) -> Optional[UpdateInfo]:
        """Check for available updates.

        Args:
            channel: Update channel to check

        Returns:
            Update info if available, None otherwise
        """
        try:
            # Get latest release from GitHub
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"

            if channel == UpdateChannel.BETA:
                # Include pre-releases
                url = f"https://api.github.com/repos/{self.github_repo}/releases"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            if channel == UpdateChannel.BETA:
                releases = response.json()
                # Get first pre-release or latest stable
                release = next(
                    (r for r in releases if r.get("prerelease")),
                    releases[0] if releases else None
                )
            else:
                release = response.json()

            if not release:
                return None

            # Parse version
            version = release["tag_name"].lstrip("v")

            # Check if newer than current
            if not self._is_newer_version(version, self.current_version):
                logger.info(f"No updates available (current: {self.current_version}, latest: {version})")
                self._save_last_check()
                return None

            # Find Windows installer asset
            asset = self._find_windows_asset(release.get("assets", []))

            if not asset:
                logger.warning("No Windows installer found in release")
                return None

            # Create update info
            update_info = UpdateInfo(
                version=version,
                release_date=datetime.fromisoformat(release["published_at"].replace("Z", "+00:00")),
                download_url=asset["browser_download_url"],
                changelog=release.get("body", "No changelog available"),
                size_bytes=asset["size"],
                is_critical=self._is_critical_update(release),
            )

            # Cache update info
            self._save_to_cache(update_info)
            self._save_last_check()

            logger.info(f"Update available: {version}")
            return update_info

        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return None

    def get_cached_update(self) -> Optional[UpdateInfo]:
        """Get cached update info.

        Returns:
            Cached update info or None
        """
        try:
            if not self.cache_file.exists():
                return None

            with open(self.cache_file, "r") as f:
                data = json.load(f)

            return UpdateInfo(**data)

        except Exception as e:
            logger.error(f"Failed to load cached update: {e}")
            return None

    def should_check_for_updates(self, interval_hours: int = 24) -> bool:
        """Check if enough time has passed since last check.

        Args:
            interval_hours: Minimum hours between checks

        Returns:
            Whether to check for updates
        """
        try:
            if not self.last_check_file.exists():
                return True

            with open(self.last_check_file, "r") as f:
                last_check_str = f.read().strip()

            last_check = datetime.fromisoformat(last_check_str)
            next_check = last_check + timedelta(hours=interval_hours)

            return datetime.utcnow() >= next_check

        except Exception:
            return True

    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """Compare version strings.

        Args:
            version1: First version
            version2: Second version

        Returns:
            True if version1 is newer than version2
        """
        try:
            # Parse versions (e.g., "0.3.0" -> [0, 3, 0])
            v1_parts = [int(x) for x in version1.split(".")]
            v2_parts = [int(x) for x in version2.split(".")]

            # Pad to same length
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts += [0] * (max_len - len(v1_parts))
            v2_parts += [0] * (max_len - len(v2_parts))

            return v1_parts > v2_parts

        except Exception:
            return False

    def _find_windows_asset(self, assets: list) -> Optional[dict]:
        """Find Windows installer in release assets.

        Args:
            assets: Release assets

        Returns:
            Windows installer asset or None
        """
        for asset in assets:
            name = asset.get("name", "").lower()
            if name.endswith(".exe") or name.endswith(".msi"):
                return asset

        return None

    def _is_critical_update(self, release: dict) -> bool:
        """Check if update is critical (security fix).

        Args:
            release: Release data

        Returns:
            Whether update is critical
        """
        body = release.get("body", "").lower()
        critical_keywords = ["critical", "security", "vulnerability", "cve"]

        return any(keyword in body for keyword in critical_keywords)

    def _save_to_cache(self, update_info: UpdateInfo) -> None:
        """Save update info to cache.

        Args:
            update_info: Update information
        """
        try:
            with open(self.cache_file, "w") as f:
                json.dump(update_info.dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save update cache: {e}")

    def _save_last_check(self) -> None:
        """Save last check timestamp."""
        try:
            with open(self.last_check_file, "w") as f:
                f.write(datetime.utcnow().isoformat())
        except Exception as e:
            logger.error(f"Failed to save last check time: {e}")
