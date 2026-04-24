from pathlib import Path

from bw_defend.ai.remediation import remediate_incident
from bw_defend.core.config import DefendConfig, RemediationPolicy
from bw_defend.core.incidents import create_incident


def _config() -> DefendConfig:
    return DefendConfig(
        edition="ai",
        remediation_policy=RemediationPolicy(
            allow_auto_quarantine=True,
            allow_auto_temp_isolation=True,
            destructive_requires_approval=True,
            auto_execute_min_confidence=0.8,
        ),
    )


def test_block_destructive_without_approval(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    sample = tmp_path / "danger.bin"
    sample.write_text("bad")

    incident = create_incident(
        source="scan",
        artifact=str(sample),
        detection_type="behavior",
        severity="critical",
        confidence=0.95,
        approval_required=True,
        remediation_plan=[{"action": "delete"}],
    )

    result = remediate_incident(incident.id, _config(), approve=False)
    assert result["ok"] is True
    assert result["actions"][0]["executed"] is False


def test_approved_destructive_action_executes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    sample = tmp_path / "danger.bin"
    sample.write_text("bad")

    incident = create_incident(
        source="scan",
        artifact=str(sample),
        detection_type="behavior",
        severity="critical",
        confidence=0.95,
        approval_required=True,
        remediation_plan=[{"action": "network_block"}],
    )

    result = remediate_incident(incident.id, _config(), approve=True)
    assert result["ok"] is True
    assert result["actions"][0]["executed"] is True


def test_unknown_remediation_action_is_blocked(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    sample = tmp_path / "artifact.bin"
    sample.write_text("bad")

    incident = create_incident(
        source="scan",
        artifact=str(sample),
        detection_type="behavior",
        severity="critical",
        confidence=0.99,
        approval_required=True,
        remediation_plan=[{"action": "self_destruct"}],
    )

    result = remediate_incident(incident.id, _config(), approve=True)
    assert result["ok"] is True
    assert result["actions"][0]["executed"] is False
    assert "unknown action" in result["actions"][0]["reason"]
