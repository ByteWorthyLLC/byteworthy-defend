"""
Pytest configuration and fixtures.

Provides common fixtures for both Phase 1 and Phase 1.5 testing:
- Phase 1: Scanner, engine, EICAR test files
- Phase 1.5: Event bus, monitors, threat intelligence, rules engine
"""

import asyncio
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from hifzdefend.config.loader import HifzDefendConfig, ClamAVConfig
from hifzdefend.core.scanner import ClamAVScanner
from hifzdefend.core.engine import ScanEngine
from hifzdefend.monitoring.event_bus import Event, EventBus, EventType


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


# Phase 1.5 Fixtures

@pytest.fixture
def monitoring_config(temp_dir):
    """Configuration with monitoring enabled."""
    config = HifzDefendConfig()

    # Override paths
    config.logging.log_dir = str(temp_dir / "logs")
    config.reporting.report_dir = str(temp_dir / "reports")
    config.quarantine.quarantine_dir = str(temp_dir / "quarantine")

    # Enable monitoring
    config.monitoring.enabled = True
    config.monitoring.check_interval = 1  # Fast interval for tests

    return config


@pytest.fixture
def event_bus():
    """Event bus instance for testing."""
    bus = EventBus()
    yield bus

    # Cleanup
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(bus.stop())
        else:
            asyncio.run(bus.stop())
    except Exception:
        pass


@pytest.fixture
async def async_event_bus():
    """Async event bus fixture."""
    bus = EventBus()
    yield bus
    await bus.stop()


@pytest.fixture
def sample_event() -> Event:
    """Sample event for testing."""
    return Event(
        event_type=EventType.THREAT_DETECTED,
        severity="warning",
        source_monitor="test_monitor",
        data={"test": "data"},
        threat_score=50,
    )


@pytest.fixture
def sample_threat_event() -> Event:
    """Sample high-threat event."""
    return Event(
        event_type=EventType.THREAT_DETECTED,
        severity="critical",
        source_monitor="test_monitor",
        data={
            "threat_type": "malware",
            "file_path": "/tmp/malicious.exe",
        },
        threat_score=95,
    )


@pytest.fixture
def sample_clean_event() -> Event:
    """Sample clean event."""
    return Event(
        event_type=EventType.FILE_MODIFIED,
        severity="info",
        source_monitor="file_monitor",
        data={"file_path": "/tmp/document.txt"},
        threat_score=0,
    )


@pytest.fixture
def mock_threat_intel_manager():
    """Mock ThreatIntelligenceManager."""
    manager = MagicMock()
    manager.check_ip_reputation = AsyncMock(return_value={
        "source": "test",
        "threat_level": "clean",
        "threat_score": 0,
    })
    manager.check_file_reputation = AsyncMock(return_value={
        "source": "test",
        "threat_level": "clean",
        "threat_score": 0,
    })
    manager.check_package_security = AsyncMock(return_value={
        "source": "test",
        "threat_level": "clean",
        "threat_score": 0,
    })
    manager.close = AsyncMock()
    return manager


@pytest.fixture
def mock_rules_engine():
    """Mock RulesEngine."""
    engine = MagicMock()
    engine.compile_rules = MagicMock()
    engine.scan_with_rules = MagicMock(return_value=[])
    engine.should_block_file = MagicMock(return_value=False)
    engine.is_whitelisted_app = MagicMock(return_value=False)
    return engine


@pytest.fixture
def mock_monitor_manager():
    """Mock MonitorManager."""
    manager = MagicMock()
    manager.start_all = AsyncMock()
    manager.stop_all = AsyncMock()
    manager.get_status = MagicMock(return_value={
        "event_bus": {"running": True, "events_processed": 0},
        "package_monitor": {"running": True, "enabled": True, "events_generated": 0},
    })
    return manager


class EventCollector:
    """Helper class to collect events in tests."""

    def __init__(self):
        self.events: list[Event] = []

    def handle_event(self, event: Event):
        self.events.append(event)

    def clear(self):
        self.events.clear()

    def get_by_type(self, event_type: EventType) -> list[Event]:
        return [e for e in self.events if e.event_type == event_type]

    def get_by_severity(self, severity: str) -> list[Event]:
        return [e for e in self.events if e.severity == severity]


@pytest.fixture
def event_collector():
    """Event collector for testing."""
    return EventCollector()


# EICAR test string (standard antivirus test)
EICAR_STRING = r"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


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
    config.addinivalue_line(
        "markers", "benchmark: marks tests as performance benchmarks"
    )
    config.addinivalue_line(
        "markers", "requires_admin: marks tests requiring administrator privileges"
    )
    config.addinivalue_line(
        "markers", "requires_docker: marks tests requiring Docker to be running"
    )
    config.addinivalue_line(
        "markers", "requires_api_keys: marks tests requiring external API keys"
    )
