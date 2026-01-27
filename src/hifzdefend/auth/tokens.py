"""JWT token management."""

import secrets
from datetime import datetime, timedelta
from typing import Optional

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class TokenManager:
    """Manage JWT tokens for authentication."""

    def __init__(self, secret_key: Optional[str] = None):
        """Initialize token manager.

        Args:
            secret_key: Secret key for signing tokens
        """
        if not JWT_AVAILABLE:
            raise ImportError("PyJWT not installed. Run: pip install pyjwt")

        self.secret_key = secret_key or self._generate_secret_key()
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(hours=24)
        self.refresh_token_expire = timedelta(days=30)
        self.reset_token_expire = timedelta(hours=1)

    @staticmethod
    def _generate_secret_key() -> str:
        """Generate random secret key.

        Returns:
            Random secret key
        """
        return secrets.token_urlsafe(32)

    def create_access_token(self, user_id: str, email: str) -> str:
        """Create JWT access token.

        Args:
            user_id: User ID
            email: User email

        Returns:
            JWT access token
        """
        expire = datetime.utcnow() + self.access_token_expire

        payload = {
            "sub": user_id,
            "email": email,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token.

        Args:
            user_id: User ID

        Returns:
            JWT refresh token
        """
        expire = datetime.utcnow() + self.refresh_token_expire

        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_reset_token(self, user_id: str, email: str) -> str:
        """Create password reset token.

        Args:
            user_id: User ID
            email: User email

        Returns:
            Reset token
        """
        expire = datetime.utcnow() + self.reset_token_expire

        payload = {
            "sub": user_id,
            "email": email,
            "type": "reset",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_verification_token(self, user_id: str, email: str) -> str:
        """Create email verification token.

        Args:
            user_id: User ID
            email: User email

        Returns:
            Verification token
        """
        expire = datetime.utcnow() + timedelta(days=7)

        payload = {
            "sub": user_id,
            "email": email,
            "type": "verification",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, token_type: Optional[str] = None) -> Optional[dict]:
        """Verify and decode JWT token.

        Args:
            token: JWT token
            token_type: Expected token type (access, refresh, reset, verification)

        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check token type if specified
            if token_type and payload.get("type") != token_type:
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_user_from_token(self, token: str) -> Optional[str]:
        """Extract user ID from token.

        Args:
            token: JWT token

        Returns:
            User ID or None
        """
        payload = self.verify_token(token, token_type="access")
        return payload.get("sub") if payload else None
