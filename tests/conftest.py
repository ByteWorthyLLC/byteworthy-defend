"""
Pytest configuration and fixtures.
"""

import os
import tempfile
import zipfile
from pathlib import Path

import pytest

from hifzdefend.config.loader import HifzDefendConfig, ClamAVConfig
from hifzdefend.core.scanner import ClamAVScanner
from hifzdefend.core.engine import ScanEngine


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def eicar_zip_path():
    """Path to encrypted EICAR test ZIP file."""
    tests_dir = Path(__file__).parent
    return tests_dir / "fixtures" / "eicar_test.zip"


@pytest.fixture
def eicar_file(temp_dir, eicar_zip_path):
    """
    Extract EICAR test file to temporary directory.

    WARNING: Requires Windows Defender exclusions for temp directory!
    """
    if not eicar_zip_path.exists():
        pytest.skip(f"EICAR test file not found: {eicar_zip_path}")

    # Extract EICAR from password-protected ZIP
    eicar_path = temp_dir / "eicar.txt"

    try:
        with zipfile.ZipFile(eicar_zip_path, 'r') as zf:
            zf.setpassword(b'infected')
            zf.extract('eicar.txt', temp_dir)
    except Exception as e:
        pytest.skip(f"Failed to extract EICAR: {e}")

    yield eicar_path

    # Cleanup
    try:
        if eicar_path.exists():
            eicar_path.unlink()
    except Exception:
        pass


@pytest.fixture
def clean_file(temp_dir):
    """Create a clean test file."""
    file_path = temp_dir / "clean.txt"
    file_path.write_text("This is a clean test file.")
    return file_path


@pytest.fixture
def test_config(temp_dir):
    """Create test configuration."""
    config = HifzDefendConfig()

    # Override paths to use temp directory
    config.logging.log_dir = str(temp_dir / "logs")
    config.reporting.report_dir = str(temp_dir / "reports")
    config.quarantine.quarantine_dir = str(temp_dir / "quarantine")

    return config


@pytest.fixture
def clamav_scanner(test_config):
    """Create ClamAV scanner instance."""
    scanner = ClamAVScanner(test_config.clamav)

    # Check if ClamAV is available
    if not scanner.ping():
        pytest.skip("ClamAV daemon not running")

    yield scanner
    scanner.close()


@pytest.fixture
def scan_engine(test_config, clamav_scanner):
    """Create scan engine instance."""
    engine = ScanEngine(test_config)

    # Check if ClamAV is available
    if not engine.check_connection():
        pytest.skip("ClamAV daemon not running")

    yield engine
    engine.close()


@pytest.fixture
def mock_clamav_config():
    """Create mock ClamAV configuration."""
    return ClamAVConfig(host="localhost", port=3310, timeout=30)


# Markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "requires_clamav: marks tests that require ClamAV daemon running",
    )
