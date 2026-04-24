from __future__ import annotations

import tomllib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .errors import ConfigValidationError
from .fs import atomic_write_text
from .paths import config_file


@dataclass(slots=True)
class RemediationPolicy:
    allow_auto_quarantine: bool = True
    allow_auto_temp_isolation: bool = True
    destructive_requires_approval: bool = True
    auto_execute_min_confidence: float = 0.85


@dataclass(slots=True)
class TelemetryConfig:
    enabled: bool = False
    endpoint: str = ""
    timeout_seconds: float = 3.0
    max_retries: int = 2
    auth_token_env: str = "BW_DEFEND_TELEMETRY_TOKEN"


@dataclass(slots=True)
class DefendConfig:
    edition: str = "core"
    remediation_policy: RemediationPolicy = field(default_factory=RemediationPolicy)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)


DEFAULT_CONFIG = """edition = "core"

[remediation_policy]
allow_auto_quarantine = true
allow_auto_temp_isolation = true
destructive_requires_approval = true
auto_execute_min_confidence = 0.85

[telemetry]
enabled = false
endpoint = ""
timeout_seconds = 3.0
max_retries = 2
auth_token_env = "BW_DEFEND_TELEMETRY_TOKEN"
"""


KEY_PREFIX = "config key "
TOKEN_ENV_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")


def ensure_config_exists() -> Path:
    path = config_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        atomic_write_text(path, DEFAULT_CONFIG, mode=0o600)
    return path


def _type_error(key: str, expected: str) -> ConfigValidationError:
    return ConfigValidationError(f"{KEY_PREFIX}'{key}' must be {expected}")


def _require_bool(source: dict[str, Any], key: str, *, default: bool) -> bool:
    if key not in source:
        return default
    value = source[key]
    if not isinstance(value, bool):
        raise _type_error(key, "boolean")
    return value


def _require_float(source: dict[str, Any], key: str, *, default: float) -> float:
    if key not in source:
        return default
    value = source[key]
    if not isinstance(value, (int, float)):
        raise _type_error(key, "numeric")
    return float(value)


def _require_int(source: dict[str, Any], key: str, *, default: int) -> int:
    if key not in source:
        return default
    value = source[key]
    if not isinstance(value, int):
        raise _type_error(key, "an integer")
    return int(value)


def _parse_edition(data: dict[str, Any]) -> str:
    edition = str(data.get("edition", "core")).strip().lower()
    if edition in {"core", "ai"}:
        return edition
    raise ConfigValidationError("edition must be one of: core, ai")


def _parse_policy(data: dict[str, Any]) -> RemediationPolicy:
    rp_data = data.get("remediation_policy", {})
    if not isinstance(rp_data, dict):
        raise ConfigValidationError("remediation_policy must be a TOML table")

    min_conf = _require_float(rp_data, "auto_execute_min_confidence", default=0.85)
    if not 0 <= min_conf <= 1:
        raise ConfigValidationError("auto_execute_min_confidence must be between 0 and 1")

    return RemediationPolicy(
        allow_auto_quarantine=_require_bool(rp_data, "allow_auto_quarantine", default=True),
        allow_auto_temp_isolation=_require_bool(rp_data, "allow_auto_temp_isolation", default=True),
        destructive_requires_approval=_require_bool(rp_data, "destructive_requires_approval", default=True),
        auto_execute_min_confidence=min_conf,
    )


def _parse_telemetry(data: dict[str, Any]) -> TelemetryConfig:
    telemetry_data = data.get("telemetry", {})
    if not isinstance(telemetry_data, dict):
        raise ConfigValidationError("telemetry must be a TOML table")
    telemetry = TelemetryConfig(
        enabled=_require_bool(telemetry_data, "enabled", default=False),
        endpoint=str(telemetry_data.get("endpoint", "")).strip(),
        timeout_seconds=_require_float(telemetry_data, "timeout_seconds", default=3.0),
        max_retries=_require_int(telemetry_data, "max_retries", default=2),
        auth_token_env=str(telemetry_data.get("auth_token_env", "BW_DEFEND_TELEMETRY_TOKEN")).strip(),
    )
    if telemetry.enabled and not telemetry.endpoint:
        raise ConfigValidationError("telemetry endpoint is required when telemetry.enabled is true")
    if telemetry.endpoint:
        parsed = urlparse(telemetry.endpoint)
        if not parsed.scheme or not parsed.netloc:
            raise ConfigValidationError("telemetry endpoint must be an absolute URL")
        if parsed.scheme != "https":
            raise ConfigValidationError("telemetry endpoint must use https")
    if not 0 < telemetry.timeout_seconds <= 30:
        raise ConfigValidationError("telemetry timeout_seconds must be between 0 and 30")
    if not 0 <= telemetry.max_retries <= 10:
        raise ConfigValidationError("telemetry max_retries must be between 0 and 10")
    if not telemetry.auth_token_env:
        raise ConfigValidationError("telemetry auth_token_env must be non-empty")
    if not TOKEN_ENV_PATTERN.fullmatch(telemetry.auth_token_env):
        raise ConfigValidationError("telemetry auth_token_env must match pattern ^[A-Z_][A-Z0-9_]*$")
    return telemetry


def load_config() -> DefendConfig:
    path = ensure_config_exists()
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise ConfigValidationError(f"config is not valid TOML: {exc}") from exc

    edition = _parse_edition(data)
    policy = _parse_policy(data)
    telemetry = _parse_telemetry(data)
    return DefendConfig(edition=edition, remediation_policy=policy, telemetry=telemetry)


def config_as_dict(config: DefendConfig) -> dict[str, Any]:
    return {
        "edition": config.edition,
        "remediation_policy": {
            "allow_auto_quarantine": config.remediation_policy.allow_auto_quarantine,
            "allow_auto_temp_isolation": config.remediation_policy.allow_auto_temp_isolation,
            "destructive_requires_approval": config.remediation_policy.destructive_requires_approval,
            "auto_execute_min_confidence": config.remediation_policy.auto_execute_min_confidence,
        },
        "telemetry": {
            "enabled": config.telemetry.enabled,
            "endpoint": config.telemetry.endpoint,
            "timeout_seconds": config.telemetry.timeout_seconds,
            "max_retries": config.telemetry.max_retries,
            "auth_token_env": config.telemetry.auth_token_env,
        },
    }
