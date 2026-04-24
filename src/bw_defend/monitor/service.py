from __future__ import annotations

import json
from datetime import datetime, timezone

from bw_defend.core.fs import atomic_write_json
from bw_defend.core.paths import monitor_state_path, state_dir


def _read_state() -> dict:
    path = monitor_state_path()
    if not path.exists():
        return {"running": False, "started_at": None}
    return json.loads(path.read_text())


def _write_state(state: dict) -> dict:
    state_dir().mkdir(parents=True, exist_ok=True)
    atomic_write_json(monitor_state_path(), state)
    return state


def start_monitor() -> dict:
    state = _read_state()
    if state.get("running"):
        state["last_transition"] = "noop_already_running"
        return _write_state(state)
    state.update(
        {
            "running": True,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_transition": "started",
        }
    )
    return _write_state(state)


def stop_monitor() -> dict:
    state = _read_state()
    if not state.get("running"):
        state["last_transition"] = "noop_already_stopped"
        return _write_state(state)
    state["running"] = False
    state["stopped_at"] = datetime.now(timezone.utc).isoformat()
    state["last_transition"] = "stopped"
    return _write_state(state)


def monitor_status() -> dict:
    return _read_state()
