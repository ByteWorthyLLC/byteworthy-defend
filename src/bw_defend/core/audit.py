from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

from bw_defend.core.fs import append_jsonl
from bw_defend.core.paths import audit_log_path, state_dir


def log_audit(event_type: str, payload: dict[str, Any]) -> None:
    state_dir().mkdir(parents=True, exist_ok=True)
    record = {
        "event_id": f"audit-{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    append_jsonl(audit_log_path(), record)
