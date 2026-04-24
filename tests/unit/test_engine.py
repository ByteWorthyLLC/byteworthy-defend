import pytest
from pathlib import Path

from bw_defend.core.engine import scan_target
from bw_defend.core.errors import ScanTargetError
from bw_defend.core.rules import ensure_rules


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
