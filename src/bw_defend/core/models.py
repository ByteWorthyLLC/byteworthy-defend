from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

INCIDENT_SCHEMA_VERSION = "v1"
INCIDENT_REQUIRED_FIELDS = {
    "id",
    "timestamp",
    "source",
    "artifact",
    "detection_type",
    "severity",
    "confidence",
    "action_state",
    "approval_required",
    "remediation_plan",
    "final_outcome",
}


@dataclass(slots=True)
class IncidentRecord:
    id: str
    timestamp: str
    source: str
    artifact: str
    detection_type: str
    severity: str
    confidence: float
    action_state: str
    approval_required: bool
    remediation_plan: list[dict[str, Any]] = field(default_factory=list)
    final_outcome: str = "pending"

    @classmethod
    def new(
        cls,
        *,
        incident_id: str,
        source: str,
        artifact: str,
        detection_type: str,
        severity: str,
        confidence: float,
        approval_required: bool,
        remediation_plan: list[dict[str, Any]] | None = None,
    ) -> "IncidentRecord":
        if confidence < 0 or confidence > 1:
            raise ValueError("incident confidence must be between 0 and 1")
        return cls(
            id=incident_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
            artifact=artifact,
            detection_type=detection_type,
            severity=severity,
            confidence=confidence,
            action_state="detected",
            approval_required=approval_required,
            remediation_plan=remediation_plan or [],
            final_outcome="pending",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": INCIDENT_SCHEMA_VERSION,
            "id": self.id,
            "timestamp": self.timestamp,
            "source": self.source,
            "artifact": self.artifact,
            "detection_type": self.detection_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "action_state": self.action_state,
            "approval_required": self.approval_required,
            "remediation_plan": self.remediation_plan,
            "final_outcome": self.final_outcome,
        }


def validate_incident_record(payload: dict[str, Any]) -> tuple[bool, str]:
    missing = [field for field in INCIDENT_REQUIRED_FIELDS if field not in payload]
    if missing:
        return False, f"missing required fields: {', '.join(sorted(missing))}"
    if not isinstance(payload["id"], str) or not payload["id"].startswith("inc-"):
        return False, "incident id must be a string prefixed with 'inc-'"
    if not isinstance(payload["confidence"], (float, int)):
        return False, "incident confidence must be numeric"
    confidence = float(payload["confidence"])
    if confidence < 0 or confidence > 1:
        return False, "incident confidence must be between 0 and 1"
    if not isinstance(payload["approval_required"], bool):
        return False, "approval_required must be boolean"
    if not isinstance(payload["remediation_plan"], list):
        return False, "remediation_plan must be a list"
    return True, "ok"
