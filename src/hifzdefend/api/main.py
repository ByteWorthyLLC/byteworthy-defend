"""Main FastAPI application."""

import json
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .models import ErrorResponse, HealthResponse
from .routers import config, quarantine, scans, stats

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and store connection."""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove connection."""
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)

        # Remove disconnected clients
        self.active_connections -= disconnected


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle handler."""
    # Startup
    print("HifzDefend API starting...")
    yield
    # Shutdown
    print("HifzDefend API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="HifzDefend API",
    description="Antivirus web application API",
    version="0.2.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scans.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(quarantine.router, prefix="/api")
app.include_router(config.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        from ...core.scanner import ClamAVScanner
        from ...config.loader import load_config

        config = load_config()
        scanner = ClamAVScanner(
            host=config.clamav.host,
            port=config.clamav.port,
            timeout=5
        )
        scanner.ping()
        clamav_connected = True
    except:
        clamav_connected = False

    return HealthResponse(
        status="healthy",
        version="0.2.0",
        clamav_connected=clamav_connected
    )


@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()

            # Echo back for now (could handle client commands)
            await websocket.send_json({
                "event_type": "echo",
                "payload": {"message": data}
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="Not Found",
            detail=str(exc.detail) if hasattr(exc, "detail") else "Resource not found",
            code="NOT_FOUND"
        ).dict()
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred",
            code="INTERNAL_ERROR"
        ).dict()
    )


# Helper function to broadcast scan progress
async def broadcast_scan_progress(scan_id: str, files_scanned: int, current_file: str, percentage: float):
    """Broadcast scan progress to all connected clients."""
    await manager.broadcast({
        "event_type": "scan_progress",
        "payload": {
            "scan_id": scan_id,
            "files_scanned": files_scanned,
            "current_file": current_file,
            "percentage": percentage
        }
    })


# Helper function to broadcast threat detection
async def broadcast_threat_detected(scan_id: str, file_path: str, threat_name: str):
    """Broadcast threat detection to all connected clients."""
    await manager.broadcast({
        "event_type": "threat_detected",
        "payload": {
            "scan_id": scan_id,
            "file_path": file_path,
            "threat_name": threat_name
        }
    })
