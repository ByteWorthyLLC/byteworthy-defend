import json

import pytest

from bw_defend.core.audit import log_audit, verify_audit_chain
from bw_defend.core.paths import audit_log_path


@pytest.fixture(autouse=True)
def _isolated_state_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))


def test_verify_audit_chain_valid() -> None:
    log_audit("incident_created", {"id": "inc-1", "severity": "high"})
    log_audit("incident_updated", {"id": "inc-1", "status": "resolved"})

    with audit_log_path().open("r", encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle if line.strip()]

    assert len(records) == 2
    assert records[0]["prev_hash"] is None
    assert records[1]["prev_hash"] == records[0]["record_hash"]

    result = verify_audit_chain()
    assert result["status"] == "ok"
    assert result["reason"] == "audit chain verified"
    assert result["count"] == 2
    assert result["verified_count"] == 2
    assert result["legacy_count"] == 0


def test_verify_audit_chain_detects_tampering() -> None:
    log_audit("remediation_action_executed", {"incident_id": "inc-2", "ok": True})
    log_audit("remediation_action_executed", {"incident_id": "inc-3", "ok": True})

    with audit_log_path().open("r", encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle if line.strip()]

    records[1]["payload"]["ok"] = False
    audit_log_path().write_text("\n".join(json.dumps(item, sort_keys=True) for item in records) + "\n", encoding="utf-8")

    result = verify_audit_chain()
    assert result["status"] == "tampered"
    assert "record_hash mismatch" in result["reason"]
    assert result["count"] == 2
    assert result["verified_count"] == 1


def test_verify_audit_chain_empty_log() -> None:
    path = audit_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")

    result = verify_audit_chain()
    assert result["status"] == "empty"
    assert result["reason"] == "audit log is empty"
    assert result["count"] == 0
    assert result["verified_count"] == 0
    assert result["legacy_count"] == 0
