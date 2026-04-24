from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any
from urllib import error, request

from bw_defend.core.config import TelemetryConfig

USER_AGENT = "bw-defend/0.1 telemetry"
TELEMETRY_ENABLED_ENV = "BW_DEFEND_TELEMETRY_ENABLED"
TELEMETRY_ENDPOINT_ENV = "BW_DEFEND_TELEMETRY_ENDPOINT"
TELEMETRY_TIMEOUT_ENV = "BW_DEFEND_TELEMETRY_TIMEOUT_SECONDS"
TELEMETRY_RETRIES_ENV = "BW_DEFEND_TELEMETRY_MAX_RETRIES"
TELEMETRY_TOKEN_ENV_ENV = "BW_DEFEND_TELEMETRY_TOKEN_ENV"


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def telemetry_from_env() -> TelemetryConfig:
    endpoint = os.getenv(TELEMETRY_ENDPOINT_ENV, "").strip()
    enabled_default = bool(endpoint)
    timeout_seconds = 3.0
    max_retries = 2
    token_env = os.getenv(TELEMETRY_TOKEN_ENV_ENV, "BW_DEFEND_TELEMETRY_TOKEN").strip() or "BW_DEFEND_TELEMETRY_TOKEN"
    try:
        timeout_seconds = float(os.getenv(TELEMETRY_TIMEOUT_ENV, "3.0"))
    except ValueError:
        timeout_seconds = 3.0
    try:
        max_retries = int(os.getenv(TELEMETRY_RETRIES_ENV, "2"))
    except ValueError:
        max_retries = 2
    timeout_seconds = min(30.0, max(0.1, timeout_seconds))
    max_retries = min(10, max(0, max_retries))
    return TelemetryConfig(
        enabled=_env_bool(TELEMETRY_ENABLED_ENV, enabled_default),
        endpoint=endpoint,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        auth_token_env=token_env,
    )


def _headers(telemetry: TelemetryConfig) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    token = os.getenv(telemetry.auth_token_env, "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def export_audit_record(
    record: dict[str, Any],
    telemetry: TelemetryConfig,
) -> dict[str, Any]:
    if not telemetry.enabled:
        return {"attempted": False, "sent": False, "reason": "telemetry disabled"}
    if not telemetry.endpoint:
        return {"attempted": False, "sent": False, "reason": "telemetry endpoint not configured"}

    payload = {
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "record": record,
    }
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    req = request.Request(
        url=telemetry.endpoint,
        data=body,
        headers=_headers(telemetry),
        method="POST",
    )

    attempts = max(0, telemetry.max_retries) + 1
    last_error = "unknown telemetry failure"
    for attempt in range(1, attempts + 1):
        try:
            with request.urlopen(req, timeout=telemetry.timeout_seconds) as response:
                status = int(getattr(response, "status", 200))
                if 200 <= status < 300:
                    return {
                        "attempted": True,
                        "sent": True,
                        "status_code": status,
                        "attempt": attempt,
                    }
                last_error = f"unexpected status: {status}"
        except (error.URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)
        if attempt < attempts:
            time.sleep(min(2**attempt, 4))

    return {
        "attempted": True,
        "sent": False,
        "attempts": attempts,
        "reason": last_error,
    }
