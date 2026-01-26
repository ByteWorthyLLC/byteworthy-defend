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


console = Console()


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
                    f"Ensure clamd is running on {config.clamav.host}:{config.clamav.port}"
                )
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
                console.print(f"\n[bold red]⚠ Threats found: {report.threats_count}[/bold red]")

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
                console.print("\n[bold green]✓ No threats detected[/bold green]")

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
                console.print("[bold green]✓[/bold green] ClamAV daemon: Running")

                # Get version
                version = engine.get_version()
                if version:
                    console.print(f"[bold]Version:[/bold] {version}")
            else:
                console.print("[bold red]✗[/bold red] ClamAV daemon: Not running")
                console.print(
                    f"  Expected at: {config.clamav.host}:{config.clamav.port}"
                )
                console.print("\n[yellow]Troubleshooting:[/yellow]")
                console.print("  1. Ensure clamd.exe is running")
                console.print("  2. Check configuration in clamd.conf")
                console.print("  3. Verify TCPSocket is enabled on port 3310")

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
            console.print("[bold green]✓[/bold green] Virus definitions updated successfully")
            if result.stdout:
                console.print(result.stdout)
        else:
            console.print("[bold red]✗[/bold red] Update failed")
            if result.stderr:
                console.print(result.stderr)

    except FileNotFoundError:
        console.print("[bold red]ERROR:[/bold red] freshclam not found")
        console.print("Ensure ClamAV is properly installed")
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
        config = get_config()

        console.print(f"\n[bold cyan]Quarantine File[/bold cyan]")
        console.print(f"File: [yellow]{file_path}[/yellow]")
        console.print(f"Threat: [red]{threat_name}[/red]\n")

        with ScanEngine(config) as engine:
            entry = engine.quarantine_file(file_path, threat_name)

            console.print("[bold green]✓[/bold green] File quarantined successfully")
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

        console.print("[bold green]✓[/bold green] All monitors started")

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

        console.print("[bold green]✓[/bold green] All monitors stopped")

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

        rule_path = Path(rule_file)
        dest_path = signatures_dir / rule_path.name

        shutil.copy2(rule_path, dest_path)

        console.print(f"[bold green]✓[/bold green] Rule added: {dest_path.name}")
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

        if not rule_path.exists():
            console.print(f"[bold red]ERROR:[/bold red] Rule not found: {rule_name}")
            return

        rule_path.unlink()

        console.print(f"[bold green]✓[/bold green] Rule removed: {rule_name}")
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

        console.print(f"\n[bold cyan]Adding to Whitelist[/bold cyan]")
        console.print(f"Application: [yellow]{app_path}[/yellow]\n")

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
        console.print("[bold red]ERROR:[/bold red] AI features not available")
        console.print("Install AI dependencies: pip install anthropic chromadb sentence-transformers")
        return

    try:
        config = get_config()

        # Check if AI is enabled
        if not config.ai.enabled or not config.ai.natural_language.enabled:
            console.print("[bold red]ERROR:[/bold red] Natural language queries are disabled")
            console.print("Enable in config: [ai.natural_language] enabled = true")
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
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
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
        console.print("[bold red]ERROR:[/bold red] AI features not available")
        console.print("Install AI dependencies: pip install anthropic chromadb sentence-transformers")
        return

    try:
        config = get_config()

        # Check if AI is enabled
        if not config.ai.enabled or not config.ai.claude.enabled:
            console.print("[bold red]ERROR:[/bold red] Claude AI is disabled")
            console.print("Enable in config: [ai.claude] enabled = true")
            return

        if not config.ai.claude.script_analysis:
            console.print("[bold red]ERROR:[/bold red] Script analysis is disabled")
            console.print("Enable in config: [ai.claude] script_analysis = true")
            return

        # Check API key
        api_key = config.ai.claude.get_api_key()
        if not api_key:
            console.print("[bold red]ERROR:[/bold red] Claude API key not set")
            console.print("Set environment variable: CLAUDE_API_KEY=sk-ant-api03-...")
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
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
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
        console.print("[bold red]ERROR:[/bold red] AI features not available")
        console.print("Install AI dependencies: pip install anthropic chromadb sentence-transformers")
        return

    try:
        config = get_config()

        # Check if AI is enabled
        if not config.ai.enabled or not config.ai.claude.enabled:
            console.print("[bold red]ERROR:[/bold red] Claude AI is disabled")
            console.print("Enable in config: [ai.claude] enabled = true")
            return

        if not config.ai.claude.plain_language_explanations:
            console.print("[bold red]ERROR:[/bold red] Plain language explanations are disabled")
            console.print("Enable in config: [ai.claude] plain_language_explanations = true")
            return

        # Check API key
        api_key = config.ai.claude.get_api_key()
        if not api_key:
            console.print("[bold red]ERROR:[/bold red] Claude API key not set")
            console.print("Set environment variable: CLAUDE_API_KEY=sk-ant-api03-...")
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
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        logging.exception("Explain command failed")


if __name__ == "__main__":
    cli()
