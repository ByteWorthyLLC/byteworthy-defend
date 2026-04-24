import json

from typer.testing import CliRunner

from bw_defend.cli.main import app
from bw_defend.core.audit import log_audit
from bw_defend.core.paths import audit_log_path
from bw_defend.core.rules import ensure_rules


runner = CliRunner()


def test_doctor_strict_exits_nonzero_on_unsupported_platform(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr("bw_defend.cli.main.platform.system", lambda: "Darwin")

    result = runner.invoke(app, ["doctor", "--strict", "--json"])
    assert result.exit_code == 2


def test_doctor_strict_passes_on_windows(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr("bw_defend.cli.main.platform.system", lambda: "Windows")

    result = runner.invoke(app, ["doctor", "--strict", "--json"])
    assert result.exit_code == 0
    assert '"supported_platform": true' in result.stdout
    assert '"platform": "windows"' in result.stdout


def test_doctor_strict_passes_on_linux(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr("bw_defend.cli.main.platform.system", lambda: "Linux")

    result = runner.invoke(app, ["doctor", "--strict", "--json"])
    assert result.exit_code == 0
    assert '"supported_platform": true' in result.stdout
    assert '"platform": "linux"' in result.stdout


def test_rules_verify_exits_two_on_checksum_mismatch(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    path = ensure_rules()
    payload = json.loads(path.read_text())
    payload["version"] = "tampered"
    path.write_text(json.dumps(payload))

    result = runner.invoke(app, ["rules", "verify", "--json"])
    assert result.exit_code == 2


def test_scan_invalid_target_exits_nonzero(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    result = runner.invoke(app, ["scan", str(tmp_path / "missing"), "--json"])
    assert result.exit_code == 1
    assert "does not exist" in result.stdout


def test_audit_verify_empty_log_exit_zero(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    result = runner.invoke(app, ["audit", "verify", "--json"])
    assert result.exit_code == 0
    assert '"status": "empty"' in result.stdout


def test_audit_verify_legacy_log_exit_two(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    log_path = audit_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        json.dumps(
            {
                "event_id": "audit-legacy",
                "timestamp": "2026-01-01T00:00:00+00:00",
                "event_type": "legacy",
                "payload": {"ok": True},
            }
        )
        + "\n"
    )
    result = runner.invoke(app, ["audit", "verify", "--json"])
    assert result.exit_code == 2
    assert '"status": "legacy_present"' in result.stdout


def test_audit_verify_chained_log_exit_zero(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    log_audit("incident_created", {"id": "inc-123"})
    result = runner.invoke(app, ["audit", "verify", "--json"])
    assert result.exit_code == 0
    assert '"status": "ok"' in result.stdout
