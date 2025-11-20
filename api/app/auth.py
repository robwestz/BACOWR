"""
Authentication and authorization utilities.
"""

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
import secrets
import bcrypt as bcrypt_lib

from .database import get_db
from .models.database import User

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"bacowr_{secrets.token_urlsafe(32)}"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # bcrypt has a max password length of 72 bytes
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt_lib.gensalt()
    hashed = bcrypt_lib.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt_lib.checkpw(password_bytes, hashed_bytes)


async def get_current_user(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current user from API key.

    Usage:
        @app.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    user = db.query(User).filter(User.api_key == api_key).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure current user is an admin.

    Usage:
        @app.delete("/admin/users/{user_id}")
        def delete_user(user_id: str, admin: User = Depends(get_current_admin_user)):
            ...
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user


def create_default_user(db: Session) -> User:
    """
    Create default admin user if no users exist.

    Returns the default user with API key.
    """
    # Check if any users exist
    existing = db.query(User).first()
    if existing:
        return existing

    # Create default admin user with password for JWT auth
    api_key = generate_api_key()
    user = User(
        email="admin@bacowr.local",
        username="admin",
        full_name="BACOWR Administrator",
        api_key=api_key,
        hashed_password=hash_password("admin123"),  # Demo password
        role="admin",
        account_status="active",
        is_active=True,
        is_admin=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    print("=" * 70)
    print("DEFAULT ADMIN USER CREATED")
    print("=" * 70)
    print(f"Email:    {user.email}")
    print(f"Password: admin123")
    print(f"API Key:  {user.api_key}")
    print("=" * 70)
    print("🎯 LOGIN CREDENTIALS:")
    print(f"   Email:    {user.email}")
    print(f"   Password: admin123")
    print("=" * 70)
    print("⚠️  CHANGE PASSWORD IN PRODUCTION!")
    print("=" * 70)

    return user
