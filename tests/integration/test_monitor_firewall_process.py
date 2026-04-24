from bw_defend.monitor.service import monitor_status, start_monitor, stop_monitor
from bw_defend.security.firewall import apply, revert, status
from bw_defend.security.process_control import kill_process


def test_monitor_lifecycle(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    assert start_monitor()["running"] is True
    assert monitor_status()["running"] is True
    assert stop_monitor()["running"] is False


def test_firewall_apply_revert(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    assert apply()["active"] is True
    assert status()["active"] is True
    assert revert()["active"] is False


def test_process_kill_requires_approval() -> None:
    result = kill_process(999999, approve=False)
    assert result["killed"] is False
    assert result["approval_required"] is True
