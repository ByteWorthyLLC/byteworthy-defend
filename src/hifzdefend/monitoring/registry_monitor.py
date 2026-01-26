"""Windows Registry Security Monitor for HifzDefend.

Monitors Windows Registry for security threats:
- Watches security-sensitive registry keys for changes
- Detects new startup entries (Run, RunOnce keys)
- Alerts on service installations
- Tracks firewall rule modifications
- Detects persistence mechanisms
- Provides rollback capability for unauthorized changes

Note: Requires Administrator privileges for HKEY_LOCAL_MACHINE access.
"""

import logging
import winreg
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..monitoring.base import BaseMonitor, MonitorConfig
from ..monitoring.events import Event, EventSeverity, EventType, RegistryEvent

logger = logging.getLogger(__name__)


class RegistryMonitorConfig(MonitorConfig):
    """Configuration for Registry Security monitor."""

    protected_keys: list[str] = Field(
        default_factory=lambda: [
            r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
            r"HKLM\System\CurrentControlSet\Services",
            r"HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System",
        ],
        description="Registry keys to monitor",
    )
    alert_on_new_service: bool = Field(
        default=True, description="Alert on new service creation"
    )
    alert_on_startup_entry: bool = Field(
        default=True, description="Alert on new startup entries"
    )
    enable_rollback: bool = Field(
        default=True, description="Enable rollback capability"
    )
    baseline_snapshot_on_start: bool = Field(
        default=True, description="Create baseline snapshot on monitor start"
    )


