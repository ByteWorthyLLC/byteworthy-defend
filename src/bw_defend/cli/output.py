from __future__ import annotations

import json
from typing import Any

from rich import print


def emit(payload: Any, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            print(f"[bold]{key}[/bold]: {value}")
    else:
        print(payload)
