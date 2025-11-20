"""
Authentication routes for Wave 5 enterprise features.

Provides JWT-based authentication endpoints including registration,
login, token refresh, and password reset.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from ..database import get_db
from ..models.schemas import (
    UserRegistrationRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserResponse,
)
from ..services.auth_service import (
    AuthService,
    get_current_user_jwt,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user.

    Creates a new user account with the provided credentials and returns
    access and refresh tokens.

    - **email**: User email address (must be unique)
    - **password**: User password (min 8 characters)
    - **full_name**: Optional full name
    - **username**: Optional username (must be unique if provided)

    Returns tokens and user information.
    """
    # Create user (default role is viewer)
    user = AuthService.register_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        username=user_data.username,
        role="viewer",  # Default role for new users
        db=db
    )

    # Generate tokens
    access_token = AuthService.create_access_token(data={"sub": user.id})
    refresh_token = AuthService.create_refresh_token(data={"sub": user.id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.

    Authenticates a user and returns access and refresh tokens.

    - **email**: User email address
    - **password**: User password

    Returns tokens and user information.
    """
    user = AuthService.authenticate_user(
        email=credentials.email,
        password=credentials.password,
        db=db
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Generate tokens
    access_token = AuthService.create_access_token(data={"sub": user.id})
    refresh_token = AuthService.create_refresh_token(data={"sub": user.id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token.

    Exchanges a valid refresh token for a new access token and refresh token.

    - **refresh_token**: Valid refresh token

    Returns new tokens and user information.
    """
    # Verify refresh token
    payload = AuthService.verify_token(refresh_data.refresh_token, token_type="refresh")
    user_id: str = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Get user
    from ..models.database import User
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Generate new tokens
    access_token = AuthService.create_access_token(data={"sub": user.id})
    new_refresh_token = AuthService.create_refresh_token(data={"sub": user.id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user_jwt)
):
    """
    Get current user information.

    Returns the profile information for the currently authenticated user.

    Requires: Bearer token in Authorization header
    """
    return UserResponse.model_validate(current_user)


@router.post("/password-reset/request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset.

    Generates a password reset token for the user. In production, this would
    send an email with the reset link.

    - **email**: User email address

    Returns success message (always returns success to prevent email enumeration).
    """
    from ..models.database import User
    user = db.query(User).filter(User.email == reset_request.email).first()

    if user:
        reset_token = AuthService.generate_reset_token(user, db)
        # TODO: Send email with reset link containing reset_token
        # For now, we just return success (in production, always return success
        # to prevent email enumeration attacks)

    return {
        "message": "If the email exists, a password reset link has been sent",
        "detail": "Check your email for reset instructions"
    }


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset.

    Resets the user's password using a valid reset token.

    - **reset_token**: Password reset token from email
    - **new_password**: New password (min 8 characters)

    Returns success message.
    """
    success = AuthService.reset_password(
        reset_token=reset_data.reset_token,
        new_password=reset_data.new_password,
        db=db
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    return {
        "message": "Password has been reset successfully",
        "detail": "You can now login with your new password"
    }


@router.post("/logout")
async def logout(current_user = Depends(get_current_user_jwt)):
    """
    Logout current user.

    Note: Since we're using stateless JWT tokens, actual logout is handled
    client-side by discarding the tokens. This endpoint is provided for
    consistency and future token blacklisting if needed.

    Requires: Bearer token in Authorization header
    """
    # TODO: Implement token blacklisting in Redis for true server-side logout
    return {
        "message": "Logged out successfully",
        "detail": "Please discard your access and refresh tokens"
    }