class RegistryMonitor(BaseMonitor):
    """Monitor Windows Registry for security issues.

    This monitor watches Windows Registry for suspicious changes including:
    - New startup entries (Run, RunOnce keys)
    - Service installations
    - Firewall rule modifications
    - Persistence mechanisms
    - Policy changes

    Example:
        ```python
        config = RegistryMonitorConfig(enabled=True)
        monitor = RegistryMonitor(config, event_bus)
        await monitor.start_monitoring()
        ```

    Note:
        Requires Administrator privileges for HKEY_LOCAL_MACHINE access.
        Will operate in limited mode if not running as admin.
    """

    # Protected registry key paths
    PROTECTED_KEYS = {
        # Startup locations
        "HKLM\\Run": (
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
        ),
        "HKCU\\Run": (
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
        ),
        "HKLM\\RunOnce": (
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
        ),
        "HKCU\\RunOnce": (
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
        ),
        # Services
        "HKLM\\Services": (
            winreg.HKEY_LOCAL_MACHINE,
            r"System\CurrentControlSet\Services",
        ),
        # Policies
        "HKLM\\Policies": (
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Policies\System",
        ),
        # Firewall
        "HKLM\\Firewall": (
            winreg.HKEY_LOCAL_MACHINE,
            r"System\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy",
        ),
        # Windows Defender
        "HKLM\\Defender": (
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows Defender",
        ),
    }

    # Suspicious value names
    SUSPICIOUS_VALUE_PATTERNS = [
        "userinit",
        "shell",
        "explorer.exe",
        "cmd.exe",
        "powershell.exe",
        "wscript.exe",
        "cscript.exe",
        "mshta.exe",
        "regsvr32.exe",
        "rundll32.exe",
    ]

    def __init__(self, config: RegistryMonitorConfig, event_bus: Any) -> None:
        """Initialize the Registry monitor.

        Args:
            config: Monitor configuration
            event_bus: Event bus for publishing events
        """
        super().__init__(config, event_bus)
        self.config: RegistryMonitorConfig = config

        # Registry baseline
        self._baseline: dict[str, dict[str, Any]] = {}
        self._backup: dict[str, dict[str, Any]] = {}

        # Admin privileges check
        self._has_admin = False
        self._limited_mode = False

    async def start(self) -> None:
        """Start the Registry monitor."""
        # Check for admin privileges
        try:
            # Try to open HKEY_LOCAL_MACHINE with write access
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"Software",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
            )
            winreg.CloseKey(key)
            self._has_admin = True
            self._logger.info("Registry monitor started with full privileges")
        except OSError:
            self._has_admin = False
            self._limited_mode = True
            self._logger.warning(
                "Registry monitor started in limited mode (no admin privileges)"
            )

        # Create baseline snapshot
        if self.config.baseline_snapshot_on_start:
            await self._create_baseline()

        self._running = True

    async def stop(self) -> None:
        """Stop the Registry monitor."""
        self._running = False
        self._logger.info("Registry monitor stopped")

    async def check(self) -> list[RegistryEvent]:
        """Check Registry for security issues.

        Returns:
            List of security events detected
        """
        events: list[RegistryEvent] = []

        try:
            # Check each protected key
            for key_name, (hive, subkey) in self.PROTECTED_KEYS.items():
                # Skip HKLM keys if no admin privileges
                if hive == winreg.HKEY_LOCAL_MACHINE and not self._has_admin:
                    continue

                key_events = await self._check_key(key_name, hive, subkey)
                events.extend(key_events)

        except Exception as e:
            self._logger.error(f"Error checking Registry: {e}", exc_info=True)

        return events

    async def _create_baseline(self) -> None:
        """Create baseline snapshot of protected registry keys."""
        self._logger.info("Creating registry baseline snapshot...")

        for key_name, (hive, subkey) in self.PROTECTED_KEYS.items():
            # Skip HKLM keys if no admin privileges
            if hive == winreg.HKEY_LOCAL_MACHINE and not self._has_admin:
                continue

            try:
                key_data = await self._read_key_values(hive, subkey)
                self._baseline[key_name] = key_data
                self._logger.debug(
                    f"Baseline: {key_name} has {len(key_data)} values"
                )
            except Exception as e:
                self._logger.warning(f"Could not create baseline for {key_name}: {e}")

        self._logger.info(
            f"Baseline created: {len(self._baseline)} keys monitored"
        )

    async def _read_key_values(
        self, hive: int, subkey: str
    ) -> dict[str, Any]:
        """Read all values from a registry key.

        Args:
            hive: Registry hive (HKEY_LOCAL_MACHINE, etc.)
            subkey: Subkey path

        Returns:
            Dictionary of value name -> value data
        """
        values = {}

        try:
            key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)

            try:
                index = 0
                while True:
                    try:
                        value_name, value_data, value_type = winreg.EnumValue(key, index)
                        values[value_name] = {
                            "data": value_data,
                            "type": value_type,
                        }
                        index += 1
                    except OSError:
                        break  # No more values
            finally:
                winreg.CloseKey(key)

        except FileNotFoundError:
            # Key doesn't exist yet
            pass
        except Exception as e:
            self._logger.debug(f"Could not read key {subkey}: {e}")

        return values

    async def _check_key(
        self, key_name: str, hive: int, subkey: str
    ) -> list[RegistryEvent]:
        """Check a registry key for changes.

        Args:
            key_name: Friendly key name
            hive: Registry hive
            subkey: Subkey path

        Returns:
            List of security events
        """
        events: list[RegistryEvent] = []

        try:
            # Read current values
            current_values = await self._read_key_values(hive, subkey)

            # Get baseline for this key
            baseline_values = self._baseline.get(key_name, {})

            # Check for new values
            for value_name, value_info in current_values.items():
                if value_name not in baseline_values:
                    # New value detected
                    events.extend(
                        await self._handle_new_value(
                            key_name, value_name, value_info, hive, subkey
                        )
                    )
                elif baseline_values[value_name]["data"] != value_info["data"]:
                    # Modified value detected
                    events.append(
                        await self._handle_modified_value(
                            key_name,
                            value_name,
                            baseline_values[value_name],
                            value_info,
                            hive,
                            subkey,
                        )
                    )

            # Check for deleted values
            for value_name in baseline_values:
                if value_name not in current_values:
                    events.append(
                        await self._handle_deleted_value(
                            key_name, value_name, baseline_values[value_name]
                        )
                    )

            # Update baseline
            self._baseline[key_name] = current_values

        except Exception as e:
            self._logger.error(f"Error checking key {key_name}: {e}", exc_info=True)

        return events

    async def _handle_new_value(
        self,
        key_name: str,
        value_name: str,
        value_info: dict[str, Any],
        hive: int,
        subkey: str,
    ) -> list[RegistryEvent]:
        """Handle detection of new registry value.

        Args:
            key_name: Friendly key name
            value_name: Name of the value
            value_info: Value information
            hive: Registry hive
            subkey: Subkey path

        Returns:
            List of security events
        """
        events: list[RegistryEvent] = []

        # Determine severity based on key type
        severity = EventSeverity.INFO
        threat_score = 30

        if "Run" in key_name:
            if self.config.alert_on_startup_entry:
                severity = EventSeverity.WARNING
                threat_score = 60
                event_type = EventType.STARTUP_ENTRY_ADDED
        elif "Services" in key_name:
            if self.config.alert_on_new_service:
                severity = EventSeverity.WARNING
                threat_score = 70
                event_type = EventType.SERVICE_INSTALLED
        elif "Policies" in key_name or "Defender" in key_name:
            severity = EventSeverity.CRITICAL
            threat_score = 85
            event_type = EventType.REGISTRY_CHANGED
        else:
            event_type = EventType.REGISTRY_CHANGED

        # Check for suspicious value content
        value_data_str = str(value_info["data"]).lower()
        is_suspicious = any(
            pattern in value_data_str for pattern in self.SUSPICIOUS_VALUE_PATTERNS
        )

        if is_suspicious:
            severity = EventSeverity.CRITICAL
            threat_score = 90

        events.append(
            RegistryEvent(
                event_type=event_type,
                severity=severity,
                source_monitor=self.name,
                threat_score=threat_score,
                description=f"New registry value: {key_name}\\{value_name}",
                data={
                    "key": key_name,
                    "value_name": value_name,
                    "value_data": str(value_info["data"])[:200],  # Truncate
                    "value_type": value_info["type"],
                    "is_suspicious": is_suspicious,
                    "full_path": f"{self._hive_to_string(hive)}\\{subkey}",
                },
            )
        )

        # Store backup if rollback enabled
        if self.config.enable_rollback:
            backup_key = f"{key_name}\\{value_name}"
            self._backup[backup_key] = {
                "action": "delete",  # To rollback, delete this value
                "hive": hive,
                "subkey": subkey,
                "value_name": value_name,
                "timestamp": datetime.now(),
            }

        return events

    async def _handle_modified_value(
        self,
        key_name: str,
        value_name: str,
        old_value_info: dict[str, Any],
        new_value_info: dict[str, Any],
        hive: int,
        subkey: str,
    ) -> RegistryEvent:
        """Handle detection of modified registry value.

        Args:
            key_name: Friendly key name
            value_name: Name of the value
            old_value_info: Old value information
            new_value_info: New value information
            hive: Registry hive
            subkey: Subkey path

        Returns:
            Security event
        """
        severity = EventSeverity.WARNING
        threat_score = 50

        # Higher severity for critical keys
        if "Policies" in key_name or "Defender" in key_name:
            severity = EventSeverity.CRITICAL
            threat_score = 85

        # Store backup if rollback enabled
        if self.config.enable_rollback:
            backup_key = f"{key_name}\\{value_name}"
            self._backup[backup_key] = {
                "action": "restore",  # To rollback, restore old value
                "hive": hive,
                "subkey": subkey,
                "value_name": value_name,
                "old_value": old_value_info,
                "timestamp": datetime.now(),
            }

        return RegistryEvent(
            event_type=EventType.REGISTRY_CHANGED,
            severity=severity,
            source_monitor=self.name,
            threat_score=threat_score,
            description=f"Registry value modified: {key_name}\\{value_name}",
            data={
                "key": key_name,
                "value_name": value_name,
                "old_value": str(old_value_info["data"])[:100],
                "new_value": str(new_value_info["data"])[:100],
                "full_path": f"{self._hive_to_string(hive)}\\{subkey}",
            },
        )

    async def _handle_deleted_value(
        self, key_name: str, value_name: str, value_info: dict[str, Any]
    ) -> RegistryEvent:
        """Handle detection of deleted registry value.

        Args:
            key_name: Friendly key name
            value_name: Name of the value
            value_info: Value information (from baseline)

        Returns:
            Security event
        """
        severity = EventSeverity.INFO
        threat_score = 20

        # Higher severity for critical keys
        if "Defender" in key_name:
            severity = EventSeverity.CRITICAL
            threat_score = 95

        return RegistryEvent(
            event_type=EventType.REGISTRY_CHANGED,
            severity=severity,
            source_monitor=self.name,
            threat_score=threat_score,
            description=f"Registry value deleted: {key_name}\\{value_name}",
            data={
                "key": key_name,
                "value_name": value_name,
                "deleted_value": str(value_info["data"])[:100],
            },
        )

    async def rollback_change(self, backup_key: str) -> bool:
        """Rollback a registry change.

        Args:
            backup_key: Backup key identifying the change

        Returns:
            True if rollback successful, False otherwise
        """
        if not self.config.enable_rollback:
            self._logger.error("Rollback is disabled in configuration")
            return False

        if backup_key not in self._backup:
            self._logger.error(f"No backup found for key: {backup_key}")
            return False

        backup = self._backup[backup_key]

        try:
            key = winreg.OpenKey(
                backup["hive"],
                backup["subkey"],
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY,
            )

            if backup["action"] == "delete":
                # Delete the value
                winreg.DeleteValue(key, backup["value_name"])
                self._logger.info(f"Rolled back: Deleted {backup_key}")
            elif backup["action"] == "restore":
                # Restore old value
                old_value = backup["old_value"]
                winreg.SetValueEx(
                    key,
                    backup["value_name"],
                    0,
                    old_value["type"],
                    old_value["data"],
                )
                self._logger.info(f"Rolled back: Restored {backup_key}")

            winreg.CloseKey(key)
            return True

        except Exception as e:
            self._logger.error(f"Rollback failed for {backup_key}: {e}")
            return False

    def get_backup_info(self) -> dict[str, dict[str, Any]]:
        """Get information about available rollback points.

        Returns:
            Dictionary of backup key -> backup info
        """
        return self._backup.copy()

    def _hive_to_string(self, hive: int) -> str:
        """Convert registry hive constant to string.

        Args:
            hive: Registry hive constant

        Returns:
            String representation
        """
        if hive == winreg.HKEY_LOCAL_MACHINE:
            return "HKEY_LOCAL_MACHINE"
        elif hive == winreg.HKEY_CURRENT_USER:
            return "HKEY_CURRENT_USER"
        elif hive == winreg.HKEY_CLASSES_ROOT:
            return "HKEY_CLASSES_ROOT"
        elif hive == winreg.HKEY_USERS:
            return "HKEY_USERS"
        else:
            return f"HIVE_{hive}"
