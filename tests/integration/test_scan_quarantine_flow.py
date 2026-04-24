from pathlib import Path

from bw_defend.core.engine import scan_target
from bw_defend.core.incidents import create_incident, list_incidents
from bw_defend.core.quarantine import quarantine_file


def test_scan_detect_and_quarantine(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    testfile = tmp_path / "sample.txt"
    testfile.write_text("EICAR-STANDARD-ANTIVIRUS-TEST-FILE")

    scan = scan_target(str(tmp_path))
    assert scan["detection_count"] >= 1

    incident = create_incident(
        source="scan",
        artifact=str(testfile),
        detection_type="signature",
        severity="high",
        confidence=0.99,
        approval_required=False,
        remediation_plan=[{"action": "quarantine"}],
    )
    assert incident.id.startswith("inc-")
    assert len(list_incidents()) == 1

    quarantine_file(str(testfile))
    assert not testfile.exists()
