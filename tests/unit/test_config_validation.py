import pytest

from bw_defend.core.config import load_config
from bw_defend.core.errors import ConfigValidationError


def test_invalid_confidence_raises_config_error(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / "cfg"
    config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("BW_DEFEND_CONFIG_DIR", str(config_dir))
    (config_dir / "config.toml").write_text(
        """
edition = "core"

[remediation_policy]
auto_execute_min_confidence = 1.5
allow_auto_quarantine = true
allow_auto_temp_isolation = true
destructive_requires_approval = true
"""
    )

    with pytest.raises(ConfigValidationError) as exc:
        load_config()
    assert "between 0 and 1" in str(exc.value)


def test_telemetry_enabled_requires_endpoint(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / "cfg"
    config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("BW_DEFEND_CONFIG_DIR", str(config_dir))
    (config_dir / "config.toml").write_text(
        """
edition = "core"

[remediation_policy]
allow_auto_quarantine = true
allow_auto_temp_isolation = true
destructive_requires_approval = true
auto_execute_min_confidence = 0.85

[telemetry]
enabled = true
endpoint = ""
"""
    )

    with pytest.raises(ConfigValidationError) as exc:
        load_config()
    assert "endpoint is required" in str(exc.value)


def test_telemetry_invalid_retry_limit_rejected(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / "cfg"
    config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("BW_DEFEND_CONFIG_DIR", str(config_dir))
    (config_dir / "config.toml").write_text(
        """
edition = "core"

[remediation_policy]
allow_auto_quarantine = true
allow_auto_temp_isolation = true
destructive_requires_approval = true
auto_execute_min_confidence = 0.85

[telemetry]
enabled = false
endpoint = ""
max_retries = 20
"""
    )

    with pytest.raises(ConfigValidationError) as exc:
        load_config()
    assert "max_retries must be between 0 and 10" in str(exc.value)
