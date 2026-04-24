from __future__ import annotations

import hashlib
import json
import string
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fs import append_jsonl
from .paths import audit_log_path, state_dir
from .telemetry import export_audit_record, telemetry_from_env

KEY_STATUS = "status"
KEY_REASON = "reason"
KEY_COUNT = "count"
KEY_VERIFIED_COUNT = "verified_count"
KEY_LEGACY_COUNT = "legacy_count"
KEY_PREV_HASH = "prev_hash"
KEY_RECORD_HASH = "record_hash"
STATUS_EMPTY = "empty"
STATUS_INVALID = "invalid"
STATUS_TAMPERED = "tampered"
STATUS_LEGACY = "legacy_present"
STATUS_OK = "ok"


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _compute_record_hash(record: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(record).encode("utf-8")).hexdigest()


def _is_sha256_hex(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in string.hexdigits for ch in value)


def _base_result(
    *,
    status: str,
    reason: str,
    count: int,
    verified_count: int,
    legacy_count: int,
) -> dict[str, Any]:
    return {
        KEY_STATUS: status,
        KEY_REASON: reason,
        KEY_COUNT: count,
        KEY_VERIFIED_COUNT: verified_count,
        KEY_LEGACY_COUNT: legacy_count,
    }


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
                # Legacy/malformed lines are skipped; chain verification handles strict validation.
                continue
            if not isinstance(record, dict):
                continue
            record_hash = record.get(KEY_RECORD_HASH)
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
        KEY_PREV_HASH: prev_hash,
    }
    record[KEY_RECORD_HASH] = _compute_record_hash(record)
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


def _line_prefix(line_number: int) -> str:
    return f"line {line_number}"


def _invalid_result(
    *,
    line_number: int,
    issue: str,
    count: int,
    verified_count: int,
    legacy_count: int,
) -> dict[str, Any]:
    return _base_result(
        status=STATUS_INVALID,
        reason=f"{_line_prefix(line_number)} {issue}",
        count=count,
        verified_count=verified_count,
        legacy_count=legacy_count,
    )


def _tampered_result(
    *,
    line_number: int,
    issue: str,
    count: int,
    verified_count: int,
    legacy_count: int,
) -> dict[str, Any]:
    return _base_result(
        status=STATUS_TAMPERED,
        reason=f"{_line_prefix(line_number)} {issue}",
        count=count,
        verified_count=verified_count,
        legacy_count=legacy_count,
    )


def _validate_record_line(
    *,
    record: dict[str, Any],
    line_number: int,
    expected_prev_hash: str | None,
    count: int,
    verified_count: int,
    legacy_count: int,
) -> tuple[str | None, dict[str, Any] | None]:
    if KEY_PREV_HASH not in record or KEY_RECORD_HASH not in record:
        return expected_prev_hash, None

    record_hash = record.get(KEY_RECORD_HASH)
    prev_hash = record.get(KEY_PREV_HASH)
    if not _is_sha256_hex(record_hash):
        return expected_prev_hash, _tampered_result(
            line_number=line_number,
            issue=f"has invalid {KEY_RECORD_HASH}",
            count=count,
            verified_count=verified_count,
            legacy_count=legacy_count,
        )
    if prev_hash is not None and not _is_sha256_hex(prev_hash):
        return expected_prev_hash, _tampered_result(
            line_number=line_number,
            issue=f"has invalid {KEY_PREV_HASH}",
            count=count,
            verified_count=verified_count,
            legacy_count=legacy_count,
        )
    if prev_hash != expected_prev_hash:
        return expected_prev_hash, _tampered_result(
            line_number=line_number,
            issue=f"{KEY_PREV_HASH} mismatch",
            count=count,
            verified_count=verified_count,
            legacy_count=legacy_count,
        )

    record_for_hash = dict(record)
    record_for_hash.pop(KEY_RECORD_HASH, None)
    expected_record_hash = _compute_record_hash(record_for_hash)
    if record_hash != expected_record_hash:
        return expected_prev_hash, _tampered_result(
            line_number=line_number,
            issue=f"{KEY_RECORD_HASH} mismatch",
            count=count,
            verified_count=verified_count,
            legacy_count=legacy_count,
        )

    return record_hash, None


def verify_audit_chain(path: Path | None = None) -> dict[str, Any]:
    target_path = path or audit_log_path()
    if not target_path.exists() or target_path.stat().st_size == 0:
        return _base_result(status=STATUS_EMPTY, reason="audit log is empty", count=0, verified_count=0, legacy_count=0)

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
                return _invalid_result(
                    line_number=line_number,
                    issue="is not valid JSON",
                    count=total_count,
                    verified_count=verified_count,
                    legacy_count=legacy_count,
                )

            if not isinstance(record, dict):
                return _invalid_result(
                    line_number=line_number,
                    issue="is not a JSON object",
                    count=total_count,
                    verified_count=verified_count,
                    legacy_count=legacy_count,
                )

            if KEY_PREV_HASH not in record or KEY_RECORD_HASH not in record:
                legacy_count += 1
                continue

            expected_prev_hash, failure = _validate_record_line(
                record=record,
                line_number=line_number,
                expected_prev_hash=expected_prev_hash,
                count=total_count,
                verified_count=verified_count,
                legacy_count=legacy_count,
            )
            if failure:
                return failure
            verified_count += 1

    if legacy_count > 0:
        return _base_result(
            status=STATUS_LEGACY,
            reason="legacy records without chain metadata are present",
            count=total_count,
            verified_count=verified_count,
            legacy_count=legacy_count,
        )

    return _base_result(
        status=STATUS_OK,
        reason="audit chain verified",
        count=total_count,
        verified_count=verified_count,
        legacy_count=legacy_count,
    )
