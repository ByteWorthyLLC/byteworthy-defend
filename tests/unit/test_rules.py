import hashlib
import json
from pathlib import Path

from bw_defend.core.rules import update_rules, verify_rules


def test_verify_missing_checksum(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    path = tmp_path / "manual-rules.json"
    path.write_text("{}")
    result = verify_rules(path)
    assert result["verified"] is False


def test_update_rules_integrity_success(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    bundle = tmp_path / "rules.json"
    bundle.write_text(json.dumps({"version": "x", "rules": []}))
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    bundle.with_suffix(".json.sha256").write_text(f"{digest}  rules.json\n")

    result = update_rules(str(bundle))
    assert result["updated"] is True
