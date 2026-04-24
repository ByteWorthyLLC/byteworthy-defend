from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from bw_defend.core.paths import audit_log_path, state_dir


def log_audit(event_type: str, payload: dict[str, Any]) -> None:
    state_dir().mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    with audit_log_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
