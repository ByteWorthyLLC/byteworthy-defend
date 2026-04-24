from __future__ import annotations

from bw_defend.core.audit import log_audit
from bw_defend.core.config import DefendConfig
from bw_defend.core.errors import QuarantineError
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
    blocked = 0
    failed = 0
    executed = 0
    for step in incident["remediation_plan"]:
        if not isinstance(step, dict) or "action" not in step:
            actions.append({"action": "unknown", "executed": False, "reason": "invalid remediation step format"})
            failed += 1
            continue
        action = str(step["action"]).strip().lower()
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
            blocked += 1
            continue

        try:
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
        except (OSError, QuarantineError, ValueError) as exc:
            result = {"action": action, "executed": False, "reason": str(exc)}

        log_audit("remediation_action_executed", {"incident_id": incident_id, **result})
        if result.get("executed"):
            executed += 1
        elif "policy" in str(result.get("reason", "")) or "approval" in str(result.get("reason", "")):
            blocked += 1
        else:
            failed += 1
        actions.append(result)

    if actions and all(a.get("executed") for a in actions):
        final_state = "remediated"
        outcome = "success"
    elif blocked > 0 and failed == 0:
        final_state = "needs_approval"
        outcome = "blocked_by_policy"
    else:
        final_state = "failed"
        outcome = "partial_failure"

    updated = update_incident(
        incident_id,
        action_state=final_state,
        final_outcome=outcome,
    )
    return {
        "ok": True,
        "incident": updated,
        "actions": actions,
        "summary": {"executed": executed, "blocked": blocked, "failed": failed},
    }
