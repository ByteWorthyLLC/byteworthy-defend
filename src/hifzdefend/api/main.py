"""
FastAPI application for HifzDefend web server.

This provides the REST API and WebSocket endpoints for the web dashboard,
system tray, and other clients.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from ..service.engine import HifzDefendEngine
from .routers import dashboard, scanning, monitoring, quarantine, config as config_router, licensing
from .websocket import router as websocket_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    FastAPI lifespan context manager.

    Handles startup and shutdown of the HifzDefend engine.
    """
    logger.info("Starting HifzDefend API server")

    # Engine is created but not started (Windows service will start it)
    # The API just provides access to the engine
    logger.info("HifzDefend API server ready")

    yield

    logger.info("Shutting down HifzDefend API server")


def create_app(engine: HifzDefendEngine) -> FastAPI:
    """
    Create and configure FastAPI application.

    Args:
        engine: HifzDefend engine instance

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="HifzDefend API",
        description="HifzDefend Antivirus REST API and WebSocket Server",
        version="0.3.0",
        lifespan=lifespan,
    )

    # Store engine in app state for access by routers
    app.state.engine = engine

    # Configure CORS for localhost
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # React dev server
            "http://localhost:8080",  # Production web UI
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(
        dashboard.router,
        prefix="/api/v1/dashboard",
        tags=["dashboard"],
    )
    app.include_router(
        scanning.router,
        prefix="/api/v1/scan",
        tags=["scanning"],
    )
    app.include_router(
        monitoring.router,
        prefix="/api/v1/monitors",
        tags=["monitoring"],
    )
    app.include_router(
        quarantine.router,
        prefix="/api/v1/quarantine",
        tags=["quarantine"],
    )
    app.include_router(
        config_router.router,
        prefix="/api/v1/config",
        tags=["configuration"],
    )
    app.include_router(
        licensing.router,
        prefix="/api/v1",
        tags=["licensing"],
    )
    app.include_router(
        websocket_router,
        prefix="/api/v1",
        tags=["websocket"],
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "HifzDefend API",
            "version": "0.3.0",
        }

    @app.get("/api/v1/status")
    async def get_status():
        """Get system status."""
        engine: HifzDefendEngine = app.state.engine
        return engine.get_system_status()

    # Serve static files (frontend) if directory exists
    static_dir = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
        logger.info(f"Serving static files from {static_dir}")

    return app
