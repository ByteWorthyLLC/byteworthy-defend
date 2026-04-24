from __future__ import annotations

import json
import uuid
from typing import Any

from .audit import log_audit
from .fs import append_jsonl, atomic_write_text
from .models import IncidentRecord
from .models import validate_incident_record
from .paths import incidents_path, state_dir


def create_incident(
    *,
    source: str,
    artifact: str,
    detection_type: str,
    severity: str,
    confidence: float,
    approval_required: bool,
    remediation_plan: list[dict[str, Any]] | None = None,
) -> IncidentRecord:
    incident = IncidentRecord.new(
        incident_id=f"inc-{uuid.uuid4().hex[:12]}",
        source=source,
        artifact=artifact,
        detection_type=detection_type,
        severity=severity,
        confidence=confidence,
        approval_required=approval_required,
        remediation_plan=remediation_plan,
    )
    state_dir().mkdir(parents=True, exist_ok=True)
    append_jsonl(incidents_path(), incident.to_dict())
    return incident


def list_incidents() -> list[dict[str, Any]]:
    path = incidents_path()
    if not path.exists():
        return []
    incidents: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            log_audit(
                "incident_parse_error",
                {"line": line_no, "reason": "invalid json", "path": str(path)},
            )
            continue
        valid, reason = validate_incident_record(payload)
        if not valid:
            log_audit(
                "incident_parse_error",
                {"line": line_no, "reason": reason, "path": str(path)},
            )
            continue
        incidents.append(payload)
    return incidents


def get_incident(incident_id: str) -> dict[str, Any] | None:
    for incident in list_incidents():
        if incident.get("id") == incident_id:
            return incident
    return None


def overwrite_incidents(incidents: list[dict[str, Any]]) -> None:
    state_dir().mkdir(parents=True, exist_ok=True)
    for incident in incidents:
        valid, reason = validate_incident_record(incident)
        if not valid:
            raise ValueError(f"refusing to write invalid incident record: {reason}")
    content = "".join(json.dumps(incident, sort_keys=True) + "\n" for incident in incidents)
    atomic_write_text(incidents_path(), content)


def update_incident(incident_id: str, **updates: Any) -> dict[str, Any] | None:
    incidents = list_incidents()
    updated: dict[str, Any] | None = None
    for incident in incidents:
        if incident.get("id") == incident_id:
            incident.update(updates)
            valid, reason = validate_incident_record(incident)
            if not valid:
                raise ValueError(f"incident update produced invalid record: {reason}")
            updated = incident
            break
    if updated:
        overwrite_incidents(incidents)
    return updated
