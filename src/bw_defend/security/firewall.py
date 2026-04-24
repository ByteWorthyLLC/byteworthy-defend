from __future__ import annotations

import json
from datetime import datetime, timezone

from bw_defend.core.fs import atomic_write_json
from bw_defend.core.paths import firewall_state_path, state_dir


def _read_state() -> dict:
    path = firewall_state_path()
    if not path.exists():
        return {"active": False, "rules_applied": []}
    return json.loads(path.read_text())


def _write_state(state: dict) -> dict:
    state_dir().mkdir(parents=True, exist_ok=True)
    atomic_write_json(firewall_state_path(), state)
    return state


def status() -> dict:
    return _read_state()


def apply() -> dict:
    state = _read_state()
    if state.get("active"):
        state["last_transition"] = "noop_already_active"
        return _write_state(state)
    state.update(
        {
            "active": True,
            "rules_applied": ["deny_known_c2", "rate_limit_outbound_dns"],
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "last_transition": "applied",
        }
    )
    return _write_state(state)


def revert() -> dict:
    state = _read_state()
    if not state.get("active"):
        state["last_transition"] = "noop_already_inactive"
        return _write_state(state)
    state.update(
        {
            "active": False,
            "rules_applied": [],
            "reverted_at": datetime.now(timezone.utc).isoformat(),
            "last_transition": "reverted",
        }
    )
    return _write_state(state)
