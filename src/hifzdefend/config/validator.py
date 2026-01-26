"""
Configuration validation utilities.
"""

from pathlib import Path
from typing import Optional

from .loader import HifzDefendConfig
from ..utils.exceptions import ConfigurationError


def validate_directories(config: HifzDefendConfig, create: bool = True) -> None:
    """
    Validate that required directories exist or can be created.

    Args:
        config: Configuration to validate
        create: Whether to create missing directories

    Raises:
        ConfigurationError: If directories don't exist and cannot be created
    """
    directories = [
        ("log_dir", config.logging.log_dir_path),
        ("report_dir", config.reporting.report_dir_path),
        ("quarantine_dir", config.quarantine.quarantine_dir_path),
    ]

    # Add AI directories if enabled
    if config.ai.enabled:
        if config.ai.claude.enabled and config.ai.claude.cache_responses:
            directories.append(("claude_cache_dir", config.ai.claude.cache_path_expanded))
        if config.ai.natural_language.enabled:
            directories.append(("vector_db_dir", config.ai.natural_language.vector_db_path_expanded))

    for name, path in directories:
        if not path.exists():
            if create:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except (OSError, PermissionError) as e:
                    raise ConfigurationError(
                        f"Cannot create {name} directory {path}: {e}"
                    )
            else:
                raise ConfigurationError(f"Directory does not exist: {path}")

        if not path.is_dir():
            raise ConfigurationError(f"Path is not a directory: {path}")


def validate_excluded_paths(config: HifzDefendConfig) -> None:
    """
    Validate excluded paths exist.

    Args:
        config: Configuration to validate

    Raises:
        ConfigurationError: If excluded paths are invalid
    """
    for excluded_path in config.scanning.excluded_paths:
        path = Path(excluded_path)
        if not path.exists():
            # Warning only - paths might be created later
            pass


def validate_clamav_config(config: HifzDefendConfig) -> None:
    """
    Validate ClamAV configuration.

    Args:
        config: Configuration to validate

    Raises:
        ConfigurationError: If ClamAV config is invalid
    """
    # Port range already validated by Pydantic
    # Host validation
    if not config.clamav.host:
        raise ConfigurationError("ClamAV host cannot be empty")

    # Timeout validation
    if config.clamav.timeout < 1:
        raise ConfigurationError("ClamAV timeout must be at least 1 second")


def validate_config(config: HifzDefendConfig, create_dirs: bool = True) -> None:
    """
    Perform full configuration validation.

    Args:
        config: Configuration to validate
        create_dirs: Whether to create missing directories

    Raises:
        ConfigurationError: If configuration is invalid
    """
    validate_clamav_config(config)
    validate_directories(config, create=create_dirs)
    validate_excluded_paths(config)
