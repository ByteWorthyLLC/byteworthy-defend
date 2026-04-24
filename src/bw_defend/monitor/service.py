from __future__ import annotations

import json
from datetime import datetime, timezone

from bw_defend.core.paths import monitor_state_path, state_dir


def _read_state() -> dict:
    path = monitor_state_path()
    if not path.exists():
        return {"running": False, "started_at": None}
    return json.loads(path.read_text())


def _write_state(state: dict) -> dict:
    state_dir().mkdir(parents=True, exist_ok=True)
    monitor_state_path().write_text(json.dumps(state, indent=2, sort_keys=True))
    return state


def start_monitor() -> dict:
    state = {"running": True, "started_at": datetime.now(timezone.utc).isoformat()}
    return _write_state(state)


def stop_monitor() -> dict:
    state = _read_state()
    state["running"] = False
    state["stopped_at"] = datetime.now(timezone.utc).isoformat()
    return _write_state(state)


def monitor_status() -> dict:
    return _read_state()
