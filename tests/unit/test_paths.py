from pathlib import Path

from bw_defend.core.paths import config_dir, state_dir


def test_windows_default_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("BW_DEFEND_CONFIG_DIR", raising=False)
    monkeypatch.delenv("BW_DEFEND_STATE_DIR", raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData" / "Roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData" / "Local"))
    monkeypatch.setattr("bw_defend.core.paths._is_windows", lambda: True)

    assert config_dir() == Path(tmp_path / "AppData" / "Roaming" / "bw-defend")
    assert state_dir() == Path(tmp_path / "AppData" / "Local" / "bw-defend" / "state")


def test_custom_paths_override_windows_defaults(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("BW_DEFEND_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr("bw_defend.core.paths._is_windows", lambda: True)

    assert config_dir() == Path(tmp_path / "cfg")
    assert state_dir() == Path(tmp_path / "state")
