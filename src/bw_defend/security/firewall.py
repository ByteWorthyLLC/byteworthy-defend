from __future__ import annotations

import json
from datetime import datetime, timezone

from ..core.fs import atomic_write_json
from ..core.paths import firewall_state_path, state_dir

KEY_ACTIVE = "active"
KEY_RULES_APPLIED = "rules_applied"
KEY_LAST_TRANSITION = "last_transition"


def _read_state() -> dict:
    path = firewall_state_path()
    if not path.exists():
        return {KEY_ACTIVE: False, KEY_RULES_APPLIED: []}
    return json.loads(path.read_text())


def _write_state(state: dict) -> dict:
    state_dir().mkdir(parents=True, exist_ok=True)
    atomic_write_json(firewall_state_path(), state)
    return state


def status() -> dict:
    return _read_state()


def apply() -> dict:
    state = _read_state()
    if state.get(KEY_ACTIVE):
        state[KEY_LAST_TRANSITION] = "noop_already_active"
        return _write_state(state)
    state.update(
        {
            KEY_ACTIVE: True,
            KEY_RULES_APPLIED: ["deny_known_c2", "rate_limit_outbound_dns"],
            "applied_at": datetime.now(timezone.utc).isoformat(),
            KEY_LAST_TRANSITION: "applied",
        }
    )
    return _write_state(state)


def revert() -> dict:
    state = _read_state()
    if not state.get(KEY_ACTIVE):
        state[KEY_LAST_TRANSITION] = "noop_already_inactive"
        return _write_state(state)
    state.update(
        {
            KEY_ACTIVE: False,
            KEY_RULES_APPLIED: [],
            "reverted_at": datetime.now(timezone.utc).isoformat(),
            KEY_LAST_TRANSITION: "reverted",
        }
    )
    return _write_state(state)
