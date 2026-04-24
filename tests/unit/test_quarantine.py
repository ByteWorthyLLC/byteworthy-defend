import os
from pathlib import Path

from bw_defend.core.quarantine import list_quarantine, purge_quarantine, quarantine_file, restore_item


def test_quarantine_restore_and_purge(tmp_path: Path, monkeypatch) -> None:
    state = tmp_path / "state"
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(state))

    infected = tmp_path / "infected.txt"
    infected.write_text("EICAR-STANDARD-ANTIVIRUS-TEST-FILE")

    item = quarantine_file(str(infected))
    assert not infected.exists()
    assert len(list_quarantine()) == 1

    restored = restore_item(item.id)
    assert restored["id"] == item.id
    assert infected.exists()

    infected.write_text("new content")
    quarantine_file(str(infected))
    purged = purge_quarantine()
    assert purged == 1
    assert list_quarantine() == []


def test_quarantine_sets_restrictive_permissions_on_posix(tmp_path: Path, monkeypatch) -> None:
    if os.name == "nt":
        return
    state = tmp_path / "state"
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(state))
    infected = tmp_path / "infected.txt"
    infected.write_text("EICAR-STANDARD-ANTIVIRUS-TEST-FILE")

    item = quarantine_file(str(infected))
    manifest = state / "quarantine" / "manifest.json"
    qfile = Path(item.quarantined_path)
    assert manifest.exists()
    assert qfile.exists()
    assert oct(manifest.stat().st_mode & 0o777) == "0o600"
    assert oct(qfile.stat().st_mode & 0o777) == "0o600"
