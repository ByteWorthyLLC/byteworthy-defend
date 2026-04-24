from __future__ import annotations

import platform
from pathlib import Path

import typer

from bw_defend.ai.remediation import remediate_incident
from bw_defend.core.audit import log_audit
from bw_defend.core.config import config_as_dict, load_config
from bw_defend.core.engine import scan_target
from bw_defend.core.errors import ConfigValidationError, DefendError
from bw_defend.core.fs import ensure_writable_dir
from bw_defend.core.incidents import create_incident
from bw_defend.core.paths import config_file, state_dir
from bw_defend.core.quarantine import list_quarantine, purge_quarantine, restore_item
from bw_defend.core.rules import list_rules, update_rules, verify_rules
from bw_defend.monitor.service import monitor_status, start_monitor, stop_monitor
from bw_defend.security import firewall, process_control
from bw_defend.cli.output import emit

SUPPORTED_PLATFORMS = {"linux", "windows"}

app = typer.Typer(help="ByteWorthy Defend terminal antivirus for Windows and Linux")
monitor_app = typer.Typer()
quarantine_app = typer.Typer()
firewall_app = typer.Typer()
process_app = typer.Typer()
ai_app = typer.Typer()
rules_app = typer.Typer()

app.add_typer(monitor_app, name="monitor")
app.add_typer(quarantine_app, name="quarantine")
app.add_typer(firewall_app, name="firewall")
app.add_typer(process_app, name="process")
app.add_typer(ai_app, name="ai")
app.add_typer(rules_app, name="rules")


def _must_be_ai_edition() -> None:
    config = load_config()
    if config.edition != "ai":
        raise typer.BadParameter(
            "AI edition command requested but config edition is not 'ai'. "
            "Set edition = \"ai\" in ~/.config/bw-defend/config.toml"
        )


def _emit_error(message: str, json_output: bool, *, code: int = 1) -> None:
    emit({"ok": False, "error": message, "exit_code": code}, json_output)
    raise typer.Exit(code)


@app.command("scan")
def scan(
    target: str = typer.Argument(..., help="Path to scan or literal 'system'"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON output"),
) -> None:
    try:
        results = scan_target(target)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)

    incident_ids = []
    try:
        for finding in results["findings"]:
            incident = create_incident(
                source="scan",
                artifact=finding["artifact"],
                detection_type=finding["detection_type"],
                severity=finding["severity"],
                confidence=finding["confidence"],
                approval_required=False,
                remediation_plan=[{"action": "quarantine", "reason": "malware signature match"}],
            )
            incident_ids.append(incident.id)
            log_audit("incident_created", incident.to_dict())
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(f"scan succeeded but incident creation failed: {exc}", json_output)
    results["incidents_created"] = len(incident_ids)
    results["incident_ids"] = incident_ids
    emit(results, json_output)


@monitor_app.command("start")
def monitor_start(json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        emit(start_monitor(), json_output)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)


@monitor_app.command("stop")
def monitor_stop(json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        emit(stop_monitor(), json_output)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)


@monitor_app.command("status")
def monitor_status_cmd(json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        emit(monitor_status(), json_output)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)


@quarantine_app.command("list")
def quarantine_list(json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        emit({"items": list_quarantine()}, json_output)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)


@quarantine_app.command("restore")
def quarantine_restore(
    item_id: str = typer.Argument(..., help="Quarantine item id"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    try:
        emit({"restored": restore_item(item_id)}, json_output)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)


@quarantine_app.command("purge")
def quarantine_purge(json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        emit({"purged_count": purge_quarantine()}, json_output)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)


@firewall_app.command("status")
def firewall_status(json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        emit(firewall.status(), json_output)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)


@firewall_app.command("apply")
def firewall_apply(json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        emit(firewall.apply(), json_output)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)


@firewall_app.command("revert")
def firewall_revert(json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        emit(firewall.revert(), json_output)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)


@process_app.command("list")
def process_list(json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        emit({"processes": process_control.list_processes()}, json_output)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)


@process_app.command("kill")
def process_kill(
    pid: int = typer.Option(..., "--pid", help="Process ID to terminate"),
    approve: bool = typer.Option(False, "--approve", help="Required for destructive kill action"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    try:
        result = process_control.kill_process(pid, approve=approve)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)
    log_audit("process_kill_attempt", result)
    emit(result, json_output)


@ai_app.command("remediate")
def ai_remediate(
    incident_id: str = typer.Argument(..., help="Incident id"),
    approve: bool = typer.Option(False, "--approve", help="Approve destructive actions"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    try:
        _must_be_ai_edition()
        config = load_config()
        result = remediate_incident(incident_id=incident_id, config=config, approve=approve)
        emit(result, json_output)
    except (DefendError, OSError, ValueError, typer.BadParameter) as exc:
        _emit_error(str(exc), json_output)


@rules_app.command("update")
def rules_update(
    bundle_path: str = typer.Argument(..., help="Path to rule bundle JSON"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    try:
        result = update_rules(bundle_path)
    except (DefendError, OSError, ValueError, FileNotFoundError) as exc:
        _emit_error(str(exc), json_output)
    emit(result, json_output)
    if not result.get("updated"):
        raise typer.Exit(2)


@rules_app.command("list")
def rules_list(json_output: bool = typer.Option(False, "--json")) -> None:
    try:
        emit(list_rules(), json_output)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)


@rules_app.command("verify")
def rules_verify(
    bundle_path: str | None = typer.Option(None, "--bundle", help="Optional file to verify instead of active rules"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    try:
        path = Path(bundle_path).expanduser().resolve() if bundle_path else None
        result = verify_rules(path)
    except (DefendError, OSError, ValueError) as exc:
        _emit_error(str(exc), json_output)
    emit(result, json_output)
    if not result.get("verified"):
        raise typer.Exit(2)


@app.command("doctor")
def doctor(
    json_output: bool = typer.Option(False, "--json"),
    strict: bool = typer.Option(False, "--strict", help="Exit non-zero when any doctor check fails"),
) -> None:
    runtime_platform = platform.system().lower()
    try:
        config = load_config()
        config_loaded = True
        config_error = ""
    except ConfigValidationError as exc:
        config = None
        config_loaded = False
        config_error = str(exc)
    writable = ensure_writable_dir(state_dir())
    payload = {
        "config_path": str(config_file()),
        "state_dir": str(state_dir()),
        "edition": config.edition if config else "unknown",
        "config": config_as_dict(config) if config else {},
        "checks": {
            "supported_platform": runtime_platform in SUPPORTED_PLATFORMS,
            "config_loaded": config_loaded,
            "state_writable": writable,
        },
        "platform": runtime_platform,
        "errors": {"config": config_error} if config_error else {},
    }
    emit(payload, json_output)
    if strict and not all(payload["checks"].values()):
        raise typer.Exit(2)


def run() -> None:
    app()


if __name__ == "__main__":
    run()
