from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

from .errors import RuleValidationError
from .fs import atomic_write_json, atomic_write_text
from .paths import active_rules_file, rules_dir

DEFAULT_RULES = {
    "version": "2026.04.0",
    "rules": [
        {"id": "MAL-EICAR-001", "pattern": "EICAR-STANDARD-ANTIVIRUS-TEST-FILE", "severity": "high"},
        {"id": "SUS-DANG-002", "pattern": "rm -rf /", "severity": "critical"},
        {"id": "SUS-WIN-003", "pattern": "powershell -enc", "severity": "critical"},
    ],
}
VALID_SEVERITIES = {"low", "medium", "high", "critical"}
RULES_SIGNATURE_REQUIRED_ENV = "BW_DEFEND_RULES_SIGNATURE_REQUIRED"
RULES_SIGNING_KEY_ENV = "BW_DEFEND_RULES_SIGNING_KEY"

KEY_VERSION = "version"
KEY_RULES = "rules"
KEY_RULE_ID = "id"
KEY_PATTERN = "pattern"
KEY_SEVERITY = "severity"
KEY_PATTERN_TYPE = "pattern_type"
KEY_REASON = "reason"
KEY_VERIFIED = "verified"
KEY_EXPECTED = "expected"
KEY_ACTUAL = "actual"
KEY_UPDATED = "updated"
CHECKSUM_SUFFIX = ".sha256"
SIGNATURE_SUFFIX = ".sig"
RULE_PATTERN_TYPES = {"literal", "regex", "hex", "sha256"}
MAX_RULE_ID_LENGTH = 128
MAX_PATTERN_LENGTH = 8192
MAX_RULE_COUNT = 5000


def ensure_rules() -> Path:
    r_dir = rules_dir()
    r_dir.mkdir(parents=True, exist_ok=True)
    path = active_rules_file()
    if not path.exists():
        atomic_write_json(path, DEFAULT_RULES)
    checksum_file = path.with_suffix(path.suffix + CHECKSUM_SUFFIX)
    if not checksum_file.exists():
        atomic_write_text(checksum_file, f"{_sha256(path)}  {path.name}\n")
    return path


def list_rules() -> dict:
    path = ensure_rules()
    data = json.loads(path.read_text())
    _validate_rules_bundle(data)
    return data


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hmac_sha256(path: Path, key: str) -> str:
    digest = hmac.new(key.encode("utf-8"), digestmod=hashlib.sha256)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return re.fullmatch(r"[0-9a-f]{64}", value.strip().lower()) is not None


def _read_integrity_digest(path: Path, *, label: str, expected_name: str) -> tuple[str | None, str | None]:
    if not path.exists():
        return None, f"missing {label} file"
    raw = path.read_text().strip()
    if not raw:
        return None, f"{label} file is empty"

    parts = raw.split()
    digest = parts[0].strip().lower()
    if not _is_sha256_hex(digest):
        return None, f"{label} file has invalid digest format"
    if len(parts) > 1 and parts[1] != expected_name:
        return None, f"{label} file name does not match target bundle"
    return digest, None


