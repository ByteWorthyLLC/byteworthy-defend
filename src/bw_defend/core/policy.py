from __future__ import annotations

from dataclasses import dataclass

from bw_defend.core.config import RemediationPolicy

DESTRUCTIVE_ACTIONS = {"delete", "kill", "network_block"}
NON_DESTRUCTIVE_ACTIONS = {"quarantine", "temp_isolation"}


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    approval_required: bool
    reason: str


def evaluate_action(
    *,
    action: str,
    confidence: float,
    policy: RemediationPolicy,
    approve: bool,
) -> PolicyDecision:
    normalized_action = action.strip().lower()
    if normalized_action not in DESTRUCTIVE_ACTIONS | NON_DESTRUCTIVE_ACTIONS:
        return PolicyDecision(
            allowed=False,
            approval_required=True,
            reason="unknown action is not allowed by policy",
        )
    is_destructive = normalized_action in DESTRUCTIVE_ACTIONS
    if is_destructive and policy.destructive_requires_approval and not approve:
        return PolicyDecision(
            allowed=False,
            approval_required=True,
            reason="destructive action requires explicit approval",
        )
    if confidence < policy.auto_execute_min_confidence and not approve:
        return PolicyDecision(
            allowed=False,
            approval_required=True,
            reason="confidence below auto-execution threshold",
        )
    if normalized_action == "quarantine" and not policy.allow_auto_quarantine and not approve:
        return PolicyDecision(
            allowed=False,
            approval_required=True,
            reason="policy blocks automatic quarantine",
        )
    if normalized_action == "temp_isolation" and not policy.allow_auto_temp_isolation and not approve:
        return PolicyDecision(
            allowed=False,
            approval_required=True,
            reason="policy blocks temporary isolation",
        )
    return PolicyDecision(allowed=True, approval_required=is_destructive, reason="allowed")
