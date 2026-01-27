"""User authentication and account management."""

import hashlib
import json
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.config import get_app_data_dir
from .models import User, UserCreate, UserLogin
from .tokens import TokenManager


class AuthManager:
    """Manage user authentication and accounts."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize auth manager.

        Args:
            data_dir: Directory for user data storage
        """
        self.data_dir = data_dir or get_app_data_dir() / "users"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.users_file = self.data_dir / "users.json"
        self.token_manager = TokenManager()

        # Initialize users file
        if not self.users_file.exists():
            self._save_users({})

    def _load_users(self) -> dict:
        """Load users from disk.

        Returns:
            Users dictionary
        """
        try:
            with open(self.users_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_users(self, users: dict) -> None:
        """Save users to disk.

        Args:
            users: Users dictionary
        """
        with open(self.users_file, "w") as f:
            json.dump(users, f, indent=2, default=str)

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA256.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        # In production, use bcrypt or argon2
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}${hashed}"

    @staticmethod
    def _verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash.

        Args:
            password: Plain text password
            hashed: Hashed password

        Returns:
            Whether password matches
        """
        try:
            salt, hash_value = hashed.split("$")
            computed = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed == hash_value
        except Exception:
            return False

    def register_user(self, user_create: UserCreate) -> User:
        """Register new user.

        Args:
            user_create: User registration data

        Returns:
            Created user

        Raises:
            ValueError: If email already exists
        """
        users = self._load_users()

        # Check if email exists
        if any(u["email"] == user_create.email for u in users.values()):
            raise ValueError("Email already registered")

        # Create user
        user_id = secrets.token_urlsafe(16)
        password_hash = self._hash_password(user_create.password)

        user_data = {
            "id": user_id,
            "email": user_create.email,
            "full_name": user_create.full_name,
            "company_name": user_create.company_name,
            "password_hash": password_hash,
            "email_verified": False,
            "is_active": True,
            "is_admin": False,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None,
            "metadata": {},
        }

        users[user_id] = user_data
        self._save_users(users)

        # Return user (without password)
        user_data_clean = {k: v for k, v in user_data.items() if k != "password_hash"}
        return User(**user_data_clean)

    def authenticate_user(self, credentials: UserLogin) -> Optional[tuple[User, str, str]]:
        """Authenticate user and generate tokens.

        Args:
            credentials: Login credentials

        Returns:
            Tuple of (user, access_token, refresh_token) or None
        """
        users = self._load_users()

        # Find user by email
        user_data = None
        for user in users.values():
            if user["email"] == credentials.email:
                user_data = user
                break

        if not user_data:
            return None

        # Verify password
        if not self._verify_password(credentials.password, user_data["password_hash"]):
            return None

        # Check if account is active
        if not user_data.get("is_active", True):
            return None

        # Update last login
        user_data["last_login"] = datetime.utcnow().isoformat()
        users[user_data["id"]] = user_data
        self._save_users(users)

        # Generate tokens
        access_token = self.token_manager.create_access_token(
            user_data["id"],
            user_data["email"]
        )
        refresh_token = self.token_manager.create_refresh_token(user_data["id"])

        # Return user (without password)
        user_data_clean = {k: v for k, v in user_data.items() if k != "password_hash"}
        return User(**user_data_clean), access_token, refresh_token

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User or None
        """
        users = self._load_users()
        user_data = users.get(user_id)

        if not user_data:
            return None

        user_data_clean = {k: v for k, v in user_data.items() if k != "password_hash"}
        return User(**user_data_clean)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User or None
        """
        users = self._load_users()

        for user_data in users.values():
            if user_data["email"] == email:
                user_data_clean = {k: v for k, v in user_data.items() if k != "password_hash"}
                return User(**user_data_clean)

        return None

    def update_user(self, user_id: str, updates: dict) -> Optional[User]:
        """Update user profile.

        Args:
            user_id: User ID
            updates: Fields to update

        Returns:
            Updated user or None
        """
        users = self._load_users()
        user_data = users.get(user_id)

        if not user_data:
            return None

        # Update allowed fields
        allowed_fields = {"full_name", "company_name", "metadata"}
        for key, value in updates.items():
            if key in allowed_fields:
                user_data[key] = value

        users[user_id] = user_data
        self._save_users(users)

        user_data_clean = {k: v for k, v in user_data.items() if k != "password_hash"}
        return User(**user_data_clean)

    def verify_email(self, user_id: str) -> bool:
        """Mark user email as verified.

        Args:
            user_id: User ID

        Returns:
            Success status
        """
        users = self._load_users()
        user_data = users.get(user_id)

        if not user_data:
            return False

        user_data["email_verified"] = True
        users[user_id] = user_data
        self._save_users(users)

        return True

    def reset_password(self, user_id: str, new_password: str) -> bool:
        """Reset user password.

        Args:
            user_id: User ID
            new_password: New password

        Returns:
            Success status
        """
        users = self._load_users()
        user_data = users.get(user_id)

        if not user_data:
            return False

        user_data["password_hash"] = self._hash_password(new_password)
        users[user_id] = user_data
        self._save_users(users)

        return True

    def get_current_user_from_token(self, token: str) -> Optional[User]:
        """Get current user from access token.

        Args:
            token: JWT access token

        Returns:
            User or None
        """
        user_id = self.token_manager.get_user_from_token(token)
        return self.get_user_by_id(user_id) if user_id else None
