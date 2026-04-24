from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
import platform
import os
from pathlib import Path
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


MAX_SCAN_BYTES = 2 * 1024 * 1024


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


def _iter_files_in_root(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    yield from (path for path in root.rglob("*") if path.is_file())


def _iter_paths(target: str) -> Iterable[Path]:
    if target == "system":
        for root in _system_scan_roots():
            yield from _iter_files_in_root(root)
        return

    start = Path(target).expanduser()
    if start.is_file():
        yield start
        return
    if start.is_dir():
        for path in start.rglob("*"):
            if path.is_file():
                yield path
        return
    raise ScanTargetError(f"scan target does not exist: {start}")


def _scan_file(path: Path) -> tuple[str | None, str | None]:
    try:
        size = path.stat().st_size
    except OSError:
        return None, "unreadable"
    if size > MAX_SCAN_BYTES:
        return None, "large"

    try:
        raw = path.read_bytes()
    except OSError:
        return None, "unreadable"
    if b"\x00" in raw:
        return None, "binary"
    return raw.decode(errors="ignore"), None


def _match_file_against_rules(
    *,
    path: Path,
    data: str,
    rules: list[dict],
    seen: set[tuple[str, str]],
) -> list[dict]:
    findings: list[dict] = []
    path_text = str(path)
    for rule in rules:
        pattern = str(rule.get("pattern", ""))
        rule_id = str(rule.get("id", "unknown"))
        key = (path_text, rule_id)
        if pattern and pattern in data and key not in seen:
            seen.add(key)
            findings.append(
                asdict(
                    Detection(
                        artifact=path_text,
                        rule_id=rule_id,
                        detection_type="signature",
                        severity=str(rule.get("severity", "medium")),
                        confidence=0.99,
                    )
                )
            )
    return findings


def scan_target(target: str) -> dict:
    started = perf_counter()
    rules_blob = list_rules()
    rules = rules_blob.get("rules", [])
    if not rules:
        raise ScanTargetError("no active rules available for scanning")

    findings: list[dict] = []
    seen: set[tuple[str, str]] = set()
    counters = {
        "scanned_files": 0,
        "skipped_unreadable": 0,
        "skipped_large": 0,
        "skipped_binary": 0,
    }

    for path in _iter_paths(target):
        counters["scanned_files"] += 1
        data, skip_reason = _scan_file(path)
        if skip_reason == "unreadable":
            counters["skipped_unreadable"] += 1
            continue
        if skip_reason == "large":
            counters["skipped_large"] += 1
            continue
        if skip_reason == "binary":
            counters["skipped_binary"] += 1
            continue
        if data is None:
            continue
        findings.extend(_match_file_against_rules(path=path, data=data, rules=rules, seen=seen))

    return {
        "target": target,
        **counters,
        "detection_count": len(findings),
        "findings": findings,
        "elapsed_ms": round((perf_counter() - started) * 1000, 2),
    }
