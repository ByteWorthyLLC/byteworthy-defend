from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
from pathlib import Path
from typing import Any

from bw_defend.core.errors import RuleValidationError
from bw_defend.core.fs import atomic_write_json, atomic_write_text
from bw_defend.core.paths import active_rules_file, rules_dir

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


def ensure_rules() -> Path:
    r_dir = rules_dir()
    r_dir.mkdir(parents=True, exist_ok=True)
    path = active_rules_file()
    if not path.exists():
        atomic_write_json(path, DEFAULT_RULES)
    checksum_file = path.with_suffix(path.suffix + ".sha256")
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


def _validate_rules_bundle(bundle: dict[str, Any]) -> None:
    if not isinstance(bundle, dict):
        raise RuleValidationError("rules bundle must be a JSON object")
    if not isinstance(bundle.get("version"), str) or not bundle["version"].strip():
        raise RuleValidationError("rules bundle must contain non-empty string 'version'")
    rules = bundle.get("rules")
    if not isinstance(rules, list):
        raise RuleValidationError("rules bundle must contain list 'rules'")
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise RuleValidationError(f"rules[{index}] must be an object")
        for key in ("id", "pattern", "severity"):
            if key not in rule or not isinstance(rule[key], str) or not rule[key].strip():
                raise RuleValidationError(f"rules[{index}] missing valid string '{key}'")
        severity = rule["severity"].lower()
        if severity not in VALID_SEVERITIES:
            raise RuleValidationError(
                f"rules[{index}] severity '{rule['severity']}' is invalid; "
                f"allowed={', '.join(sorted(VALID_SEVERITIES))}"
            )


def _signature_is_required() -> bool:
    return os.getenv(RULES_SIGNATURE_REQUIRED_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def _verify_detached_signature(path: Path, *, required: bool) -> tuple[bool, dict[str, str]]:
    signature_file = path.with_suffix(path.suffix + ".sig")
    if not signature_file.exists():
        if required:
            return False, {"reason": "missing signature file"}
        return True, {}

    signing_key = os.getenv(RULES_SIGNING_KEY_ENV, "").strip()
    if not signing_key:
        return False, {"reason": f"missing signing key env '{RULES_SIGNING_KEY_ENV}'"}

    signature_text = signature_file.read_text().strip()
    if not signature_text:
        return False, {"reason": "signature file is empty"}

    expected = signature_text.split()[0]
    actual = hmac.new(signing_key.encode("utf-8"), path.read_bytes(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected.lower(), actual.lower()):
        return False, {"reason": "signature mismatch", "expected": expected, "actual": actual}
    return True, {}


def verify_rules(path: Path | None = None) -> dict[str, str | bool]:
    target = path or ensure_rules()
    hash_file = target.with_suffix(target.suffix + ".sha256")
    actual = _sha256(target)
    if not hash_file.exists():
        return {"verified": False, "reason": "missing checksum file", "sha256": actual}
    expected = hash_file.read_text().strip().split()[0]
    if expected == actual:
        try:
            _validate_rules_bundle(json.loads(target.read_text()))
        except (json.JSONDecodeError, RuleValidationError) as exc:
            return {
                "verified": False,
                "expected": expected,
                "actual": actual,
                "reason": f"schema validation failed: {exc}",
            }
        signature_ok, signature_payload = _verify_detached_signature(target, required=_signature_is_required())
        if not signature_ok:
            payload: dict[str, str | bool] = {"verified": False, "expected": expected, "actual": actual}
            payload.update(signature_payload)
            return payload
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

    try:
        payload = json.loads(src.read_text())
    except json.JSONDecodeError as exc:
        return {"updated": False, "reason": f"bundle is not valid JSON: {exc}"}
    try:
        _validate_rules_bundle(payload)
    except RuleValidationError as exc:
        return {"updated": False, "reason": str(exc)}

    signature_ok, signature_payload = _verify_detached_signature(src, required=_signature_is_required())
    if not signature_ok:
        payload = {"updated": False}
        payload.update(signature_payload)
        return payload

    dst = ensure_rules()
    shutil.copyfile(src, dst)
    atomic_write_text(dst.with_suffix(dst.suffix + ".sha256"), f"{actual}  {dst.name}\n")
    src_signature = src.with_suffix(src.suffix + ".sig")
    dst_signature = dst.with_suffix(dst.suffix + ".sig")
    if src_signature.exists():
        shutil.copyfile(src_signature, dst_signature)
    elif dst_signature.exists():
        dst_signature.unlink()
    return {"updated": True, "reason": "rules updated and verified", "sha256": actual}
