import json

from typer.testing import CliRunner

from bw_defend.cli.main import app
from bw_defend.core.models import INCIDENT_REQUIRED_FIELDS, INCIDENT_SCHEMA_VERSION, IncidentRecord


runner = CliRunner()

REQUIRED_TOP_LEVEL_COMMANDS = {
    "scan",
    "monitor",
    "quarantine",
    "firewall",
    "process",
    "ai",
    "rules",
    "audit",
    "doctor",
}


def test_cli_command_surface_contract_v1() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in REQUIRED_TOP_LEVEL_COMMANDS:
        assert command in result.stdout


def test_incident_schema_contract_v1() -> None:
    incident = IncidentRecord.new(
        incident_id="inc-contractv1",
        source="scan",
        artifact="/tmp/sample",
        detection_type="signature",
        severity="high",
        confidence=0.99,
        approval_required=False,
        remediation_plan=[{"action": "quarantine"}],
    )
    payload = incident.to_dict()
    assert payload["schema_version"] == INCIDENT_SCHEMA_VERSION
    for field in INCIDENT_REQUIRED_FIELDS:
        assert field in payload


def test_doctor_json_contract_v1(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr("bw_defend.cli.main.platform.system", lambda: "Linux")

    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert set(payload["checks"].keys()) == {"supported_platform", "config_loaded", "state_writable"}
    assert payload["platform"] == "linux"
