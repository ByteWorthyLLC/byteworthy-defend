from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
        path.write_text(DEFAULT_CONFIG)
    return path


def load_config() -> DefendConfig:
    path = ensure_config_exists()
    data = tomllib.loads(path.read_text())
    edition = str(data.get("edition", "core")).lower()
    if edition not in {"core", "ai"}:
        raise ValueError("edition must be one of: core, ai")
    rp_data = data.get("remediation_policy", {})
    policy = RemediationPolicy(
        allow_auto_quarantine=bool(rp_data.get("allow_auto_quarantine", True)),
        allow_auto_temp_isolation=bool(rp_data.get("allow_auto_temp_isolation", True)),
        destructive_requires_approval=bool(rp_data.get("destructive_requires_approval", True)),
        auto_execute_min_confidence=float(rp_data.get("auto_execute_min_confidence", 0.85)),
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
