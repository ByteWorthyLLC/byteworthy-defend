"""Authentication data models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """User registration request."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    full_name: Optional[str] = Field(None, description="Full name")
    company_name: Optional[str] = Field(None, description="Company name")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Password")


class User(BaseModel):
    """User model."""

    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    company_name: Optional[str] = Field(None, description="Company name")

    # Account status
    email_verified: bool = Field(default=False, description="Email verification status")
    is_active: bool = Field(default=True, description="Account active status")
    is_admin: bool = Field(default=False, description="Admin privileges")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    # Metadata
    metadata: dict = Field(default_factory=dict)

    class Config:
        """Pydantic config."""
        from_attributes = True


class UserProfile(BaseModel):
    """User profile (public info)."""

    id: str
    email: EmailStr
    full_name: Optional[str]
    company_name: Optional[str]
    email_verified: bool
    created_at: datetime
    license_count: int = Field(default=0, description="Number of active licenses")


class UserUpdate(BaseModel):
    """User profile update request."""

    full_name: Optional[str] = None
    company_name: Optional[str] = None


class PasswordReset(BaseModel):
    """Password reset request."""

    email: EmailStr = Field(..., description="User email")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""

    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class EmailVerification(BaseModel):
    """Email verification request."""

    token: str = Field(..., description="Verification token")
