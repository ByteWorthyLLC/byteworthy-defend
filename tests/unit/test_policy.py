from bw_defend.core.config import RemediationPolicy
from bw_defend.core.policy import evaluate_action


def test_destructive_action_requires_approval() -> None:
    policy = RemediationPolicy()
    decision = evaluate_action(action="kill", confidence=0.99, policy=policy, approve=False)
    assert decision.allowed is False
    assert decision.approval_required is True


def test_non_destructive_quarantine_allowed() -> None:
    policy = RemediationPolicy()
    decision = evaluate_action(action="quarantine", confidence=0.99, policy=policy, approve=False)
    assert decision.allowed is True


def test_confidence_gate_requires_approval() -> None:
    policy = RemediationPolicy(auto_execute_min_confidence=0.9)
    decision = evaluate_action(action="quarantine", confidence=0.5, policy=policy, approve=False)
    assert decision.allowed is False
    assert "confidence" in decision.reason
