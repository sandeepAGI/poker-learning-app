"""
Authentication utilities for MVP.
Handles password hashing (bcrypt) and JWT tokens.
"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

load_dotenv()

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 30

# Security scheme for FastAPI
security = HTTPBearer()

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Bcrypt hashed password (60 chars)
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password to verify
        password_hash: Bcrypt hash to check against

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

def create_token(user_id: str) -> str:
    """
    Create JWT token for user.

    Args:
        user_id: User ID to encode in token

    Returns:
        JWT token string
    """
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def verify_token_string(token: str) -> str:
    """
    Verify JWT token string and return user_id.

    Args:
        token: JWT token string

    Returns:
        user_id from token

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency to verify JWT token from Authorization header.

    Usage:
        @app.get("/protected")
        def protected_route(user_id: str = Depends(verify_token)):
            return {"user_id": user_id}

    Args:
        credentials: Injected by FastAPI from Authorization header

    Returns:
        user_id from token

    Raises:
        HTTPException: If token is invalid or expired
    """
    return verify_token_string(credentials.credentials)
