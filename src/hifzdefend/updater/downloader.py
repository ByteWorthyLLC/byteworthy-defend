"""Update downloader - downloads update files."""

import hashlib
import logging
from pathlib import Path
from typing import Optional, Callable
import time

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..core.config import get_app_data_dir
from .models import UpdateInfo, UpdateProgress, UpdateStatus

logger = logging.getLogger(__name__)


class UpdateDownloader:
    """Download update files."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize update downloader.

        Args:
            data_dir: Directory for downloads
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests package required. Run: pip install requests")

        self.data_dir = data_dir or get_app_data_dir() / "updates" / "downloads"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_update(
        self,
        update_info: UpdateInfo,
        progress_callback: Optional[Callable[[UpdateProgress], None]] = None
    ) -> Optional[Path]:
        """Download update file.

        Args:
            update_info: Update information
            progress_callback: Callback for progress updates

        Returns:
            Path to downloaded file or None
        """
        try:
            filename = f"hifzdefend-{update_info.version}-setup.exe"
            download_path = self.data_dir / filename

            # Skip if already downloaded
            if download_path.exists() and self._verify_checksum(download_path, update_info.sha256):
                logger.info(f"Update already downloaded: {download_path}")
                if progress_callback:
                    progress_callback(UpdateProgress(
                        status=UpdateStatus.READY,
                        progress_percent=100,
                        bytes_downloaded=update_info.size_bytes,
                        bytes_total=update_info.size_bytes,
                    ))
                return download_path

            # Download file
            logger.info(f"Downloading update from {update_info.download_url}")

            response = requests.get(update_info.download_url, stream=True, timeout=30)
            response.raise_for_status()

            bytes_downloaded = 0
            start_time = time.time()

            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)

                        # Update progress
                        if progress_callback:
                            elapsed = time.time() - start_time
                            speed = bytes_downloaded / elapsed if elapsed > 0 else 0
                            eta = int((update_info.size_bytes - bytes_downloaded) / speed) if speed > 0 else None

                            progress_callback(UpdateProgress(
                                status=UpdateStatus.DOWNLOADING,
                                progress_percent=int((bytes_downloaded / update_info.size_bytes) * 100),
                                bytes_downloaded=bytes_downloaded,
                                bytes_total=update_info.size_bytes,
                                speed_bytes_per_sec=int(speed),
                                eta_seconds=eta,
                            ))

            # Verify checksum if provided
            if update_info.sha256:
                if not self._verify_checksum(download_path, update_info.sha256):
                    download_path.unlink()
                    raise ValueError("Checksum verification failed")

            logger.info(f"Download completed: {download_path}")

            if progress_callback:
                progress_callback(UpdateProgress(
                    status=UpdateStatus.READY,
                    progress_percent=100,
                    bytes_downloaded=update_info.size_bytes,
                    bytes_total=update_info.size_bytes,
                ))

            return download_path

        except Exception as e:
            logger.error(f"Download failed: {e}")
            if progress_callback:
                progress_callback(UpdateProgress(
                    status=UpdateStatus.FAILED,
                    error=str(e),
                ))
            return None

    def _verify_checksum(self, file_path: Path, expected_sha256: Optional[str]) -> bool:
        """Verify file checksum.

        Args:
            file_path: Path to file
            expected_sha256: Expected SHA256 hash

        Returns:
            Whether checksum matches
        """
        if not expected_sha256:
            return True

        try:
            sha256 = hashlib.sha256()

            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)

            actual = sha256.hexdigest()
            return actual.lower() == expected_sha256.lower()

        except Exception as e:
            logger.error(f"Checksum verification failed: {e}")
            return False

    def cleanup_old_downloads(self, keep_count: int = 2) -> None:
        """Clean up old downloaded updates.

        Args:
            keep_count: Number of recent downloads to keep
        """
        try:
            downloads = sorted(
                self.data_dir.glob("*.exe"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            for download in downloads[keep_count:]:
                logger.info(f"Removing old download: {download}")
                download.unlink()

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
