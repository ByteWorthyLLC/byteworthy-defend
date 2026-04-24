from __future__ import annotations

import csv
import io
import os
import signal
import subprocess

KEY_KILLED = "killed"
KEY_APPROVAL_REQUIRED = "approval_required"
KEY_REASON = "reason"
KEY_PID = "pid"


def _list_processes_unix(limit: int) -> list[dict[str, str]]:
    try:
        proc = subprocess.run(
            ["ps", "-eo", "pid=,comm=,etime="],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.SubprocessError as exc:
        raise ValueError(f"unable to list processes: {exc}") from exc
    rows = [row.strip() for row in proc.stdout.splitlines() if row.strip()]
    items = []
    for row in rows[:limit]:
        parts = row.split(maxsplit=2)
        if len(parts) != 3:
            continue
        pid, command, etime = parts
        items.append({"pid": pid, "command": command, "etime": etime})
    return items


def _list_processes_windows(limit: int) -> list[dict[str, str]]:
    try:
        proc = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        raise ValueError(f"unable to list processes: {exc}") from exc

    reader = csv.reader(io.StringIO(proc.stdout))
    items = []
    for row in reader:
        if len(row) < 2:
            continue
        command = row[0].strip()
        pid = row[1].strip()
        if not pid.isdigit():
            continue
        items.append({"pid": pid, "command": command, "etime": "unknown"})
        if len(items) >= limit:
            break
    return items


def list_processes(limit: int = 20) -> list[dict[str, str]]:
    if limit < 1:
        raise ValueError("process list limit must be at least 1")
    if os.name == "nt":
        return _list_processes_windows(limit)
    return _list_processes_unix(limit)


def kill_process(pid: int, *, approve: bool) -> dict:
    base = {KEY_PID: pid}
    if pid <= 0:
        return {**base, KEY_KILLED: False, KEY_APPROVAL_REQUIRED: False, KEY_REASON: "pid must be a positive integer"}
    if pid == os.getpid():
        return {
            **base,
            KEY_KILLED: False,
            KEY_APPROVAL_REQUIRED: False,
            KEY_REASON: "refusing to terminate current bw-defend process",
        }
    if not approve:
        return {**base, KEY_KILLED: False, KEY_APPROVAL_REQUIRED: True, KEY_REASON: "destructive kill requires --approve"}
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return {**base, KEY_KILLED: False, KEY_APPROVAL_REQUIRED: False, KEY_REASON: "process not found"}
    except PermissionError:
        return {**base, KEY_KILLED: False, KEY_APPROVAL_REQUIRED: False, KEY_REASON: "permission denied"}
    except OSError:
        return {**base, KEY_KILLED: False, KEY_APPROVAL_REQUIRED: False, KEY_REASON: "process termination failed"}
    return {**base, KEY_KILLED: True, KEY_APPROVAL_REQUIRED: False}
