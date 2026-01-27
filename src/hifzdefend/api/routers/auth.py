"""Authentication API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

from ...auth import AuthManager, UserCreate, UserLogin, UserProfile, UserUpdate
from ...auth import PasswordReset, PasswordResetConfirm, EmailVerification
from ..dependencies import get_auth_manager

router = APIRouter(prefix="/auth", tags=["authentication"])


class TokenResponse(BaseModel):
    """Token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserProfile


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


@router.post("/register", response_model=UserProfile)
async def register(
    user_create: UserCreate,
    manager: AuthManager = Depends(get_auth_manager)
) -> UserProfile:
    """Register new user account.

    Args:
        user_create: Registration data
        manager: Auth manager

    Returns:
        Created user profile
    """
    try:
        user = manager.register_user(user_create)

        # Send verification email (stub)
        # verification_token = manager.token_manager.create_verification_token(user.id, user.email)
        # await send_verification_email(user.email, verification_token)

        return UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            company_name=user.company_name,
            email_verified=user.email_verified,
            created_at=user.created_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    manager: AuthManager = Depends(get_auth_manager)
) -> TokenResponse:
    """Login user and get access tokens.

    Args:
        credentials: Login credentials
        manager: Auth manager

    Returns:
        Access and refresh tokens
    """
    result = manager.authenticate_user(credentials)

    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    user, access_token, refresh_token = result

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            company_name=user.company_name,
            email_verified=user.email_verified,
            created_at=user.created_at,
        )
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user(
    authorization: str = Header(None),
    manager: AuthManager = Depends(get_auth_manager)
) -> UserProfile:
    """Get current user profile.

    Args:
        authorization: Authorization header (Bearer token)
        manager: Auth manager

    Returns:
        Current user profile
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = authorization.replace("Bearer ", "")
    user = manager.get_current_user_from_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        company_name=user.company_name,
        email_verified=user.email_verified,
        created_at=user.created_at,
    )


@router.put("/me", response_model=UserProfile)
async def update_profile(
    updates: UserUpdate,
    authorization: str = Header(None),
    manager: AuthManager = Depends(get_auth_manager)
) -> UserProfile:
    """Update current user profile.

    Args:
        updates: Profile updates
        authorization: Authorization header
        manager: Auth manager

    Returns:
        Updated user profile
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = authorization.replace("Bearer ", "")
    user = manager.get_current_user_from_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    updated_user = manager.update_user(user.id, updates.dict(exclude_unset=True))

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfile(
        id=updated_user.id,
        email=updated_user.email,
        full_name=updated_user.full_name,
        company_name=updated_user.company_name,
        email_verified=updated_user.email_verified,
        created_at=updated_user.created_at,
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verification: EmailVerification,
    manager: AuthManager = Depends(get_auth_manager)
) -> MessageResponse:
    """Verify user email address.

    Args:
        verification: Verification token
        manager: Auth manager

    Returns:
        Success message
    """
    # Verify token
    payload = manager.token_manager.verify_token(verification.token, token_type="verification")

    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user_id = payload.get("sub")
    success = manager.verify_email(user_id)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return MessageResponse(message="Email verified successfully")


@router.post("/reset-password", response_model=MessageResponse)
async def request_password_reset(
    request: PasswordReset,
    manager: AuthManager = Depends(get_auth_manager)
) -> MessageResponse:
    """Request password reset email.

    Args:
        request: Password reset request
        manager: Auth manager

    Returns:
        Success message
    """
    user = manager.get_user_by_email(request.email)

    if user:
        # Generate reset token
        reset_token = manager.token_manager.create_reset_token(user.id, user.email)

        # Send reset email (stub)
        # await send_password_reset_email(user.email, reset_token)
        pass

    # Always return success to prevent email enumeration
    return MessageResponse(
        message="If that email exists, a password reset link has been sent"
    )


@router.post("/reset-password/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    confirm: PasswordResetConfirm,
    manager: AuthManager = Depends(get_auth_manager)
) -> MessageResponse:
    """Confirm password reset with token.

    Args:
        confirm: Password reset confirmation
        manager: Auth manager

    Returns:
        Success message
    """
    # Verify token
    payload = manager.token_manager.verify_token(confirm.token, token_type="reset")

    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user_id = payload.get("sub")
    success = manager.reset_password(user_id, confirm.new_password)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return MessageResponse(message="Password reset successfully")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    manager: AuthManager = Depends(get_auth_manager)
) -> TokenResponse:
    """Refresh access token.

    Args:
        refresh_token: Refresh token
        manager: Auth manager

    Returns:
        New access and refresh tokens
    """
    # Verify refresh token
    payload = manager.token_manager.verify_token(refresh_token, token_type="refresh")

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    user = manager.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate new tokens
    new_access_token = manager.token_manager.create_access_token(user.id, user.email)
    new_refresh_token = manager.token_manager.create_refresh_token(user.id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            company_name=user.company_name,
            email_verified=user.email_verified,
            created_at=user.created_at,
        )
    )
