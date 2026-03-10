"""Authentication routes - register, login, and account management endpoints."""
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from auth import hash_password, verify_password, create_token, verify_token
from models import User
from database import get_db
from app_state import RegisterRequest, LoginRequest, AuthResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register new user.

    Validates:
    - Username not empty
    - Password not empty
    - Username not already taken

    Returns JWT token for immediate login.
    """
    # Validate input
    if not request.username or not request.username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if not request.password or not request.password.strip():
        raise HTTPException(status_code=400, detail="Password cannot be empty")

    # Check if username exists
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create user
    user_id = str(uuid.uuid4())
    user = User(
        user_id=user_id,
        username=request.username,
        password_hash=hash_password(request.password)
    )
    db.add(user)
    db.commit()

    return AuthResponse(
        token=create_token(user_id),
        user_id=user_id,
        username=request.username
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login user.

    Validates credentials and returns JWT token.
    Updates last_login timestamp.
    """
    # Find user
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return AuthResponse(
        token=create_token(user.user_id),
        user_id=user.user_id,
        username=request.username
    )


@router.delete("/account")
async def delete_account(user_id: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Delete user account and all associated data (cascade)."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Clean up any active in-memory games
    from app_state import games, deleted_games, game_tasks
    user_games = [gid for gid, (game, _) in games.items()
                  if hasattr(game, 'user_id') and game.user_id == user_id]
    for gid in user_games:
        if gid in game_tasks:
            game_tasks[gid].cancel()
            del game_tasks[gid]
        deleted_games.add(gid)
        del games[gid]

    db.delete(user)  # Cascade deletes Game -> Hand -> AnalysisCache
    db.commit()

    return {"message": "Account deleted successfully"}
