"""
Authentication and authorization utilities.

Supports dual authentication:
- API Key authentication (X-API-Key header)
- JWT Bearer token authentication (Authorization: Bearer <token>)
"""

from fastapi import Depends, HTTPException, status, Security, Request
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
import secrets
import os
from passlib.context import CryptContext
from typing import Optional

from .database import get_db
from .models.database import User
from .models.schemas import TokenData

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT Bearer token
bearer_scheme = HTTPBearer(auto_error=False)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================================
# Password Functions
# ============================================================================

def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"bacowr_{secrets.token_urlsafe(32)}"


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT Token Functions
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode (should include user_id, email)
        expires_delta: Custom expiration time (defaults to ACCESS_TOKEN_EXPIRE_MINUTES)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Payload data to encode (should include user_id, email)
        expires_delta: Custom expiration time (defaults to REFRESH_TOKEN_EXPIRE_DAYS)

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> TokenData:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        TokenData with decoded information

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        token_type: str = payload.get("token_type")

        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}, got {token_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(user_id=user_id, email=email, token_type=token_type)

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
    """
    Authenticate a user with email and password.

    Args:
        email: User email
        password: Plain text password
        db: Database session

    Returns:
        User object if authentication successful, None otherwise
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not user.hashed_password:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


# ============================================================================
# Authentication Dependencies
# ============================================================================

async def get_current_user_from_api_key(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get user from API key.

    Returns User if valid API key, None otherwise.
    """
    if not api_key:
        return None

    user = db.query(User).filter(User.api_key == api_key).first()

    if not user or not user.is_active:
        return None

    return user


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get user from JWT bearer token.

    Returns User if valid token, None otherwise.
    """
    if not credentials:
        return None

    token_data = verify_token(credentials.credentials, expected_type="access")

    user = db.query(User).filter(User.id == token_data.user_id).first()

    if not user or not user.is_active:
        return None

    return user


async def get_current_user(
    user_from_api_key: Optional[User] = Depends(get_current_user_from_api_key),
    user_from_token: Optional[User] = Depends(get_current_user_from_token),
) -> User:
    """
    Dependency to get current user from either API key or JWT token.

    Supports dual authentication:
    - API Key: X-API-Key header
    - JWT: Authorization: Bearer <token>

    Usage:
        @app.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    # Try API key first, then token
    user = user_from_api_key or user_from_token

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide either X-API-Key or Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
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


async def get_refresh_token_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get user from refresh token.

    Used specifically for token refresh endpoint.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = verify_token(credentials.credentials, expected_type="refresh")

    user = db.query(User).filter(User.id == token_data.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_user_optional(
    request: Request,
    db: Session
) -> Optional[User]:
    """
    Get current user from request without raising exceptions.

    Used in middleware for rate limiting to optionally identify users.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    # Try API key from header
    api_key = request.headers.get("x-api-key")
    if api_key:
        user = db.query(User).filter(User.api_key == api_key).first()
        if user and user.is_active:
            return user

    # Try JWT bearer token
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            token_type = payload.get("token_type")

            # Only use access tokens for user identification
            if user_id and token_type == "access":
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.is_active:
                    return user
        except JWTError:
            pass

    return None


# ============================================================================
# User Management
# ============================================================================

def create_default_user(db: Session) -> User:
    """
    Create default admin user if no users exist.

    Returns the default user with API key.
    """
    # Check if any users exist
    existing = db.query(User).first()
    if existing:
        return existing

    # Create default admin user
    api_key = generate_api_key()
    user = User(
        email="admin@bacowr.local",
        api_key=api_key,
        is_active=True,
        is_admin=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    print("=" * 70)
    print("DEFAULT ADMIN USER CREATED")
    print("=" * 70)
    print(f"Email:   {user.email}")
    print(f"API Key: {user.api_key}")
    print("=" * 70)
    print("⚠️  SAVE THIS API KEY - IT WON'T BE SHOWN AGAIN!")
    print("=" * 70)

    return user