def _validate_rule(rule: Any, *, index: int) -> None:
    if not isinstance(rule, dict):
        raise RuleValidationError(f"rules[{index}] must be an object")
    required = (KEY_RULE_ID, KEY_PATTERN, KEY_SEVERITY)
    missing = [key for key in required if not isinstance(rule.get(key), str) or not str(rule.get(key)).strip()]
    if missing:
        raise RuleValidationError(f"rules[{index}] missing valid string '{missing[0]}'")
    rule_id = str(rule[KEY_RULE_ID]).strip()
    if len(rule_id) > MAX_RULE_ID_LENGTH:
        raise RuleValidationError(f"rules[{index}] id exceeds max length {MAX_RULE_ID_LENGTH}")

    pattern = str(rule[KEY_PATTERN])
    if len(pattern) > MAX_PATTERN_LENGTH:
        raise RuleValidationError(f"rules[{index}] pattern exceeds max length {MAX_PATTERN_LENGTH}")

    severity = str(rule[KEY_SEVERITY]).lower()
    if severity not in VALID_SEVERITIES:
        raise RuleValidationError(
            f"rules[{index}] severity '{rule[KEY_SEVERITY]}' is invalid; "
            f"allowed={', '.join(sorted(VALID_SEVERITIES))}"
        )
    if "case_sensitive" in rule and not isinstance(rule.get("case_sensitive"), bool):
        raise RuleValidationError(f"rules[{index}] case_sensitive must be boolean when provided")
    pattern_type = str(rule.get(KEY_PATTERN_TYPE, "literal")).strip().lower()
    if pattern_type not in RULE_PATTERN_TYPES:
        raise RuleValidationError(
            f"rules[{index}] pattern_type '{pattern_type}' is invalid; "
            f"allowed={', '.join(sorted(RULE_PATTERN_TYPES))}"
        )
    _validate_pattern_by_type(pattern=pattern, pattern_type=pattern_type, index=index)


def _validate_pattern_by_type(*, pattern: str, pattern_type: str, index: int) -> None:
    if pattern_type == "regex":
        try:
            re.compile(pattern)
        except re.error as exc:
            raise RuleValidationError(f"rules[{index}] regex pattern is invalid: {exc}") from exc
        return
    if pattern_type == "hex":
        compact = "".join(pattern.split())
        if not compact:
            raise RuleValidationError(f"rules[{index}] hex pattern must be non-empty")
        if len(compact) % 2 != 0:
            raise RuleValidationError(f"rules[{index}] hex pattern must contain an even number of characters")
        try:
            bytes.fromhex(compact)
        except ValueError as exc:
            raise RuleValidationError(f"rules[{index}] hex pattern is invalid: {exc}") from exc
        return
    if pattern_type == "sha256":
        compact = pattern.strip().lower()
        if not _is_sha256_hex(compact):
            raise RuleValidationError(f"rules[{index}] sha256 pattern must be a 64-character lowercase hex digest")


def _validate_rules_bundle(bundle: dict[str, Any]) -> None:
    if not isinstance(bundle, dict):
        raise RuleValidationError("rules bundle must be a JSON object")
    if not isinstance(bundle.get(KEY_VERSION), str) or not str(bundle[KEY_VERSION]).strip():
        raise RuleValidationError("rules bundle must contain non-empty string 'version'")
    rules = bundle.get(KEY_RULES)
    if not isinstance(rules, list):
        raise RuleValidationError("rules bundle must contain list 'rules'")
    if len(rules) > MAX_RULE_COUNT:
        raise RuleValidationError(f"rules bundle exceeds max rule count {MAX_RULE_COUNT}")
    seen_rule_ids: set[str] = set()
    for index, rule in enumerate(rules):
        _validate_rule(rule, index=index)
        rule_id = str(rule[KEY_RULE_ID]).strip().lower()
        if rule_id in seen_rule_ids:
            raise RuleValidationError(f"rules[{index}] duplicate id '{rule[KEY_RULE_ID]}'")
        seen_rule_ids.add(rule_id)


