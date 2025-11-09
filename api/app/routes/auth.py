"""
Authentication routes for user registration, login, and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.database import User
from ..models.schemas import (
    UserRegister, UserLogin, Token, TokenRefresh,
    UserProfileResponse, UserUpdate, PasswordChange,
    UserResponse
)
from ..auth import (
    hash_password, verify_password, authenticate_user,
    create_access_token, create_refresh_token,
    get_current_user, get_current_admin_user, get_refresh_token_user,
    generate_api_key, ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user.

    Creates a new user account with email and password.
    Returns JWT tokens for immediate authentication.

    Requirements:
    - Unique email address
    - Password: minimum 8 characters, uppercase, lowercase, and digit
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        api_key=generate_api_key(),
        is_active=True,
        is_admin=False
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate tokens
    token_data = {"sub": user.id, "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.

    Returns JWT access and refresh tokens.

    Authentication Flow:
    1. Verify email and password
    2. Generate access token (30 min expiry)
    3. Generate refresh token (30 day expiry)
    4. Return both tokens
    """
    user = authenticate_user(credentials.email, credentials.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Generate tokens
    token_data = {"sub": user.id, "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
def refresh_token(
    user: User = Depends(get_refresh_token_user)
):
    """
    Refresh access token using refresh token.

    Send refresh token in Authorization header:
    Authorization: Bearer <refresh_token>

    Returns new access and refresh tokens.
    """
    # Generate new tokens
    token_data = {"sub": user.id, "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.

    Returns user information (without sensitive data like API key).

    Authentication:
    - API Key: X-API-Key header
    - JWT: Authorization: Bearer <token>
    """
    return current_user


@router.put("/me", response_model=UserProfileResponse)
def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.

    Can update:
    - full_name
    - email (must be unique)
    """
    # Check if email is being changed and already exists
    if update_data.email and update_data.email != current_user.email:
        existing = db.query(User).filter(User.email == update_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_user.email = update_data.email

    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name

    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.

    Requirements:
    - Current password must be correct
    - New password must meet complexity requirements
    """
    # Verify current password
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a password set"
        )

    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Update password
    current_user.hashed_password = hash_password(password_data.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


@router.get("/api-key")
def get_api_key(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's API key.

    Returns the API key for use in X-API-Key header.
    """
    return {
        "api_key": current_user.api_key,
        "usage": "Include in requests as 'X-API-Key' header"
    }


@router.post("/regenerate-api-key")
def regenerate_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Regenerate API key.

    Generates a new API key and invalidates the old one.

    WARNING: All existing integrations using the old API key will stop working.
    """
    current_user.api_key = generate_api_key()
    db.commit()
    db.refresh(current_user)

    return {
        "api_key": current_user.api_key,
        "message": "API key regenerated successfully. Old key is now invalid."
    }


# ============================================================================
# Admin Endpoints
# ============================================================================

@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only).

    Supports pagination with skip and limit parameters.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.patch("/users/{user_id}/activate")
def activate_user(
    user_id: str,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Activate a user account (admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = True
    db.commit()

    return {"message": f"User {user.email} activated successfully"}


@router.patch("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: str,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user account (admin only).

    Prevents user from logging in or using API.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    user.is_active = False
    db.commit()

    return {"message": f"User {user.email} deactivated successfully"}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user account (admin only).

    WARNING: This will also delete all jobs and backlinks associated with the user.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    db.delete(user)
    db.commit()

    return None
