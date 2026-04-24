from bw_defend.core.config import load_config


def test_default_config_bootstrap(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_CONFIG_DIR", str(tmp_path / "config"))
    config = load_config()
    assert config.edition == "core"