def _signature_is_required() -> bool:
    return os.getenv(RULES_SIGNATURE_REQUIRED_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def _verify_detached_signature(path: Path, *, required: bool) -> tuple[bool, dict[str, str]]:
    signature_file = path.with_suffix(path.suffix + SIGNATURE_SUFFIX)
    if not signature_file.exists():
        if required:
            return False, {KEY_REASON: "missing signature file"}
        return True, {}

    signing_key = os.getenv(RULES_SIGNING_KEY_ENV, "").strip()
    if not signing_key:
        return False, {KEY_REASON: f"missing signing key env '{RULES_SIGNING_KEY_ENV}'"}

    expected, parse_error = _read_integrity_digest(signature_file, label="signature", expected_name=path.name)
    if parse_error or expected is None:
        return False, {KEY_REASON: parse_error or "signature parse failed"}
    actual = _hmac_sha256(path, signing_key)
    if not hmac.compare_digest(expected, actual.lower()):
        return False, {KEY_REASON: "signature mismatch", KEY_EXPECTED: expected, KEY_ACTUAL: actual}
    return True, {}


def verify_rules(path: Path | None = None) -> dict[str, str | bool]:
    target = path or ensure_rules()
    hash_file = target.with_suffix(target.suffix + CHECKSUM_SUFFIX)
    actual = _sha256(target)
    expected, parse_error = _read_integrity_digest(hash_file, label="checksum", expected_name=target.name)
    if parse_error or expected is None:
        return {KEY_VERIFIED: False, KEY_REASON: parse_error or "checksum parse failed", "sha256": actual}
    if expected != actual:
        return {KEY_VERIFIED: False, KEY_EXPECTED: expected, KEY_ACTUAL: actual, KEY_REASON: "checksum mismatch"}

    try:
        _validate_rules_bundle(json.loads(target.read_text()))
    except (json.JSONDecodeError, RuleValidationError):
        return {KEY_VERIFIED: False, KEY_EXPECTED: expected, KEY_ACTUAL: actual, KEY_REASON: "schema validation failed"}

    signature_ok, signature_payload = _verify_detached_signature(target, required=_signature_is_required())
    if not signature_ok:
        payload: dict[str, str | bool] = {KEY_VERIFIED: False, KEY_EXPECTED: expected, KEY_ACTUAL: actual}
        payload.update(signature_payload)
        return payload

    return {KEY_VERIFIED: True, KEY_EXPECTED: expected, KEY_ACTUAL: actual, KEY_REASON: "ok"}


def update_rules(bundle_path: str) -> dict[str, str | bool]:
    src = Path(bundle_path.strip()).expanduser().resolve()
    checksum = src.with_suffix(src.suffix + CHECKSUM_SUFFIX)
    if not src.exists() or not src.is_file():
        raise FileNotFoundError(f"bundle not found: {src}")

    actual = _sha256(src)
    expected, parse_error = _read_integrity_digest(checksum, label="checksum", expected_name=src.name)
    if parse_error or expected is None:
        return {KEY_UPDATED: False, KEY_REASON: parse_error or "checksum parse failed", KEY_ACTUAL: actual}
    if actual != expected:
        return {KEY_UPDATED: False, KEY_REASON: "bundle integrity verification failed", KEY_EXPECTED: expected, KEY_ACTUAL: actual}

    try:
        payload = json.loads(src.read_text())
    except json.JSONDecodeError:
        return {KEY_UPDATED: False, KEY_REASON: "bundle is not valid JSON"}
    try:
        _validate_rules_bundle(payload)
    except RuleValidationError as exc:
        return {KEY_UPDATED: False, KEY_REASON: str(exc)}

    signature_ok, signature_payload = _verify_detached_signature(src, required=_signature_is_required())
    if not signature_ok:
        payload = {KEY_UPDATED: False}
        payload.update(signature_payload)
        return payload

    dst = ensure_rules()
    shutil.copyfile(src, dst)
    atomic_write_text(dst.with_suffix(dst.suffix + CHECKSUM_SUFFIX), f"{actual}  {dst.name}\n")
    src_signature = src.with_suffix(src.suffix + SIGNATURE_SUFFIX)
    dst_signature = dst.with_suffix(dst.suffix + SIGNATURE_SUFFIX)
    if src_signature.exists():
        shutil.copyfile(src_signature, dst_signature)
    elif dst_signature.exists():
        dst_signature.unlink()
    return {KEY_UPDATED: True, KEY_REASON: "rules updated and verified", "sha256": actual}
