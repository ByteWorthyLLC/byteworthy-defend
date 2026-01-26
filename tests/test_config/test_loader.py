"""
Unit tests for configuration loader.
"""

import pytest
from pathlib import Path

from hifzdefend.config.loader import (
    HifzDefendConfig,
    ClamAVConfig,
    ScanningConfig,
    load_config,
)
from hifzdefend.utils.exceptions import ConfigurationError


class TestClamAVConfig:
    """Tests for ClamAV configuration."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ClamAVConfig()
        assert config.host == "localhost"
        assert config.port == 3310
        assert config.timeout == 60

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ClamAVConfig(host="127.0.0.1", port=3311, timeout=30)
        assert config.host == "127.0.0.1"
        assert config.port == 3311
        assert config.timeout == 30

    def test_invalid_port(self):
        """Test validation of invalid port."""
        with pytest.raises(ValueError):
            ClamAVConfig(port=0)

        with pytest.raises(ValueError):
            ClamAVConfig(port=99999)


class TestScanningConfig:
    """Tests for scanning configuration."""

    def test_default_values(self):
        """Test default scanning configuration."""
        config = ScanningConfig()
        assert config.max_file_size == 104857600  # 100 MB
        assert config.scan_archives is True
        assert config.scan_recursively is True
        assert config.follow_symlinks is False

    def test_extension_validation(self):
        """Test extension validation (adds dot if missing)."""
        config = ScanningConfig(excluded_extensions=["txt", ".log", "tmp"])
        assert ".txt" in config.excluded_extensions
        assert ".log" in config.excluded_extensions
        assert ".tmp" in config.excluded_extensions


class TestHifzDefendConfig:
    """Tests for main configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = HifzDefendConfig()
        assert config.clamav.host == "localhost"
        assert config.scanning.scan_archives is True
        assert config.quarantine.enabled is True

    def test_nested_config(self):
        """Test nested configuration."""
        config = HifzDefendConfig(
            clamav=ClamAVConfig(port=3311),
            scanning=ScanningConfig(max_file_size=50000000),
        )
        assert config.clamav.port == 3311
        assert config.scanning.max_file_size == 50000000


class TestLoadConfig:
    """Tests for configuration loading."""

    def test_load_default_config(self):
        """Test loading default configuration."""
        config = load_config()
        assert isinstance(config, HifzDefendConfig)
        assert config.clamav.host == "localhost"

    def test_load_nonexistent_file(self):
        """Test loading nonexistent config file."""
        nonexistent = Path("/nonexistent/config.toml")
        with pytest.raises(ConfigurationError):
            load_config(nonexistent)

    def test_load_invalid_toml(self, temp_dir):
        """Test loading invalid TOML file."""
        invalid_toml = temp_dir / "invalid.toml"
        invalid_toml.write_text("this is not valid TOML {{{")

        with pytest.raises(ConfigurationError):
            load_config(invalid_toml)
