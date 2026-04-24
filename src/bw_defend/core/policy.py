from __future__ import annotations

from dataclasses import dataclass

from .config import RemediationPolicy

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
    approved_or_non_gated = approve or confidence >= policy.auto_execute_min_confidence
    reason = "allowed"
    allowed = True
    approval_required = normalized_action in DESTRUCTIVE_ACTIONS

    if normalized_action not in DESTRUCTIVE_ACTIONS | NON_DESTRUCTIVE_ACTIONS:
        allowed = False
        reason = "unknown action is not allowed by policy"
        approval_required = True
    elif approval_required and policy.destructive_requires_approval and not approve:
        allowed = False
        reason = "destructive action requires explicit approval"
    elif not approved_or_non_gated:
        allowed = False
        reason = "confidence below auto-execution threshold"
        approval_required = True
    elif normalized_action == "quarantine" and not policy.allow_auto_quarantine and not approve:
        allowed = False
        reason = "policy blocks automatic quarantine"
        approval_required = True
    elif normalized_action == "temp_isolation" and not policy.allow_auto_temp_isolation and not approve:
        allowed = False
        reason = "policy blocks temporary isolation"
        approval_required = True

    return PolicyDecision(allowed=allowed, approval_required=approval_required, reason=reason)
