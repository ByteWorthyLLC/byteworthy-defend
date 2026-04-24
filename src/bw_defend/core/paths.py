from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "bw-defend"


def _is_windows() -> bool:
    return os.name == "nt"


def config_dir() -> Path:
    if custom := os.getenv("BW_DEFEND_CONFIG_DIR"):
        return Path(custom).expanduser()
    if _is_windows():
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / APP_NAME
    return Path.home() / ".config" / APP_NAME


def config_file() -> Path:
    return config_dir() / "config.toml"


def state_dir() -> Path:
    if custom := os.getenv("BW_DEFEND_STATE_DIR"):
        return Path(custom).expanduser()
    if _is_windows():
        local_appdata = os.getenv("LOCALAPPDATA")
        if local_appdata:
            return Path(local_appdata) / APP_NAME / "state"
    return Path.home() / ".local" / "state" / APP_NAME


def quarantine_dir() -> Path:
    return state_dir() / "quarantine"


def incidents_path() -> Path:
    return state_dir() / "incidents.jsonl"


def audit_log_path() -> Path:
    return state_dir() / "audit.log"


def monitor_state_path() -> Path:
    return state_dir() / "monitor.json"


def firewall_state_path() -> Path:
    return state_dir() / "firewall.json"


def rules_dir() -> Path:
    return state_dir() / "rules"


def active_rules_file() -> Path:
    return rules_dir() / "active-rules.json"
