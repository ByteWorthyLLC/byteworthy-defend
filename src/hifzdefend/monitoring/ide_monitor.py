"""IDE and Code Editor Security Monitor for HifzDefend.

Monitors IDE and code editor activity for security threats:
- Scans VS Code extension installations
- Checks extension permissions for suspicious activity
- Monitors Claude Code CLI activity for injections
- Tracks GitHub Desktop operations
- Detects malicious extensions
- Alerts on unauthorized repository clones
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..monitoring.base import BaseMonitor, MonitorConfig
from ..monitoring.events import Event, EventSeverity, EventType

logger = logging.getLogger(__name__)


class IDEMonitorConfig(MonitorConfig):
    """Configuration for IDE Security monitor."""

    vscode: bool = Field(default=True, description="Monitor VS Code extensions")
    claude_code_cli: bool = Field(default=True, description="Monitor Claude Code CLI")
    github_desktop: bool = Field(default=True, description="Monitor GitHub Desktop")
    check_extension_permissions: bool = Field(
        default=True, description="Check extension permissions"
    )
    alert_on_repo_clone: bool = Field(
        default=False, description="Alert on repository clones (can be noisy)"
    )
    whitelist_extensions: list[str] = Field(
        default_factory=lambda: [
            "ms-python.python",
            "ms-vscode.cpptools",
            "ms-vscode.powershell",
            "dbaeumer.vscode-eslint",
            "esbenp.prettier-vscode",
        ],
        description="Whitelisted extension IDs",
    )


class IDEMonitor(BaseMonitor):
    """Monitor IDE and code editor security.

    This monitor watches IDE and code editor activity for security issues including:
    - Malicious VS Code extensions
    - Suspicious extension permissions
    - Claude Code CLI injection attempts
    - GitHub Desktop credential theft
    - Unauthorized repository clones

    Example:
        ```python
        config = IDEMonitorConfig(enabled=True)
        monitor = IDEMonitor(config, event_bus)
        await monitor.start_monitoring()
        ```
    """

    # Suspicious extension permissions
    SUSPICIOUS_PERMISSIONS = [
        "all",
        "*",
        "clipboardRead",
        "clipboardWrite",
        "experimental",
        "geolocation",
        "nativeMessaging",
        "webRequest",
        "webRequestBlocking",
    ]

    # Known malicious extensions (examples - would be maintained database)
    MALICIOUS_EXTENSIONS = [
        "theme-darcula",  # Known malicious extension
        "prettier-code-formatter",  # Typosquat of prettier
        "python-2020",  # Suspicious Python extension
    ]

    # Suspicious Claude CLI patterns
    SUSPICIOUS_CLI_PATTERNS = [
        "eval(",
        "exec(",
        "subprocess.run",
        "os.system(",
        "__import__",
        "compile(",
    ]

    def __init__(self, config: IDEMonitorConfig, event_bus: Any) -> None:
        """Initialize the IDE monitor.

        Args:
            config: Monitor configuration
            event_bus: Event bus for publishing events
        """
        super().__init__(config, event_bus)
        self.config: IDEMonitorConfig = config

        # VS Code paths
        self.vscode_extensions_path = Path(
            os.path.expandvars(r"%USERPROFILE%\.vscode\extensions")
        )

        # Claude Code CLI paths
        self.claude_cli_path = Path(os.path.expandvars(r"%LOCALAPPDATA%\claude"))
        self.claude_logs_path = self.claude_cli_path / "logs"

        # GitHub Desktop paths
        self.github_desktop_path = Path(
            os.path.expandvars(r"%LOCALAPPDATA%\GitHub Desktop")
        )

        # Tracked extensions and logs
        self._monitored_extensions: set[str] = set()
        self._processed_log_entries: set[str] = set()

    async def start(self) -> None:
        """Start the IDE monitor."""
        self._running = True

        # Create baseline of existing extensions
        if self.config.vscode and self.vscode_extensions_path.exists():
            try:
                for ext_dir in self.vscode_extensions_path.iterdir():
                    if ext_dir.is_dir():
                        self._monitored_extensions.add(ext_dir.name)
                self._logger.info(
                    f"Baseline: {len(self._monitored_extensions)} VS Code extensions"
                )
            except Exception as e:
                self._logger.warning(f"Could not create extension baseline: {e}")

        self._logger.info("IDE monitor started")

    async def stop(self) -> None:
        """Stop the IDE monitor."""
        self._running = False
        self._logger.info("IDE monitor stopped")

    async def check(self) -> list[Event]:
        """Check IDE and editor activity for security issues.

        Returns:
            List of security events detected
        """
        events: list[Event] = []

        try:
            # Check VS Code extensions
            if self.config.vscode:
                vscode_events = await self._check_vscode_extensions()
                events.extend(vscode_events)

            # Check Claude Code CLI
            if self.config.claude_code_cli:
                claude_events = await self._check_claude_cli()
                events.extend(claude_events)

            # Check GitHub Desktop
            if self.config.github_desktop:
                github_events = await self._check_github_desktop()
                events.extend(github_events)

        except Exception as e:
            self._logger.error(f"Error checking IDE activity: {e}", exc_info=True)

        return events

    async def _check_vscode_extensions(self) -> list[Event]:
        """Check VS Code extensions for security issues.

        Returns:
            List of security events
        """
        events: list[Event] = []

        if not self.vscode_extensions_path.exists():
            return events

        try:
            for ext_dir in self.vscode_extensions_path.iterdir():
                if not ext_dir.is_dir():
                    continue

                ext_name = ext_dir.name

                # Skip if already monitored
                if ext_name in self._monitored_extensions:
                    continue

                self._monitored_extensions.add(ext_name)

                # Log extension installation
                events.append(
                    Event(
                        event_type=EventType.IDE_EXTENSION_INSTALLED,
                        severity=EventSeverity.INFO,
                        source_monitor=self.name,
                        threat_score=0,
                        description=f"VS Code extension installed: {ext_name}",
                        data={
                            "extension_name": ext_name,
                            "extension_path": str(ext_dir),
                        },
                    )
                )

                # Check extension manifest
                manifest_path = ext_dir / "package.json"
                if manifest_path.exists():
                    manifest_events = await self._check_extension_manifest(
                        ext_name, manifest_path
                    )
                    events.extend(manifest_events)

        except Exception as e:
            self._logger.error(f"Error checking VS Code extensions: {e}", exc_info=True)

        return events

    async def _check_extension_manifest(
        self, ext_name: str, manifest_path: Path
    ) -> list[Event]:
        """Check extension manifest for suspicious permissions.

        Args:
            ext_name: Extension name
            manifest_path: Path to package.json

        Returns:
            List of security events
        """
        events: list[Event] = []

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            # Get extension ID
            ext_id = f"{manifest.get('publisher', 'unknown')}.{manifest.get('name', 'unknown')}"

            # Check if whitelisted
            if ext_id in self.config.whitelist_extensions:
                return events

            # Check if known malicious
            if ext_id in self.MALICIOUS_EXTENSIONS or ext_name in self.MALICIOUS_EXTENSIONS:
                events.append(
                    Event(
                        event_type=EventType.MALICIOUS_EXTENSION_DETECTED,
                        severity=EventSeverity.CRITICAL,
                        source_monitor=self.name,
                        threat_score=95,
                        description=f"Known malicious VS Code extension: {ext_id}",
                        data={
                            "extension_id": ext_id,
                            "extension_name": ext_name,
                            "recommendation": "Uninstall immediately",
                        },
                    )
                )

            # Check permissions if enabled
            if self.config.check_extension_permissions:
                contributes = manifest.get("contributes", {})
                permissions = manifest.get("permissions", [])

                # Check for suspicious permissions
                suspicious_perms = []
                for perm in permissions:
                    if perm in self.SUSPICIOUS_PERMISSIONS:
                        suspicious_perms.append(perm)

                if suspicious_perms:
                    events.append(
                        Event(
                            event_type=EventType.SUSPICIOUS_ACTIVITY,
                            severity=EventSeverity.WARNING,
                            source_monitor=self.name,
                            threat_score=60,
                            description=f"VS Code extension has suspicious permissions: {ext_id}",
                            data={
                                "extension_id": ext_id,
                                "suspicious_permissions": suspicious_perms,
                                "recommendation": "Review extension carefully",
                            },
                        )
                    )

                # Check for command contributions
                commands = contributes.get("commands", [])
                if len(commands) > 20:  # Unusual number of commands
                    events.append(
                        Event(
                            event_type=EventType.SUSPICIOUS_ACTIVITY,
                            severity=EventSeverity.INFO,
                            source_monitor=self.name,
                            threat_score=30,
                            description=f"VS Code extension registers many commands: {ext_id}",
                            data={
                                "extension_id": ext_id,
                                "command_count": len(commands),
                            },
                        )
                    )

        except json.JSONDecodeError:
            self._logger.warning(f"Invalid package.json for extension: {ext_name}")
        except Exception as e:
            self._logger.error(
                f"Error checking extension manifest for {ext_name}: {e}", exc_info=True
            )

        return events

    async def _check_claude_cli(self) -> list[Event]:
        """Check Claude Code CLI for suspicious activity.

        Returns:
            List of security events
        """
        events: list[Event] = []

        if not self.claude_logs_path.exists():
            return events

        try:
            # Check recent log files
            log_files = sorted(
                self.claude_logs_path.glob("*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )[:5]  # Check 5 most recent

            for log_file in log_files:
                try:
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()

                    for line in lines:
                        # Create unique ID for this log entry
                        entry_id = f"{log_file.name}:{hash(line)}"

                        if entry_id in self._processed_log_entries:
                            continue

                        self._processed_log_entries.add(entry_id)

                        # Check for suspicious patterns
                        for pattern in self.SUSPICIOUS_CLI_PATTERNS:
                            if pattern in line:
                                events.append(
                                    Event(
                                        event_type=EventType.SUSPICIOUS_ACTIVITY,
                                        severity=EventSeverity.WARNING,
                                        source_monitor=self.name,
                                        threat_score=70,
                                        description=f"Suspicious pattern in Claude CLI logs: {pattern}",
                                        data={
                                            "log_file": log_file.name,
                                            "pattern": pattern,
                                            "line_preview": line[:100],
                                        },
                                    )
                                )

                except Exception as e:
                    self._logger.debug(f"Could not read log file {log_file}: {e}")

        except Exception as e:
            self._logger.error(f"Error checking Claude CLI logs: {e}", exc_info=True)

        return events

    async def _check_github_desktop(self) -> list[Event]:
        """Check GitHub Desktop for suspicious operations.

        Returns:
            List of security events
        """
        events: list[Event] = []

        if not self.github_desktop_path.exists():
            return events

        try:
            # Check for GitHub Desktop logs
            logs_path = self.github_desktop_path / "logs"
            if not logs_path.exists():
                return events

            # Get recent log files
            log_files = sorted(
                logs_path.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True
            )[:3]  # Check 3 most recent

            for log_file in log_files:
                try:
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Look for credential operations
                    if "credential" in content.lower() and "error" in content.lower():
                        events.append(
                            Event(
                                event_type=EventType.SUSPICIOUS_ACTIVITY,
                                severity=EventSeverity.WARNING,
                                source_monitor=self.name,
                                threat_score=50,
                                description="GitHub Desktop credential error detected",
                                data={
                                    "log_file": log_file.name,
                                    "recommendation": "Verify GitHub credentials",
                                },
                            )
                        )

                    # Look for clone operations if enabled
                    if self.config.alert_on_repo_clone and "git clone" in content.lower():
                        events.append(
                            Event(
                                event_type=EventType.SUSPICIOUS_ACTIVITY,
                                severity=EventSeverity.INFO,
                                source_monitor=self.name,
                                threat_score=10,
                                description="Repository clone operation detected",
                                data={"log_file": log_file.name},
                            )
                        )

                except Exception as e:
                    self._logger.debug(f"Could not read GitHub log {log_file}: {e}")

        except Exception as e:
            self._logger.error(
                f"Error checking GitHub Desktop activity: {e}", exc_info=True
            )

        return events
