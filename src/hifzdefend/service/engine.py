"""
Core engine orchestrator for HifzDefend service.

This module provides the main service engine that coordinates all components
including scanning, monitoring, quarantine, and AI features.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ..config import load_config, HifzDefendConfig
from ..core.scanner import Scanner
from ..core.quarantine import QuarantineManager
from ..monitoring.manager import MonitorManager
from .state import (
    ServiceState,
    ProtectionStatus,
    MonitorStatus,
    ThreatInfo,
    ThreatSeverity,
)
from .events import EventEmitter, EventType

logger = logging.getLogger(__name__)


class HifzDefendEngine:
    """
    Core engine for HifzDefend service.

    This is the main orchestrator that manages all components and provides
    a unified API for the Windows service, CLI, system tray, and web dashboard.
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize the HifzDefend engine.

        Args:
            config_path: Optional path to configuration file
        """
        logger.info("Initializing HifzDefend engine")

        # Load configuration
        self.config: HifzDefendConfig = load_config(config_path)

        # Initialize state and events
        self.state = ServiceState()
        self.events = EventEmitter()

        # Initialize components (lazy loading)
        self._scanner: Optional[Scanner] = None
        self._quarantine: Optional[QuarantineManager] = None
        self._monitor_manager: Optional[MonitorManager] = None

        # Service state
        self._running = False

        logger.info("HifzDefend engine initialized")

    @property
    def scanner(self) -> Scanner:
        """Get scanner instance (lazy load)."""
        if self._scanner is None:
            from ..core.scanner import Scanner

            self._scanner = Scanner(self.config)
        return self._scanner

    @property
    def quarantine(self) -> QuarantineManager:
        """Get quarantine manager instance (lazy load)."""
        if self._quarantine is None:
            from ..core.quarantine import QuarantineManager

            self._quarantine = QuarantineManager(self.config)
        return self._quarantine

    @property
    def monitor_manager(self) -> MonitorManager:
        """Get monitor manager instance (lazy load)."""
        if self._monitor_manager is None:
            from ..monitoring.manager import MonitorManager
            from ..monitoring.event_bus import get_event_bus

            # MonitorManager only takes event_bus, not config
            self._monitor_manager = MonitorManager(event_bus=get_event_bus())

            # Register all monitors if monitoring is enabled
            if self.config.monitoring.enabled:
                self._register_all_monitors()
        return self._monitor_manager

    def _register_all_monitors(self) -> None:
        """
        Register all security monitors with the monitor manager.

        This method instantiates and registers all 13 security monitors
        based on the configuration.
        """
        from ..monitoring.event_bus import get_event_bus
        from ..monitoring import (
            registry_monitor,
            powershell_monitor,
            network_monitor,
            clipboard_monitor,
            cryptominer_monitor,
            dns_monitor,
            download_monitor,
            hardware_monitor,
            spyware_monitor,
            ransomware_monitor,
            package_monitor,
            docker_monitor,
            ide_monitor,
        )

        event_bus = get_event_bus()

        # Registry Monitor
        if hasattr(self.config.monitoring, 'registry') and self.config.monitoring.registry.enabled:
            monitor = registry_monitor.RegistryMonitor(
                config=self.config.monitoring.registry,
                event_bus=event_bus
            )
            self._monitor_manager.register_monitor(monitor)
            logger.debug("Registered RegistryMonitor")

        # PowerShell Monitor
        if hasattr(self.config.monitoring, 'powershell') and self.config.monitoring.powershell.enabled:
            monitor = powershell_monitor.PowerShellMonitor(
                config=self.config.monitoring.powershell,
                event_bus=event_bus
            )
            self._monitor_manager.register_monitor(monitor)
            logger.debug("Registered PowerShellMonitor")

        # Network Monitor
        if hasattr(self.config.monitoring, 'network') and self.config.monitoring.network.enabled:
            monitor = network_monitor.NetworkMonitor(
                config=self.config.monitoring.network,
                event_bus=event_bus
            )
            self._monitor_manager.register_monitor(monitor)
            logger.debug("Registered NetworkMonitor")

        # Clipboard Monitor
        if hasattr(self.config.monitoring, 'clipboard') and self.config.monitoring.clipboard.enabled:
            monitor = clipboard_monitor.ClipboardMonitor(
                config=self.config.monitoring.clipboard,
                event_bus=event_bus
            )
            self._monitor_manager.register_monitor(monitor)
            logger.debug("Registered ClipboardMonitor")

        # Cryptominer Monitor
        if hasattr(self.config.monitoring, 'cryptominer') and self.config.monitoring.cryptominer.enabled:
            monitor = cryptominer_monitor.CryptominerMonitor(
                config=self.config.monitoring.cryptominer,
                event_bus=event_bus
            )
            self._monitor_manager.register_monitor(monitor)
            logger.debug("Registered CryptominerMonitor")

        # DNS Monitor
        if hasattr(self.config.monitoring, 'dns') and self.config.monitoring.dns.enabled:
            monitor = dns_monitor.DNSMonitor(
                config=self.config.monitoring.dns,
                event_bus=event_bus
            )
            self._monitor_manager.register_monitor(monitor)
            logger.debug("Registered DNSMonitor")

        # Download Monitor
        if hasattr(self.config.monitoring, 'download') and self.config.monitoring.download.enabled:
            monitor = download_monitor.DownloadMonitor(
                config=self.config.monitoring.download,
                event_bus=event_bus
            )
            self._monitor_manager.register_monitor(monitor)
            logger.debug("Registered DownloadMonitor")

        # Hardware Monitor
        if hasattr(self.config.monitoring, 'hardware') and self.config.monitoring.hardware.enabled:
            monitor = hardware_monitor.HardwareMonitor(
                config=self.config.monitoring.hardware,
                event_bus=event_bus
            )
            self._monitor_manager.register_monitor(monitor)
            logger.debug("Registered HardwareMonitor")

        # Spyware Monitor
        if hasattr(self.config.monitoring, 'spyware') and self.config.monitoring.spyware.enabled:
            monitor = spyware_monitor.SpywareMonitor(
                config=self.config.monitoring.spyware,
                event_bus=event_bus
            )
            self._monitor_manager.register_monitor(monitor)
            logger.debug("Registered SpywareMonitor")

        # Ransomware Monitor
        if hasattr(self.config.monitoring, 'ransomware') and self.config.monitoring.ransomware.enabled:
            monitor = ransomware_monitor.RansomwareMonitor(
                config=self.config.monitoring.ransomware,
                event_bus=event_bus
            )
            self._monitor_manager.register_monitor(monitor)
            logger.debug("Registered RansomwareMonitor")

        # Package Monitor
        if hasattr(self.config.monitoring, 'package') and self.config.monitoring.package.enabled:
            monitor = package_monitor.PackageMonitor(
                config=self.config.monitoring.package,
                event_bus=event_bus
            )
            self._monitor_manager.register_monitor(monitor)
            logger.debug("Registered PackageMonitor")

        # Docker Monitor
        if hasattr(self.config.monitoring, 'docker') and self.config.monitoring.docker.enabled:
            monitor = docker_monitor.DockerMonitor(
                config=self.config.monitoring.docker,
                event_bus=event_bus
            )
            self._monitor_manager.register_monitor(monitor)
            logger.debug("Registered DockerMonitor")

        # IDE Monitor
        if hasattr(self.config.monitoring, 'ide') and self.config.monitoring.ide.enabled:
            monitor = ide_monitor.IDEMonitor(
                config=self.config.monitoring.ide,
                event_bus=event_bus
            )
            self._monitor_manager.register_monitor(monitor)
            logger.debug("Registered IDEMonitor")

        logger.info(f"Registered {len(self._monitor_manager.monitors)} monitors")

    def start(self) -> None:
        """
        Start the HifzDefend service.

        This starts all enabled monitors and initializes the protection system.
        """
        if self._running:
            logger.warning("Service already running")
            return

        logger.info("Starting HifzDefend service")

        try:
            # Update state
            self.state.start_service()
            self._running = True

            # Start monitoring if enabled
            if self.config.monitoring.enabled:
                logger.info("Starting monitoring system")
                self._start_monitors()

            # Emit service started event
            self.events.emit_service_started()

            logger.info("HifzDefend service started successfully")

        except Exception as e:
            logger.error(f"Failed to start service: {e}", exc_info=True)
            self.state.protection_status = ProtectionStatus.ERROR
            self.events.emit(
                EventType.SERVICE_ERROR,
                {"error": str(e)},
                priority=3,
            )
            raise

    def stop(self) -> None:
        """
        Stop the HifzDefend service.

        This gracefully shuts down all monitors and stops the protection system.
        """
        if not self._running:
            logger.warning("Service not running")
            return

        logger.info("Stopping HifzDefend service")

        try:
            # Stop monitors
            if self._monitor_manager is not None:
                logger.info("Stopping monitoring system")
                self._stop_monitors()

            # Update state
            self.state.stop_service()
            self._running = False

            # Emit service stopped event
            self.events.emit_service_stopped()

            logger.info("HifzDefend service stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping service: {e}", exc_info=True)
            raise

    def _start_monitors(self) -> None:
        """Start all enabled monitors (synchronous wrapper)."""
        import asyncio

        # Get registered monitors from manager
        registered_monitors = self.monitor_manager.list_monitors()

        # Register monitors in service state
        for monitor_name in registered_monitors:
            # Convert monitor class name to ID (e.g., "RegistryMonitor" -> "registry")
            monitor_id = monitor_name.lower().replace("monitor", "").strip()
            self.state.register_monitor(
                monitor_id=monitor_id,
                monitor_name=monitor_name,
                enabled=True,
            )

        # Start all monitors asynchronously
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(self.monitor_manager.start_all())

        # Update state for started monitors
        for monitor_name in registered_monitors:
            monitor_id = monitor_name.lower().replace("monitor", "").strip()
            self.state.update_monitor_status(monitor_id, MonitorStatus.RUNNING)

        logger.info(f"Started {len(registered_monitors)} monitors")

    def _stop_monitors(self) -> None:
        """Stop all monitors (synchronous wrapper)."""
        import asyncio

        if self._monitor_manager is None:
            return

        registered_monitors = self.monitor_manager.list_monitors()

        # Stop all monitors asynchronously
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(self.monitor_manager.stop_all())

        # Update state for stopped monitors
        for monitor_name in registered_monitors:
            monitor_id = monitor_name.lower().replace("monitor", "").strip()
            self.state.update_monitor_status(monitor_id, MonitorStatus.STOPPED)

        logger.info(f"Stopped {len(registered_monitors)} monitors")

    def scan_path(
        self,
        path: str,
        recursive: bool = True,
        callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Scan a file or directory.

        Args:
            path: Path to scan
            recursive: Whether to scan recursively
            callback: Optional progress callback

        Returns:
            Scan results dictionary
        """
        scan_id = str(uuid.uuid4())
        logger.info(f"Starting scan {scan_id} for path: {path}")

        # Register scan in state
        self.state.start_scan(scan_id, path)

        # Emit scan started event
        self.events.emit_scan_started(scan_id, path)

        try:
            # Perform scan
            result = self.scanner.scan_path(
                Path(path),
                recursive=recursive,
                callback=callback,
            )

            # Update state with results
            threats = result.get("threats", [])
            self.state.update_scan_progress(
                scan_id,
                files_scanned=result.get("files_scanned", 0),
                threats_found=len(threats),
            )

            # Process threats
            for threat in threats:
                threat_info = ThreatInfo(
                    id=str(uuid.uuid4()),
                    name=threat.get("name", "Unknown"),
                    severity=ThreatSeverity.MALICIOUS,
                    detected_at=datetime.now(),
                    path=threat.get("path", ""),
                    quarantined=threat.get("quarantined", False),
                )
                self.state.add_threat(threat_info)

                # Emit threat detected event
                self.events.emit_threat_detected(
                    threat_info.id,
                    threat_info.name,
                    threat_info.path,
                    threat_info.severity.value,
                )

            # Complete scan
            self.state.complete_scan(scan_id, threats)

            # Emit scan completed event
            self.events.emit_scan_completed(
                scan_id,
                result.get("files_scanned", 0),
                len(threats),
            )

            return {
                "scan_id": scan_id,
                "path": path,
                "files_scanned": result.get("files_scanned", 0),
                "threats_found": len(threats),
                "threats": threats,
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"Scan {scan_id} failed: {e}", exc_info=True)
            self.events.emit(
                EventType.SCAN_ERROR,
                {"scan_id": scan_id, "error": str(e)},
                priority=2,
            )
            raise

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status.

        Returns:
            System status dictionary
        """
        status = self.state.get_system_status()
        return {
            "protection_status": status.protection_status.value,
            "monitors": {
                "active": status.monitors_active,
                "total": status.monitors_total,
            },
            "threats": {
                "today": status.threats_today,
                "week": status.threats_week,
                "total": status.threats_total,
            },
            "last_scan": status.last_scan.isoformat() if status.last_scan else None,
            "last_update": (
                status.last_update.isoformat() if status.last_update else None
            ),
            "resources": {
                "cpu_usage": status.cpu_usage,
                "memory_usage": status.memory_usage,
            },
        }

    def get_monitors_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all monitors.

        Returns:
            List of monitor status dictionaries
        """
        monitors = self.state.get_all_monitors()
        return [
            {
                "id": m.id,
                "name": m.name,
                "status": m.status.value,
                "enabled": m.enabled,
                "event_count": m.event_count,
                "last_event": m.last_event.isoformat() if m.last_event else None,
                "error_message": m.error_message,
            }
            for m in monitors
        ]

    def toggle_monitor(self, monitor_id: str, enabled: bool) -> Dict[str, Any]:
        """
        Enable or disable a monitor.

        Args:
            monitor_id: Monitor identifier (e.g., "registry", "powershell")
            enabled: Whether to enable the monitor

        Returns:
            Updated monitor status
        """
        import asyncio

        logger.info(f"Toggling monitor {monitor_id}: enabled={enabled}")

        # Get state monitor info
        monitor_state = self.state.get_monitor_state(monitor_id)
        if not monitor_state:
            raise ValueError(f"Monitor not found: {monitor_id}")

        # Convert monitor ID to class name (e.g., "registry" -> "RegistryMonitor")
        monitor_name = monitor_id.capitalize() + "Monitor"

        # Get actual monitor from manager
        actual_monitor = self.monitor_manager.get_monitor(monitor_name)
        if not actual_monitor:
            raise ValueError(f"Monitor implementation not found: {monitor_name}")

        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            if enabled:
                # Start the monitor
                loop.run_until_complete(self.monitor_manager.start_monitor(monitor_name))
                self.state.update_monitor_status(monitor_id, MonitorStatus.RUNNING)
                self.events.emit_monitor_started(monitor_id, monitor_state.name)
                logger.info(f"Monitor {monitor_name} started")
            else:
                # Stop the monitor
                loop.run_until_complete(self.monitor_manager.stop_monitor(monitor_name))
                self.state.update_monitor_status(monitor_id, MonitorStatus.STOPPED)
                self.events.emit_monitor_stopped(monitor_id, monitor_state.name)
                logger.info(f"Monitor {monitor_name} stopped")

            # Get updated state
            updated_state = self.state.get_monitor_state(monitor_id)
            return {
                "id": monitor_id,
                "enabled": enabled,
                "status": updated_state.status.value if updated_state else "unknown",
            }

        except Exception as e:
            logger.error(f"Error toggling monitor {monitor_id}: {e}", exc_info=True)
            self.state.update_monitor_status(monitor_id, MonitorStatus.ERROR)
            raise

    def pause_monitor(self, monitor_id: str) -> Dict[str, Any]:
        """
        Pause a monitor (keeps it running but stops checks).

        Args:
            monitor_id: Monitor identifier

        Returns:
            Updated monitor status
        """
        logger.info(f"Pausing monitor {monitor_id}")

        monitor_state = self.state.get_monitor_state(monitor_id)
        if not monitor_state:
            raise ValueError(f"Monitor not found: {monitor_id}")

        monitor_name = monitor_id.capitalize() + "Monitor"
        self.monitor_manager.pause_monitor(monitor_name)

        return {
            "id": monitor_id,
            "status": "paused",
        }

    def resume_monitor(self, monitor_id: str) -> Dict[str, Any]:
        """
        Resume a paused monitor.

        Args:
            monitor_id: Monitor identifier

        Returns:
            Updated monitor status
        """
        logger.info(f"Resuming monitor {monitor_id}")

        monitor_state = self.state.get_monitor_state(monitor_id)
        if not monitor_state:
            raise ValueError(f"Monitor not found: {monitor_id}")

        monitor_name = monitor_id.capitalize() + "Monitor"
        self.monitor_manager.resume_monitor(monitor_name)
        self.state.update_monitor_status(monitor_id, MonitorStatus.RUNNING)

        return {
            "id": monitor_id,
            "status": "running",
        }

    def restart_monitor(self, monitor_id: str) -> Dict[str, Any]:
        """
        Restart a monitor (stop then start).

        Args:
            monitor_id: Monitor identifier

        Returns:
            Updated monitor status
        """
        import asyncio

        logger.info(f"Restarting monitor {monitor_id}")

        monitor_state = self.state.get_monitor_state(monitor_id)
        if not monitor_state:
            raise ValueError(f"Monitor not found: {monitor_id}")

        monitor_name = monitor_id.capitalize() + "Monitor"

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            # Stop the monitor
            loop.run_until_complete(self.monitor_manager.stop_monitor(monitor_name))
            self.state.update_monitor_status(monitor_id, MonitorStatus.STOPPED)

            # Wait a moment
            import time
            time.sleep(1)

            # Start the monitor
            loop.run_until_complete(self.monitor_manager.start_monitor(monitor_name))
            self.state.update_monitor_status(monitor_id, MonitorStatus.RUNNING)

            logger.info(f"Monitor {monitor_name} restarted successfully")

            return {
                "id": monitor_id,
                "status": "running",
            }

        except Exception as e:
            logger.error(f"Error restarting monitor {monitor_id}: {e}", exc_info=True)
            self.state.update_monitor_status(monitor_id, MonitorStatus.ERROR)
            raise

    def get_monitor_health(self) -> Dict[str, Any]:
        """
        Get health status of all monitors.

        Returns:
            Health check results for all monitors
        """
        if self._monitor_manager is None:
            return {
                "healthy": False,
                "manager_running": False,
                "monitors": [],
            }

        all_status = self.monitor_manager.get_all_status()
        manager_status = self.monitor_manager.get_status()

        monitors_health = []
        unhealthy_count = 0

        for monitor_name, status in all_status.items():
            is_healthy = (
                status.running
                and status.errors == 0
                and status.last_check is not None
            )

            if not is_healthy:
                unhealthy_count += 1

            monitors_health.append({
                "name": monitor_name,
                "healthy": is_healthy,
                "running": status.running,
                "errors": status.errors,
                "last_check": status.last_check.isoformat() if status.last_check else None,
                "status_message": status.status_message,
            })

        return {
            "healthy": unhealthy_count == 0,
            "manager_running": manager_status["manager_running"],
            "total_monitors": manager_status["total_monitors"],
            "running_monitors": manager_status["running_monitors"],
            "unhealthy_monitors": unhealthy_count,
            "monitors": monitors_health,
        }

    def get_quarantine_list(self) -> List[Dict[str, Any]]:
        """
        Get list of quarantined files.

        Returns:
            List of quarantined file information
        """
        items = self.quarantine.list_quarantine()
        return [
            {
                "id": item.get("id"),
                "original_path": item.get("original_path"),
                "threat_name": item.get("threat_name"),
                "quarantined_at": item.get("quarantined_at"),
                "size": item.get("size"),
            }
            for item in items
        ]

    def restore_from_quarantine(self, quarantine_id: str) -> Dict[str, Any]:
        """
        Restore a file from quarantine.

        Args:
            quarantine_id: Quarantine item ID

        Returns:
            Restore result
        """
        logger.info(f"Restoring from quarantine: {quarantine_id}")
        result = self.quarantine.restore(quarantine_id)
        return {
            "success": result,
            "id": quarantine_id,
        }

    def get_recent_threats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent detected threats.

        Args:
            limit: Maximum number of threats to return

        Returns:
            List of threat information
        """
        threats = self.state.get_recent_threats(limit)
        return [
            {
                "id": t.id,
                "name": t.name,
                "severity": t.severity.value,
                "detected_at": t.detected_at.isoformat(),
                "path": t.path,
                "quarantined": t.quarantined,
                "description": t.description,
            }
            for t in threats
        ]

    def get_scan_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get scan history.

        Args:
            limit: Maximum number of scans to return

        Returns:
            List of scan results
        """
        scans = self.state.get_scan_history(limit)
        return [
            {
                "id": s.id,
                "path": s.path,
                "started_at": s.started_at.isoformat(),
                "completed_at": (
                    s.completed_at.isoformat() if s.completed_at else None
                ),
                "status": s.status,
                "files_scanned": s.files_scanned,
                "threats_found": s.threats_found,
            }
            for s in scans
        ]

    def update_config(self, section: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update configuration.

        Args:
            section: Configuration section to update
            updates: Dictionary of updates to apply

        Returns:
            Updated configuration
        """
        logger.info(f"Updating configuration section: {section}")

        # TODO: Implement configuration persistence
        # For now, just emit event
        self.events.emit_config_changed(section, updates)

        return {"success": True, "section": section, "updates": updates}

    # ============================================================================
    # ClamAV Operations
    # ============================================================================

    def check_clamav_connection(self) -> Dict[str, Any]:
        """
        Check if ClamAV daemon is reachable.

        Returns:
            Connection status information
        """
        try:
            is_connected = self.scanner.check_connection()
            version = None
            if is_connected:
                version = self.scanner.get_version()

            return {
                "connected": is_connected,
                "host": self.config.clamav.host,
                "port": self.config.clamav.port,
                "version": version,
            }
        except Exception as e:
            logger.error(f"ClamAV connection check failed: {e}")
            return {
                "connected": False,
                "host": self.config.clamav.host,
                "port": self.config.clamav.port,
                "error": str(e),
            }

    def update_virus_definitions(self) -> Dict[str, Any]:
        """
        Update ClamAV virus definitions using freshclam.

        Returns:
            Update result information
        """
        import subprocess

        logger.info("Updating virus definitions")

        try:
            result = subprocess.run(
                ["freshclam"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            success = result.returncode == 0
            if success:
                logger.info("Virus definitions updated successfully")
                self.events.emit(
                    EventType.SYSTEM_UPDATE,
                    {"component": "virus_definitions", "status": "updated"},
                    priority=1,
                )
            else:
                logger.error(f"Virus definitions update failed: {result.stderr}")

            return {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }

        except FileNotFoundError:
            logger.error("freshclam not found")
            return {
                "success": False,
                "error": "freshclam not found - ClamAV may not be installed",
            }
        except subprocess.TimeoutExpired:
            logger.error("freshclam update timed out")
            return {
                "success": False,
                "error": "Update timed out after 5 minutes",
            }
        except Exception as e:
            logger.error(f"Error updating virus definitions: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }

    # ============================================================================
    # AI Operations
    # ============================================================================

    def analyze_script_with_ai(
        self,
        script_path: str,
        script_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a script for security threats using Claude AI.

        Args:
            script_path: Path to script file
            script_type: Optional script type (auto-detect if None)

        Returns:
            Analysis results dictionary

        Raises:
            ValueError: If AI features are not available or not enabled
        """
        # Check if AI is available
        if not self.config.ai.enabled:
            raise ValueError("AI features are not enabled in configuration")

        # Import AI components (lazy import)
        try:
            from ..ai.claude_analyzer import ClaudeAnalyzer
        except ImportError:
            raise ValueError("AI dependencies not installed")

        # Get API key
        api_key = self.config.ai.claude.get_api_key()
        if not api_key:
            raise ValueError("Claude API key not set")

        logger.info(f"Analyzing script with AI: {script_path}")

        # Read script content
        script_path_obj = Path(script_path)
        if not script_path_obj.exists():
            raise ValueError(f"Script file not found: {script_path}")

        try:
            with open(script_path_obj, "r", encoding="utf-8") as f:
                script_content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(script_path_obj, "r", encoding="latin-1") as f:
                script_content = f.read()

        # Initialize Claude analyzer
        claude = ClaudeAnalyzer(
            api_key=api_key,
            model=self.config.ai.claude.model,
            max_tokens=self.config.ai.claude.max_tokens,
            temperature=self.config.ai.claude.temperature,
            timeout=self.config.ai.claude.timeout,
            cache_enabled=self.config.ai.claude.cache_responses,
            cache_dir=self.config.ai.claude.cache_path_expanded,
            cache_ttl=self.config.ai.claude.cache_ttl,
            max_requests_per_hour=self.config.ai.claude.max_requests_per_hour,
            log_costs=self.config.ai.claude.log_api_costs,
            fallback_on_error=self.config.ai.claude.fallback_on_error,
            retry_attempts=self.config.ai.claude.retry_attempts,
            retry_delay=self.config.ai.claude.retry_delay,
        )

        # Auto-detect script type if not provided
        if not script_type or script_type == "auto":
            extension = script_path_obj.suffix.lower()
            script_type_map = {
                ".ps1": "powershell",
                ".bat": "batch",
                ".cmd": "batch",
                ".py": "python",
                ".sh": "bash",
                ".vbs": "vbscript",
                ".js": "javascript",
            }
            script_type = script_type_map.get(extension, "unknown")

        # Perform analysis
        try:
            analysis = claude.analyze_script(
                script_content=script_content,
                script_type=script_type,
                filename=script_path_obj.name,
            )

            # Get cost stats if enabled
            cost_info = None
            if self.config.ai.claude.log_api_costs:
                stats = claude.get_cost_stats()
                cost_info = {
                    "total_cost_usd": stats["total_cost_usd"],
                    "input_tokens": stats["input_tokens"],
                    "output_tokens": stats["output_tokens"],
                }

            logger.info(
                f"AI analysis complete: threat_level={analysis.get('threat_level')}"
            )

            return {
                "success": True,
                "file_path": str(script_path),
                "script_type": script_type,
                "analysis": analysis,
                "cost": cost_info,
            }

        except Exception as e:
            logger.error(f"AI script analysis failed: {e}", exc_info=True)
            return {
                "success": False,
                "file_path": str(script_path),
                "error": str(e),
            }

    def query_with_ai(
        self,
        question: str,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query security logs using natural language (Claude AI).

        Args:
            question: Natural language question
            context: Optional additional context

        Returns:
            Query results dictionary

        Raises:
            ValueError: If AI/NL features are not available or not enabled
        """
        # Check if AI and NL are enabled
        if not self.config.ai.enabled:
            raise ValueError("AI features are not enabled in configuration")

        if not self.config.ai.natural_language.enabled:
            raise ValueError("Natural language queries are not enabled in configuration")

        # Import AI components (lazy import)
        try:
            from ..ai.claude_analyzer import ClaudeAnalyzer
            from ..ai.nl_interface import NaturalLanguageInterface
        except ImportError:
            raise ValueError("AI/ChromaDB dependencies not installed")

        # Get API key
        api_key = self.config.ai.claude.get_api_key()
        if not api_key:
            raise ValueError("Claude API key not set")

        logger.info(f"AI query: {question}")

        # Initialize Claude analyzer
        claude = ClaudeAnalyzer(
            api_key=api_key,
            model=self.config.ai.claude.model,
            max_tokens=self.config.ai.claude.max_tokens,
            temperature=self.config.ai.claude.temperature,
            timeout=self.config.ai.claude.timeout,
            cache_enabled=self.config.ai.claude.cache_responses,
            cache_dir=self.config.ai.claude.cache_path_expanded,
            cache_ttl=self.config.ai.claude.cache_ttl,
            max_requests_per_hour=self.config.ai.claude.max_requests_per_hour,
            log_costs=self.config.ai.claude.log_api_costs,
            fallback_on_error=self.config.ai.claude.fallback_on_error,
            retry_attempts=self.config.ai.claude.retry_attempts,
            retry_delay=self.config.ai.claude.retry_delay,
        )

        # Initialize NL interface
        nl_interface = NaturalLanguageInterface(
            vector_db_path=self.config.ai.natural_language.vector_db_path_expanded,
            claude_analyzer=claude,
            embedding_model=self.config.ai.natural_language.embedding_model,
            collection_name=self.config.ai.natural_language.chromadb.collection_name,
            max_context_results=self.config.ai.natural_language.max_context_results,
        )

        # Perform query
        try:
            result = nl_interface.query(question)

            # Get cost stats if enabled
            cost_info = None
            if self.config.ai.claude.log_api_costs:
                stats = claude.get_cost_stats()
                cost_info = {
                    "total_cost_usd": stats["total_cost_usd"],
                    "input_tokens": stats["input_tokens"],
                    "output_tokens": stats["output_tokens"],
                }

            logger.info(f"AI query complete: {result['num_results']} results found")

            return {
                "success": True,
                "question": question,
                "answer": result["answer"],
                "num_results": result["num_results"],
                "sources": result.get("sources", []),
                "cost": cost_info,
            }

        except Exception as e:
            logger.error(f"AI query failed: {e}", exc_info=True)
            return {
                "success": False,
                "question": question,
                "error": str(e),
            }

    @property
    def is_running(self) -> bool:
        """Check if service is running."""
        return self._running
