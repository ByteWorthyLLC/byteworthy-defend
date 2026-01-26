"""Event Bus for centralized event management in HifzDefend.

The EventBus implements a publish-subscribe pattern for monitor communication.
It provides asynchronous event processing, priority queuing, and event persistence
for audit trails.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional

from .events import Event, EventSeverity, EventType

logger = logging.getLogger(__name__)


class EventBus:
    """Central event bus for monitor communication.

    The EventBus manages event publication, subscription, and processing.
    It supports:
    - Asynchronous event processing
    - Multiple subscribers per event type
    - Priority-based event queue
    - Event persistence for audit trails
    - Rate limiting to prevent event storms

    Example:
        ```python
        bus = EventBus()

        def handle_threat(event: Event):
            print(f"Threat detected: {event.description}")

        bus.subscribe(EventType.THREAT_DETECTED, handle_threat)

        event = Event(
            event_type=EventType.THREAT_DETECTED,
            severity=EventSeverity.CRITICAL,
            source_monitor="TestMonitor",
            threat_score=90,
            description="Test threat"
        )

        bus.publish(event)
        await bus.process_events()
        ```
    """

    _instance: Optional["EventBus"] = None
    _initialized: bool = False

    def __new__(cls) -> "EventBus":
        """Singleton pattern - only one EventBus instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        max_queue_size: int = 1000,
        event_retention_days: int = 30,
        max_events_per_minute: int = 100,
    ) -> None:
        """Initialize the EventBus.

        Args:
            max_queue_size: Maximum number of events in queue before blocking
            event_retention_days: How long to keep events in persistence store
            max_events_per_minute: Rate limit for event processing
        """
        # Only initialize once (singleton pattern)
        if EventBus._initialized:
            return

        self._subscribers: dict[EventType, list[Callable[[Event], None]]] = defaultdict(list)
        self._event_queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=max_queue_size)
        self._logger = logging.getLogger(__name__)
        self._running = False
        self._worker_task: Optional[asyncio.Task[None]] = None

        # Configuration
        self._max_queue_size = max_queue_size
        self._event_retention_days = event_retention_days
        self._max_events_per_minute = max_events_per_minute

        # Event storage for audit trail
        self._event_history: list[Event] = []
        self._event_counts: dict[EventType, int] = defaultdict(int)

        # Rate limiting
        self._recent_events: list[datetime] = []
        self._rate_limit_window = timedelta(minutes=1)

        EventBus._initialized = True
        self._logger.info("EventBus initialized")

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: The type of events to subscribe to
            callback: Function to call when event is published
        """
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            self._logger.debug(f"Subscribed {callback.__name__} to {event_type.value}")

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Unsubscribe from events of a specific type.

        Args:
            event_type: The type of events to unsubscribe from
            callback: The callback function to remove
        """
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            self._logger.debug(f"Unsubscribed {callback.__name__} from {event_type.value}")

    def publish(self, event: Event) -> None:
        """Publish an event to the bus.

        The event is added to the queue for asynchronous processing.
        Rate limiting is applied to prevent event storms.

        Args:
            event: The event to publish

        Raises:
            RuntimeError: If event queue is full
        """
        # Rate limiting check
        if self._is_rate_limited():
            self._logger.warning(
                f"Rate limit exceeded, dropping event: {event.event_type.value}"
            )
            return

        try:
            # Try to add to queue without blocking
            self._event_queue.put_nowait(event)
            self._event_counts[event.event_type] += 1
            self._recent_events.append(datetime.now())

            self._logger.debug(
                f"Event published: {event.event_type.value} "
                f"(severity={event.severity.value}, score={event.threat_score})"
            )
        except asyncio.QueueFull:
            self._logger.error(
                f"Event queue full ({self._max_queue_size}), "
                f"dropping event: {event.event_type.value}"
            )

    def _is_rate_limited(self) -> bool:
        """Check if we're exceeding the rate limit.

        Returns:
            True if rate limited, False otherwise
        """
        # Clean up old events outside the time window
        cutoff = datetime.now() - self._rate_limit_window
        self._recent_events = [e for e in self._recent_events if e > cutoff]

        # Check if we're over the limit
        return len(self._recent_events) >= self._max_events_per_minute

    async def process_events(self) -> None:
        """Process events from the queue.

        This method runs continuously, pulling events from the queue
        and notifying all subscribers. It should be run as an async task.
        """
        self._running = True
        self._logger.info("EventBus event processor started")

        while self._running:
            try:
                # Wait for event with timeout to allow graceful shutdown
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)

                # Store in history (with size limit)
                self._store_event(event)

                # Notify all subscribers for this event type
                callbacks = self._subscribers.get(event.event_type, [])
                for callback in callbacks:
                    try:
                        # Execute callback (synchronous)
                        callback(event)
                    except Exception as e:
                        self._logger.error(
                            f"Error in event callback {callback.__name__}: {e}",
                            exc_info=True,
                        )

                # Mark task as done
                self._event_queue.task_done()

            except asyncio.TimeoutError:
                # No events in queue, continue loop
                continue
            except Exception as e:
                self._logger.error(f"Error processing event: {e}", exc_info=True)

        self._logger.info("EventBus event processor stopped")

    def _store_event(self, event: Event) -> None:
        """Store event in history for audit trail.

        Args:
            event: Event to store
        """
        self._event_history.append(event)

        # Limit history size (keep last 10000 events)
        if len(self._event_history) > 10000:
            self._event_history = self._event_history[-10000:]

    async def start(self) -> None:
        """Start the event bus worker.

        This starts the background task that processes events.
        """
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self.process_events())
            self._logger.info("EventBus worker started")

    async def stop(self) -> None:
        """Stop the event bus worker.

        This stops the background event processing task gracefully.
        """
        self._running = False

        if self._worker_task:
            await self._worker_task
            self._worker_task = None

        self._logger.info("EventBus worker stopped")

    def get_event_history(
        self,
        event_type: Optional[EventType] = None,
        severity: Optional[EventSeverity] = None,
        limit: int = 100,
    ) -> list[Event]:
        """Get event history with optional filtering.

        Args:
            event_type: Filter by event type
            severity: Filter by severity
            limit: Maximum number of events to return

        Returns:
            List of events matching the criteria
        """
        events = self._event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if severity:
            events = [e for e in events if e.severity == severity]

        # Return most recent events first
        return list(reversed(events[-limit:]))

    def get_event_counts(self) -> dict[EventType, int]:
        """Get counts of events by type.

        Returns:
            Dictionary mapping event types to their counts
        """
        return dict(self._event_counts)

    def clear_history(self) -> None:
        """Clear all event history.

        This is useful for testing or after exporting events to persistent storage.
        """
        self._event_history.clear()
        self._event_counts.clear()
        self._recent_events.clear()
        self._logger.info("Event history cleared")

    def get_queue_size(self) -> int:
        """Get current size of event queue.

        Returns:
            Number of events waiting to be processed
        """
        return self._event_queue.qsize()

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the event bus.

        Returns:
            Dictionary containing event bus statistics
        """
        return {
            "running": self._running,
            "queue_size": self.get_queue_size(),
            "max_queue_size": self._max_queue_size,
            "total_events_processed": sum(self._event_counts.values()),
            "events_by_type": {k.value: v for k, v in self._event_counts.items()},
            "history_size": len(self._event_history),
            "recent_events_count": len(self._recent_events),
            "rate_limited": self._is_rate_limited(),
        }


# Global singleton instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global EventBus singleton instance.

    Returns:
        The global EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
