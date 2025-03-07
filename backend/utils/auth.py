# backend/utils/auth.py
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from typing import Optional
import jwt
from datetime import datetime, timedelta

# Mock secret key - in production, use environment variables
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Define API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a new JWT token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_player(api_key: str = Security(api_key_header)):
    """Validate API key and return player_id"""
    if api_key is None:
        raise HTTPException(status_code=401, detail="API key required")
    
    try:
        payload = jwt.decode(api_key, SECRET_KEY, algorithms=[ALGORITHM])
        player_id = payload.get("sub")
        if player_id is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return player_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid API key")