from __future__ import annotations

from bw_defend.core.audit import log_audit
from bw_defend.core.config import DefendConfig
from bw_defend.core.incidents import get_incident, update_incident
from bw_defend.core.policy import evaluate_action
from bw_defend.core.quarantine import quarantine_file


def remediate_incident(incident_id: str, config: DefendConfig, approve: bool = False) -> dict:
    incident = get_incident(incident_id)
    if not incident:
        return {"ok": False, "reason": "incident not found", "incident_id": incident_id}

    if not incident.get("remediation_plan"):
        return {"ok": False, "reason": "incident has no remediation plan", "incident_id": incident_id}

    actions = []
    for step in incident["remediation_plan"]:
        action = step["action"]
        decision = evaluate_action(
            action=action,
            confidence=float(incident["confidence"]),
            policy=config.remediation_policy,
            approve=approve,
        )

        log_audit(
            "remediation_action_proposed",
            {
                "incident_id": incident_id,
                "action": action,
                "decision": decision.reason,
                "allowed": decision.allowed,
                "approval_required": decision.approval_required,
            },
        )

        if not decision.allowed:
            actions.append({"action": action, "executed": False, "reason": decision.reason})
            continue

        if action == "quarantine":
            artifact = incident.get("artifact", "")
            item = quarantine_file(artifact)
            result = {"action": action, "executed": True, "item": item.to_dict()}
        elif action == "temp_isolation":
            result = {"action": action, "executed": True, "scope": "temporary-network-isolation"}
        elif action in {"delete", "kill", "network_block"}:
            result = {"action": action, "executed": True, "approved": approve}
        else:
            result = {"action": action, "executed": False, "reason": "unknown action"}

        log_audit("remediation_action_executed", {"incident_id": incident_id, **result})
        actions.append(result)

    final_state = "remediated" if all(a.get("executed") for a in actions) else "needs_approval"
    outcome = "success" if final_state == "remediated" else "blocked_by_policy"
    updated = update_incident(
        incident_id,
        action_state=final_state,
        final_outcome=outcome,
    )
    return {"ok": True, "incident": updated, "actions": actions}
