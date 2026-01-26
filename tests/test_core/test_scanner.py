"""
Unit tests for ClamAV scanner.
"""

import pytest
from unittest.mock import Mock, patch

from hifzdefend.core.scanner import ClamAVScanner, ScanResult
from hifzdefend.utils.exceptions import ClamAVConnectionError


class TestScanResult:
    """Tests for ScanResult class."""

    def test_clean_result(self):
        """Test clean scan result."""
        result = ScanResult("test.txt", is_infected=False)
        assert result.is_clean
        assert not result.is_infected
        assert not result.has_error
        assert result.threat_name is None

    def test_infected_result(self):
        """Test infected scan result."""
        result = ScanResult("test.txt", is_infected=True, threat_name="Test.Virus")
        assert not result.is_clean
        assert result.is_infected
        assert not result.has_error
        assert result.threat_name == "Test.Virus"

    def test_error_result(self):
        """Test scan result with error."""
        result = ScanResult("test.txt", is_infected=False, error="File not found")
        assert not result.is_clean
        assert not result.is_infected
        assert result.has_error
        assert result.error == "File not found"


@pytest.mark.requires_clamav
class TestClamAVScanner:
    """Tests for ClamAVScanner class (requires ClamAV running)."""

    def test_scanner_initialization(self, mock_clamav_config):
        """Test scanner can be initialized."""
        scanner = ClamAVScanner(mock_clamav_config)
        assert scanner.config == mock_clamav_config

    def test_ping_success(self, clamav_scanner):
        """Test ping to ClamAV daemon."""
        result = clamav_scanner.ping()
        assert result is True

    def test_get_version(self, clamav_scanner):
        """Test getting ClamAV version."""
        version = clamav_scanner.get_version()
        assert version is not None
        assert isinstance(version, str)
        assert "ClamAV" in version

    def test_scan_clean_file(self, clamav_scanner, clean_file):
        """Test scanning a clean file."""
        result = clamav_scanner.scan_file(clean_file)
        assert result.is_clean
        assert not result.is_infected
        assert result.threat_name is None

    def test_scan_nonexistent_file(self, clamav_scanner, temp_dir):
        """Test scanning a nonexistent file."""
        nonexistent = temp_dir / "nonexistent.txt"
        result = clamav_scanner.scan_file(nonexistent)
        assert result.has_error
        assert "not found" in result.error.lower()

    def test_scan_eicar(self, clamav_scanner, eicar_file):
        """Test scanning EICAR test file."""
        result = clamav_scanner.scan_file(eicar_file)
        assert result.is_infected
        assert result.threat_name is not None
        assert "EICAR" in result.threat_name or "Eicar" in result.threat_name

    def test_context_manager(self, test_config):
        """Test scanner as context manager."""
        with ClamAVScanner(test_config.clamav) as scanner:
            assert scanner.ping()


class TestClamAVScannerMocked:
    """Tests for ClamAVScanner with mocked connection."""

    @patch('hifzdefend.core.scanner.clamd.ClamdNetworkSocket')
    def test_connection_failure(self, mock_clamd, mock_clamav_config):
        """Test handling of connection failure."""
        mock_clamd.side_effect = Exception("Connection refused")

        scanner = ClamAVScanner(mock_clamav_config)
        with pytest.raises(ClamAVConnectionError):
            scanner._get_connection()

    @patch('hifzdefend.core.scanner.clamd.ClamdNetworkSocket')
    def test_ping_failure(self, mock_clamd, mock_clamav_config):
        """Test ping failure handling."""
        mock_instance = Mock()
        mock_instance.ping.side_effect = Exception("Timeout")
        mock_clamd.return_value = mock_instance

        scanner = ClamAVScanner(mock_clamav_config)
        result = scanner.ping()
        assert result is False
