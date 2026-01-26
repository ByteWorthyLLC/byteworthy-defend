"""
Configuration loader with Pydantic validation.
"""

import os
import sys
from pathlib import Path
from typing import Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from pydantic import BaseModel, Field, field_validator

from ..utils.exceptions import ConfigurationError
from ..utils.helpers import expand_windows_path


class ClamAVConfig(BaseModel):
    """ClamAV daemon connection configuration."""

    host: str = "localhost"
    port: int = Field(default=3310, ge=1, le=65535)
    timeout: int = Field(default=60, ge=1, le=600)


class ScanningConfig(BaseModel):
    """Scanning configuration."""

    max_file_size: int = Field(default=104857600, ge=0)
    scan_archives: bool = True
    scan_recursively: bool = True
    follow_symlinks: bool = False
    excluded_paths: list[str] = Field(default_factory=list)
    excluded_extensions: list[str] = Field(default_factory=list)

    @field_validator("excluded_extensions")
    @classmethod
    def validate_extensions(cls, v: list[str]) -> list[str]:
        """Ensure extensions start with a dot."""
        return [ext if ext.startswith(".") else f".{ext}" for ext in v]


class MonitoringConfig(BaseModel):
    """Real-time monitoring configuration."""

    enabled: bool = False
    watch_paths: list[str] = Field(default_factory=list)
    scan_on_create: bool = True
    scan_on_modify: bool = False


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_dir: str = Field(default="%LOCALAPPDATA%\\HifzDefend\\logs")
    max_log_size: int = Field(default=10485760, ge=1024)
    backup_count: int = Field(default=5, ge=0, le=100)
    format: str = Field(default="json", pattern=r"^(json|text)$")

    @property
    def log_dir_path(self) -> Path:
        """Return expanded log directory path."""
        return expand_windows_path(self.log_dir)


class ReportingConfig(BaseModel):
    """Reporting configuration."""

    report_dir: str = Field(default="%LOCALAPPDATA%\\HifzDefend\\reports")
    save_clean_scans: bool = False
    report_format: str = Field(default="json", pattern=r"^(json|html|text)$")

    @property
    def report_dir_path(self) -> Path:
        """Return expanded report directory path."""
        return expand_windows_path(self.report_dir)


class QuarantineConfig(BaseModel):
    """Quarantine configuration."""

    enabled: bool = True
    quarantine_dir: str = Field(default="%LOCALAPPDATA%\\HifzDefend\\quarantine")
    auto_quarantine: bool = True

    @property
    def quarantine_dir_path(self) -> Path:
        """Return expanded quarantine directory path."""
        return expand_windows_path(self.quarantine_dir)


class HifzDefendConfig(BaseModel):
    """Main HifzDefend configuration."""

    clamav: ClamAVConfig = Field(default_factory=ClamAVConfig)
    scanning: ScanningConfig = Field(default_factory=ScanningConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
    quarantine: QuarantineConfig = Field(default_factory=QuarantineConfig)


def find_config_file() -> Optional[Path]:
    """
    Find configuration file using search order:
    1. HIFZDEFEND_CONFIG environment variable
    2. %LOCALAPPDATA%\\HifzDefend\\hifzdefend.toml
    3. Project config/hifzdefend.defaults.toml

    Returns:
        Path to config file or None if not found
    """
    # 1. Check environment variable
    env_config = os.environ.get("HIFZDEFEND_CONFIG")
    if env_config:
        env_path = Path(env_config)
        if env_path.exists() and env_path.is_file():
            return env_path

    # 2. Check user config directory
    local_appdata = Path(os.environ.get("LOCALAPPDATA", "~/.local/share")).expanduser()
    user_config = local_appdata / "HifzDefend" / "hifzdefend.toml"
    if user_config.exists() and user_config.is_file():
        return user_config

    # 3. Check project defaults
    # Get project root (4 levels up from this file: config/loader.py -> config -> src -> project)
    project_root = Path(__file__).parent.parent.parent.parent
    default_config = project_root / "config" / "hifzdefend.defaults.toml"
    if default_config.exists() and default_config.is_file():
        return default_config

    return None


def load_config(config_path: Optional[Path] = None) -> HifzDefendConfig:
    """
    Load configuration from TOML file.

    Args:
        config_path: Optional explicit path to config file

    Returns:
        Validated HifzDefendConfig instance

    Raises:
        ConfigurationError: If config cannot be loaded or is invalid
    """
    # If no explicit path, find config file
    if config_path is None:
        config_path = find_config_file()

    # If still no config found, use defaults
    if config_path is None:
        return HifzDefendConfig()

    # Load TOML file
    try:
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)
    except FileNotFoundError:
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    except PermissionError:
        raise ConfigurationError(f"Permission denied reading config: {config_path}")
    except Exception as e:
        raise ConfigurationError(f"Failed to parse TOML config: {e}")

    # Validate with Pydantic
    try:
        return HifzDefendConfig(**config_data)
    except Exception as e:
        raise ConfigurationError(f"Invalid configuration: {e}")


def get_config() -> HifzDefendConfig:
    """
    Get configuration singleton.

    Returns:
        HifzDefendConfig instance
    """
    # Simple implementation - can be enhanced with caching if needed
    return load_config()
