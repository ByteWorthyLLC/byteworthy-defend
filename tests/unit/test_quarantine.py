import os
import json
from pathlib import Path

import pytest

from bw_defend.core.errors import QuarantineError
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


def test_quarantine_rejects_symlink_artifact(tmp_path: Path, monkeypatch) -> None:
    if os.name == "nt":
        pytest.skip("symlink creation is not reliable across all windows CI environments")
    state = tmp_path / "state"
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(state))
    real_file = tmp_path / "real.txt"
    real_file.write_text("EICAR-STANDARD-ANTIVIRUS-TEST-FILE")
    linked = tmp_path / "linked.txt"
    linked.symlink_to(real_file)

    with pytest.raises(QuarantineError, match="must not be a symlink"):
        quarantine_file(str(linked))


def test_restore_refuses_overwrite_existing_destination(tmp_path: Path, monkeypatch) -> None:
    state = tmp_path / "state"
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(state))
    infected = tmp_path / "infected.txt"
    infected.write_text("EICAR-STANDARD-ANTIVIRUS-TEST-FILE")
    item = quarantine_file(str(infected))

    infected.write_text("safe replacement")
    with pytest.raises(QuarantineError, match="refusing to overwrite existing destination"):
        restore_item(item.id)


def test_purge_rejects_manifest_path_escape(tmp_path: Path, monkeypatch) -> None:
    state = tmp_path / "state"
    monkeypatch.setenv("BW_DEFEND_STATE_DIR", str(state))
    outside = tmp_path / "outside.txt"
    outside.write_text("keep me")
    qdir = state / "quarantine"
    qdir.mkdir(parents=True, exist_ok=True)
    (qdir / "manifest.json").write_text(
        json.dumps(
            [
                {
                    "id": "q-badentry",
                    "original_path": str(tmp_path / "orig.txt"),
                    "quarantined_path": str(outside),
                    "timestamp": "2026-01-01T00:00:00+00:00",
                }
            ]
        )
    )

    with pytest.raises(QuarantineError, match="escapes quarantine directory"):
        purge_quarantine()
    assert outside.exists()
