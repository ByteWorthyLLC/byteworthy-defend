from __future__ import annotations

import json
import http.client
import ipaddress
import os
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import ParseResult, urlparse

from .config import TelemetryConfig

USER_AGENT = "bw-defend/0.1 telemetry"
TELEMETRY_ENABLED_ENV = "BW_DEFEND_TELEMETRY_ENABLED"
TELEMETRY_ENDPOINT_ENV = "BW_DEFEND_TELEMETRY_ENDPOINT"
TELEMETRY_TIMEOUT_ENV = "BW_DEFEND_TELEMETRY_TIMEOUT_SECONDS"
TELEMETRY_RETRIES_ENV = "BW_DEFEND_TELEMETRY_MAX_RETRIES"
TELEMETRY_TOKEN_ENV_ENV = "BW_DEFEND_TELEMETRY_TOKEN_ENV"
TELEMETRY_ALLOW_PRIVATE_ENDPOINTS_ENV = "BW_DEFEND_TELEMETRY_ALLOW_PRIVATE_ENDPOINTS"

ATTEMPTED = "attempted"
SENT = "sent"
REASON = "reason"


def _env_bool(name: str, *, default: bool) -> bool:
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
        enabled=_env_bool(TELEMETRY_ENABLED_ENV, default=enabled_default),
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


def _is_public_ip(ip_text: str) -> bool:
    try:
        candidate = ipaddress.ip_address(ip_text)
    except ValueError:
        return False
    return not (
        candidate.is_private
        or candidate.is_loopback
        or candidate.is_link_local
        or candidate.is_multicast
        or candidate.is_reserved
        or candidate.is_unspecified
    )


def _validated_endpoint(endpoint: str) -> tuple[ParseResult | None, str]:
    parsed = urlparse(endpoint)
    if parsed.scheme != "https":
        return None, "telemetry endpoint must use https"
    if not parsed.netloc or not parsed.hostname:
        return None, "telemetry endpoint must include a hostname"
    if parsed.username or parsed.password:
        return None, "telemetry endpoint must not include embedded credentials"

    allow_private = _env_bool(TELEMETRY_ALLOW_PRIVATE_ENDPOINTS_ENV, default=False)
    if allow_private:
        return parsed, "ok"

    hostname = parsed.hostname.lower()
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        return None, "telemetry endpoint must not target localhost"
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        return parsed, "ok"
    if not _is_public_ip(hostname):
        return None, "telemetry endpoint must use a public IP when configured as literal address"
    return parsed, "ok"


def _send_payload(
    *,
    endpoint: ParseResult,
    body: bytes,
    headers: dict[str, str],
    timeout_seconds: float,
) -> int:
    if endpoint.hostname is None:
        raise OSError("endpoint has no hostname")
    target = endpoint.path or "/"
    if endpoint.query:
        target = f"{target}?{endpoint.query}"
    connection = http.client.HTTPSConnection(endpoint.hostname, endpoint.port or 443, timeout=timeout_seconds)
    try:
        connection.request("POST", target, body=body, headers=headers)
        response = connection.getresponse()
        response.read()
        return int(response.status)
    finally:
        connection.close()


def export_audit_record(
    record: dict[str, Any],
    telemetry: TelemetryConfig,
) -> dict[str, Any]:
    if not telemetry.enabled:
        return {ATTEMPTED: False, SENT: False, REASON: "telemetry disabled"}
    if not telemetry.endpoint:
        return {ATTEMPTED: False, SENT: False, REASON: "telemetry endpoint not configured"}
    endpoint, endpoint_reason = _validated_endpoint(telemetry.endpoint)
    if endpoint is None:
        return {ATTEMPTED: False, SENT: False, REASON: endpoint_reason}

    payload = {
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "record": record,
    }
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    headers = _headers(telemetry)

    attempts = max(0, telemetry.max_retries) + 1
    last_error = "unknown telemetry failure"
    for attempt in range(1, attempts + 1):
        try:
            status = _send_payload(
                endpoint=endpoint,
                body=body,
                headers=headers,
                timeout_seconds=telemetry.timeout_seconds,
            )
            if 200 <= status < 300:
                return {
                    ATTEMPTED: True,
                    SENT: True,
                    "status_code": status,
                    "attempt": attempt,
                }
            last_error = f"unexpected status: {status}"
        except (http.client.HTTPException, TimeoutError, OSError) as exc:
            last_error = str(exc)
        if attempt < attempts:
            time.sleep(min(2**attempt, 4))

    return {
        ATTEMPTED: True,
        SENT: False,
        "attempts": attempts,
        REASON: last_error,
    }
