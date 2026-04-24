from __future__ import annotations
import hashlib
import json
import string
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bw_defend.core.fs import append_jsonl
from bw_defend.core.paths import audit_log_path, state_dir
from bw_defend.core.telemetry import export_audit_record, telemetry_from_env


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _compute_record_hash(record: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(record).encode("utf-8")).hexdigest()


def _is_sha256_hex(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in string.hexdigits for ch in value)


def _last_valid_record_hash(path: Path) -> str | None:
    if not path.exists():
        return None

    last_hash: str | None = None
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            record_hash = record.get("record_hash")
            if _is_sha256_hex(record_hash):
                last_hash = record_hash
    return last_hash


def log_audit(event_type: str, payload: dict[str, Any]) -> None:
    state_dir().mkdir(parents=True, exist_ok=True)
    path = audit_log_path()
    prev_hash = _last_valid_record_hash(path)
    record = {
        "event_id": f"audit-{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
        "prev_hash": prev_hash,
    }
    record["record_hash"] = _compute_record_hash(record)
    append_jsonl(path, record)
    _export_telemetry(record)


def _export_telemetry(record: dict[str, Any]) -> None:
    telemetry = telemetry_from_env()
    result = export_audit_record(record, telemetry)
    if result.get("attempted") and not result.get("sent"):
        append_jsonl(
            state_dir() / "telemetry_failures.jsonl",
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": result.get("reason", "telemetry export failed"),
                "record_event_id": record.get("event_id", "unknown"),
            },
        )


def verify_audit_chain(path: Path | None = None) -> dict[str, Any]:
    target_path = path or audit_log_path()
    if not target_path.exists() or target_path.stat().st_size == 0:
        return {
            "status": "empty",
            "reason": "audit log is empty",
            "count": 0,
            "verified_count": 0,
            "legacy_count": 0,
        }

    total_count = 0
    verified_count = 0
    legacy_count = 0
    expected_prev_hash: str | None = None

    with target_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue

            total_count += 1

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                return {
                    "status": "invalid",
                    "reason": f"line {line_number} is not valid JSON",
                    "count": total_count,
                    "verified_count": verified_count,
                    "legacy_count": legacy_count,
                }

            if not isinstance(record, dict):
                return {
                    "status": "invalid",
                    "reason": f"line {line_number} is not a JSON object",
                    "count": total_count,
                    "verified_count": verified_count,
                    "legacy_count": legacy_count,
                }

            if "prev_hash" not in record or "record_hash" not in record:
                legacy_count += 1
                continue

            record_hash = record.get("record_hash")
            prev_hash = record.get("prev_hash")

            if not _is_sha256_hex(record_hash):
                return {
                    "status": "tampered",
                    "reason": f"line {line_number} has invalid record_hash",
                    "count": total_count,
                    "verified_count": verified_count,
                    "legacy_count": legacy_count,
                }

            if prev_hash is not None and not _is_sha256_hex(prev_hash):
                return {
                    "status": "tampered",
                    "reason": f"line {line_number} has invalid prev_hash",
                    "count": total_count,
                    "verified_count": verified_count,
                    "legacy_count": legacy_count,
                }

            if prev_hash != expected_prev_hash:
                return {
                    "status": "tampered",
                    "reason": f"line {line_number} prev_hash mismatch",
                    "count": total_count,
                    "verified_count": verified_count,
                    "legacy_count": legacy_count,
                }

            record_for_hash = dict(record)
            record_for_hash.pop("record_hash", None)
            expected_record_hash = _compute_record_hash(record_for_hash)
            if record_hash != expected_record_hash:
                return {
                    "status": "tampered",
                    "reason": f"line {line_number} record_hash mismatch",
                    "count": total_count,
                    "verified_count": verified_count,
                    "legacy_count": legacy_count,
                }

            verified_count += 1
            expected_prev_hash = record_hash

    if legacy_count > 0:
        return {
            "status": "legacy_present",
            "reason": "legacy records without chain metadata are present",
            "count": total_count,
            "verified_count": verified_count,
            "legacy_count": legacy_count,
        }

    return {
        "status": "ok",
        "reason": "audit chain verified",
        "count": total_count,
        "verified_count": verified_count,
        "legacy_count": legacy_count,
    }
