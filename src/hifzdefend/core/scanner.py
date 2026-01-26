"""
ClamAV scanner integration.
"""

import logging
import socket
from pathlib import Path
from typing import Optional, Union

import clamd

from ..config.loader import ClamAVConfig
from ..utils.exceptions import (
    ClamAVConnectionError,
    ClamAVTimeoutError,
    ScannerError,
)


class ScanResult:
    """Represents the result of a scan operation."""

    def __init__(
        self,
        file_path: Union[str, Path],
        is_infected: bool,
        threat_name: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """
        Initialize scan result.

        Args:
            file_path: Path to scanned file
            is_infected: Whether file is infected
            threat_name: Name of detected threat (if any)
            error: Error message (if scan failed)
        """
        self.file_path = Path(file_path)
        self.is_infected = is_infected
        self.threat_name = threat_name
        self.error = error

    @property
    def is_clean(self) -> bool:
        """Check if file is clean (not infected and no errors)."""
        return not self.is_infected and self.error is None

    @property
    def has_error(self) -> bool:
        """Check if scan encountered an error."""
        return self.error is not None

    def __repr__(self) -> str:
        """String representation of scan result."""
        if self.has_error:
            return f"ScanResult(file={self.file_path}, error={self.error})"
        elif self.is_infected:
            return f"ScanResult(file={self.file_path}, threat={self.threat_name})"
        else:
            return f"ScanResult(file={self.file_path}, clean=True)"


class ClamAVScanner:
    """ClamAV scanner wrapper."""

    def __init__(self, config: ClamAVConfig):
        """
        Initialize ClamAV scanner.

        Args:
            config: ClamAV configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._connection: Optional[clamd.ClamdNetworkSocket] = None

    def _get_connection(self) -> clamd.ClamdNetworkSocket:
        """
        Get or create connection to ClamAV daemon.

        Returns:
            ClamAV connection object

        Raises:
            ClamAVConnectionError: If connection fails
        """
        if self._connection is None:
            try:
                self._connection = clamd.ClamdNetworkSocket(
                    host=self.config.host,
                    port=self.config.port,
                    timeout=self.config.timeout,
                )
            except Exception as e:
                raise ClamAVConnectionError(
                    f"Failed to connect to ClamAV daemon at "
                    f"{self.config.host}:{self.config.port}: {e}"
                )

        return self._connection

    def ping(self) -> bool:
        """
        Check if ClamAV daemon is responding.

        Returns:
            True if daemon is responding, False otherwise
        """
        try:
            connection = self._get_connection()
            response = connection.ping()
            return response == "PONG"
        except (ClamAVConnectionError, socket.timeout, socket.error):
            return False
        except Exception as e:
            self.logger.warning(f"Unexpected error during ping: {e}")
            return False

    def get_version(self) -> Optional[str]:
        """
        Get ClamAV version information.

        Returns:
            Version string or None if unavailable
        """
        try:
            connection = self._get_connection()
            return connection.version()
        except Exception as e:
            self.logger.error(f"Failed to get ClamAV version: {e}")
            return None

    def scan_file(self, file_path: Union[str, Path]) -> ScanResult:
        """
        Scan a single file.

        Args:
            file_path: Path to file to scan

        Returns:
            ScanResult object
        """
        file_path = Path(file_path)

        # Check if file exists
        if not file_path.exists():
            return ScanResult(file_path, False, error="File not found")

        if not file_path.is_file():
            return ScanResult(file_path, False, error="Not a file")

        try:
            connection = self._get_connection()

            # Scan file
            result = connection.scan(str(file_path))

            # Parse result
            if result is None:
                # No threats found
                return ScanResult(file_path, False)

            # Result format: {'/path/to/file': ('FOUND', 'Threat.Name')}
            file_key = str(file_path)
            if file_key in result:
                status, threat_name = result[file_key]
                if status == "FOUND":
                    self.logger.warning(
                        f"Threat detected in {file_path}: {threat_name}"
                    )
                    return ScanResult(file_path, True, threat_name=threat_name)
                elif status == "ERROR":
                    return ScanResult(file_path, False, error=threat_name)

            # Clean file
            return ScanResult(file_path, False)

        except socket.timeout:
            raise ClamAVTimeoutError(
                f"Scan timeout for {file_path} "
                f"(timeout: {self.config.timeout}s)"
            )
        except ClamAVConnectionError:
            raise
        except Exception as e:
            self.logger.error(f"Scan error for {file_path}: {e}")
            return ScanResult(file_path, False, error=str(e))

    def scan_directory(
        self, directory_path: Union[str, Path], recursive: bool = True
    ) -> list[ScanResult]:
        """
        Scan a directory.

        Args:
            directory_path: Path to directory to scan
            recursive: Whether to scan recursively

        Returns:
            List of ScanResult objects

        Raises:
            ScannerError: If directory doesn't exist or is not a directory
        """
        directory_path = Path(directory_path)

        if not directory_path.exists():
            raise ScannerError(f"Directory not found: {directory_path}")

        if not directory_path.is_dir():
            raise ScannerError(f"Not a directory: {directory_path}")

        results = []

        # Get files to scan
        if recursive:
            files = list(directory_path.rglob("*"))
        else:
            files = list(directory_path.glob("*"))

        # Filter only files
        files = [f for f in files if f.is_file()]

        # Scan each file
        for file_path in files:
            try:
                result = self.scan_file(file_path)
                results.append(result)
            except ClamAVTimeoutError as e:
                self.logger.warning(str(e))
                results.append(ScanResult(file_path, False, error="Timeout"))
            except Exception as e:
                self.logger.error(f"Error scanning {file_path}: {e}")
                results.append(ScanResult(file_path, False, error=str(e)))

        return results

    def reload_database(self) -> bool:
        """
        Reload virus database.

        Returns:
            True if successful, False otherwise
        """
        try:
            connection = self._get_connection()
            connection.reload()
            self.logger.info("ClamAV database reloaded")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reload database: {e}")
            return False

    def close(self) -> None:
        """Close connection to ClamAV daemon."""
        if self._connection is not None:
            # clamd doesn't have explicit close method
            self._connection = None
            self.logger.debug("ClamAV connection closed")

    def __enter__(self) -> "ClamAVScanner":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
