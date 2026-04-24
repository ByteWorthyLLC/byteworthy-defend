from __future__ import annotations

import os
import signal
import subprocess


def list_processes(limit: int = 20) -> list[dict[str, str]]:
    proc = subprocess.run(
        ["ps", "-eo", "pid=,comm=,etime="],
        capture_output=True,
        text=True,
        check=True,
    )
    rows = [row.strip() for row in proc.stdout.splitlines() if row.strip()]
    items = []
    for row in rows[:limit]:
        pid, command, etime = row.split(maxsplit=2)
        items.append({"pid": pid, "command": command, "etime": etime})
    return items


def kill_process(pid: int, approve: bool) -> dict:
    if not approve:
        return {
            "killed": False,
            "approval_required": True,
            "reason": "destructive kill requires --approve",
            "pid": pid,
        }
    os.kill(pid, signal.SIGTERM)
    return {"killed": True, "approval_required": False, "pid": pid}
