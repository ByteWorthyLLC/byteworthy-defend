from __future__ import annotations

from bw_defend.core.config import TelemetryConfig
from bw_defend.core.telemetry import export_audit_record, telemetry_from_env


def test_export_audit_record_skips_when_disabled() -> None:
    telemetry = TelemetryConfig(enabled=False)
    result = export_audit_record({"event_type": "x"}, telemetry)
    assert result["sent"] is False
    assert result["attempted"] is False


def test_export_audit_record_sends_payload(monkeypatch) -> None:
    calls = {"count": 0, "body": b""}

    def _fake_send_payload(*, endpoint, body, headers, timeout_seconds):
        calls["count"] += 1
        calls["body"] = body
        assert endpoint.hostname == "example.test"
        assert endpoint.path == "/ingest"
        assert headers["Content-Type"] == "application/json"
        assert timeout_seconds == 3.0
        return 202

    monkeypatch.setattr("bw_defend.core.telemetry._send_payload", _fake_send_payload)

    telemetry = TelemetryConfig(enabled=True, endpoint="https://example.test/ingest", max_retries=0)
    result = export_audit_record({"event_type": "incident_created"}, telemetry)

    assert result["sent"] is True
    assert result["attempt"] == 1
    assert calls["count"] == 1
    assert b'"event_type": "incident_created"' in calls["body"]


def test_telemetry_from_env_defaults_enabled_when_endpoint_present(monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_TELEMETRY_ENDPOINT", "https://example.test/telemetry")
    monkeypatch.delenv("BW_DEFEND_TELEMETRY_ENABLED", raising=False)
    cfg = telemetry_from_env()
    assert cfg.enabled is True
    assert cfg.endpoint == "https://example.test/telemetry"
