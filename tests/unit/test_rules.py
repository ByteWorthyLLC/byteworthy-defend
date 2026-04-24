import hashlib
import hmac
import json
from pathlib import Path

from bw_defend.core.rules import update_rules, verify_rules


def _write_bundle(bundle: Path, payload: dict) -> None:
    bundle.write_text(json.dumps(payload))
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    bundle.with_suffix(".json.sha256").write_text(f"{digest}  {bundle.name}\n")


def _write_signature(bundle: Path, key: str, signature: str | None = None) -> None:
    actual_signature = signature or hmac.new(key.encode("utf-8"), bundle.read_bytes(), hashlib.sha256).hexdigest()
    bundle.with_suffix(".json.sig").write_text(f"{actual_signature}  {bundle.name}\n")


def test_verify_missing_checksum(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNATURE_REQUIRED", "false")
    path = tmp_path / "manual-rules.json"
    path.write_text("{}")
    result = verify_rules(path)
    assert result["verified"] is False


def test_verify_allows_missing_signature_when_not_required(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNATURE_REQUIRED", "false")
    bundle = tmp_path / "rules.json"
    _write_bundle(bundle, {"version": "x", "rules": []})

    result = verify_rules(bundle)
    assert result["verified"] is True
    assert result["reason"] == "ok"


def test_update_rules_integrity_success(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNATURE_REQUIRED", "false")
    bundle = tmp_path / "rules.json"
    _write_bundle(bundle, {"version": "x", "rules": []})

    result = update_rules(str(bundle))
    assert result["updated"] is True


def test_update_rules_rejects_invalid_schema(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNATURE_REQUIRED", "false")
    bundle = tmp_path / "rules.json"
    _write_bundle(bundle, {"version": "x", "rules": [{"id": "bad", "pattern": "x", "severity": "urgent"}]})

    result = update_rules(str(bundle))
    assert result["updated"] is False
    assert "severity" in str(result["reason"])


def test_verify_requires_signature_when_enabled(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNATURE_REQUIRED", "true")
    bundle = tmp_path / "rules.json"
    _write_bundle(bundle, {"version": "x", "rules": []})

    result = verify_rules(bundle)
    assert result["verified"] is False
    assert result["reason"] == "missing signature file"


def test_verify_rejects_invalid_signature_when_required(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNATURE_REQUIRED", "true")
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNING_KEY", "dev-signing-key")
    bundle = tmp_path / "rules.json"
    _write_bundle(bundle, {"version": "x", "rules": []})
    _write_signature(bundle, "dev-signing-key", signature="0" * 64)

    result = verify_rules(bundle)
    assert result["verified"] is False
    assert result["reason"] == "signature mismatch"


def test_update_rules_requires_signature_when_enabled(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNATURE_REQUIRED", "true")
    bundle = tmp_path / "rules.json"
    _write_bundle(bundle, {"version": "x", "rules": []})

    result = update_rules(str(bundle))
    assert result["updated"] is False
    assert result["reason"] == "missing signature file"


def test_update_rules_rejects_invalid_signature_when_required(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNATURE_REQUIRED", "true")
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNING_KEY", "dev-signing-key")
    bundle = tmp_path / "rules.json"
    _write_bundle(bundle, {"version": "x", "rules": []})
    _write_signature(bundle, "dev-signing-key", signature="f" * 64)

    result = update_rules(str(bundle))
    assert result["updated"] is False
    assert result["reason"] == "signature mismatch"


def test_update_rules_accepts_hex_and_sha256_pattern_types(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNATURE_REQUIRED", "false")
    bundle = tmp_path / "rules.json"
    _write_bundle(
        bundle,
        {
            "version": "x",
            "rules": [
                {"id": "HEX-001", "pattern_type": "hex", "pattern": "45 49 43 41 52", "severity": "high"},
                {
                    "id": "HASH-001",
                    "pattern_type": "sha256",
                    "pattern": "a" * 64,
                    "severity": "critical",
                },
            ],
        },
    )
    result = update_rules(str(bundle))
    assert result["updated"] is True


def test_update_rules_rejects_invalid_regex_pattern(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNATURE_REQUIRED", "false")
    bundle = tmp_path / "rules.json"
    _write_bundle(
        bundle,
        {
            "version": "x",
            "rules": [
                {"id": "REG-001", "pattern_type": "regex", "pattern": "(unterminated", "severity": "high"},
            ],
        },
    )
    result = update_rules(str(bundle))
    assert result["updated"] is False
    assert "regex pattern is invalid" in str(result["reason"])


def test_update_rules_rejects_invalid_sha256_pattern(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNATURE_REQUIRED", "false")
    bundle = tmp_path / "rules.json"
    _write_bundle(
        bundle,
        {
            "version": "x",
            "rules": [
                {"id": "HASH-001", "pattern_type": "sha256", "pattern": "not-a-digest", "severity": "high"},
            ],
        },
    )
    result = update_rules(str(bundle))
    assert result["updated"] is False
    assert "sha256 pattern must be a 64-character lowercase hex digest" in str(result["reason"])
