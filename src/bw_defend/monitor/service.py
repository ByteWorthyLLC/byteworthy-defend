from __future__ import annotations

import json
from datetime import datetime, timezone

from ..core.fs import atomic_write_json
from ..core.paths import monitor_state_path, state_dir

KEY_RUNNING = "running"
KEY_LAST_TRANSITION = "last_transition"


def _read_state() -> dict:
    path = monitor_state_path()
    if not path.exists():
        return {KEY_RUNNING: False, "started_at": None}
    return json.loads(path.read_text())


def _write_state(state: dict) -> dict:
    state_dir().mkdir(parents=True, exist_ok=True)
    atomic_write_json(monitor_state_path(), state)
    return state


def start_monitor() -> dict:
    state = _read_state()
    if state.get(KEY_RUNNING):
        state[KEY_LAST_TRANSITION] = "noop_already_running"
        return _write_state(state)
    state.update(
        {
            KEY_RUNNING: True,
            "started_at": datetime.now(timezone.utc).isoformat(),
            KEY_LAST_TRANSITION: "started",
        }
    )
    return _write_state(state)


def stop_monitor() -> dict:
    state = _read_state()
    if not state.get(KEY_RUNNING):
        state[KEY_LAST_TRANSITION] = "noop_already_stopped"
        return _write_state(state)
    state[KEY_RUNNING] = False
    state["stopped_at"] = datetime.now(timezone.utc).isoformat()
    state[KEY_LAST_TRANSITION] = "stopped"
    return _write_state(state)


def monitor_status() -> dict:
    return _read_state()
