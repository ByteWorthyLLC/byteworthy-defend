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
    check_interval: int = Field(default=60, ge=1)
    max_events_per_minute: int = Field(default=100, ge=1)
    event_retention_days: int = Field(default=30, ge=1)


class FileBlockingConfig(BaseModel):
    """File blocking configuration."""

    enabled: bool = True
    blocked_extensions: list[str] = Field(default_factory=lambda: [".scr", ".pif"])
    context_aware: bool = True


class AppWhitelistConfig(BaseModel):
    """Application whitelist configuration."""

    enabled: bool = True
    whitelist_mode: bool = False
    whitelisted_apps: list[str] = Field(default_factory=list)
    verify_signatures: bool = True
    check_file_hash: bool = True


class RulesEngineConfig(BaseModel):
    """Custom rules engine configuration."""

    yara_rules_enabled: bool = True
    custom_signatures_path: str = Field(default="%LOCALAPPDATA%\\HifzDefend\\signatures\\custom")
    community_signatures_path: str = Field(default="%LOCALAPPDATA%\\HifzDefend\\signatures\\community")
    file_blocking: FileBlockingConfig = Field(default_factory=FileBlockingConfig)
    app_whitelist: AppWhitelistConfig = Field(default_factory=AppWhitelistConfig)
    default_action: str = Field(default="alert", pattern=r"^(alert|block|quarantine|terminate|log_only)$")
    auto_quarantine_critical: bool = True
    auto_terminate_processes: bool = False

    @property
    def custom_signatures_path_expanded(self) -> Path:
        """Return expanded custom signatures path."""
        return expand_windows_path(self.custom_signatures_path)

    @property
    def community_signatures_path_expanded(self) -> Path:
        """Return expanded community signatures path."""
        return expand_windows_path(self.community_signatures_path)


class ThreatIntelAPIKeys(BaseModel):
    """Threat intelligence API keys."""

    abuseipdb: str = ""
    virustotal: str = ""
    snyk: str = ""
    socket_dev: str = ""


class ThreatIntelCache(BaseModel):
    """Threat intelligence cache configuration."""

    enabled: bool = True
    max_entries: int = Field(default=10000, ge=100)
    eviction_policy: str = Field(default="lru", pattern=r"^(lru|fifo)$")


class ThreatIntelConfig(BaseModel):
    """Threat intelligence integration configuration."""

    enabled: bool = True
    cache_ttl: int = Field(default=3600, ge=60)
    rate_limit_per_minute: int = Field(default=60, ge=1)
    api_keys: ThreatIntelAPIKeys = Field(default_factory=ThreatIntelAPIKeys)
    cache: ThreatIntelCache = Field(default_factory=ThreatIntelCache)


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


class ClaudeConfig(BaseModel):
    """Claude AI configuration."""

    enabled: bool = True
    api_key: str = Field(default="${CLAUDE_API_KEY}")
    model: str = Field(default="claude-sonnet-4-20250514")
    max_tokens: int = Field(default=2048, ge=256, le=8192)
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    timeout: int = Field(default=30, ge=5, le=300)

    # Caching
    cache_responses: bool = True
    cache_ttl: int = Field(default=3600, ge=60)
    cache_path: str = Field(default="%LOCALAPPDATA%\\HifzDefend\\data\\cache\\claude")

    # Cost controls
    max_requests_per_hour: int = Field(default=100, ge=1)
    warn_at_cost: float = Field(default=10.0, ge=0.0)
    stop_at_cost: float = Field(default=50.0, ge=0.0)
    log_api_costs: bool = True

    # Error handling
    fallback_on_error: bool = True
    retry_attempts: int = Field(default=3, ge=1, le=10)
    retry_delay: int = Field(default=2, ge=1, le=60)

    # Features
    script_analysis: bool = True
    network_analysis: bool = True
    file_analysis: bool = True
    incident_reports: bool = True
    plain_language_explanations: bool = True

    @property
    def cache_path_expanded(self) -> Path:
        """Return expanded cache path."""
        return expand_windows_path(self.cache_path)

    def get_api_key(self) -> str:
        """
        Get API key, resolving environment variable if needed.

        Returns:
            Resolved API key
        """
        import logging

        api_key = self.api_key

        # Check if using environment variable (recommended)
        if api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            api_key = os.environ.get(env_var, "")
        else:
            # Warn if API key is hardcoded in config file (security risk)
            if api_key and api_key.startswith("sk-ant-"):
                logger = logging.getLogger(__name__)
                logger.warning(
                    "API key is stored directly in config file. "
                    "This is less secure than using environment variables. "
                    "Recommended: Set api_key='${CLAUDE_API_KEY}' in config and use environment variable instead."
                )

        return api_key


class ChromaDBConfig(BaseModel):
    """ChromaDB vector database configuration."""

    collection_name: str = Field(default="security_logs")
    distance_metric: str = Field(default="cosine", pattern=r"^(cosine|l2|ip)$")
    persist_directory: str = Field(default="%LOCALAPPDATA%\\HifzDefend\\data\\vector_db")

    @property
    def persist_directory_path(self) -> Path:
        """Return expanded persist directory path."""
        return expand_windows_path(self.persist_directory)


class NaturalLanguageConfig(BaseModel):
    """Natural language query interface configuration."""

    enabled: bool = True
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    vector_db_path: str = Field(default="%LOCALAPPDATA%\\HifzDefend\\data\\vector_db")
    max_context_results: int = Field(default=5, ge=1, le=20)
    interactive_mode: bool = True
    chromadb: ChromaDBConfig = Field(default_factory=ChromaDBConfig)

    @property
    def vector_db_path_expanded(self) -> Path:
        """Return expanded vector DB path."""
        return expand_windows_path(self.vector_db_path)


class AIConfig(BaseModel):
    """AI integration configuration."""

    enabled: bool = True
    claude: ClaudeConfig = Field(default_factory=ClaudeConfig)
    natural_language: NaturalLanguageConfig = Field(default_factory=NaturalLanguageConfig)


class HifzDefendConfig(BaseModel):
    """Main HifzDefend configuration."""

    clamav: ClamAVConfig = Field(default_factory=ClamAVConfig)
    scanning: ScanningConfig = Field(default_factory=ScanningConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
    quarantine: QuarantineConfig = Field(default_factory=QuarantineConfig)
    rules: RulesEngineConfig = Field(default_factory=RulesEngineConfig)
    threat_intel: ThreatIntelConfig = Field(default_factory=ThreatIntelConfig)
    ai: AIConfig = Field(default_factory=AIConfig)


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


def _ensure_config_permissions(config_path: Path) -> None:
    """
    Ensure config file has restrictive permissions (owner read/write only).

    Args:
        config_path: Path to configuration file

    Note:
        This is a best-effort operation. Warnings are logged on failure.
    """
    import logging
    import stat

    logger = logging.getLogger(__name__)

    try:
        # Set permissions to 0o600 (rw-------)
        # Owner can read/write, no access for group/others
        os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
        logger.debug(f"Set restrictive permissions on config file: {config_path}")
    except Exception as e:
        logger.warning(
            f"Could not set restrictive permissions on config file {config_path}: {e}. "
            f"Consider setting file permissions manually to prevent unauthorized access."
        )


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

    # Enforce restrictive permissions on config file (security best practice)
    _ensure_config_permissions(config_path)

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
