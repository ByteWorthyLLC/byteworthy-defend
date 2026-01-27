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
from ..reporting.formatter import save_report as save_scan_report
from ..reporting.logger import setup_logger
from ..utils.exceptions import HifzDefendError


console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="HifzDefend")
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


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to listen on")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def web(host: str, port: int, reload: bool):
    """Start HifzDefend web application."""
    import webbrowser
    import uvicorn
    from threading import Timer

    console.print("\n[bold cyan]HifzDefend Web Application[/bold cyan]\n")
    console.print(f"Starting web server on http://{host}:{port}")
    console.print("Press Ctrl+C to stop\n")

    # Open browser after 1 second
    def open_browser():
        webbrowser.open(f"http://localhost:{port}")

    Timer(1.0, open_browser).start()

    # Start server
    uvicorn.run(
        "hifzdefend.api.main:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    cli()
