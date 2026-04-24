#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bw_defend.monitor.service import monitor_status, start_monitor, stop_monitor
from bw_defend.security.firewall import apply as firewall_apply
from bw_defend.security.firewall import revert as firewall_revert
from bw_defend.security.firewall import status as firewall_status


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run_monitor_cycles(cycles: int) -> dict[str, int]:
    starts = 0
    stops = 0
    for index in range(cycles):
        started = start_monitor()
        _assert(started.get("running") is True, f"monitor start failed at cycle {index}")
        current = monitor_status()
        _assert(current.get("running") is True, f"monitor status failed after start at cycle {index}")
        starts += 1

        stopped = stop_monitor()
        _assert(stopped.get("running") is False, f"monitor stop failed at cycle {index}")
        current = monitor_status()
        _assert(current.get("running") is False, f"monitor status failed after stop at cycle {index}")
        stops += 1

    return {"monitor_starts": starts, "monitor_stops": stops}


def run_firewall_cycles(cycles: int) -> dict[str, int]:
    applies = 0
    reverts = 0
    for index in range(cycles):
        applied = firewall_apply()
        _assert(applied.get("active") is True, f"firewall apply failed at cycle {index}")
        state = firewall_status()
        _assert(state.get("active") is True, f"firewall status failed after apply at cycle {index}")
        applies += 1

        reverted = firewall_revert()
        _assert(reverted.get("active") is False, f"firewall revert failed at cycle {index}")
        state = firewall_status()
        _assert(state.get("active") is False, f"firewall status failed after revert at cycle {index}")
        reverts += 1

    return {"firewall_applies": applies, "firewall_reverts": reverts}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run reliability drill cycles for monitor and firewall controls")
    parser.add_argument("--monitor-cycles", type=int, default=50, help="Number of monitor start/stop cycles")
    parser.add_argument("--firewall-cycles", type=int, default=10, help="Number of firewall apply/revert cycles")
    parser.add_argument("--output", type=str, default="", help="Optional JSON output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.monitor_cycles < 1 or args.firewall_cycles < 1:
        print("cycle counts must be >= 1", file=sys.stderr)
        return 2

    try:
        summary = {}
        summary.update(run_monitor_cycles(args.monitor_cycles))
        summary.update(run_firewall_cycles(args.firewall_cycles))
        payload = {
            "ok": True,
            "summary": summary,
            "targets": {
                "monitor_cycles": args.monitor_cycles,
                "firewall_cycles": args.firewall_cycles,
            },
        }
    except RuntimeError as exc:
        payload = {"ok": False, "error": str(exc)}

    output = json.dumps(payload, sort_keys=True)
    print(output)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output + "\n", encoding="utf-8")

    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
