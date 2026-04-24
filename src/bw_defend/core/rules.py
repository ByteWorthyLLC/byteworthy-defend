from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from bw_defend.core.paths import active_rules_file, rules_dir

DEFAULT_RULES = {
    "version": "2026.04.0",
    "rules": [
        {"id": "MAL-EICAR-001", "pattern": "EICAR-STANDARD-ANTIVIRUS-TEST-FILE", "severity": "high"},
        {"id": "SUS-DANG-002", "pattern": "rm -rf /", "severity": "critical"},
    ],
}


def ensure_rules() -> Path:
    r_dir = rules_dir()
    r_dir.mkdir(parents=True, exist_ok=True)
    path = active_rules_file()
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_RULES, indent=2, sort_keys=True))
    checksum_file = path.with_suffix(path.suffix + ".sha256")
    if not checksum_file.exists():
        checksum_file.write_text(f"{_sha256(path)}  {path.name}\n")
    return path


def list_rules() -> dict:
    path = ensure_rules()
    return json.loads(path.read_text())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_rules(path: Path | None = None) -> dict[str, str | bool]:
    target = path or ensure_rules()
    hash_file = target.with_suffix(target.suffix + ".sha256")
    actual = _sha256(target)
    if not hash_file.exists():
        return {"verified": False, "reason": "missing checksum file", "sha256": actual}
    expected = hash_file.read_text().strip().split()[0]
    return {
        "verified": expected == actual,
        "expected": expected,
        "actual": actual,
        "reason": "ok" if expected == actual else "checksum mismatch",
    }


def update_rules(bundle_path: str) -> dict[str, str | bool]:
    src = Path(bundle_path).expanduser().resolve()
    checksum = src.with_suffix(src.suffix + ".sha256")
    if not src.exists():
        raise FileNotFoundError(f"bundle not found: {src}")
    if not checksum.exists():
        raise FileNotFoundError(f"checksum file not found: {checksum}")

    actual = _sha256(src)
    expected = checksum.read_text().strip().split()[0]
    if actual != expected:
        return {
            "updated": False,
            "reason": "bundle integrity verification failed",
            "expected": expected,
            "actual": actual,
        }

    dst = ensure_rules()
    shutil.copyfile(src, dst)
    dst.with_suffix(dst.suffix + ".sha256").write_text(f"{actual}  {dst.name}\n")
    return {"updated": True, "reason": "rules updated and verified", "sha256": actual}
