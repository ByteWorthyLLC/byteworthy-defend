from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from bw_defend.core.rules import list_rules


@dataclass(slots=True)
class Detection:
    artifact: str
    rule_id: str
    detection_type: str
    severity: str
    confidence: float


def _iter_paths(target: str) -> Iterable[Path]:
    if target == "system":
        roots = [Path("/etc"), Path("/tmp")]
        for root in roots:
            if root.exists():
                for path in root.rglob("*"):
                    if path.is_file():
                        yield path
        return

    start = Path(target).expanduser()
    if start.is_file():
        yield start
        return
    if start.is_dir():
        for path in start.rglob("*"):
            if path.is_file():
                yield path


def scan_target(target: str) -> dict:
    rules_blob = list_rules()
    rules = rules_blob.get("rules", [])
    findings: list[dict] = []
    scanned = 0

    for path in _iter_paths(target):
        scanned += 1
        try:
            data = path.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for rule in rules:
            pattern = str(rule.get("pattern", ""))
            if pattern and pattern in data:
                findings.append(
                    asdict(
                        Detection(
                            artifact=str(path),
                            rule_id=str(rule.get("id", "unknown")),
                            detection_type="signature",
                            severity=str(rule.get("severity", "medium")),
                            confidence=0.99,
                        )
                    )
                )

    return {
        "target": target,
        "scanned_files": scanned,
        "detection_count": len(findings),
        "findings": findings,
    }
