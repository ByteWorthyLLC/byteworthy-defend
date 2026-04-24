from __future__ import annotations

from ..core.audit import log_audit
from ..core.config import DefendConfig
from ..core.errors import QuarantineError
from ..core.incidents import get_incident, update_incident
from ..core.policy import evaluate_action
from ..core.quarantine import quarantine_file

KEY_OK = "ok"
KEY_REASON = "reason"
KEY_ACTION = "action"
KEY_EXECUTED = "executed"
KEY_INCIDENT_ID = "incident_id"


def _error_result(reason: str, incident_id: str) -> dict:
    return {KEY_OK: False, KEY_REASON: reason, KEY_INCIDENT_ID: incident_id}


def _evaluate_step(action: str, incident: dict, config: DefendConfig, *, approve: bool) -> dict:
    decision = evaluate_action(
        action=action,
        confidence=float(incident["confidence"]),
        policy=config.remediation_policy,
        approve=approve,
    )
    log_audit(
        "remediation_action_proposed",
        {
            KEY_INCIDENT_ID: incident["id"],
            KEY_ACTION: action,
            "decision": decision.reason,
            "allowed": decision.allowed,
            "approval_required": decision.approval_required,
        },
    )
    if not decision.allowed:
        return {KEY_ACTION: action, KEY_EXECUTED: False, KEY_REASON: decision.reason}
    return {}


def _execute_action(action: str, incident: dict, *, approve: bool) -> dict:
    if action == "quarantine":
        item = quarantine_file(str(incident.get("artifact", "")))
        return {KEY_ACTION: action, KEY_EXECUTED: True, "item": item.to_dict()}
    if action == "temp_isolation":
        return {KEY_ACTION: action, KEY_EXECUTED: True, "scope": "temporary-network-isolation"}
    if action in {"delete", "kill", "network_block"}:
        return {KEY_ACTION: action, KEY_EXECUTED: True, "approved": approve}
    return {KEY_ACTION: action, KEY_EXECUTED: False, KEY_REASON: "unknown action"}


def _summary_state(actions: list[dict], *, blocked: int, failed: int) -> tuple[str, str]:
    if actions and all(action.get(KEY_EXECUTED) for action in actions):
        return "remediated", "success"
    if blocked > 0 and failed == 0:
        return "needs_approval", "blocked_by_policy"
    return "failed", "partial_failure"


def remediate_incident(incident_id: str, config: DefendConfig, *, approve: bool = False) -> dict:
    incident = get_incident(incident_id)
    if not incident:
        return _error_result("incident not found", incident_id)

    if not incident.get("remediation_plan"):
        return _error_result("incident has no remediation plan", incident_id)

    actions: list[dict] = []
    blocked = 0
    failed = 0
    executed = 0
    for step in incident["remediation_plan"]:
        if not isinstance(step, dict) or KEY_ACTION not in step:
            actions.append({KEY_ACTION: "unknown", KEY_EXECUTED: False, KEY_REASON: "invalid remediation step format"})
            failed += 1
            continue

        action = str(step[KEY_ACTION]).strip().lower()
        blocked_result = _evaluate_step(action, incident, config, approve=approve)
        if blocked_result:
            actions.append(blocked_result)
            blocked += 1
            continue

        try:
            result = _execute_action(action, incident, approve=approve)
        except (OSError, QuarantineError, ValueError):
            result = {KEY_ACTION: action, KEY_EXECUTED: False, KEY_REASON: "action execution failed"}

        log_audit("remediation_action_executed", {KEY_INCIDENT_ID: incident_id, **result})
        if result.get(KEY_EXECUTED):
            executed += 1
        elif "policy" in str(result.get(KEY_REASON, "")) or "approval" in str(result.get(KEY_REASON, "")):
            blocked += 1
        else:
            failed += 1
        actions.append(result)

    final_state, outcome = _summary_state(actions, blocked=blocked, failed=failed)
    updated = update_incident(
        incident_id,
        action_state=final_state,
        final_outcome=outcome,
    )
    return {
        KEY_OK: True,
        "incident": updated,
        "actions": actions,
        "summary": {"executed": executed, "blocked": blocked, "failed": failed},
    }
