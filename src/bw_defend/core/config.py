from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bw_defend.core.errors import ConfigValidationError
from bw_defend.core.fs import atomic_write_text
from bw_defend.core.paths import config_file


@dataclass(slots=True)
class RemediationPolicy:
    allow_auto_quarantine: bool = True
    allow_auto_temp_isolation: bool = True
    destructive_requires_approval: bool = True
    auto_execute_min_confidence: float = 0.85


@dataclass(slots=True)
class DefendConfig:
    edition: str = "core"
    remediation_policy: RemediationPolicy = field(default_factory=RemediationPolicy)


DEFAULT_CONFIG = """edition = "core"

[remediation_policy]
allow_auto_quarantine = true
allow_auto_temp_isolation = true
destructive_requires_approval = true
auto_execute_min_confidence = 0.85
"""


def ensure_config_exists() -> Path:
    path = config_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        atomic_write_text(path, DEFAULT_CONFIG, mode=0o600)
    return path


def _require_bool(source: dict[str, Any], key: str, default: bool) -> bool:
    if key not in source:
        return default
    value = source[key]
    if not isinstance(value, bool):
        raise ConfigValidationError(f"config key '{key}' must be boolean")
    return value


def _require_float(source: dict[str, Any], key: str, default: float) -> float:
    if key not in source:
        return default
    value = source[key]
    if not isinstance(value, (int, float)):
        raise ConfigValidationError(f"config key '{key}' must be numeric")
    return float(value)


def load_config() -> DefendConfig:
    path = ensure_config_exists()
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise ConfigValidationError(f"config is not valid TOML: {exc}") from exc

    edition = str(data.get("edition", "core")).lower()
    if edition not in {"core", "ai"}:
        raise ConfigValidationError("edition must be one of: core, ai")

    rp_data = data.get("remediation_policy", {})
    if not isinstance(rp_data, dict):
        raise ConfigValidationError("remediation_policy must be a TOML table")

    min_conf = _require_float(rp_data, "auto_execute_min_confidence", 0.85)
    if min_conf < 0 or min_conf > 1:
        raise ConfigValidationError("auto_execute_min_confidence must be between 0 and 1")

    policy = RemediationPolicy(
        allow_auto_quarantine=_require_bool(rp_data, "allow_auto_quarantine", True),
        allow_auto_temp_isolation=_require_bool(rp_data, "allow_auto_temp_isolation", True),
        destructive_requires_approval=_require_bool(rp_data, "destructive_requires_approval", True),
        auto_execute_min_confidence=min_conf,
    )
    return DefendConfig(edition=edition, remediation_policy=policy)


def config_as_dict(config: DefendConfig) -> dict[str, Any]:
    return {
        "edition": config.edition,
        "remediation_policy": {
            "allow_auto_quarantine": config.remediation_policy.allow_auto_quarantine,
            "allow_auto_temp_isolation": config.remediation_policy.allow_auto_temp_isolation,
            "destructive_requires_approval": config.remediation_policy.destructive_requires_approval,
            "auto_execute_min_confidence": config.remediation_policy.auto_execute_min_confidence,
        },
    }
