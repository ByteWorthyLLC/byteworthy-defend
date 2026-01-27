"""
FastAPI dependencies for authentication and shared resources.

This module provides dependency injection for authentication, rate limiting,
and access to the HifzDefend engine.
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets

from ..service.engine import HifzDefendEngine
from ..licensing.manager import LicenseManager
from ..auth.manager import AuthManager

logger = logging.getLogger(__name__)

# Global license manager instance
_license_manager: Optional[LicenseManager] = None

# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_license_manager() -> LicenseManager:
    """Get the global license manager instance.

    Returns:
        License manager
    """
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager


def get_auth_manager() -> AuthManager:
    """Get the global auth manager instance.

    Returns:
        Auth manager
    """
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager

# Security scheme for authentication
security = HTTPBearer(auto_error=False)

# Simple token-based authentication (will be replaced with proper auth later)
# In production, this should be stored securely and generated per-installation
API_TOKEN: Optional[str] = None


def set_api_token(token: str) -> None:
    """
    Set the API authentication token.

    Args:
        token: API token for authentication
    """
    global API_TOKEN
    API_TOKEN = token
    logger.info("API token configured")


def generate_api_token() -> str:
    """
    Generate a random API token.

    Returns:
        Random API token
    """
    return secrets.token_urlsafe(32)


def get_engine(request: Request) -> HifzDefendEngine:
    """
    Get HifzDefend engine from request state.

    Args:
        request: FastAPI request

    Returns:
        HifzDefend engine instance
    """
    return request.app.state.engine


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> bool:
    """
    Verify API token for authentication.

    Args:
        credentials: HTTP bearer credentials

    Returns:
        True if authenticated

    Raises:
        HTTPException: If authentication fails
    """
    # If no token is set, allow access (localhost-only mode)
    if API_TOKEN is None:
        return True

    # Check credentials
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    if credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True


async def check_localhost(request: Request) -> bool:
    """
    Check if request is from localhost.

    Args:
        request: FastAPI request

    Returns:
        True if from localhost

    Raises:
        HTTPException: If not from localhost when required
    """
    client_host = request.client.host if request.client else None

    # Allow localhost connections
    if client_host in ["127.0.0.1", "::1", "localhost"]:
        return True

    # If API token is set, allow authenticated requests from any host
    if API_TOKEN is not None:
        return True

    # Otherwise, reject non-localhost connections
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: Only localhost connections are allowed",
    )


# Combined dependency for protected endpoints
async def authenticate(
    _localhost: bool = Depends(check_localhost),
    _auth: bool = Depends(verify_token),
) -> bool:
    """
    Combined authentication dependency.

    Checks both localhost requirement and token authentication.
    """
    return True
