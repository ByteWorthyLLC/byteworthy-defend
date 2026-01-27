"""
HifzDefend FastAPI Web Server

This module provides the REST API and WebSocket server for the web dashboard
and serves as the IPC mechanism for communication between service components.
"""

from .main import create_app

__all__ = ["create_app"]
