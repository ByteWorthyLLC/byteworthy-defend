"""Base monitor class for HifzDefend security monitors.

All security monitors inherit from BaseMonitor, which provides a standardized
interface for lifecycle management, event publishing, and configuration.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from .event_bus import EventBus, get_event_bus
from .events import Event, EventSeverity, EventType, MonitoringEvent


class MonitorConfig(BaseModel):
    """Base configuration for monitors.

    All monitor configurations should inherit from this class.
    """

    enabled: bool = Field(
        default=True,
        description="Whether this monitor is enabled",
    )
    check_interval: int = Field(
        default=60,
        ge=1,
        description="How often to run checks (in seconds)",
    )


class MonitorStatus(BaseModel):
    """Status information for a monitor."""

    name: str = Field(description="Monitor name")
    enabled: bool = Field(description="Whether monitor is enabled")
    running: bool = Field(description="Whether monitor is currently running")
    last_check: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last check",
    )
    events_generated: int = Field(
        default=0,
        description="Total number of events generated",
    )
    errors: int = Field(
        default=0,
        description="Number of errors encountered",
    )
    status_message: str = Field(
        default="",
        description="Current status message",
    )


class BaseMonitor(ABC):
    """Abstract base class for all security monitors.

    All monitors must implement:
    - start(): Initialize and start monitoring
    - stop(): Gracefully stop monitoring
    - check(): Perform a single check and return events

    Monitors automatically publish events to the EventBus and manage
    their own lifecycle through the MonitorManager.

    Example:
        ```python
        class MyMonitor(BaseMonitor):
            async def start(self) -> None:
                self._logger.info("Starting MyMonitor")
                self._running = True

            async def stop(self) -> None:
                self._logger.info("Stopping MyMonitor")
                self._running = False

            async def check(self) -> list[Event]:
                # Perform security check
                events = []
                if self._detect_threat():
                    events.append(Event(
                        event_type=EventType.THREAT_DETECTED,
                        severity=EventSeverity.WARNING,
                        source_monitor=self.name,
                        threat_score=75,
                        description="Threat detected"
                    ))
                return events
        ```
    """

    def __init__(
        self,
        config: MonitorConfig,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """Initialize the monitor.

        Args:
            config: Monitor configuration
            event_bus: EventBus instance (optional, uses global singleton if not provided)
        """
        self.config = config
        self.event_bus = event_bus or get_event_bus()
        self.name = self.__class__.__name__
        self._running = False
        self._paused = False
        self._logger = logging.getLogger(f"hifzdefend.monitoring.{self.name}")

        # Statistics
        self._events_generated = 0
        self._errors = 0
        self._last_check: Optional[datetime] = None
        self._status_message = "Initialized"

        # Background task for periodic checks
        self._check_task: Optional[asyncio.Task[None]] = None

        self._logger.debug(f"{self.name} initialized")

    @abstractmethod
    async def start(self) -> None:
        """Start the monitor.

        This method should initialize any resources needed for monitoring
        and set self._running = True.

        Raises:
            Exception: If monitor fails to start
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the monitor.

        This method should clean up resources and set self._running = False.
        """
        pass

    @abstractmethod
    async def check(self) -> list[Event]:
        """Perform a single monitoring check.

        This method should:
        1. Perform the security check
        2. Generate events for any threats detected
        3. Return the list of events

        Returns:
            List of events generated during this check

        Raises:
            Exception: If check fails
        """
        pass

    async def run(self) -> None:
        """Run the monitor continuously with periodic checks.

        This method runs in the background and calls check() at regular intervals
        defined by config.check_interval.
        """
        self._logger.info(f"{self.name} starting periodic checks every {self.config.check_interval}s")

        while self._running:
            try:
                # Skip check if paused
                if self._paused:
                    await asyncio.sleep(1)
                    continue

                # Perform check
                events = await self.check()
                self._last_check = datetime.now()

                # Publish all events
                for event in events:
                    self.publish_event(event)

                # Update statistics
                self._events_generated += len(events)

                if events:
                    self._logger.debug(f"{self.name} generated {len(events)} events")

                # Wait for next check interval
                await asyncio.sleep(self.config.check_interval)

            except asyncio.CancelledError:
                self._logger.info(f"{self.name} check task cancelled")
                break
            except Exception as e:
                self._errors += 1
                self._status_message = f"Error: {str(e)}"
                self._logger.error(f"{self.name} check failed: {e}", exc_info=True)

                # Publish error event
                self.publish_event(
                    MonitoringEvent(
                        event_type=EventType.MONITOR_ERROR,
                        severity=EventSeverity.WARNING,
                        source_monitor=self.name,
                        threat_score=0,
                        description=f"Monitor error: {str(e)}",
                        data={"error": str(e)},
                    )
                )

                # Wait before retrying
                await asyncio.sleep(self.config.check_interval)

        self._logger.info(f"{self.name} periodic checks stopped")

    def publish_event(self, event: Event) -> None:
        """Publish an event to the event bus.

        This is a convenience method for monitors to publish events.

        Args:
            event: Event to publish
        """
        # Ensure source_monitor is set correctly
        if not event.source_monitor or event.source_monitor == "":
            # Create a new event with the correct source monitor
            event_dict = event.model_dump()
            event_dict["source_monitor"] = self.name
            event = event.__class__(**event_dict)

        self.event_bus.publish(event)

    async def start_monitoring(self) -> None:
        """Start the monitor and begin periodic checks.

        This method calls start() and then runs the monitoring loop in the background.
        """
        if not self.config.enabled:
            self._logger.info(f"{self.name} is disabled, not starting")
            return

        if self._running:
            self._logger.warning(f"{self.name} is already running")
            return

        # Start the monitor
        await self.start()

        # Publish monitor started event
        self.publish_event(
            MonitoringEvent(
                event_type=EventType.MONITOR_STARTED,
                severity=EventSeverity.INFO,
                source_monitor=self.name,
                threat_score=0,
                description=f"{self.name} started",
            )
        )

        # Start background check task
        self._check_task = asyncio.create_task(self.run())
        self._status_message = "Running"

    async def stop_monitoring(self) -> None:
        """Stop the monitor and cancel periodic checks."""
        if not self._running:
            self._logger.warning(f"{self.name} is not running")
            return

        self._logger.info(f"{self.name} stopping")

        # Cancel background task
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
            self._check_task = None

        # Stop the monitor
        await self.stop()

        # Publish monitor stopped event
        self.publish_event(
            MonitoringEvent(
                event_type=EventType.MONITOR_STOPPED,
                severity=EventSeverity.INFO,
                source_monitor=self.name,
                threat_score=0,
                description=f"{self.name} stopped",
            )
        )

        self._status_message = "Stopped"

    def pause(self) -> None:
        """Pause monitoring checks.

        The monitor continues running but doesn't perform checks.
        """
        if not self._running:
            self._logger.warning(f"{self.name} is not running")
            return

        self._paused = True
        self._status_message = "Paused"
        self._logger.info(f"{self.name} paused")

    def resume(self) -> None:
        """Resume monitoring checks after pause."""
        if not self._running:
            self._logger.warning(f"{self.name} is not running")
            return

        self._paused = False
        self._status_message = "Running"
        self._logger.info(f"{self.name} resumed")

    def get_status(self) -> MonitorStatus:
        """Get current monitor status.

        Returns:
            MonitorStatus object with current status information
        """
        return MonitorStatus(
            name=self.name,
            enabled=self.config.enabled,
            running=self._running,
            last_check=self._last_check,
            events_generated=self._events_generated,
            errors=self._errors,
            status_message=self._status_message,
        )

    def is_running(self) -> bool:
        """Check if monitor is currently running.

        Returns:
            True if running, False otherwise
        """
        return self._running

    def is_paused(self) -> bool:
        """Check if monitor is currently paused.

        Returns:
            True if paused, False otherwise
        """
        return self._paused
