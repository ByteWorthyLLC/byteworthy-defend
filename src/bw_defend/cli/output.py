from __future__ import annotations

import json
from typing import Any

from rich.console import Console

CONSOLE = Console()


def emit(payload: Any, *, json_output: bool) -> None:
    if json_output:
        CONSOLE.print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            CONSOLE.print(f"[bold]{key}[/bold]: {value}")
    else:
        CONSOLE.print(payload)
