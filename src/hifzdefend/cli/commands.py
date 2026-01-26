"""
CLI commands for HifzDefend.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from ..config.loader import get_config
from ..config.validator import validate_config
from ..core.engine import ScanEngine
from ..monitoring.manager import MonitorManager
from ..reporting.formatter import save_report as save_scan_report
from ..reporting.logger import setup_logger
from ..rules.app_whitelist import ApplicationWhitelist
from ..rules.engine import RulesEngine
from ..threat_intel.manager import ThreatIntelligenceManager
from ..utils.exceptions import HifzDefendError
from ..utils.helpers import validate_path

# AI imports (conditional - only if AI is enabled)
try:
    from ..ai.claude_analyzer import ClaudeAnalyzer
    from ..ai import CHROMADB_AVAILABLE

    AI_AVAILABLE = True

    # NaturalLanguageInterface requires ChromaDB
    if CHROMADB_AVAILABLE:
        from ..ai.nl_interface import NaturalLanguageInterface
    else:
        NaturalLanguageInterface = None  # type: ignore
except (ImportError, Exception):
    AI_AVAILABLE = False
    CHROMADB_AVAILABLE = False
    NaturalLanguageInterface = None  # type: ignore


console = Console(force_terminal=True, legacy_windows=False)


# Helper functions for consistent error messaging
def print_ai_not_available_error():
    """Print error message when AI features are not available."""
    console.print("[bold red]ERROR:[/bold red] AI features not available")
    console.print("\n[yellow]To enable AI features:[/yellow]")
    console.print("  1. Install dependencies:")
    console.print("     pip install anthropic chromadb sentence-transformers")
    console.print("  2. Get Claude API key from:")
    console.print("     https://console.anthropic.com/settings/keys")
    console.print("  3. Set environment variable:")
    console.print("     $env:CLAUDE_API_KEY = 'sk-ant-api03-...'")
    console.print("\n[cyan]Need help?[/cyan] See docs/AI_USAGE.md")


def print_api_key_not_set_error():
    """Print error message when Claude API key is not set."""
    console.print("[bold red]ERROR:[/bold red] Claude API key not set")
    console.print("\n[yellow]To set your API key:[/yellow]")
    console.print("  1. Get a key from: https://console.anthropic.com/settings/keys")
    console.print("  2. Set it temporarily:")
    console.print("     $env:CLAUDE_API_KEY = 'sk-ant-api03-...'")
    console.print("  3. Or set it permanently (Windows):")
    console.print("     [Environment]::SetEnvironmentVariable('CLAUDE_API_KEY', 'sk-ant-api03-...', 'User')")
    console.print("\n[cyan]Need help?[/cyan] See docs/QUICKSTART.md")


def validate_api_key(api_key: str) -> tuple[bool, str]:
    """
    Validate Claude API key format.

    Returns:
        (is_valid, error_message)
    """
    if not api_key:
        return False, "API key is empty"

    if not api_key.startswith("sk-ant-"):
        return False, "API key must start with 'sk-ant-'"

    if len(api_key) < 20:
        return False, "API key is too short (seems invalid)"

    return True, ""


def print_api_key_invalid_error(reason: str):
    """Print error message when API key format is invalid."""
    console.print(f"[bold red]ERROR:[/bold red] Invalid API key format: {reason}")
    console.print("\n[yellow]Valid API key format:[/yellow]")
    console.print("  - Must start with: sk-ant-")
    console.print("  - Example: sk-ant-api03-...")
    console.print("\n[yellow]Get a valid key from:[/yellow]")
    console.print("  https://console.anthropic.com/settings/keys")
    console.print("\n[cyan]Need help?[/cyan] See docs/TROUBLESHOOTING.md")


def print_api_error_with_hints(error: Exception, context: str = ""):
    """Print API error with troubleshooting hints."""
    error_str = str(error).lower()

    console.print(f"[bold red]ERROR:[/bold red] {context}: {error}")
    console.print("\n[yellow]Troubleshooting:[/yellow]")

    # Authentication errors
    if "authentication" in error_str or "401" in error_str or "unauthorized" in error_str:
        console.print("  • Your API key is invalid or expired")
        console.print("  • Get a new key: https://console.anthropic.com/settings/keys")
        console.print("  • Verify with: hifzdefend ai test")

    # Rate limit errors
    elif "rate limit" in error_str or "429" in error_str:
        console.print("  • You've exceeded the API rate limit")
        console.print("  • Wait a few minutes and try again")
        console.print("  • Check usage: hifzdefend ai stats")
        console.print("  • Adjust rate limit in config: max_requests_per_hour")

    # Network errors
    elif "timeout" in error_str or "connection" in error_str or "network" in error_str:
        console.print("  • Check your internet connection")
        console.print("  • Firewall may be blocking the connection")
        console.print("  • Check Anthropic status: https://status.anthropic.com")

    # Quota/billing errors
    elif "quota" in error_str or "billing" in error_str or "payment" in error_str:
        console.print("  • Your account may have exceeded its quota")
        console.print("  • Check billing: https://console.anthropic.com/settings/billing")
        console.print("  • Add payment method if needed")

    # Generic fallback
    else:
        console.print("  • Test connection: hifzdefend ai test")
        console.print("  • Check API status: https://status.anthropic.com")
        console.print("  • View docs: docs/TROUBLESHOOTING.md")

    console.print("\n[cyan]Still need help?[/cyan] See docs/TROUBLESHOOTING.md")


def validate_resource_value(resource_type: str, resource_value: str) -> tuple[bool, str]:
    """
    Validate resource value based on type (IP, file hash, or package).

    Args:
        resource_type: Type of resource (ip, file, package)
        resource_value: Value to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    import re

    if resource_type == "ip":
        # Validate IPv4 address
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ipv4_pattern, resource_value):
            return False, "Invalid IPv4 address format (expected: x.x.x.x)"

        # Validate octets are in range 0-255
        octets = resource_value.split('.')
        if not all(0 <= int(octet) <= 255 for octet in octets):
            return False, "IPv4 octets must be between 0 and 255"

    elif resource_type == "file":
        # Validate file hash (SHA256 = 64 hex chars, MD5 = 32 hex chars, SHA1 = 40 hex chars)
        if not re.match(r'^[a-fA-F0-9]{32}$|^[a-fA-F0-9]{40}$|^[a-fA-F0-9]{64}$', resource_value):
            return False, "Invalid file hash (expected: MD5, SHA1, or SHA256 hex string)"

    elif resource_type == "package":
        # Validate package name format (name@version or @scope/name@version)
        # Allow alphanumeric, hyphens, underscores, dots, slashes for scoped packages
        package_pattern = r'^(@?[a-zA-Z0-9_\-\.\/]+)(@[a-zA-Z0-9_\-\.]+)?$'
        if not re.match(package_pattern, resource_value):
            return False, "Invalid package format (expected: package@version or @scope/package@version)"

        # Check for suspicious patterns
        suspicious_patterns = ['..', '//', '\\', '<', '>', '|', '&', ';', '`']
        if any(pattern in resource_value for pattern in suspicious_patterns):
            return False, "Package name contains suspicious characters"

    return True, ""


