from __future__ import annotations

from bw_defend.core.config import TelemetryConfig
from bw_defend.core.telemetry import export_audit_record, telemetry_from_env


class _Response:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _CaptureUrlOpen:
    def __init__(self) -> None:
        self.calls = 0
        self.last_request_body = b""

    def __call__(self, req, timeout):
        self.calls += 1
        self.last_request_body = req.data or b""
        return _Response(202)


def test_export_audit_record_skips_when_disabled() -> None:
    telemetry = TelemetryConfig(enabled=False)
    result = export_audit_record({"event_type": "x"}, telemetry)
    assert result["sent"] is False
    assert result["attempted"] is False


def test_export_audit_record_sends_payload(monkeypatch) -> None:
    capture = _CaptureUrlOpen()
    monkeypatch.setattr("bw_defend.core.telemetry.request.urlopen", capture)

    telemetry = TelemetryConfig(enabled=True, endpoint="https://example.test/ingest", max_retries=0)
    result = export_audit_record({"event_type": "incident_created"}, telemetry)

    assert result["sent"] is True
    assert result["attempt"] == 1
    assert capture.calls == 1
    assert b'"event_type": "incident_created"' in capture.last_request_body


def test_telemetry_from_env_defaults_enabled_when_endpoint_present(monkeypatch) -> None:
    monkeypatch.setenv("BW_DEFEND_TELEMETRY_ENDPOINT", "https://example.test/telemetry")
    monkeypatch.delenv("BW_DEFEND_TELEMETRY_ENABLED", raising=False)
    cfg = telemetry_from_env()
    assert cfg.enabled is True
    assert cfg.endpoint == "https://example.test/telemetry"
