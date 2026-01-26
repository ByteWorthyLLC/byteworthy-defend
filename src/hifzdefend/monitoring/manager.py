"""Monitor manager for orchestrating all security monitors in HifzDefend.

The MonitorManager is responsible for:
- Registering and managing all security monitors
- Starting and stopping monitors based on configuration
- Collecting status information from all monitors
- Coordinating monitor lifecycle
"""

import asyncio
import logging
from typing import Any, Optional

from .base import BaseMonitor, MonitorStatus
from .event_bus import EventBus, get_event_bus

logger = logging.getLogger(__name__)


class MonitorManager:
    """Manages the lifecycle of all security monitors.

    The MonitorManager coordinates multiple monitors, ensuring they are
    started and stopped correctly, and provides a unified interface for
    managing the monitoring system.

    Example:
        ```python
        # Create manager
        manager = MonitorManager(config)

        # Register monitors
        manager.register_monitor(PackageMonitor(config.package_manager, event_bus))
        manager.register_monitor(DockerMonitor(config.docker, event_bus))

        # Start all monitors
        await manager.start_all()

        # Get status
        status = manager.get_status()

        # Stop all monitors
        await manager.stop_all()
        ```
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """Initialize the monitor manager.

        Args:
            event_bus: EventBus instance (optional, uses global singleton if not provided)
        """
        self.event_bus = event_bus or get_event_bus()
        self.monitors: dict[str, BaseMonitor] = {}
        self._logger = logging.getLogger(__name__)
        self._running = False

        self._logger.info("MonitorManager initialized")

    def register_monitor(self, monitor: BaseMonitor) -> None:
        """Register a monitor with the manager.

        Args:
            monitor: The monitor to register

        Raises:
            ValueError: If a monitor with the same name is already registered
        """
        if monitor.name in self.monitors:
            raise ValueError(f"Monitor {monitor.name} is already registered")

        self.monitors[monitor.name] = monitor
        self._logger.info(f"Registered monitor: {monitor.name}")

    def unregister_monitor(self, monitor_name: str) -> None:
        """Unregister a monitor from the manager.

        Args:
            monitor_name: Name of the monitor to unregister

        Raises:
            ValueError: If monitor is not found
        """
        if monitor_name not in self.monitors:
            raise ValueError(f"Monitor {monitor_name} not found")

        monitor = self.monitors[monitor_name]
        if monitor.is_running():
            self._logger.warning(
                f"Unregistering running monitor {monitor_name}, stopping it first"
            )
            # Note: Can't await here, caller should stop monitor first
            raise RuntimeError(f"Cannot unregister running monitor {monitor_name}")

        del self.monitors[monitor_name]
        self._logger.info(f"Unregistered monitor: {monitor_name}")

    def get_monitor(self, monitor_name: str) -> Optional[BaseMonitor]:
        """Get a monitor by name.

        Args:
            monitor_name: Name of the monitor

        Returns:
            The monitor instance or None if not found
        """
        return self.monitors.get(monitor_name)

    def list_monitors(self) -> list[str]:
        """List all registered monitor names.

        Returns:
            List of monitor names
        """
        return list(self.monitors.keys())

    async def start_monitor(self, monitor_name: str) -> None:
        """Start a specific monitor.

        Args:
            monitor_name: Name of the monitor to start

        Raises:
            ValueError: If monitor is not found
        """
        monitor = self.monitors.get(monitor_name)
        if not monitor:
            raise ValueError(f"Monitor {monitor_name} not found")

        if monitor.is_running():
            self._logger.warning(f"Monitor {monitor_name} is already running")
            return

        self._logger.info(f"Starting monitor: {monitor_name}")
        await monitor.start_monitoring()

    async def stop_monitor(self, monitor_name: str) -> None:
        """Stop a specific monitor.

        Args:
            monitor_name: Name of the monitor to stop

        Raises:
            ValueError: If monitor is not found
        """
        monitor = self.monitors.get(monitor_name)
        if not monitor:
            raise ValueError(f"Monitor {monitor_name} not found")

        if not monitor.is_running():
            self._logger.warning(f"Monitor {monitor_name} is not running")
            return

        self._logger.info(f"Stopping monitor: {monitor_name}")
        await monitor.stop_monitoring()

    async def start_all(self) -> None:
        """Start all enabled monitors.

        Only monitors with config.enabled=True will be started.
        """
        self._logger.info("Starting all enabled monitors")

        # Start event bus first
        await self.event_bus.start()

        # Start all enabled monitors concurrently
        start_tasks = []
        for monitor_name, monitor in self.monitors.items():
            if monitor.config.enabled:
                self._logger.info(f"Starting {monitor_name}")
                start_tasks.append(monitor.start_monitoring())
            else:
                self._logger.info(f"Skipping disabled monitor: {monitor_name}")

        # Wait for all monitors to start
        if start_tasks:
            await asyncio.gather(*start_tasks, return_exceptions=True)

        self._running = True
        self._logger.info(f"Started {len(start_tasks)} monitors")

    async def stop_all(self) -> None:
        """Stop all running monitors.

        This gracefully stops all monitors and the event bus.
        """
        self._logger.info("Stopping all monitors")

        # Stop all running monitors concurrently
        stop_tasks = []
        for monitor_name, monitor in self.monitors.items():
            if monitor.is_running():
                self._logger.info(f"Stopping {monitor_name}")
                stop_tasks.append(monitor.stop_monitoring())

        # Wait for all monitors to stop
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

        # Stop event bus
        await self.event_bus.stop()

        self._running = False
        self._logger.info(f"Stopped {len(stop_tasks)} monitors")

    def pause_monitor(self, monitor_name: str) -> None:
        """Pause a specific monitor.

        Args:
            monitor_name: Name of the monitor to pause

        Raises:
            ValueError: If monitor is not found
        """
        monitor = self.monitors.get(monitor_name)
        if not monitor:
            raise ValueError(f"Monitor {monitor_name} not found")

        monitor.pause()

    def resume_monitor(self, monitor_name: str) -> None:
        """Resume a paused monitor.

        Args:
            monitor_name: Name of the monitor to resume

        Raises:
            ValueError: If monitor is not found
        """
        monitor = self.monitors.get(monitor_name)
        if not monitor:
            raise ValueError(f"Monitor {monitor_name} not found")

        monitor.resume()

    def pause_all(self) -> None:
        """Pause all running monitors."""
        self._logger.info("Pausing all monitors")
        for monitor in self.monitors.values():
            if monitor.is_running() and not monitor.is_paused():
                monitor.pause()

    def resume_all(self) -> None:
        """Resume all paused monitors."""
        self._logger.info("Resuming all monitors")
        for monitor in self.monitors.values():
            if monitor.is_running() and monitor.is_paused():
                monitor.resume()

    def get_monitor_status(self, monitor_name: str) -> Optional[MonitorStatus]:
        """Get status of a specific monitor.

        Args:
            monitor_name: Name of the monitor

        Returns:
            MonitorStatus object or None if monitor not found
        """
        monitor = self.monitors.get(monitor_name)
        if not monitor:
            return None

        return monitor.get_status()

    def get_all_status(self) -> dict[str, MonitorStatus]:
        """Get status of all monitors.

        Returns:
            Dictionary mapping monitor names to their status
        """
        return {name: monitor.get_status() for name, monitor in self.monitors.items()}

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive status of the monitoring system.

        Returns:
            Dictionary containing system status information
        """
        all_status = self.get_all_status()

        return {
            "manager_running": self._running,
            "total_monitors": len(self.monitors),
            "running_monitors": sum(1 for m in self.monitors.values() if m.is_running()),
            "paused_monitors": sum(1 for m in self.monitors.values() if m.is_paused()),
            "enabled_monitors": sum(1 for m in self.monitors.values() if m.config.enabled),
            "total_events_generated": sum(s.events_generated for s in all_status.values()),
            "total_errors": sum(s.errors for s in all_status.values()),
            "event_bus_stats": self.event_bus.get_stats(),
            "monitors": {name: status.model_dump() for name, status in all_status.items()},
        }

    def is_running(self) -> bool:
        """Check if the monitor manager is running.

        Returns:
            True if running, False otherwise
        """
        return self._running

    async def run_forever(self) -> None:
        """Run the monitoring system indefinitely.

        This method starts all monitors and keeps them running until
        manually stopped or interrupted.
        """
        self._logger.info("Starting monitoring system")
        await self.start_all()

        try:
            # Keep running until interrupted
            while self._running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self._logger.info("Keyboard interrupt received")
        finally:
            await self.stop_all()