def validate_threat_name(threat_name: str) -> tuple[bool, str]:
    """
    Validate threat name to prevent path traversal and command injection.

    Args:
        threat_name: Threat name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    import re

    # Limit length
    if len(threat_name) > 200:
        return False, "Threat name too long (max 200 characters)"

    # Check for path traversal patterns
    if '..' in threat_name or '/' in threat_name or '\\' in threat_name:
        return False, "Threat name cannot contain path separators or '..'"

    # Allow only alphanumeric, spaces, hyphens, underscores, dots, parentheses
    if not re.match(r'^[a-zA-Z0-9 _\-\.\(\)]+$', threat_name):
        return False, "Threat name contains invalid characters (only alphanumeric, spaces, -_.() allowed)"

    # Check for null bytes
    if '\x00' in threat_name:
        return False, "Threat name contains null bytes"

    return True, ""


@click.group()
@click.version_option(version="0.2.0", prog_name="HifzDefend")
def cli():
    """
    HifzDefend - Custom Windows Antivirus Solution

    Preserving Your Digital Safety (حفظ)
    """
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--save-report", is_flag=True, help="Save scan report to file")
def scan(path: str, save_report: bool):
    """Scan a file or directory for malware."""
    try:
        # Load configuration
        config = get_config()
        validate_config(config)

        # Setup logger
        logger = setup_logger("hifzdefend", config.logging, console=False)

        console.print(f"\n[bold cyan]HifzDefend Scanner[/bold cyan]")
        console.print(f"Scanning: [yellow]{path}[/yellow]\n")

        # Create scan engine
        with ScanEngine(config) as engine:
            # Check ClamAV connection
            if not engine.check_connection():
                console.print(
                    "[bold red]ERROR:[/bold red] Cannot connect to ClamAV daemon"
                )
                console.print(
                    f"Expected at: {config.clamav.host}:{config.clamav.port}"
                )
                console.print("\n[yellow]ClamAV is required for file scanning[/yellow]")
                console.print("  Download: https://www.clamav.net/downloads")
                console.print("  Or use AI features instead (no ClamAV needed):")
                console.print("    hifzdefend analyze-script <file.ps1>")
                console.print("\n[cyan]Need help?[/cyan] See docs/TROUBLESHOOTING.md")
                return

            # Perform scan with progress
            scan_path = Path(path)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Scanning...", total=None
                )

                report = engine.scan_path(scan_path)
                progress.update(task, completed=True)

            # Display results
            console.print("\n[bold]Scan Results:[/bold]")
            console.print(f"Files scanned: {report.files_scanned}")
            console.print(f"Duration: {report.duration:.2f} seconds")

            if report.has_threats:
                console.print(f"\n[bold red][WARNING] Threats found: {report.threats_count}[/bold red]")

                # Display threats table
                table = Table(title="Detected Threats")
                table.add_column("File", style="cyan")
                table.add_column("Threat", style="red")
                table.add_column("Quarantined", style="yellow")

                for threat in report.threats_found:
                    table.add_row(
                        threat["file_path"],
                        threat["threat_name"],
                        "Yes" if threat["quarantined"] else "No",
                    )

                console.print(table)
            else:
                console.print("\n[bold green][OK] No threats detected[/bold green]")

            # Save report if requested
            if save_report or report.has_threats:
                report_path = save_scan_report(report, config.reporting)
                console.print(f"\nReport saved: [cyan]{report_path}[/cyan]")

            logger.info(
                f"Scan completed: {report.files_scanned} files, "
                f"{report.threats_count} threats"
            )

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        logging.exception("Scan command failed")


@cli.command()
def status():
    """Display system status and ClamAV information."""
    try:
        # Load configuration
        config = get_config()

        console.print("\n[bold cyan]HifzDefend Status[/bold cyan]\n")

        # Check ClamAV connection
        with ScanEngine(config) as engine:
            if engine.check_connection():
                console.print("[bold green][OK][/bold green] ClamAV daemon: Running")

                # Get version
                version = engine.get_version()
                if version:
                    console.print(f"[bold]Version:[/bold] {version}")
            else:
                console.print("[bold red][FAIL][/bold red] ClamAV daemon: Not running")
                console.print(
                    f"  Expected at: {config.clamav.host}:{config.clamav.port}"
                )
                console.print("\n[yellow]Note:[/yellow] ClamAV is OPTIONAL for AI features")
                console.print("  AI script analysis works WITHOUT ClamAV")
                console.print("  ClamAV is only needed for traditional antivirus scanning")
                console.print("\n[yellow]If you want to use ClamAV:[/yellow]")
                console.print("  1. Download from: https://www.clamav.net/downloads")
                console.print("  2. Ensure clamd.exe is running")
                console.print("  3. Check configuration in clamd.conf")
                console.print("  4. Verify TCPSocket is enabled on port 3310")
                console.print("\n[cyan]Need help?[/cyan] See docs/TROUBLESHOOTING.md")

        # Display configuration
        console.print("\n[bold]Configuration:[/bold]")
        console.print(f"  Log directory: {config.logging.log_dir}")
        console.print(f"  Report directory: {config.reporting.report_dir}")
        console.print(f"  Quarantine: {'Enabled' if config.quarantine.enabled else 'Disabled'}")
        if config.quarantine.enabled:
            console.print(f"  Quarantine directory: {config.quarantine.quarantine_dir}")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        logging.exception("Status command failed")


@cli.command()
def update():
    """Update virus definitions."""
    import subprocess

    console.print("\n[bold cyan]Updating Virus Definitions[/bold cyan]\n")

    try:
        # Try to run freshclam
        result = subprocess.run(
            ["freshclam"],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            console.print("[bold green][OK][/bold green] Virus definitions updated successfully")
            if result.stdout:
                console.print(result.stdout)
        else:
            console.print("[bold red][FAIL][/bold red] Update failed")
            if result.stderr:
                console.print(result.stderr)

    except FileNotFoundError:
        console.print("[bold red]ERROR:[/bold red] freshclam not found")
        console.print("\n[yellow]ClamAV is not installed or not in PATH[/yellow]")
        console.print("  Download ClamAV: https://www.clamav.net/downloads")
        console.print("  Or add ClamAV bin directory to PATH")
        console.print("\n[yellow]Note:[/yellow] ClamAV is optional for AI features")
        console.print("  Use AI commands without ClamAV: hifzdefend ai --help")
    except subprocess.TimeoutExpired:
        console.print("[bold red]ERROR:[/bold red] Update timed out")
    except Exception as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--threat-name", required=True, help="Name of detected threat")
def quarantine(file_path: str, threat_name: str):
    """Manually quarantine a file."""
    try:
        # Validate threat name to prevent path traversal and injection
        is_valid, error_msg = validate_threat_name(threat_name)
        if not is_valid:
            console.print(f"[bold red]ERROR:[/bold red] Invalid threat name: {error_msg}")
            console.print("\n[yellow]Example:[/yellow]")
            console.print("  hifzdefend quarantine suspicious.exe --threat-name \"Trojan.Generic\"")
            return

        config = get_config()

        console.print(f"\n[bold cyan]Quarantine File[/bold cyan]")
        console.print(f"File: [yellow]{file_path}[/yellow]")
        console.print(f"Threat: [red]{threat_name}[/red]\n")

        with ScanEngine(config) as engine:
            entry = engine.quarantine_file(file_path, threat_name)

            console.print("[bold green][OK][/bold green] File quarantined successfully")
            console.print(f"Quarantine ID: {entry.quarantine_id}")
            console.print(f"Hash: {entry.file_hash}")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


@cli.command("list-quarantine")
def list_quarantine():
    """List quarantined files."""
    try:
        config = get_config()
        quarantine_dir = config.quarantine.quarantine_dir_path

        console.print("\n[bold cyan]Quarantined Files[/bold cyan]\n")

        if not quarantine_dir.exists():
            console.print("No quarantined files found")
            return

        # List quarantined files
        quarantined_files = list(quarantine_dir.glob("*.quarantined"))

        if not quarantined_files:
            console.print("No quarantined files found")
            return

        table = Table(title=f"Quarantine Directory: {quarantine_dir}")
        table.add_column("Quarantine ID", style="cyan")
        table.add_column("File", style="yellow")
        table.add_column("Size", style="green")

        for qfile in quarantined_files:
            qid = qfile.stem
            size = qfile.stat().st_size
            size_str = f"{size / 1024:.2f} KB"
            table.add_row(qid, qfile.name, size_str)

        console.print(table)
        console.print(f"\nTotal: {len(quarantined_files)} files")

    except Exception as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")


@cli.command("config-show")
def config_show():
    """Display current configuration."""
    try:
        config = get_config()

        console.print("\n[bold cyan]HifzDefend Configuration[/bold cyan]\n")

        # Convert to dict and display as JSON
        config_dict = config.model_dump()
        console.print(json.dumps(config_dict, indent=2))

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


# ============================================================================
# MONITORING COMMANDS (Phase 1.5)
# ============================================================================


@cli.group()
def monitor():
    """Manage security monitors."""
    pass


@monitor.command()
def start():
    """Start all enabled monitors."""
    import asyncio

    try:
        config = get_config()

        console.print("\n[bold cyan]Starting Security Monitors[/bold cyan]\n")

        # Create monitor manager
        manager = MonitorManager()

        # Start monitors asynchronously
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Starting monitors...", total=None)

            asyncio.run(manager.start_all())

            progress.update(task, completed=True)

        console.print("[bold green][OK][/bold green] All monitors started")

        # Display status
        status_data = manager.get_status()
        table = Table(title="Monitor Status")
        table.add_column("Monitor", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Events", style="yellow")

        for monitor_name, monitor_status in status_data.items():
            if monitor_name != "event_bus":
                status_str = "Running" if monitor_status.get("running", False) else "Stopped"
                events = monitor_status.get("events_generated", 0)
                table.add_row(monitor_name, status_str, str(events))

        console.print("\n")
        console.print(table)
        console.print("\n[yellow]Note:[/yellow] Monitors running in background. Use 'hifzdefend monitor stop' to stop.")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        logging.exception("Monitor start command failed")


@monitor.command()
def stop():
    """Stop all monitors."""
    import asyncio

    try:
        config = get_config()

        console.print("\n[bold cyan]Stopping Security Monitors[/bold cyan]\n")

        # Create monitor manager
        manager = MonitorManager()

        # Stop monitors asynchronously
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Stopping monitors...", total=None)

            asyncio.run(manager.stop_all())

            progress.update(task, completed=True)

        console.print("[bold green][OK][/bold green] All monitors stopped")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        logging.exception("Monitor stop command failed")


@monitor.command("status")
def monitor_status():
    """Display monitor status."""
    try:
        config = get_config()

        console.print("\n[bold cyan]Monitor Status[/bold cyan]\n")

        # Create monitor manager
        manager = MonitorManager()

        # Get status
        status_data = manager.get_status()

        # Event bus status
        if "event_bus_stats" in status_data:
            bus_status = status_data["event_bus_stats"]
            console.print("[bold]Event Bus:[/bold]")
            console.print(f"  Status: {'Running' if bus_status.get('running', False) else 'Stopped'}")
            console.print(f"  Events processed: {bus_status.get('events_processed', 0)}")
            console.print(f"  Queue size: {bus_status.get('queue_size', 0)}\n")

        # Manager status
        console.print("[bold]Manager:[/bold]")
        console.print(f"  Running: {status_data.get('manager_running', False)}")
        console.print(f"  Total monitors: {status_data.get('total_monitors', 0)}")
        console.print(f"  Running monitors: {status_data.get('running_monitors', 0)}\n")

        # Monitors table
        table = Table(title="Security Monitors")
        table.add_column("Monitor", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Enabled", style="yellow")
        table.add_column("Events", style="blue")
        table.add_column("Last Check", style="magenta")

        monitors_data = status_data.get("monitors", {})
        for monitor_name, monitor_status in monitors_data.items():
            status_str = "Running" if monitor_status.get("running", False) else "Stopped"
            enabled_str = "Yes" if monitor_status.get("enabled", False) else "No"
            events = monitor_status.get("events_generated", 0)
            last_check = monitor_status.get("last_check", "Never")

            table.add_row(
                monitor_name,
                status_str,
                enabled_str,
                str(events),
                last_check,
            )

        console.print(table)

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        logging.exception("Monitor status command failed")


@monitor.command()
@click.argument("monitor_name")
def enable(monitor_name: str):
    """Enable a specific monitor."""
    try:
        config = get_config()

        console.print(f"\n[bold cyan]Enabling Monitor:[/bold cyan] {monitor_name}\n")

        # Update configuration
        # Note: This requires implementing config persistence
        console.print("[yellow]Note:[/yellow] Configuration persistence not yet implemented")
        console.print("To enable, modify your configuration file:")
        console.print(f"  [monitoring.{monitor_name}]")
        console.print(f"  enabled = true")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


@monitor.command()
@click.argument("monitor_name")
def disable(monitor_name: str):
    """Disable a specific monitor."""
    try:
        config = get_config()

        console.print(f"\n[bold cyan]Disabling Monitor:[/bold cyan] {monitor_name}\n")

        # Update configuration
        # Note: This requires implementing config persistence
        console.print("[yellow]Note:[/yellow] Configuration persistence not yet implemented")
        console.print("To disable, modify your configuration file:")
        console.print(f"  [monitoring.{monitor_name}]")
        console.print(f"  enabled = false")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


@cli.group()
def alerts():
    """Manage security alerts."""
    pass


@alerts.command("list")
@click.option("--limit", default=50, help="Maximum number of alerts to display")
@click.option("--severity", type=click.Choice(["info", "warning", "critical"]), help="Filter by severity")
def alerts_list(limit: int, severity: Optional[str]):
    """List recent security alerts."""
    try:
        config = get_config()

        console.print("\n[bold cyan]Security Alerts[/bold cyan]\n")

        # Note: This requires implementing event storage
        console.print("[yellow]Note:[/yellow] Alert storage not yet implemented")
        console.print("Alerts are currently logged to:")
        console.print(f"  {config.logging.log_dir}/hifzdefend.log")

        # Placeholder: Read from log file
        log_file = Path(config.logging.log_dir) / "hifzdefend.log"
        if log_file.exists():
            console.print(f"\n[bold]Recent log entries:[/bold]")
            with open(log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if severity:
                        if severity.upper() in line:
                            console.print(line.strip())
                    else:
                        console.print(line.strip())

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


@alerts.command()
def clear():
    """Clear alert history."""
    try:
        console.print("\n[bold cyan]Clear Alert History[/bold cyan]\n")

        console.print("[yellow]Note:[/yellow] Alert storage not yet implemented")
        console.print("To clear logs, manually delete log files from:")

        config = get_config()
        console.print(f"  {config.logging.log_dir}")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


@cli.group()
def rules():
    """Manage custom detection rules."""
    pass


@rules.command("list")
def rules_list():
    """List active detection rules."""
    try:
        config = get_config()

        console.print("\n[bold cyan]Active Detection Rules[/bold cyan]\n")

        # Create rules engine
        rules_engine = RulesEngine(config.rules)

        # List YARA rules
        console.print("[bold]YARA Rules:[/bold]")
        # Note: Requires implementing rule listing in RulesEngine
        console.print("  Custom signatures path: " + str(config.rules.custom_signatures_path))

        # List file blocking rules
        console.print("\n[bold]File Blocking Rules:[/bold]")
        if config.rules.file_blocking.enabled:
            console.print(f"  Status: Enabled")
            console.print(f"  Blocked extensions: {', '.join(config.rules.file_blocking.blocked_extensions)}")
            console.print(f"  Context-aware: {config.rules.file_blocking.context_aware}")
        else:
            console.print("  Status: Disabled")

        # List whitelist rules
        console.print("\n[bold]Application Whitelist:[/bold]")
        if config.rules.app_whitelist.enabled:
            console.print(f"  Mode: {'Whitelist' if config.rules.app_whitelist.whitelist_mode else 'Blacklist'}")
            console.print(f"  Whitelisted apps: {len(config.rules.app_whitelist.whitelisted_apps)}")
        else:
            console.print("  Status: Disabled")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        logging.exception("Rules list command failed")


@rules.command()
@click.argument("rule_file", type=click.Path(exists=True))
def add(rule_file: str):
    """Add a custom YARA rule."""
    import shutil

    try:
        config = get_config()

        console.print(f"\n[bold cyan]Adding Custom Rule[/bold cyan]")
        console.print(f"Rule file: [yellow]{rule_file}[/yellow]\n")

        # Copy rule file to custom signatures directory
        signatures_dir = Path(config.rules.custom_signatures_path)
        signatures_dir.mkdir(parents=True, exist_ok=True)

        # Validate rule file path to prevent path traversal
        rule_path = validate_path(Path(rule_file))
        dest_path = signatures_dir / rule_path.name

        shutil.copy2(rule_path, dest_path)

        console.print(f"[bold green][OK][/bold green] Rule added: {dest_path.name}")
        console.print("\n[yellow]Note:[/yellow] Restart monitors for changes to take effect")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


@rules.command()
@click.argument("rule_name")
def remove(rule_name: str):
    """Remove a custom rule."""
    try:
        config = get_config()

        console.print(f"\n[bold cyan]Removing Custom Rule[/bold cyan]")
        console.print(f"Rule: [yellow]{rule_name}[/yellow]\n")

        # Remove rule file
        signatures_dir = Path(config.rules.custom_signatures_path)
        rule_path = signatures_dir / rule_name

        # Validate rule path to prevent path traversal
        rule_path = validate_path(rule_path, base_path=signatures_dir)

        if not rule_path.exists():
            console.print(f"[bold red]ERROR:[/bold red] Rule not found: {rule_name}")
            return

        rule_path.unlink()

        console.print(f"[bold green][OK][/bold green] Rule removed: {rule_name}")
        console.print("\n[yellow]Note:[/yellow] Restart monitors for changes to take effect")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


@cli.group("threat-intel")
def threat_intel():
    """Check threat intelligence."""
    pass


@threat_intel.command()
@click.argument("resource_type", type=click.Choice(["ip", "file", "package"]))
@click.argument("resource_value")
def check(resource_type: str, resource_value: str):
    """Check IP, file hash, or package reputation.

    Examples:
        hifzdefend threat-intel check ip 1.2.3.4
        hifzdefend threat-intel check file <sha256>
        hifzdefend threat-intel check package lodash@4.17.21
    """
    import asyncio

    try:
        # Validate resource value before processing
        is_valid, error_msg = validate_resource_value(resource_type, resource_value)
        if not is_valid:
            console.print(f"[bold red]ERROR:[/bold red] {error_msg}")
            console.print("\n[yellow]Examples:[/yellow]")
            if resource_type == "ip":
                console.print("  hifzdefend threat-intel check ip 1.2.3.4")
            elif resource_type == "file":
                console.print("  hifzdefend threat-intel check file a1b2c3d4...")
            elif resource_type == "package":
                console.print("  hifzdefend threat-intel check package lodash@4.17.21")
            return

        config = get_config()

        console.print(f"\n[bold cyan]Threat Intelligence Check[/bold cyan]")
        console.print(f"Type: [yellow]{resource_type}[/yellow]")
        console.print(f"Value: [yellow]{resource_value}[/yellow]\n")

        # Create threat intel manager
        manager = ThreatIntelligenceManager(config.threat_intel)

        # Perform check based on type
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Checking...", total=None)

            if resource_type == "ip":
                result = asyncio.run(manager.check_ip_reputation(resource_value))
            elif resource_type == "file":
                result = asyncio.run(manager.check_file_reputation(resource_value))
            elif resource_type == "package":
                # Parse package format (name@version or name==version)
                if "@" in resource_value:
                    name, version = resource_value.split("@", 1)
                    ecosystem = "npm"
                elif "==" in resource_value:
                    name, version = resource_value.split("==", 1)
                    ecosystem = "pypi"
                else:
                    console.print("[bold red]ERROR:[/bold red] Invalid package format")
                    console.print("Use: name@version (npm) or name==version (pypi)")
                    return

                result = asyncio.run(manager.check_package_security(name, version, ecosystem))

            progress.update(task, completed=True)

        # Display results
        console.print("\n[bold]Results:[/bold]")
        console.print(f"Source: {result.source}")
        console.print(f"Threat Level: {result.threat_level.value}")
        console.print(f"Threat Score: {result.threat_score}/100")

        if result.cached:
            console.print("Cached: Yes")

        if result.error:
            console.print(f"\n[bold red]Error:[/bold red] {result.error}")
        else:
            console.print("\n[bold]Details:[/bold]")
            for key, value in result.details.items():
                console.print(f"  {key}: {value}")

        # Close manager
        asyncio.run(manager.close())

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        logging.exception("Threat intel check command failed")


@cli.group()
def whitelist():
    """Manage application whitelist."""
    pass


@whitelist.command()
@click.argument("app_path", type=click.Path(exists=True))
def add(app_path: str):
    """Add application to whitelist."""
    try:
        config = get_config()

        # Validate app path to prevent path traversal
        app_path_validated = validate_path(Path(app_path))

        console.print(f"\n[bold cyan]Adding to Whitelist[/bold cyan]")
        console.print(f"Application: [yellow]{app_path_validated}[/yellow]\n")

        # Note: This requires implementing whitelist persistence
        console.print("[yellow]Note:[/yellow] Configuration persistence not yet implemented")
        console.print("To whitelist, add to your configuration file:")
        console.print(f"  [rules.app_whitelist]")
        console.print(f"  whitelisted_apps = [")
        console.print(f'    "{app_path}",')
        console.print(f"  ]")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


@whitelist.command()
@click.argument("app_path")
def remove(app_path: str):
    """Remove application from whitelist."""
    try:
        config = get_config()

        console.print(f"\n[bold cyan]Removing from Whitelist[/bold cyan]")
        console.print(f"Application: [yellow]{app_path}[/yellow]\n")

        # Note: This requires implementing whitelist persistence
        console.print("[yellow]Note:[/yellow] Configuration persistence not yet implemented")
        console.print("To remove, edit your configuration file:")
        console.print(f"  [rules.app_whitelist]")
        console.print(f"  Remove the entry for: {app_path}")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


# ============================================================================
# AI Commands (Phase 2)
# ============================================================================


@cli.command()
@click.argument("question")
@click.option("--interactive", "-i", is_flag=True, help="Start interactive query mode")
def query(question: str, interactive: bool):
    """
    Query security logs using natural language.

    Examples:
      hifzdefend query "what threats were detected today?"
      hifzdefend query "show me all PowerShell alerts"
      hifzdefend query --interactive
    """
    if not AI_AVAILABLE:
        print_ai_not_available_error()
        return

    try:
        config = get_config()

        # Check if AI is enabled
        if not config.ai.enabled or not config.ai.natural_language.enabled:
            console.print("[bold red]ERROR:[/bold red] Natural language queries are disabled in configuration")
            console.print("\n[yellow]To enable queries:[/yellow]")
            console.print("  Edit config file and set:")
            console.print("  [ai.natural_language] enabled = true")
            console.print("\n[cyan]Config location:[/cyan] %LOCALAPPDATA%\\HifzDefend\\hifzdefend.toml")
            return

        # Check Claude API key
        api_key = config.ai.claude.get_api_key()
        if not api_key:
            console.print("[bold red]ERROR:[/bold red] Claude API key not set")
            console.print("Set environment variable: CLAUDE_API_KEY=sk-ant-api03-...")
            console.print("Or configure in: [ai.claude] api_key = \"your-key\"")
            return

        console.print("\n[bold cyan]HifzDefend Natural Language Query[/bold cyan]\n")

        # Initialize Claude analyzer
        claude = ClaudeAnalyzer(
            api_key=api_key,
            model=config.ai.claude.model,
            max_tokens=config.ai.claude.max_tokens,
            temperature=config.ai.claude.temperature,
            timeout=config.ai.claude.timeout,
            cache_enabled=config.ai.claude.cache_responses,
            cache_dir=config.ai.claude.cache_path_expanded,
            cache_ttl=config.ai.claude.cache_ttl,
            max_requests_per_hour=config.ai.claude.max_requests_per_hour,
            log_costs=config.ai.claude.log_api_costs,
            fallback_on_error=config.ai.claude.fallback_on_error,
            retry_attempts=config.ai.claude.retry_attempts,
            retry_delay=config.ai.claude.retry_delay,
        )

        # Initialize NL interface
        nl_interface = NaturalLanguageInterface(
            vector_db_path=config.ai.natural_language.vector_db_path_expanded,
            claude_analyzer=claude,
            embedding_model=config.ai.natural_language.embedding_model,
            collection_name=config.ai.natural_language.chromadb.collection_name,
            max_context_results=config.ai.natural_language.max_context_results,
        )

        if interactive:
            # Start interactive mode
            nl_interface.interactive_query()
        else:
            # Single query
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Searching logs...", total=None)
                result = nl_interface.query(question)
                progress.update(task, completed=True)

            # Display result
            console.print(f"\n[bold]Q:[/bold] {question}")
            console.print(f"\n[bold green]A:[/bold green] {result['answer']}\n")

            if result['num_results'] > 0:
                console.print(f"[dim]Found {result['num_results']} relevant log entries[/dim]")

                # Show cost stats
                if config.ai.claude.log_api_costs:
                    stats = claude.get_cost_stats()
                    console.print(
                        f"[dim]Cost: ${stats['total_cost_usd']:.4f} "
                        f"({stats['input_tokens']} in, {stats['output_tokens']} out)[/dim]"
                    )

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        print_api_error_with_hints(e, "Natural language query failed")
        logging.exception("Query command failed")


@cli.command()
@click.argument("script_path", type=click.Path(exists=True))
@click.option("--type", "-t", default="auto", help="Script type (auto, powershell, batch, python)")
@click.option("--save", "-s", is_flag=True, help="Save analysis report")
def analyze_script(script_path: str, type: str, save: bool):
    """
    Analyze a script for security threats using Claude AI.

    Examples:
      hifzdefend analyze-script suspicious.ps1
      hifzdefend analyze-script malware.bat --type batch
      hifzdefend analyze-script script.py --save
    """
    if not AI_AVAILABLE:
        print_ai_not_available_error()
        return

    try:
        config = get_config()

        # Check if AI is enabled
        if not config.ai.enabled or not config.ai.claude.enabled:
            console.print("[bold red]ERROR:[/bold red] Claude AI is disabled in configuration")
            console.print("\n[yellow]To enable AI features:[/yellow]")
            console.print("  1. Edit your config file:")
            console.print("     %LOCALAPPDATA%\\HifzDefend\\hifzdefend.toml")
            console.print("  2. Or edit: config/hifzdefend.defaults.toml")
            console.print("  3. Set: [ai.claude] enabled = true")
            console.print("\n[cyan]Need help?[/cyan] See docs/AI_USAGE.md")
            return

        if not config.ai.claude.script_analysis:
            console.print("[bold red]ERROR:[/bold red] Script analysis is disabled in configuration")
            console.print("\n[yellow]To enable script analysis:[/yellow]")
            console.print("  Edit config file and set:")
            console.print("  [ai.claude] script_analysis = true")
            console.print("\n[cyan]Config location:[/cyan] %LOCALAPPDATA%\\HifzDefend\\hifzdefend.toml")
            return

        # Check API key
        api_key = config.ai.claude.get_api_key()
        if not api_key:
            print_api_key_not_set_error()
            return

        # Validate API key format
        is_valid, error_msg = validate_api_key(api_key)
        if not is_valid:
            print_api_key_invalid_error(error_msg)
            return

        console.print(f"\n[bold cyan]Claude Script Analyzer[/bold cyan]")
        console.print(f"Analyzing: [yellow]{script_path}[/yellow]\n")

        # Initialize Claude analyzer
        claude = ClaudeAnalyzer(
            api_key=api_key,
            model=config.ai.claude.model,
            max_tokens=config.ai.claude.max_tokens,
            temperature=config.ai.claude.temperature,
            timeout=config.ai.claude.timeout,
            cache_enabled=config.ai.claude.cache_responses,
            cache_dir=config.ai.claude.cache_path_expanded,
            cache_ttl=config.ai.claude.cache_ttl,
            max_requests_per_hour=config.ai.claude.max_requests_per_hour,
            log_costs=config.ai.claude.log_api_costs,
            fallback_on_error=config.ai.claude.fallback_on_error,
            retry_attempts=config.ai.claude.retry_attempts,
            retry_delay=config.ai.claude.retry_delay,
        )

        # Analyze script
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Analyzing script with Claude...", total=None)
            result = claude.analyze_script(Path(script_path), script_type=type)
            progress.update(task, completed=True)

        # Display results
        console.print("\n[bold]Analysis Results:[/bold]\n")

        # Threat level with color
        threat_colors = {
            "safe": "green",
            "suspicious": "yellow",
            "malicious": "red",
            "critical": "bold red",
            "unknown": "dim",
        }
        color = threat_colors.get(result.threat_level, "white")
        console.print(f"Threat Level: [{color}]{result.threat_level.upper()}[/{color}]")
        console.print(f"Confidence: {result.confidence * 100:.1f}%\n")

        console.print(f"[bold]Summary:[/bold]")
        console.print(f"{result.summary}\n")

        if result.indicators:
            console.print(f"[bold]Threat Indicators:[/bold]")
            for indicator in result.indicators:
                console.print(f"  • {indicator}")
            console.print()

        if result.recommendations:
            console.print(f"[bold]Recommendations:[/bold]")
            for i, rec in enumerate(result.recommendations, 1):
                console.print(f"  {i}. {rec}")
            console.print()

        # Show details
        if result.details:
            console.print(f"[bold]Technical Details:[/bold]")
            for key, value in result.details.items():
                if isinstance(value, list) and value:
                    console.print(f"  {key}: {', '.join(map(str, value))}")
                elif value and not isinstance(value, list):
                    console.print(f"  {key}: {value}")

        # Show cost stats
        if config.ai.claude.log_api_costs:
            stats = claude.get_cost_stats()
            console.print(
                f"\n[dim]API Cost: ${stats['total_cost_usd']:.4f} "
                f"({stats['input_tokens']} in, {stats['output_tokens']} out)[/dim]"
            )

        # Save report if requested
        if save:
            report_path = (
                config.reporting.report_dir_path
                / f"script_analysis_{Path(script_path).stem}_{result.threat_level}.json"
            )
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w") as f:
                json.dump(result.model_dump(), f, indent=2)
            console.print(f"\nReport saved: [cyan]{report_path}[/cyan]")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        print_api_error_with_hints(e, "Script analysis failed")
        logging.exception("Analyze-script command failed")


@cli.command()
@click.argument("threat_id")
def explain(threat_id: str):
    """
    Explain a threat in plain language using Claude AI.

    Examples:
      hifzdefend explain THR-001
      hifzdefend explain "Trojan.Win32.Generic"
    """
    if not AI_AVAILABLE:
        print_ai_not_available_error()
        return

    try:
        config = get_config()

        # Check if AI is enabled
        if not config.ai.enabled or not config.ai.claude.enabled:
            console.print("[bold red]ERROR:[/bold red] Claude AI is disabled in configuration")
            console.print("\n[yellow]To enable AI features:[/yellow]")
            console.print("  1. Edit your config file:")
            console.print("     %LOCALAPPDATA%\\HifzDefend\\hifzdefend.toml")
            console.print("  2. Or edit: config/hifzdefend.defaults.toml")
            console.print("  3. Set: [ai.claude] enabled = true")
            console.print("\n[cyan]Need help?[/cyan] See docs/AI_USAGE.md")
            return

        if not config.ai.claude.plain_language_explanations:
            console.print("[bold red]ERROR:[/bold red] Plain language explanations are disabled in configuration")
            console.print("\n[yellow]To enable explanations:[/yellow]")
            console.print("  Edit config file and set:")
            console.print("  [ai.claude] plain_language_explanations = true")
            console.print("\n[cyan]Config location:[/cyan] %LOCALAPPDATA%\\HifzDefend\\hifzdefend.toml")
            return

        # Check API key
        api_key = config.ai.claude.get_api_key()
        if not api_key:
            print_api_key_not_set_error()
            return

        # Validate API key format
        is_valid, error_msg = validate_api_key(api_key)
        if not is_valid:
            print_api_key_invalid_error(error_msg)
            return

        console.print(f"\n[bold cyan]Threat Explanation[/bold cyan]")
        console.print(f"Threat ID: [yellow]{threat_id}[/yellow]\n")

        # Initialize Claude analyzer
        claude = ClaudeAnalyzer(
            api_key=api_key,
            model=config.ai.claude.model,
            max_tokens=config.ai.claude.max_tokens,
            temperature=config.ai.claude.temperature,
            timeout=config.ai.claude.timeout,
            cache_enabled=config.ai.claude.cache_responses,
            cache_dir=config.ai.claude.cache_path_expanded,
            cache_ttl=config.ai.claude.cache_ttl,
            max_requests_per_hour=config.ai.claude.max_requests_per_hour,
            log_costs=config.ai.claude.log_api_costs,
            fallback_on_error=config.ai.claude.fallback_on_error,
            retry_attempts=config.ai.claude.retry_attempts,
            retry_delay=config.ai.claude.retry_delay,
        )

        # TODO: Load actual threat data from quarantine/logs
        # For now, use threat_id as the data
        threat_data = {"threat_id": threat_id, "description": "Threat details pending implementation"}

        # Get explanation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Generating explanation...", total=None)
            explanation = claude.explain_threat(threat_id, threat_data)
            progress.update(task, completed=True)

        # Display explanation
        console.print(f"\n{explanation}\n")

        # Show cost stats
        if config.ai.claude.log_api_costs:
            stats = claude.get_cost_stats()
            console.print(
                f"[dim]API Cost: ${stats['total_cost_usd']:.4f} "
                f"({stats['input_tokens']} in, {stats['output_tokens']} out)[/dim]"
            )

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        print_api_error_with_hints(e, "Threat explanation failed")
        logging.exception("Explain command failed")


@cli.group()
def ai():
    """Manage AI features and costs."""
    pass


@ai.command()
def stats():
    """Display AI usage statistics."""
    if not AI_AVAILABLE:
        print_ai_not_available_error()
        return

    try:
        config = get_config()

        # Check if AI is enabled
        if not config.ai.enabled or not config.ai.claude.enabled:
            console.print("[bold red]ERROR:[/bold red] Claude AI is disabled in configuration")
            console.print("\n[yellow]To enable AI features:[/yellow]")
            console.print("  1. Edit your config file:")
            console.print("     %LOCALAPPDATA%\\HifzDefend\\hifzdefend.toml")
            console.print("  2. Or edit: config/hifzdefend.defaults.toml")
            console.print("  3. Set: [ai.claude] enabled = true")
            console.print("\n[cyan]Need help?[/cyan] See docs/AI_USAGE.md")
            return

        # Check API key
        api_key = config.ai.claude.get_api_key()
        if not api_key:
            print_api_key_not_set_error()
            return

        # Validate API key format
        is_valid, error_msg = validate_api_key(api_key)
        if not is_valid:
            print_api_key_invalid_error(error_msg)
            return

        console.print("\n[bold cyan]AI Usage Statistics[/bold cyan]\n")

        # Initialize Claude analyzer
        claude = ClaudeAnalyzer(
            api_key=api_key,
            model=config.ai.claude.model,
            max_tokens=config.ai.claude.max_tokens,
            temperature=config.ai.claude.temperature,
            timeout=config.ai.claude.timeout,
            cache_enabled=config.ai.claude.cache_responses,
            cache_dir=config.ai.claude.cache_path_expanded,
            cache_ttl=config.ai.claude.cache_ttl,
            max_requests_per_hour=config.ai.claude.max_requests_per_hour,
            log_costs=config.ai.claude.log_api_costs,
            fallback_on_error=config.ai.claude.fallback_on_error,
            retry_attempts=config.ai.claude.retry_attempts,
            retry_delay=config.ai.claude.retry_delay,
        )

        # Get cost stats
        stats = claude.get_cost_stats()

        # Display statistics
        console.print("[bold]API Usage:[/bold]")
        console.print(f"  Model: {config.ai.claude.model}")
        console.print(f"  Total requests: {stats.get('total_requests', 0)}")
        console.print(f"  Successful requests: {stats.get('successful_requests', 0)}")
        console.print(f"  Failed requests: {stats.get('failed_requests', 0)}")
        console.print(f"  Cached responses: {stats.get('cached_responses', 0)}")

        console.print("\n[bold]Token Usage:[/bold]")
        console.print(f"  Input tokens: {stats.get('input_tokens', 0):,}")
        console.print(f"  Output tokens: {stats.get('output_tokens', 0):,}")
        console.print(f"  Total tokens: {stats.get('input_tokens', 0) + stats.get('output_tokens', 0):,}")

        console.print("\n[bold]Cost Information:[/bold]")
        console.print(f"  Input cost: ${stats.get('input_cost_usd', 0):.4f}")
        console.print(f"  Output cost: ${stats.get('output_cost_usd', 0):.4f}")
        console.print(f"  Total cost: ${stats.get('total_cost_usd', 0):.4f}")

        console.print("\n[bold]Rate Limiting:[/bold]")
        console.print(f"  Max requests/hour: {config.ai.claude.max_requests_per_hour}")
        console.print(f"  Requests this hour: {stats.get('requests_this_hour', 0)}")
        remaining = max(0, config.ai.claude.max_requests_per_hour - stats.get('requests_this_hour', 0))
        console.print(f"  Remaining this hour: {remaining}")

        console.print("\n[bold]Cache Status:[/bold]")
        console.print(f"  Caching enabled: {'Yes' if config.ai.claude.cache_responses else 'No'}")
        console.print(f"  Cache TTL: {config.ai.claude.cache_ttl / 3600:.1f} hours")
        console.print(f"  Cache directory: {config.ai.claude.cache_path_expanded}")

        # Check cache size
        cache_dir = Path(config.ai.claude.cache_path_expanded)
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*"))
            total_size = sum(f.stat().st_size for f in cache_files if f.is_file())
            console.print(f"  Cached entries: {len(cache_files)}")
            console.print(f"  Cache size: {total_size / 1024 / 1024:.2f} MB")

        # Cost projection
        if stats.get('total_requests', 0) > 0:
            avg_cost_per_request = stats.get('total_cost_usd', 0) / stats.get('total_requests', 0)
            console.print("\n[bold]Projections:[/bold]")
            console.print(f"  Average cost/request: ${avg_cost_per_request:.4f}")
            console.print(f"  Est. cost for 100 requests: ${avg_cost_per_request * 100:.2f}")
            console.print(f"  Est. monthly cost (1000 req): ${avg_cost_per_request * 1000:.2f}")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        print_api_error_with_hints(e, "Failed to retrieve AI statistics")
        logging.exception("AI stats command failed")


@ai.command()
def cost():
    """Display detailed cost breakdown."""
    if not AI_AVAILABLE:
        print_ai_not_available_error()
        return

    try:
        config = get_config()

        # Check if AI is enabled
        if not config.ai.enabled or not config.ai.claude.enabled:
            console.print("[bold red]ERROR:[/bold red] Claude AI is disabled")
            return

        # Check API key
        api_key = config.ai.claude.get_api_key()
        if not api_key:
            console.print("[bold red]ERROR:[/bold red] Claude API key not set")
            return

        console.print("\n[bold cyan]AI Cost Breakdown[/bold cyan]\n")

        # Initialize Claude analyzer
        claude = ClaudeAnalyzer(
            api_key=api_key,
            model=config.ai.claude.model,
            max_tokens=config.ai.claude.max_tokens,
            temperature=config.ai.claude.temperature,
            timeout=config.ai.claude.timeout,
            cache_enabled=config.ai.claude.cache_responses,
            cache_dir=config.ai.claude.cache_path_expanded,
            cache_ttl=config.ai.claude.cache_ttl,
            max_requests_per_hour=config.ai.claude.max_requests_per_hour,
            log_costs=config.ai.claude.log_api_costs,
            fallback_on_error=config.ai.claude.fallback_on_error,
            retry_attempts=config.ai.claude.retry_attempts,
            retry_delay=config.ai.claude.retry_delay,
        )

        # Get cost stats
        stats = claude.get_cost_stats()

        # Create cost table
        table = Table(title="Cost Analysis")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow", justify="right")
        table.add_column("Cost (USD)", style="green", justify="right")

        # Model pricing (approximate - update based on actual pricing)
        if "sonnet" in config.ai.claude.model.lower():
            input_price_per_mtok = 3.00
            output_price_per_mtok = 15.00
        elif "opus" in config.ai.claude.model.lower():
            input_price_per_mtok = 15.00
            output_price_per_mtok = 75.00
        elif "haiku" in config.ai.claude.model.lower():
            input_price_per_mtok = 0.25
            output_price_per_mtok = 1.25
        else:
            input_price_per_mtok = 3.00
            output_price_per_mtok = 15.00

        # Add rows
        input_tokens = stats.get('input_tokens', 0)
        output_tokens = stats.get('output_tokens', 0)
        input_cost = (input_tokens / 1_000_000) * input_price_per_mtok
        output_cost = (output_tokens / 1_000_000) * output_price_per_mtok
        total_cost = input_cost + output_cost

        table.add_row(
            "Input Tokens",
            f"{input_tokens:,}",
            f"${input_cost:.4f}"
        )
        table.add_row(
            "Output Tokens",
            f"{output_tokens:,}",
            f"${output_cost:.4f}"
        )
        table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{input_tokens + output_tokens:,}[/bold]",
            f"[bold]${total_cost:.4f}[/bold]"
        )

        console.print(table)

        # Pricing info
        console.print(f"\n[bold]Pricing (per 1M tokens):[/bold]")
        console.print(f"  Model: {config.ai.claude.model}")
        console.print(f"  Input: ${input_price_per_mtok:.2f}")
        console.print(f"  Output: ${output_price_per_mtok:.2f}")

        # Usage breakdown
        console.print(f"\n[bold]Request Breakdown:[/bold]")
        console.print(f"  Total requests: {stats.get('total_requests', 0)}")
        console.print(f"  Successful: {stats.get('successful_requests', 0)}")
        console.print(f"  Failed: {stats.get('failed_requests', 0)}")
        console.print(f"  From cache: {stats.get('cached_responses', 0)}")

        # Cost savings from cache
        cached = stats.get('cached_responses', 0)
        if cached > 0 and stats.get('total_requests', 0) > 0:
            avg_cost = total_cost / max(1, stats.get('successful_requests', 0) - cached)
            estimated_savings = avg_cost * cached
            console.print(f"\n[bold green]Cache Savings:[/bold green]")
            console.print(f"  Estimated savings: ${estimated_savings:.4f}")
            console.print(f"  Cached responses: {cached}")

        # Budget recommendations
        console.print(f"\n[bold]Budget Recommendations:[/bold]")
        if total_cost < 1.00:
            console.print("  [green]Low usage - well within budget[/green]")
        elif total_cost < 5.00:
            console.print("  [yellow]Moderate usage - monitor costs[/yellow]")
        else:
            console.print("  [red]High usage - consider optimization[/red]")

        # Optimization tips
        if stats.get('cached_responses', 0) == 0 and stats.get('total_requests', 0) > 5:
            console.print("\n[yellow]Tip:[/yellow] Enable caching to reduce costs")
        if "opus" in config.ai.claude.model.lower() and stats.get('total_requests', 0) > 20:
            console.print("\n[yellow]Tip:[/yellow] Consider using Claude Sonnet or Haiku for lower costs")

        # View detailed costs
        console.print("\n[dim]For real-time costs, visit: https://console.anthropic.com/settings/costs[/dim]")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        print_api_error_with_hints(e, "Failed to retrieve cost information")
        logging.exception("AI cost command failed")


@ai.command("reset-cache")
def reset_cache():
    """Clear the AI response cache."""
    if not AI_AVAILABLE:
        console.print("[bold red]ERROR:[/bold red] AI features not available")
        return

    try:
        config = get_config()

        console.print("\n[bold cyan]Clear AI Cache[/bold cyan]\n")

        cache_dir = Path(config.ai.claude.cache_path_expanded)

        if not cache_dir.exists():
            console.print("[yellow]No cache directory found[/yellow]")
            return

        # Count cache files
        cache_files = list(cache_dir.glob("*"))
        total_size = sum(f.stat().st_size for f in cache_files if f.is_file())

        console.print(f"Cache directory: {cache_dir}")
        console.print(f"Cached entries: {len(cache_files)}")
        console.print(f"Cache size: {total_size / 1024 / 1024:.2f} MB\n")

        # Confirm deletion
        response = click.confirm("Are you sure you want to clear the cache?", default=False)

        if not response:
            console.print("[yellow]Cache clearing cancelled[/yellow]")
            return

        # Delete cache files
        deleted = 0
        for cache_file in cache_files:
            try:
                if cache_file.is_file():
                    cache_file.unlink()
                    deleted += 1
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Could not delete {cache_file.name}: {e}")

        console.print(f"\n[bold green][OK][/bold green] Cleared {deleted} cache entries")
        console.print("[dim]Note: Cost statistics are stored separately and not affected[/dim]")

        # Check vector DB cache
        if CHROMADB_AVAILABLE:
            vector_db_path = Path(config.ai.natural_language.vector_db_path_expanded)
            if vector_db_path.exists():
                console.print(f"\n[yellow]Note:[/yellow] Vector database not cleared: {vector_db_path}")
                console.print("To clear vector DB, delete the directory manually:")
                console.print(f"  Remove-Item -Recurse '{vector_db_path}'")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        logging.exception("Reset cache command failed")


@ai.command()
def test():
    """Test Claude API connection."""
    if not AI_AVAILABLE:
        print_ai_not_available_error()
        return

    try:
        config = get_config()

        console.print("\n[bold cyan]Testing Claude API Connection[/bold cyan]\n")

        # Check if AI is enabled
        if not config.ai.enabled or not config.ai.claude.enabled:
            console.print("[bold red]ERROR:[/bold red] Claude AI is disabled in configuration")
            console.print("\n[yellow]To enable AI features:[/yellow]")
            console.print("  1. Edit your config file:")
            console.print("     %LOCALAPPDATA%\\HifzDefend\\hifzdefend.toml")
            console.print("  2. Or edit: config/hifzdefend.defaults.toml")
            console.print("  3. Set: [ai.claude] enabled = true")
            console.print("\n[cyan]Need help?[/cyan] See docs/AI_USAGE.md")
            return

        # Check API key
        api_key = config.ai.claude.get_api_key()
        if not api_key:
            console.print("[bold red]ERROR:[/bold red] Claude API key not set")
            console.print("\nTo set your API key:")
            console.print("  1. Get key from: https://console.anthropic.com/settings/keys")
            console.print("  2. Set environment variable:")
            console.print("     $env:CLAUDE_API_KEY = 'sk-ant-api03-...'")
            console.print("  3. Or add to .env file")
            return

        console.print("[bold]Configuration:[/bold]")
        console.print(f"  API key: {api_key[:12]}...{api_key[-4:]}")
        console.print(f"  Model: {config.ai.claude.model}")
        console.print(f"  Max tokens: {config.ai.claude.max_tokens}")
        console.print(f"  Timeout: {config.ai.claude.timeout}s")
        console.print(f"  Caching: {'Enabled' if config.ai.claude.cache_responses else 'Disabled'}")

        # Test connection
        console.print("\n[bold]Testing connection...[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Sending test request to Claude...", total=None)

            # Initialize Claude analyzer
            claude = ClaudeAnalyzer(
                api_key=api_key,
                model=config.ai.claude.model,
                max_tokens=config.ai.claude.max_tokens,
                temperature=config.ai.claude.temperature,
                timeout=config.ai.claude.timeout,
                cache_enabled=False,  # Don't cache test requests
                cache_dir=config.ai.claude.cache_path_expanded,
                cache_ttl=config.ai.claude.cache_ttl,
                max_requests_per_hour=config.ai.claude.max_requests_per_hour,
                log_costs=config.ai.claude.log_api_costs,
                fallback_on_error=config.ai.claude.fallback_on_error,
                retry_attempts=config.ai.claude.retry_attempts,
                retry_delay=config.ai.claude.retry_delay,
            )

            # Send test request
            test_prompt = "Reply with 'OK' if you receive this message."
            try:
                response = claude.client.messages.create(
                    model=claude.model,
                    max_tokens=50,
                    temperature=0,
                    messages=[{"role": "user", "content": test_prompt}]
                )

                progress.update(task, completed=True)

                console.print("\n[bold green][OK][/bold green] Connection successful!")
                console.print(f"\n[bold]Response:[/bold]")
                console.print(f"  {response.content[0].text}")

                console.print(f"\n[bold]Usage:[/bold]")
                console.print(f"  Input tokens: {response.usage.input_tokens}")
                console.print(f"  Output tokens: {response.usage.output_tokens}")

                # Calculate cost
                if "sonnet" in config.ai.claude.model.lower():
                    input_price_per_mtok = 3.00
                    output_price_per_mtok = 15.00
                elif "opus" in config.ai.claude.model.lower():
                    input_price_per_mtok = 15.00
                    output_price_per_mtok = 75.00
                elif "haiku" in config.ai.claude.model.lower():
                    input_price_per_mtok = 0.25
                    output_price_per_mtok = 1.25
                else:
                    input_price_per_mtok = 3.00
                    output_price_per_mtok = 15.00

                test_cost = (
                    (response.usage.input_tokens / 1_000_000) * input_price_per_mtok +
                    (response.usage.output_tokens / 1_000_000) * output_price_per_mtok
                )
                console.print(f"  Test cost: ${test_cost:.6f}")

                console.print("\n[bold green]All systems operational![/bold green]")
                console.print("\nYou can now use:")
                console.print("  • hifzdefend analyze-script <file>")
                console.print("  • hifzdefend query \"<question>\"")
                console.print("  • hifzdefend explain \"<threat>\"")

            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"\n[bold red][FAIL][/bold red] Connection failed")
                console.print(f"\n[bold]Error:[/bold] {str(e)}")

                # Provide troubleshooting hints
                if "authentication" in str(e).lower() or "api key" in str(e).lower():
                    console.print("\n[yellow]Troubleshooting:[/yellow]")
                    console.print("  • Check your API key is correct")
                    console.print("  • Verify key is active at: https://console.anthropic.com/settings/keys")
                    console.print("  • Try generating a new API key")
                elif "rate limit" in str(e).lower():
                    console.print("\n[yellow]Troubleshooting:[/yellow]")
                    console.print("  • You've hit the rate limit")
                    console.print("  • Wait a few minutes and try again")
                    console.print("  • Check usage at: https://console.anthropic.com/")
                elif "timeout" in str(e).lower():
                    console.print("\n[yellow]Troubleshooting:[/yellow]")
                    console.print("  • Check your internet connection")
                    console.print("  • Increase timeout in config")
                    console.print("  • Try again in a moment")
                else:
                    console.print("\n[yellow]Troubleshooting:[/yellow]")
                    console.print("  • Check internet connection")
                    console.print("  • Verify firewall settings")
                    console.print("  • See docs/TROUBLESHOOTING.md")

    except HifzDefendError as e:
        console.print(f"[bold red]ERROR:[/bold red] {e}")
    except Exception as e:
        print_api_error_with_hints(e, "API connection test failed")
        logging.exception("AI test command failed")


if __name__ == "__main__":
    cli()
