"""
WebSocket router for real-time event streaming.

Provides WebSocket endpoint for real-time updates to the web dashboard.
"""

import logging
import asyncio
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from ..service.engine import HifzDefendEngine
from ..service.events import ServiceEvent
from .dependencies import get_engine

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """
    WebSocket connection manager.

    Manages all active WebSocket connections and broadcasts events to them.
    """

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message dictionary to broadcast
        """
        async with self._lock:
            connections = list(self.active_connections)

        # Send to all connections
        disconnected = []
        for connection in connections:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                else:
                    disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        if disconnected:
            async with self._lock:
                for connection in disconnected:
                    self.active_connections.discard(connection)

    async def send_personal(self, message: dict, websocket: WebSocket) -> None:
        """
        Send a message to a specific client.

        Args:
            message: Message dictionary to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            await self.disconnect(websocket)


# Global connection manager
manager = ConnectionManager()


def event_handler(event: ServiceEvent) -> None:
    """
    Handle service events and broadcast to WebSocket clients.

    This is registered as a global event handler in the engine.

    Args:
        event: Service event to broadcast
    """
    # Convert event to dict for JSON serialization
    message = event.to_dict()

    # Schedule broadcast in event loop
    # Note: This is called from a thread, so we need to be careful
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(manager.broadcast(message))
    except Exception as e:
        logger.error(f"Error broadcasting event: {e}")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):
    """
    WebSocket endpoint for real-time event streaming.

    Clients connect to this endpoint to receive real-time updates about:
    - System status changes
    - Monitor events
    - Scan progress
    - Threat detections
    - Configuration changes

    The connection sends periodic ping messages to keep the connection alive.
    """
    await manager.connect(websocket)

    # Get engine from app state (WebSocket doesn't support Depends injection well)
    engine: HifzDefendEngine = websocket.app.state.engine

    # Register event handler if not already registered
    if event_handler not in engine.events._global_handlers:
        engine.events.subscribe(None, event_handler)
        logger.info("Registered WebSocket event handler")

    try:
        # Send initial system status
        initial_status = engine.get_system_status()
        await manager.send_personal(
            {
                "type": "initial_status",
                "data": initial_status,
            },
            websocket,
        )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (ping/pong, commands, etc.)
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0,  # 30 second timeout
                )

                # Handle client messages
                message_type = data.get("type")

                if message_type == "ping":
                    # Respond to ping
                    await manager.send_personal({"type": "pong"}, websocket)

                elif message_type == "subscribe":
                    # Client can request specific event types
                    # TODO: Implement selective event subscription
                    pass

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await manager.send_personal({"type": "ping"}, websocket)
                except:
                    break

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        await manager.disconnect(websocket)


@router.get("/ws/connections")
async def get_websocket_connections() -> dict:
    """
    Get number of active WebSocket connections.

    Returns:
        Connection count
    """
    return {
        "active_connections": len(manager.active_connections),
    }
