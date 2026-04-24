from __future__ import annotations

import json
import uuid
from typing import Any

from bw_defend.core.models import IncidentRecord
from bw_defend.core.paths import incidents_path, state_dir


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
    with incidents_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(incident.to_dict(), sort_keys=True) + "\n")
    return incident


def list_incidents() -> list[dict[str, Any]]:
    path = incidents_path()
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def get_incident(incident_id: str) -> dict[str, Any] | None:
    for incident in list_incidents():
        if incident.get("id") == incident_id:
            return incident
    return None


def overwrite_incidents(incidents: list[dict[str, Any]]) -> None:
    state_dir().mkdir(parents=True, exist_ok=True)
    with incidents_path().open("w", encoding="utf-8") as handle:
        for incident in incidents:
            handle.write(json.dumps(incident, sort_keys=True) + "\n")


def update_incident(incident_id: str, **updates: Any) -> dict[str, Any] | None:
    incidents = list_incidents()
    updated: dict[str, Any] | None = None
    for incident in incidents:
        if incident.get("id") == incident_id:
            incident.update(updates)
            updated = incident
            break
    if updated:
        overwrite_incidents(incidents)
    return updated
