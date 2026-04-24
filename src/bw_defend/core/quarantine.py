from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .errors import QuarantineError
from .fs import atomic_write_json
from .paths import quarantine_dir, state_dir


@dataclass(slots=True)
class QuarantineItem:
    id: str
    original_path: str
    quarantined_path: str
    timestamp: str

    def to_dict(self) -> dict[str, str]:
        return {
            KEY_ID: self.id,
            KEY_ORIGINAL_PATH: self.original_path,
            KEY_QUARANTINED_PATH: self.quarantined_path,
            KEY_TIMESTAMP: self.timestamp,
        }


MANIFEST = "manifest.json"
KEY_ID = "id"
KEY_ORIGINAL_PATH = "original_path"
KEY_QUARANTINED_PATH = "quarantined_path"
KEY_TIMESTAMP = "timestamp"
REQUIRED_ENTRY_KEYS = (KEY_ID, KEY_ORIGINAL_PATH, KEY_QUARANTINED_PATH, KEY_TIMESTAMP)


def _best_effort_chmod(path: Path, mode: int) -> None:
    try:
        path.chmod(mode)
    except OSError:
        return


def _path_within(parent: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(parent)
        return True
    except ValueError:
        return False


def _move_file_into_quarantine(src: Path, dst: Path) -> None:
    with src.open("rb") as src_handle, dst.open("xb") as dst_handle:
        shutil.copyfileobj(src_handle, dst_handle, length=1024 * 64)
    _best_effort_chmod(dst, 0o600)
    src.unlink()


def _manifest_path() -> Path:
    return quarantine_dir() / MANIFEST


def _validate_manifest_entry(entry: object, index: int) -> dict[str, str]:
    if not isinstance(entry, dict):
        raise QuarantineError(f"quarantine manifest entry {index} must be object")
    for key in REQUIRED_ENTRY_KEYS:
        value = entry.get(key)
        if not isinstance(value, str):
            raise QuarantineError(f"quarantine manifest entry {index} missing '{key}'")
        if not value.strip():
            raise QuarantineError(f"quarantine manifest entry {index} has empty '{key}'")
    if not str(entry[KEY_ID]).startswith("q-"):
        raise QuarantineError(f"quarantine manifest entry {index} has invalid id format")
    return entry  # type: ignore[return-value]


def _load_manifest() -> list[dict[str, str]]:
    path = _manifest_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise QuarantineError("quarantine manifest is not valid JSON") from exc
    if not isinstance(data, list):
        raise QuarantineError("quarantine manifest must be a list")
    return [_validate_manifest_entry(entry, index) for index, entry in enumerate(data)]


def _save_manifest(entries: list[dict[str, str]]) -> None:
    q_dir = quarantine_dir()
    q_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    _best_effort_chmod(q_dir, 0o700)
    atomic_write_json(_manifest_path(), entries, mode=0o600)


def quarantine_file(path: str) -> QuarantineItem:
    raw = Path(path).expanduser()
    if raw.is_symlink():
        raise QuarantineError(f"artifact must not be a symlink: {raw}")
    src = raw.resolve()
    if not src.exists():
        raise QuarantineError(f"artifact does not exist: {src}")
    if not src.is_file():
        raise QuarantineError(f"artifact must be a regular file: {src}")
    state_dir().mkdir(parents=True, exist_ok=True)
    q_dir = quarantine_dir()
    q_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    _best_effort_chmod(q_dir, 0o700)
    if q_dir in src.parents:
        raise QuarantineError("artifact is already under quarantine directory")

    item_id = f"q-{uuid.uuid4().hex[:12]}"
    dst = q_dir / item_id
    _move_file_into_quarantine(src, dst)

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
    q_root = quarantine_dir().resolve()
    for entry in entries:
        if entry[KEY_ID] == item_id:
            src = Path(entry[KEY_QUARANTINED_PATH]).expanduser().resolve()
            if not _path_within(q_root, src):
                raise QuarantineError(f"quarantined artifact path escapes quarantine directory: {src}")
            if not src.exists():
                raise QuarantineError(f"quarantined artifact no longer exists: {src}")
            dst = Path(entry[KEY_ORIGINAL_PATH]).expanduser().resolve(strict=False)
            if _path_within(q_root, dst):
                raise QuarantineError("refusing to restore into quarantine directory")
            if dst.exists():
                raise QuarantineError(f"refusing to overwrite existing destination: {dst}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            entries.remove(entry)
            _save_manifest(entries)
            return entry
    raise QuarantineError(f"quarantine item not found: {item_id}")


def purge_quarantine() -> int:
    entries = _load_manifest()
    removed = 0
    q_root = quarantine_dir().resolve()
    for entry in entries:
        q_path = Path(entry[KEY_QUARANTINED_PATH]).expanduser().resolve()
        if not _path_within(q_root, q_path):
            raise QuarantineError(f"quarantined artifact path escapes quarantine directory: {q_path}")
        if q_path.exists():
            if not q_path.is_file():
                raise QuarantineError(f"quarantined artifact is not a regular file: {q_path}")
            q_path.unlink()
            removed += 1
    _save_manifest([])
    return removed
