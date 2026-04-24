import pytest
import hashlib
import json
import os
from pathlib import Path

from bw_defend.core.engine import scan_target
from bw_defend.core.errors import ScanTargetError
from bw_defend.core.rules import ensure_rules, update_rules


def _write_bundle(bundle: Path, payload: dict) -> None:
    bundle.write_text(json.dumps(payload))
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    bundle.with_suffix(".json.sha256").write_text(f"{digest}  {bundle.name}\n")


def test_scan_target_missing_path_raises() -> None:
    with pytest.raises(ScanTargetError):
        scan_target("/tmp/path/that/does/not/exist-12345")


def test_scan_target_system_uses_env_override(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    ensure_rules()
    root = tmp_path / "root"
    root.mkdir()
    sample = root / "sample.txt"
    sample.write_text("EICAR-STANDARD-ANTIVIRUS-TEST-FILE")
    monkeypatch.setenv("BW_DEFEND_SYSTEM_SCAN_ROOTS", str(root))

    result = scan_target("system")
    assert result["detection_count"] >= 1
    assert any(Path(item["artifact"]) == sample for item in result["findings"])


def test_scan_target_detects_binary_literal_patterns(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    ensure_rules()
    binary = tmp_path / "payload.bin"
    binary.write_bytes(b"\x00fooEICAR-STANDARD-ANTIVIRUS-TEST-FILE\x00bar")

    result = scan_target(str(binary))
    assert result["detection_count"] == 1
    assert result["skipped_binary"] == 0


def test_scan_target_supports_regex_and_sha256_rules(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("BW_DEFEND_RULES_SIGNATURE_REQUIRED", "false")
    sample = tmp_path / "sample.ps1"
    sample.write_text("powershell -enc AAAA")
    sha256_value = hashlib.sha256(sample.read_bytes()).hexdigest()
    bundle = tmp_path / "rules.json"
    _write_bundle(
        bundle,
        {
            "version": "x",
            "rules": [
                {
                    "id": "REG-001",
                    "pattern_type": "regex",
                    "pattern": r"powershell\s+-enc\s+[A-Za-z0-9+/=]+",
                    "severity": "critical",
                },
                {
                    "id": "HASH-001",
                    "pattern_type": "sha256",
                    "pattern": sha256_value,
                    "severity": "critical",
                },
            ],
        },
    )
    update_result = update_rules(str(bundle))
    assert update_result["updated"] is True

    result = scan_target(str(sample))
    assert result["detection_count"] == 2
    types = {finding["detection_type"] for finding in result["findings"]}
    assert "hash" in types
    assert "signature" in types


def test_scan_target_honors_max_scan_bytes_env(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    ensure_rules()
    monkeypatch.setenv("BW_DEFEND_MAX_SCAN_BYTES", "16")
    large = tmp_path / "large.txt"
    large.write_text("EICAR-STANDARD-ANTIVIRUS-TEST-FILE and more")

    result = scan_target(str(large))
    assert result["detection_count"] == 0
    assert result["skipped_large"] == 1
    assert result["max_scan_bytes"] == 16


def test_scan_target_skips_symlink_files(tmp_path, monkeypatch) -> None:
    if os.name == "nt":
        pytest.skip("symlink creation is not reliable across all windows CI environments")
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    ensure_rules()
    real_file = tmp_path / "real.txt"
    real_file.write_text("EICAR-STANDARD-ANTIVIRUS-TEST-FILE")
    linked = tmp_path / "linked.txt"
    linked.symlink_to(real_file)

    result = scan_target(str(linked))
    assert result["detection_count"] == 0
    assert result["scanned_files"] == 0
