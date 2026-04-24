from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from bw_defend.core.errors import QuarantineError
from bw_defend.core.fs import atomic_write_json
from bw_defend.core.paths import quarantine_dir, state_dir


@dataclass(slots=True)
class QuarantineItem:
    id: str
    original_path: str
    quarantined_path: str
    timestamp: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "original_path": self.original_path,
            "quarantined_path": self.quarantined_path,
            "timestamp": self.timestamp,
        }


MANIFEST = "manifest.json"


def _manifest_path() -> Path:
    return quarantine_dir() / MANIFEST


def _load_manifest() -> list[dict[str, str]]:
    path = _manifest_path()
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise QuarantineError("quarantine manifest must be a list")
    for index, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise QuarantineError(f"quarantine manifest entry {index} must be object")
        for key in ("id", "original_path", "quarantined_path", "timestamp"):
            if key not in entry or not isinstance(entry[key], str):
                raise QuarantineError(f"quarantine manifest entry {index} missing '{key}'")
    return data


def _save_manifest(entries: list[dict[str, str]]) -> None:
    q_dir = quarantine_dir()
    q_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(_manifest_path(), entries)


def quarantine_file(path: str) -> QuarantineItem:
    src = Path(path).expanduser().resolve()
    if not src.exists():
        raise QuarantineError(f"artifact does not exist: {src}")
    if not src.is_file():
        raise QuarantineError(f"artifact must be a regular file: {src}")
    state_dir().mkdir(parents=True, exist_ok=True)
    q_dir = quarantine_dir()
    q_dir.mkdir(parents=True, exist_ok=True)
    if q_dir in src.parents:
        raise QuarantineError("artifact is already under quarantine directory")

    item_id = f"q-{uuid.uuid4().hex[:12]}-{src.name}"
    dst = q_dir / item_id
    shutil.move(str(src), str(dst))

    item = QuarantineItem(
        id=item_id,
        original_path=str(src),
        quarantined_path=str(dst),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    entries = _load_manifest()
    entries.append(item.to_dict())
    _save_manifest(entries)
    return item


def list_quarantine() -> list[dict[str, str]]:
    return _load_manifest()


def restore_item(item_id: str) -> dict[str, str]:
    entries = _load_manifest()
    for entry in entries:
        if entry["id"] == item_id:
            src = Path(entry["quarantined_path"])
            if not src.exists():
                raise QuarantineError(f"quarantined artifact no longer exists: {src}")
            dst = Path(entry["original_path"])
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            entries.remove(entry)
            _save_manifest(entries)
            return entry
    raise QuarantineError(f"quarantine item not found: {item_id}")


def purge_quarantine() -> int:
    entries = _load_manifest()
    removed = 0
    for entry in entries:
        q_path = Path(entry["quarantined_path"])
        if q_path.exists():
            q_path.unlink()
            removed += 1
    _save_manifest([])
    return removed
