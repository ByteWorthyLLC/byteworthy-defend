from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
import os
import platform
import re
from pathlib import Path
from time import perf_counter
from typing import Iterable

from .errors import ScanTargetError
from .rules import list_rules


@dataclass(slots=True)
class Detection:
    artifact: str
    rule_id: str
    detection_type: str
    severity: str
    confidence: float


MAX_SCAN_BYTES_DEFAULT = 2 * 1024 * 1024
MAX_SCAN_BYTES_ENV = "BW_DEFEND_MAX_SCAN_BYTES"


def _default_system_roots() -> list[Path]:
    runtime_platform = platform.system().lower()
    if runtime_platform == "windows":
        roots: list[Path] = []
        for env in ("ProgramData", "TEMP", "TMP", "USERPROFILE"):
            value = os.getenv(env)
            if value:
                roots.append(Path(value).expanduser())
        return roots
    return [Path("/etc"), Path("/tmp"), Path("/var/tmp"), Path.home()]


def _system_scan_roots() -> list[Path]:
    custom = os.getenv("BW_DEFEND_SYSTEM_SCAN_ROOTS", "").strip()
    if custom:
        return [Path(part).expanduser() for part in custom.split(os.pathsep) if part.strip()]
    return _default_system_roots()


def _max_scan_bytes() -> int:
    raw = os.getenv(MAX_SCAN_BYTES_ENV, "").strip()
    if not raw:
        return MAX_SCAN_BYTES_DEFAULT
    try:
        value = int(raw)
    except ValueError:
        return MAX_SCAN_BYTES_DEFAULT
    return value if value > 0 else MAX_SCAN_BYTES_DEFAULT


def _iter_files_in_root(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    yield from (path for path in root.rglob("*") if path.is_file() and not path.is_symlink())


def _iter_paths(target: str) -> Iterable[Path]:
    if target == "system":
        for root in _system_scan_roots():
            yield from _iter_files_in_root(root)
        return

    start = Path(target).expanduser()
    if start.is_file():
        if start.is_symlink():
            return
        yield start
        return
    if start.is_dir():
        for path in start.rglob("*"):
            if path.is_file() and not path.is_symlink():
                yield path
        return
    raise ScanTargetError(f"scan target does not exist: {start}")


def _scan_file(path: Path, *, max_scan_bytes: int) -> tuple[bytes | None, str | None]:
    try:
        size = path.stat().st_size
    except OSError:
        return None, "unreadable"
    if size > max_scan_bytes:
        return None, "large"

    try:
        return path.read_bytes(), None
    except OSError:
        return None, "unreadable"


def _rule_pattern_type(rule: dict) -> str:
    return str(rule.get("pattern_type", "literal")).strip().lower()


def _matches_rule(*, rule: dict, data_bytes: bytes, data_text: str, file_sha256: str) -> bool:
    pattern = str(rule.get("pattern", ""))
    if not pattern:
        return False
    pattern_type = _rule_pattern_type(rule)
    if pattern_type == "sha256":
        return pattern.strip().lower() == file_sha256
    if pattern_type == "hex":
        needle = bytes.fromhex("".join(pattern.split()))
        return needle in data_bytes
    if pattern_type == "regex":
        flags = 0 if bool(rule.get("case_sensitive", True)) else re.IGNORECASE
        return re.search(pattern, data_text, flags=flags) is not None
    needle = pattern.encode("utf-8", errors="ignore")
    return (needle in data_bytes) if needle else (pattern in data_text)


def _match_file_against_rules(
    *,
    path: Path,
    data: bytes,
    rules: list[dict],
    seen: set[tuple[str, str]],
) -> list[dict]:
    findings: list[dict] = []
    path_text = str(path)
    data_text = data.decode("utf-8", errors="ignore")
    file_sha256 = hashlib.sha256(data).hexdigest()
    for rule in rules:
        rule_id = str(rule.get("id", "unknown"))
        key = (path_text, rule_id)
        if key in seen:
            continue
        try:
            matched = _matches_rule(rule=rule, data_bytes=data, data_text=data_text, file_sha256=file_sha256)
        except ValueError:
            # Invalid hex/regex payloads are rejected in rule validation; skip defensively here.
            continue
        except re.error:
            continue
        if not matched:
            continue
        seen.add(key)
        rule_type = _rule_pattern_type(rule)
        findings.append(
            asdict(
                Detection(
                    artifact=path_text,
                    rule_id=rule_id,
                    detection_type="hash" if rule_type == "sha256" else "signature",
                    severity=str(rule.get("severity", "medium")),
                    confidence=1.0 if rule_type == "sha256" else 0.99,
                )
            )
        )
    return findings


def scan_target(target: str) -> dict:
    started = perf_counter()
    max_scan_bytes = _max_scan_bytes()
    rules_blob = list_rules()
    rules = rules_blob.get("rules", [])
    if not rules:
        raise ScanTargetError("no active rules available for scanning")

    findings: list[dict] = []
    seen: set[tuple[str, str]] = set()
    counters = {
        "scanned_files": 0,
        "scanned_bytes": 0,
        "skipped_unreadable": 0,
        "skipped_large": 0,
        "skipped_binary": 0,
        "skipped_symlink": 0,
    }

    for path in _iter_paths(target):
        if path.is_symlink():
            counters["skipped_symlink"] += 1
            continue
        counters["scanned_files"] += 1
        data, skip_reason = _scan_file(path, max_scan_bytes=max_scan_bytes)
        if skip_reason == "unreadable":
            counters["skipped_unreadable"] += 1
            continue
        if skip_reason == "large":
            counters["skipped_large"] += 1
            continue
        if data is None:
            continue
        counters["scanned_bytes"] += len(data)
        findings.extend(_match_file_against_rules(path=path, data=data, rules=rules, seen=seen))

    return {
        "target": target,
        "max_scan_bytes": max_scan_bytes,
        **counters,
        "detection_count": len(findings),
        "findings": findings,
        "elapsed_ms": round((perf_counter() - started) * 1000, 2),
    }
