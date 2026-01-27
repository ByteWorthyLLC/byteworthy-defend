"""Update installer - installs downloaded updates."""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class UpdateInstaller:
    """Install downloaded updates."""

    def __init__(self):
        """Initialize update installer."""
        pass

    def install_update(self, installer_path: Path, silent: bool = False) -> bool:
        """Install update.

        Args:
            installer_path: Path to installer
            silent: Whether to run installer silently

        Returns:
            Success status
        """
        if not installer_path.exists():
            logger.error(f"Installer not found: {installer_path}")
            return False

        try:
            logger.info(f"Installing update from {installer_path}")

            # Build installer command
            cmd = [str(installer_path)]

            if silent:
                # Common silent install flags
                cmd.extend(["/S", "/silent", "/quiet", "/qn"])

            # Run installer
            # Note: This will typically require elevation
            result = subprocess.run(cmd, check=False)

            success = result.returncode == 0

            if success:
                logger.info("Update installed successfully")
            else:
                logger.error(f"Installer failed with code {result.returncode}")

            return success

        except Exception as e:
            logger.error(f"Installation failed: {e}")
            return False

    def install_and_restart(self, installer_path: Path) -> bool:
        """Install update and restart application.

        Args:
            installer_path: Path to installer

        Returns:
            Success status
        """
        try:
            # Launch installer in background
            # The installer should handle replacing files and restarting
            subprocess.Popen(
                [str(installer_path), "/S", "/restart"],
                creationflags=subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0
            )

            logger.info("Update installation started, application will restart")

            # Exit current process
            # The installer will restart the application
            sys.exit(0)

        except Exception as e:
            logger.error(f"Install and restart failed: {e}")
            return False

    def create_backup(self) -> Optional[Path]:
        """Create backup of current installation.

        Returns:
            Path to backup or None
        """
        # This would copy the current installation to a backup location
        # For simplicity, we rely on the installer's built-in rollback
        logger.info("Backup creation not implemented - relying on installer rollback")
        return None

    def rollback_update(self, backup_path: Path) -> bool:
        """Rollback to previous version.

        Args:
            backup_path: Path to backup

        Returns:
            Success status
        """
        # This would restore from backup
        logger.warning("Rollback not fully implemented")
        return False

    def schedule_install(self, installer_path: Path, delay_seconds: int = 5) -> bool:
        """Schedule installation after delay.

        Args:
            installer_path: Path to installer
            delay_seconds: Delay before installation

        Returns:
            Success status
        """
        try:
            # Use Windows Task Scheduler to run installer after delay
            if sys.platform == "win32":
                # Create scheduled task
                task_name = "HifzDefend_Update"
                cmd = [
                    "schtasks", "/create",
                    "/tn", task_name,
                    "/tr", f'"{installer_path}" /S',
                    "/sc", "once",
                    "/st", "00:00",  # This would be calculated based on delay
                    "/f"  # Force create
                ]

                result = subprocess.run(cmd, check=False, capture_output=True)

                if result.returncode == 0:
                    logger.info(f"Update scheduled: {task_name}")
                    return True
                else:
                    logger.error(f"Failed to schedule update: {result.stderr}")
                    return False

            else:
                # Non-Windows platforms
                logger.warning("Scheduled install not supported on this platform")
                return False

        except Exception as e:
            logger.error(f"Schedule install failed: {e}")
            return False
