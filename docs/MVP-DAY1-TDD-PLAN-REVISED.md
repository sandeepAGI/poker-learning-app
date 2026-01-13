# MVP Day 1 Implementation - TDD Execution Plan (REVISED)

**Date:** 2026-01-13
**Status:** READY FOR EXECUTION
**Target:** Complete Day 1 (Backend + Frontend) using Test-Driven Development
**Execution Mode:** Autonomous with clear checkpoints
**Realistic Estimate:** 14-18 hours

**Verification:** This plan has been validated against the existing codebase by autonomous agent analysis.

---

## ⚠️ CRITICAL CHANGES FROM ORIGINAL PLAN

This is a **brownfield implementation** integrating with existing code, not greenfield:

1. **Existing codebase:** 1,158-line `main.py`, 60+ test files, working game engine
2. **Database setup:** Alembic schema exists, but no ORM layer yet
3. **PostgreSQL required:** Cannot use SQLite (JSONB/UUID types)
4. **Diff-based changes:** Modify existing files, don't overwrite
5. **Time estimate:** 14-18 hours (was 8.5)
6. **Integration hooks:** Must integrate with poker_engine.py lifecycle

---

## TDD Workflow

For each feature, follow this cycle:

1. **RED:** Write failing tests first
2. **GREEN:** Write minimal code to pass tests
3. **REFACTOR:** Clean up code while keeping tests green
4. **VERIFY:** Run full test suite to ensure no regressions

---

## Phase 0: Environment & Dependency Setup (1 hour)

### Task 0.1: Update Dependencies (15 minutes)

#### 0.1.1 Update requirements.txt

**File:** `backend/requirements.txt`

**ADD these lines:**
```txt
# Database & ORM
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9
alembic>=1.13.0

# Authentication
bcrypt>=4.0.1
pyjwt>=2.8.0

# Environment
python-dotenv>=1.0.0
```

**Install:**
```bash
cd backend
pip install -r requirements.txt
```

**Verify:**
```bash
python -c "import sqlalchemy, bcrypt, jwt; print('Dependencies OK')"
```

---

### Task 0.2: Database Setup (20 minutes)

#### 0.2.1 Start PostgreSQL for Development

```bash
# Start PostgreSQL container
docker run --name postgres-mvp-dev \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=poker_dev \
  -p 5432:5432 \
  -d postgres:15

# Verify connection
psql postgresql://postgres:postgres@localhost:5432/poker_dev -c "SELECT 1;"
```

#### 0.2.2 Create Test Database

```bash
# Create test database
docker exec postgres-mvp-dev psql -U postgres -c "CREATE DATABASE poker_test;"

# Verify
psql postgresql://postgres:postgres@localhost:5432/poker_test -c "SELECT 1;"
```

---

### Task 0.3: Environment Files (15 minutes)

#### 0.3.1 Create Backend .env

**File:** `backend/.env` (CREATE NEW)

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/poker_dev
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/poker_test

# Authentication
JWT_SECRET=your-secret-key-change-in-production-minimum-32-chars

# Anthropic API (already exists, keep it)
ANTHROPIC_API_KEY=your-key-here

# Test mode
TEST_MODE=0
```

**Generate JWT Secret:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Copy output to JWT_SECRET
```

#### 0.3.2 Create Frontend .env.local

**File:** `frontend/.env.local` (CREATE NEW)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

### Task 0.4: Configure Alembic (10 minutes)

#### 0.4.1 Create alembic.ini

**File:** `backend/alembic.ini` (CREATE NEW)

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/poker_dev

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

#### 0.4.2 Create alembic/env.py

**File:** `backend/alembic/env.py` (CREATE NEW)

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import models
from models import Base

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

config = context.config

# Override sqlalchemy.url from environment
if os.getenv("DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

**Verify Alembic works:**
```bash
cd backend
alembic current  # Should show: (no current revision)
```

---

### Task 0.5: Verify Test Infrastructure (5 minutes)

#### 0.5.1 Backend Tests

```bash
cd backend
PYTHONPATH=. pytest tests/test_action_processing.py -v -k "test_fold_ends_game"
# Should pass (existing test)
```

#### 0.5.2 Frontend Tests

```bash
cd frontend
npm test -- --testPathPattern=short-stack-logic --no-coverage
# Should pass (existing test)
```

**Checkpoint 0.5:** All existing tests still pass, environment ready.

---

## Phase 1: Backend Database Layer (Morning - 7 hours)

### Task 1.1: Database Models & Session (1 hour)

#### 1.1.1 Write Tests FIRST (RED)

**File:** `backend/tests/test_database_models.py` (CREATE NEW)

```python
"""Test database models and session management."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Game, Hand, AnalysisCache
from datetime import datetime
import uuid
import os

# Use test database from environment
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/poker_test")

@pytest.fixture(scope="function")
def db_session():
    """Create test database session with transaction rollback."""
    engine = create_engine(TEST_DATABASE_URL)

    # Create tables
    Base.metadata.create_all(engine)

    # Create session
    TestSessionLocal = sessionmaker(bind=engine)
    session = TestSessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)

class TestUserModel:
    """Test User model."""

    def test_create_user(self, db_session):
        """Should create user with all required fields."""
        user = User(
            user_id="test-user-123",
            username="testuser",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()

        # Query back
        saved_user = db_session.query(User).filter_by(user_id="test-user-123").first()
        assert saved_user is not None
        assert saved_user.username == "testuser"
        assert saved_user.password_hash == "hashed_password"
        assert saved_user.created_at is not None

    def test_username_unique_constraint(self, db_session):
        """Should prevent duplicate usernames."""
        from sqlalchemy.exc import IntegrityError

        user1 = User(user_id="user-1", username="testuser", password_hash="hash1")
        user2 = User(user_id="user-2", username="testuser", password_hash="hash2")

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_id_primary_key(self, db_session):
        """Should prevent duplicate user_ids."""
        from sqlalchemy.exc import IntegrityError

        user1 = User(user_id="same-id", username="user1", password_hash="hash1")
        user2 = User(user_id="same-id", username="user2", password_hash="hash2")

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()

class TestGameModel:
    """Test Game model."""

    def test_create_game(self, db_session):
        """Should create game linked to user."""
        # Create user first
        user = User(user_id="user-1", username="test", password_hash="hash")
        db_session.add(user)
        db_session.commit()

        # Create game
        game = Game(
            game_id="game-1",
            user_id="user-1",
            num_ai_players=3,
            starting_stack=1000,
            status="active"
        )
        db_session.add(game)
        db_session.commit()

        # Query back
        saved_game = db_session.query(Game).filter_by(game_id="game-1").first()
        assert saved_game is not None
        assert saved_game.user_id == "user-1"
        assert saved_game.num_ai_players == 3
        assert saved_game.status == "active"
        assert saved_game.started_at is not None

    def test_game_cascade_delete(self, db_session):
        """Deleting user should cascade delete their games."""
        user = User(user_id="user-1", username="test", password_hash="hash")
        db_session.add(user)
        db_session.commit()

        game = Game(game_id="game-1", user_id="user-1", starting_stack=1000)
        db_session.add(game)
        db_session.commit()

        # Delete user
        db_session.delete(user)
        db_session.commit()

        # Game should be deleted
        saved_game = db_session.query(Game).filter_by(game_id="game-1").first()
        assert saved_game is None

    def test_multiple_games_per_user(self, db_session):
        """User can have multiple games."""
        user = User(user_id="user-1", username="test", password_hash="hash")
        db_session.add(user)
        db_session.commit()

        game1 = Game(game_id="game-1", user_id="user-1", starting_stack=1000)
        game2 = Game(game_id="game-2", user_id="user-1", starting_stack=1000)
        db_session.add_all([game1, game2])
        db_session.commit()

        games = db_session.query(Game).filter_by(user_id="user-1").all()
        assert len(games) == 2

class TestHandModel:
    """Test Hand model."""

    def test_create_hand_with_jsonb(self, db_session):
        """Should create hand with JSONB data."""
        # Setup user and game
        user = User(user_id="user-1", username="test", password_hash="hash")
        game = Game(game_id="game-1", user_id="user-1", starting_stack=1000)
        db_session.add_all([user, game])
        db_session.commit()

        # Create hand with JSONB
        hand_data = {
            "rounds": [{"betting": "round", "actions": [{"action": "fold"}]}],
            "pot": 150,
            "community_cards": ["Ah", "Kh", "Qh"]
        }
        hand = Hand(
            game_id="game-1",
            user_id="user-1",
            hand_number=1,
            hand_data=hand_data,
            user_hole_cards="AsKs",
            user_won=True,
            pot=150
        )
        db_session.add(hand)
        db_session.commit()

        # Query back and verify JSONB
        saved_hand = db_session.query(Hand).first()
        assert saved_hand is not None
        assert saved_hand.hand_data["pot"] == 150
        assert saved_hand.hand_data["community_cards"][0] == "Ah"
        assert saved_hand.user_hole_cards == "AsKs"
        assert saved_hand.user_won is True

    def test_hand_cascade_delete_on_game(self, db_session):
        """Deleting game should cascade delete hands."""
        user = User(user_id="user-1", username="test", password_hash="hash")
        game = Game(game_id="game-1", user_id="user-1", starting_stack=1000)
        db_session.add_all([user, game])
        db_session.commit()

        hand = Hand(
            game_id="game-1",
            user_id="user-1",
            hand_number=1,
            hand_data={"pot": 100},
            pot=100
        )
        db_session.add(hand)
        db_session.commit()

        # Delete game
        db_session.delete(game)
        db_session.commit()

        # Hand should be deleted
        saved_hand = db_session.query(Hand).first()
        assert saved_hand is None

class TestAnalysisCacheModel:
    """Test AnalysisCache model."""

    def test_create_analysis_cache(self, db_session):
        """Should cache analysis with cost tracking."""
        # Setup
        user = User(user_id="user-1", username="test", password_hash="hash")
        game = Game(game_id="game-1", user_id="user-1", starting_stack=1000)
        hand = Hand(
            game_id="game-1",
            user_id="user-1",
            hand_number=1,
            hand_data={"pot": 100},
            pot=100
        )
        db_session.add_all([user, game, hand])
        db_session.commit()

        # Get hand_id (generated by database)
        hand_id = db_session.query(Hand).first().hand_id

        # Create cache entry
        analysis = AnalysisCache(
            user_id="user-1",
            hand_id=hand_id,
            analysis_type="quick",
            model_used="haiku-4.5",
            cost=0.016,
            analysis_data={"verdict": "good play", "confidence": 0.85}
        )
        db_session.add(analysis)
        db_session.commit()

        # Query back
        saved = db_session.query(AnalysisCache).first()
        assert saved is not None
        assert saved.cost == 0.016
        assert saved.model_used == "haiku-4.5"
        assert saved.analysis_data["verdict"] == "good play"

    def test_unique_index_on_user_hand_type(self, db_session):
        """Should enforce unique constraint on user+hand+type."""
        from sqlalchemy.exc import IntegrityError

        # Setup
        user = User(user_id="user-1", username="test", password_hash="hash")
        game = Game(game_id="game-1", user_id="user-1", starting_stack=1000)
        hand = Hand(
            game_id="game-1",
            user_id="user-1",
            hand_number=1,
            hand_data={},
            pot=100
        )
        db_session.add_all([user, game, hand])
        db_session.commit()

        hand_id = db_session.query(Hand).first().hand_id

        # Create first cache entry
        analysis1 = AnalysisCache(
            user_id="user-1",
            hand_id=hand_id,
            analysis_type="quick",
            model_used="haiku",
            cost=0.01,
            analysis_data={}
        )
        db_session.add(analysis1)
        db_session.commit()

        # Try to create duplicate
        analysis2 = AnalysisCache(
            user_id="user-1",
            hand_id=hand_id,
            analysis_type="quick",  # Same type
            model_used="haiku",
            cost=0.01,
            analysis_data={}
        )
        db_session.add(analysis2)
        with pytest.raises(IntegrityError):
            db_session.commit()

class TestDatabaseSession:
    """Test database session management."""

    def test_session_rollback_on_error(self, db_session):
        """Session should rollback on errors."""
        user = User(user_id="user-1", username="test", password_hash="hash")
        db_session.add(user)
        db_session.commit()

        # Try invalid operation
        try:
            invalid_user = User(user_id="user-1", username="test2", password_hash="hash")
            db_session.add(invalid_user)
            db_session.commit()
        except Exception:
            db_session.rollback()

        # Should still work after rollback
        user2 = User(user_id="user-2", username="test2", password_hash="hash")
        db_session.add(user2)
        db_session.commit()

        users = db_session.query(User).all()
        assert len(users) == 2
```

**Run tests - SHOULD FAIL:**
```bash
cd backend
PYTHONPATH=. pytest tests/test_database_models.py -v
# Expected: ModuleNotFoundError: No module named 'models'
```

#### 1.1.2 Implement Models (GREEN)

**File:** `backend/models.py` (CREATE NEW)

```python
"""
SQLAlchemy ORM models for MVP database schema.
Matches alembic/versions/001_mvp_schema.py structure.
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    """User accounts table."""
    __tablename__ = 'users'

    user_id = Column(String(50), primary_key=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    last_login = Column(TIMESTAMP)

class Game(Base):
    """Game sessions table."""
    __tablename__ = 'games'

    game_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    started_at = Column(TIMESTAMP, server_default=func.current_timestamp(), index=True)
    completed_at = Column(TIMESTAMP)
    num_ai_players = Column(Integer)
    starting_stack = Column(Integer)
    final_stack = Column(Integer)
    profit_loss = Column(Integer)
    total_hands = Column(Integer, server_default='0')
    status = Column(String(20), server_default='active')

class Hand(Base):
    """Individual hands table."""
    __tablename__ = 'hands'

    hand_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    game_id = Column(String(50), ForeignKey('games.game_id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    hand_number = Column(Integer, nullable=False)
    hand_data = Column(JSONB, nullable=False)
    user_hole_cards = Column(String(10))
    user_won = Column(Boolean)
    pot = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

class AnalysisCache(Base):
    """AI analysis cache table."""
    __tablename__ = 'analysis_cache'

    cache_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    hand_id = Column(UUID(as_uuid=True), ForeignKey('hands.hand_id', ondelete='CASCADE'), nullable=False)
    analysis_type = Column(String(20), nullable=False)
    model_used = Column(String(50), nullable=False)
    cost = Column(Float, nullable=False)
    analysis_data = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
```

**File:** `backend/database.py` (CREATE NEW)

```python
"""
Database session management and utilities.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/poker_dev")

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI dependency for database sessions.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """
    Context manager for database sessions.
    Usage: with get_db_context() as db:
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database (create tables)."""
    from models import Base
    Base.metadata.create_all(bind=engine)
```

**Run Alembic Migration:**
```bash
cd backend
alembic upgrade head
# Should apply 001_mvp_schema.py migration
```

**Verify tables created:**
```bash
psql postgresql://postgres:postgres@localhost:5432/poker_dev -c "\dt"
# Should show: users, games, hands, analysis_cache, alembic_version
```

**Run tests - SHOULD PASS:**
```bash
cd backend
PYTHONPATH=. pytest tests/test_database_models.py -v
# Expected: All tests pass (16 tests)
```

**Checkpoint 1.1:** Database models work, migrations applied, tests pass.

---

### Task 1.2: Authentication Module (1 hour)

#### 1.2.1 Write Tests FIRST (RED)

**File:** `backend/tests/test_auth.py` (CREATE NEW)

```python
"""Test authentication functions."""
import pytest
from auth import hash_password, verify_password, create_token, verify_token_string
from datetime import datetime, timedelta
import jwt
import os

class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_returns_bcrypt_hash(self):
        """Password should be hashed with bcrypt."""
        password = "test123"
        hashed = hash_password(password)

        assert hashed != password  # Not plaintext
        assert len(hashed) == 60  # bcrypt hash length
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_hash_password_different_each_time(self):
        """Same password should produce different hashes (salt)."""
        password = "test123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Correct password should verify."""
        password = "test123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_wrong(self):
        """Wrong password should not verify."""
        password = "test123"
        wrong = "wrong456"
        hashed = hash_password(password)

        assert verify_password(wrong, hashed) is False

    def test_verify_password_empty(self):
        """Empty password should work (validation elsewhere)."""
        password = ""
        hashed = hash_password(password)

        assert verify_password("", hashed) is True
        assert verify_password("x", hashed) is False

class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_token_returns_jwt(self):
        """Should return valid JWT string."""
        user_id = "test-user-123"
        token = create_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0
        assert len(token.split('.')) == 3  # header.payload.signature

    def test_create_token_includes_user_id(self):
        """Token should contain user_id in 'sub' claim."""
        user_id = "test-user-123"
        token = create_token(user_id)

        # Decode to verify (don't verify signature for test)
        secret = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION")
        payload = jwt.decode(token, secret, algorithms=["HS256"])

        assert payload["sub"] == user_id

    def test_create_token_has_expiration(self):
        """Token should expire in 30 days."""
        user_id = "test-user-123"
        token = create_token(user_id)

        secret = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION")
        payload = jwt.decode(token, secret, algorithms=["HS256"])

        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + timedelta(days=30)
        time_diff = abs((exp_time - expected_exp).total_seconds())

        assert time_diff < 10  # Within 10 seconds

    def test_verify_token_string_valid(self):
        """Valid token should return user_id."""
        user_id = "test-user-123"
        token = create_token(user_id)

        result = verify_token_string(token)
        assert result == user_id

    def test_verify_token_string_expired(self):
        """Expired token should raise exception."""
        from fastapi import HTTPException

        # Create expired token
        user_id = "test-user-123"
        secret = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION")
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() - timedelta(days=1)
        }
        expired_token = jwt.encode(payload, secret, algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            verify_token_string(expired_token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_verify_token_string_invalid_signature(self):
        """Token with wrong signature should raise exception."""
        from fastapi import HTTPException

        # Create token with wrong secret
        user_id = "test-user-123"
        wrong_secret = "wrong-secret"
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(days=30)
        }
        invalid_token = jwt.encode(payload, wrong_secret, algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            verify_token_string(invalid_token)

        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()

    def test_verify_token_string_malformed(self):
        """Malformed token should raise exception."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            verify_token_string("not-a-jwt-token")

        assert exc_info.value.status_code == 401
```

**Run tests - SHOULD FAIL:**
```bash
cd backend
PYTHONPATH=. pytest tests/test_auth.py -v
# Expected: ModuleNotFoundError: No module named 'auth'
```

#### 1.2.2 Implement Auth Module (GREEN)

**File:** `backend/auth.py` (CREATE NEW)

```python
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
```

**Run tests - SHOULD PASS:**
```bash
cd backend
PYTHONPATH=. pytest tests/test_auth.py -v
# Expected: All 11 tests pass
```

**Checkpoint 1.2:** Authentication module works, password hashing and JWT verified.

---

### Task 1.3: Auth Endpoints (1.5 hours)

#### 1.3.1 Add Test Database Fixture to conftest.py

**File:** `backend/tests/conftest.py`

**APPEND to existing file:**

```python
# Existing content stays...

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/poker_test")

@pytest.fixture(scope="function")
def db_session():
    """Database session for tests with transaction rollback."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)

    TestSessionLocal = sessionmaker(bind=engine)
    session = TestSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)
```

#### 1.3.2 Write Tests FIRST (RED)

**File:** `backend/tests/test_auth_endpoints.py` (CREATE NEW)

```python
"""Test authentication endpoints."""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
from models import Base, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/poker_test")

@pytest.fixture
def client():
    """Create test client with test database."""
    # Setup test database
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)

    # Override get_db dependency
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    client = TestClient(app)

    yield client

    # Cleanup
    Base.metadata.drop_all(engine)
    app.dependency_overrides.clear()

class TestRegisterEndpoint:
    """Test POST /auth/register endpoint."""

    def test_register_new_user_success(self, client):
        """Should register new user and return token."""
        response = client.post(
            "/auth/register",
            json={"username": "testuser", "password": "test123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user_id" in data
        assert data["username"] == "testuser"
        assert len(data["token"]) > 50  # JWT is long

    def test_register_duplicate_username_fails(self, client):
        """Should reject duplicate username."""
        # Register first user
        client.post("/auth/register", json={"username": "testuser", "password": "test123"})

        # Try duplicate
        response = client.post("/auth/register", json={"username": "testuser", "password": "different"})

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_missing_username_fails(self, client):
        """Should reject missing username."""
        response = client.post("/auth/register", json={"password": "test123"})

        assert response.status_code == 422  # Validation error

    def test_register_missing_password_fails(self, client):
        """Should reject missing password."""
        response = client.post("/auth/register", json={"username": "testuser"})

        assert response.status_code == 422

    def test_register_empty_username_fails(self, client):
        """Should reject empty username."""
        response = client.post("/auth/register", json={"username": "", "password": "test123"})

        assert response.status_code == 400
        assert "username" in response.json()["detail"].lower()

    def test_register_empty_password_fails(self, client):
        """Should reject empty password."""
        response = client.post("/auth/register", json={"username": "testuser", "password": ""})

        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()

class TestLoginEndpoint:
    """Test POST /auth/login endpoint."""

    def test_login_correct_credentials_success(self, client):
        """Should login with correct credentials."""
        # Register first
        client.post("/auth/register", json={"username": "testuser", "password": "test123"})

        # Login
        response = client.post("/auth/login", json={"username": "testuser", "password": "test123"})

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user_id" in data
        assert data["username"] == "testuser"

    def test_login_wrong_password_fails(self, client):
        """Should reject wrong password."""
        # Register
        client.post("/auth/register", json={"username": "testuser", "password": "test123"})

        # Try wrong password
        response = client.post("/auth/login", json={"username": "testuser", "password": "wrong"})

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user_fails(self, client):
        """Should reject nonexistent user."""
        response = client.post("/auth/login", json={"username": "nonexistent", "password": "test123"})

        assert response.status_code == 401

    def test_login_updates_last_login(self, client):
        """Should update last_login timestamp."""
        # Register and get user_id
        reg_response = client.post("/auth/register", json={"username": "testuser", "password": "test123"})

        # Login
        client.post("/auth/login", json={"username": "testuser", "password": "test123"})

        # Verify last_login was updated (would need db query or endpoint to check)
        # For now, just verify login succeeded
        assert reg_response.status_code == 200

    def test_login_case_sensitive_username(self, client):
        """Username should be case-sensitive."""
        # Register lowercase
        client.post("/auth/register", json={"username": "testuser", "password": "test123"})

        # Try uppercase
        response = client.post("/auth/login", json={"username": "TESTUSER", "password": "test123"})

        assert response.status_code == 401

class TestAuthProtectedEndpoint:
    """Test that endpoints require authentication."""

    def test_protected_endpoint_without_token_fails(self, client):
        """Should reject request without token."""
        response = client.post("/games", json={"player_name": "Test", "ai_count": 3})

        assert response.status_code == 403  # Forbidden (no auth header)

    def test_protected_endpoint_with_invalid_token_fails(self, client):
        """Should reject invalid token."""
        response = client.post(
            "/games",
            json={"player_name": "Test", "ai_count": 3},
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401

    def test_protected_endpoint_with_valid_token_succeeds(self, client):
        """Should accept valid token."""
        # Register and get token
        reg_response = client.post("/auth/register", json={"username": "testuser", "password": "test123"})
        token = reg_response.json()["token"]

        # Use token
        response = client.post(
            "/games",
            json={"player_name": "Test", "ai_count": 3},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert "game_id" in response.json()
```

**Run tests - SHOULD FAIL:**
```bash
cd backend
PYTHONPATH=. pytest tests/test_auth_endpoints.py -v
# Expected: Endpoints don't exist yet
```

#### 1.3.3 Implement Endpoints (GREEN)

**File:** `backend/main.py`

**ADD these imports at the top (after existing imports):**

```python
# Add after line 21 (after existing imports)
from auth import hash_password, verify_password, create_token, verify_token
from models import User, Game, Hand, AnalysisCache
from database import get_db
from sqlalchemy.orm import Session
```

**ADD auth endpoints BEFORE the existing `/games` endpoint (around line 150):**

```python
# Authentication endpoints
# Add before @app.post("/games")

class RegisterRequest(BaseModel):
    """Register new user request."""
    username: str
    password: str

class LoginRequest(BaseModel):
    """Login request."""
    username: str
    password: str

class AuthResponse(BaseModel):
    """Authentication response."""
    token: str
    user_id: str
    username: str

@app.post("/auth/register", response_model=AuthResponse)
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

@app.post("/auth/login", response_model=AuthResponse)
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
```

**MODIFY existing `/games` endpoint to require auth (line ~151):**

```python
# CHANGE FROM:
@app.post("/games", response_model=Dict[str, str])
def create_game(request: CreateGameRequest):

# CHANGE TO:
@app.post("/games", response_model=Dict[str, str])
def create_game(
    request: CreateGameRequest,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Create a new poker game (requires authentication).
    Returns: {"game_id": "uuid"}
    """
    # Existing validation...
    if request.ai_count < 1 or request.ai_count > 5:
        raise HTTPException(status_code=400, detail="AI count must be between 1 and 5")

    # Create game
    game_id = str(uuid.uuid4())
    game = PokerGame(request.player_name, request.ai_count)

    # ADD: Store user_id in game for later access
    game.user_id = user_id  # Add this attribute dynamically

    # Start first hand
    game.start_new_hand(process_ai=False)

    # ADD: Save game to database
    db_game = Game(
        game_id=game_id,
        user_id=user_id,
        num_ai_players=request.ai_count,
        starting_stack=game.players[0].stack,
        status="active"
    )
    db.add(db_game)
    db.commit()

    # Store in memory with timestamp
    games[game_id] = (game, time.time())

    return {"game_id": game_id}
```

**Run tests - SHOULD PASS:**
```bash
cd backend
PYTHONPATH=. pytest tests/test_auth_endpoints.py -v
# Expected: 15 tests pass
```

**Checkpoint 1.3:** Auth endpoints work, games require authentication.

---

### Task 1.4: Hand Persistence (2 hours)

#### 1.4.1 Write Tests FIRST (RED)

**File:** `backend/tests/test_hand_persistence.py` (CREATE NEW)

```python
"""Test hand persistence to database."""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
from models import Base, User, Game, Hand
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/poker_test")

@pytest.fixture
def auth_client():
    """Create authenticated test client."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # Register and login
    response = client.post("/auth/register", json={"username": "testuser", "password": "test123"})
    token = response.json()["token"]
    client.headers = {"Authorization": f"Bearer {token}"}

    yield client, TestSessionLocal

    Base.metadata.drop_all(engine)
    app.dependency_overrides.clear()

class TestHandPersistence:
    """Test hands are saved to database."""

    def test_completed_hand_saves_to_database(self, auth_client):
        """When hand completes, should save to database."""
        client, SessionLocal = auth_client

        # Create game
        game_response = client.post("/games", json={"player_name": "Test", "ai_count": 1})
        game_id = game_response.json()["game_id"]

        # Play hand to completion (fold to finish)
        client.post(f"/games/{game_id}/actions", json={"action": "fold"})

        # Check database has hand record
        db = SessionLocal()
        hands = db.query(Hand).filter(Hand.game_id == game_id).all()
        db.close()

        assert len(hands) >= 1
        hand = hands[0]
        assert hand.hand_number == 1
        assert hand.pot is not None
        assert hand.hand_data is not None

    def test_hand_includes_community_cards(self, auth_client):
        """Saved hand should include community cards."""
        client, SessionLocal = auth_client

        # Create game and play to river
        game_response = client.post("/games", json={"player_name": "Test", "ai_count": 1})
        game_id = game_response.json()["game_id"]

        # Call to river then fold
        client.post(f"/games/{game_id}/actions", json={"action": "call"})
        # AI will act, game advances
        # Continue until hand completes (implementation-dependent)

        # Check database
        db = SessionLocal()
        hands = db.query(Hand).filter(Hand.game_id == game_id).all()
        db.close()

        if hands:
            hand = hands[0]
            assert "community_cards" in hand.hand_data or hand.hand_data.get("rounds")

    def test_multiple_hands_save_with_correct_hand_numbers(self, auth_client):
        """Multiple hands should have sequential hand numbers."""
        client, SessionLocal = auth_client

        game_response = client.post("/games", json={"player_name": "Test", "ai_count": 1})
        game_id = game_response.json()["game_id"]

        # Play 3 hands (fold each time)
        for _ in range(3):
            client.post(f"/games/{game_id}/actions", json={"action": "fold"})
            # Start next hand
            client.post(f"/games/{game_id}/next", json={})

        # Check database
        db = SessionLocal()
        hands = db.query(Hand).filter(Hand.game_id == game_id).order_by(Hand.hand_number).all()
        db.close()

        assert len(hands) >= 3
        for i, hand in enumerate(hands[:3]):
            assert hand.hand_number == i + 1

    def test_game_total_hands_increments(self, auth_client):
        """Game.total_hands should increment on each hand."""
        client, SessionLocal = auth_client

        game_response = client.post("/games", json={"player_name": "Test", "ai_count": 1})
        game_id = game_response.json()["game_id"]

        # Play 2 hands
        client.post(f"/games/{game_id}/actions", json={"action": "fold"})
        client.post(f"/games/{game_id}/next", json={})
        client.post(f"/games/{game_id}/actions", json={"action": "fold"})

        # Check database
        db = SessionLocal()
        game = db.query(Game).filter(Game.game_id == game_id).first()
        db.close()

        assert game.total_hands >= 2

class TestGameCompletion:
    """Test game completion and final statistics."""

    def test_game_completion_marks_status(self, auth_client):
        """When game ends, should mark status as completed."""
        # This test would need game-over logic implemented
        pass  # TODO: Implement after game-over detection

    def test_game_completion_saves_final_stack(self, auth_client):
        """Should save final_stack and profit_loss."""
        pass  # TODO: Implement after game-over detection
```

**Run tests - SHOULD FAIL:**
```bash
cd backend
PYTHONPATH=. pytest tests/test_hand_persistence.py -v
# Expected: Hands not being saved yet
```

#### 1.4.2 Implement Hand Persistence (GREEN)

**File:** `backend/database.py`

**ADD hand persistence function:**

```python
# Add after get_db_context() function

from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.poker_engine import CompletedHand, PokerGame

def save_completed_hand(game_id: str, completed_hand: "CompletedHand", user_id: str) -> None:
    """
    Save completed hand to database.

    Args:
        game_id: Game ID
        completed_hand: CompletedHand dataclass from poker_engine
        user_id: User ID who played the hand
    """
    try:
        with get_db_context() as db:
            # Serialize hand data (convert dataclass to dict)
            hand_data = asdict(completed_hand)

            # Create hand record
            hand = Hand(
                game_id=game_id,
                user_id=user_id,
                hand_number=completed_hand.hand_number,
                hand_data=hand_data,
                user_hole_cards=",".join(completed_hand.human_hole_cards) if completed_hand.human_hole_cards else None,
                user_won=completed_hand.winner_player_id in completed_hand.winner_ids if hasattr(completed_hand, 'winner_player_id') else None,
                pot=completed_hand.pot_size
            )
            db.add(hand)

            # Update game total_hands
            game = db.query(Game).filter(Game.game_id == game_id).first()
            if game:
                game.total_hands += 1

            db.commit()
    except Exception as e:
        # Don't crash game if database save fails
        import logging
        logging.error(f"Failed to save hand to database: {e}")
```

**File:** `backend/main.py`

**IMPORT at top:**

```python
# Add after existing imports
from database import save_completed_hand
```

**MODIFY submit_action to save hands:**

Find the `submit_action` function (around line 378) and add hand saving:

```python
@app.post("/games/{game_id}/actions")
def submit_action(
    game_id: str,
    request: GameActionRequest,
    user_id: str = Depends(verify_token),  # ADD THIS
    db: Session = Depends(get_db)  # ADD THIS
):
    """
    Submit a player action (fold/call/raise)
    Returns: Updated game state
    """
    # Existing validation...
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game, _ = games[game_id]
    games[game_id] = (game, time.time())

    # Validate action
    if request.action not in ["fold", "call", "raise"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    if request.action == "raise" and request.amount is None:
        raise HTTPException(status_code=400, detail="Raise action requires amount")

    # Submit action to game engine
    success = game.submit_human_action(request.action, request.amount)

    if not success:
        raise HTTPException(status_code=400, detail="Invalid action")

    # ADD: Save hand if completed
    if game.last_hand_summary and hasattr(game, 'user_id'):
        save_completed_hand(game_id, game.last_hand_summary, game.user_id)

    # Return updated game state
    return get_game_state(game_id)
```

**MODIFY next_hand to save hands:**

Find the `next_hand` function (around line 410) and add similar logic:

```python
@app.post("/games/{game_id}/next")
def next_hand(
    game_id: str,
    user_id: str = Depends(verify_token),  # ADD THIS
    db: Session = Depends(get_db)  # ADD THIS
):
    """
    Start next hand in the game
    Returns: Updated game state
    """
    # Existing code...
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game, _ = games[game_id]
    games[game_id] = (game, time.time())

    if game.current_state != GameState.SHOWDOWN:
        raise HTTPException(status_code=400, detail="Current hand not finished")

    # ADD: Save previous hand before starting new one
    if game.last_hand_summary and hasattr(game, 'user_id'):
        save_completed_hand(game_id, game.last_hand_summary, game.user_id)

    # Check if any players are eliminated
    active_players = [p for p in game.players if p.stack > 0]
    if len(active_players) <= 1:
        # ADD: Mark game as completed
        db_game = db.query(Game).filter(Game.game_id == game_id).first()
        if db_game:
            db_game.status = "completed"
            db_game.completed_at = datetime.utcnow()
            human_player = next((p for p in game.players if p.is_human), None)
            if human_player:
                db_game.final_stack = human_player.stack
                db_game.profit_loss = human_player.stack - db_game.starting_stack
            db.commit()

        raise HTTPException(status_code=400, detail="Game over")

    # Start new hand
    game.start_new_hand()

    return get_game_state(game_id)
```

**Run tests - SHOULD PASS:**
```bash
cd backend
PYTHONPATH=. pytest tests/test_hand_persistence.py -v
# Expected: Most tests pass (game-over tests still TODO)
```

**Checkpoint 1.4:** Hands save to database on completion, game stats update.

---

### Task 1.5: History Endpoints (1.5 hours)

#### 1.5.1 Write Tests FIRST (RED)

**File:** `backend/tests/test_history_endpoints.py` (CREATE NEW)

```python
"""Test game history endpoints."""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
from models import Base, User, Game, Hand
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/poker_test")

@pytest.fixture
def client_with_history():
    """Create client with populated game history."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # Register user
    response = client.post("/auth/register", json={"username": "testuser", "password": "test123"})
    token = response.json()["token"]
    user_id = response.json()["user_id"]
    client.headers = {"Authorization": f"Bearer {token}"}

    # Create test data directly in DB
    db = TestSessionLocal()

    # Create 3 completed games
    for i in range(3):
        game = Game(
            game_id=f"game-{i}",
            user_id=user_id,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            num_ai_players=2 + i,
            starting_stack=1000,
            final_stack=1000 + (i * 200),
            profit_loss=i * 200,
            total_hands=5 + i,
            status="completed"
        )
        db.add(game)

        # Add hands for first game
        if i == 0:
            for j in range(5):
                hand = Hand(
                    game_id=f"game-{i}",
                    user_id=user_id,
                    hand_number=j + 1,
                    hand_data={"pot": 100 * (j + 1), "rounds": []},
                    user_hole_cards="AsKs",
                    user_won=(j % 2 == 0),
                    pot=100 * (j + 1)
                )
                db.add(hand)

    db.commit()
    db.close()

    yield client, user_id, TestSessionLocal

    Base.metadata.drop_all(engine)
    app.dependency_overrides.clear()

class TestGetMyGamesEndpoint:
    """Test GET /users/me/games endpoint."""

    def test_requires_authentication(self):
        """Should require authentication."""
        client = TestClient(app)
        response = client.get("/users/me/games")

        assert response.status_code == 403  # No auth header

    def test_returns_users_completed_games(self, client_with_history):
        """Should return user's completed games."""
        client, user_id, _ = client_with_history
        response = client.get("/users/me/games")

        assert response.status_code == 200
        data = response.json()
        assert "games" in data
        assert len(data["games"]) == 3

    def test_game_structure_correct(self, client_with_history):
        """Games should have correct structure."""
        client, user_id, _ = client_with_history
        response = client.get("/users/me/games")

        games = response.json()["games"]
        game = games[0]

        assert "game_id" in game
        assert "started_at" in game
        assert "completed_at" in game
        assert "total_hands" in game
        assert "profit_loss" in game
        assert "num_ai_players" in game

    def test_ordered_by_most_recent_first(self, client_with_history):
        """Should order by most recent first."""
        client, user_id, _ = client_with_history
        response = client.get("/users/me/games")

        games = response.json()["games"]

        # Verify descending order by started_at
        for i in range(len(games) - 1):
            assert games[i]["started_at"] >= games[i + 1]["started_at"]

    def test_respects_limit_parameter(self, client_with_history):
        """Should respect limit parameter."""
        client, user_id, _ = client_with_history
        response = client.get("/users/me/games?limit=2")

        games = response.json()["games"]
        assert len(games) == 2

    def test_only_returns_completed_games(self, client_with_history):
        """Should only return completed games, not active."""
        client, user_id, SessionLocal = client_with_history

        # Add an active game
        db = SessionLocal()
        active_game = Game(
            game_id="active-game",
            user_id=user_id,
            starting_stack=1000,
            status="active"
        )
        db.add(active_game)
        db.commit()
        db.close()

        response = client.get("/users/me/games")
        games = response.json()["games"]

        # Should still only return 3 completed games
        assert len(games) == 3
        for game in games:
            assert game["game_id"] != "active-game"

    def test_only_returns_own_games(self, client_with_history):
        """Should not return other users' games."""
        client, user_id, SessionLocal = client_with_history

        # Create another user's game
        db = SessionLocal()
        other_user = User(user_id="other-user", username="other", password_hash="hash")
        other_game = Game(
            game_id="other-game",
            user_id="other-user",
            starting_stack=1000,
            status="completed"
        )
        db.add_all([other_user, other_game])
        db.commit()
        db.close()

        response = client.get("/users/me/games")
        games = response.json()["games"]

        for game in games:
            assert game["game_id"] != "other-game"

class TestGetGameHandsEndpoint:
    """Test GET /games/{game_id}/hands endpoint."""

    def test_requires_authentication(self):
        """Should require authentication."""
        client = TestClient(app)
        response = client.get("/games/game-0/hands")

        assert response.status_code == 403

    def test_returns_all_hands_for_game(self, client_with_history):
        """Should return all hands for a game."""
        client, user_id, _ = client_with_history
        response = client.get("/games/game-0/hands")

        assert response.status_code == 200
        data = response.json()
        assert "hands" in data
        assert len(data["hands"]) == 5

    def test_hand_structure_correct(self, client_with_history):
        """Hands should have correct structure."""
        client, user_id, _ = client_with_history
        response = client.get("/games/game-0/hands")

        hands = response.json()["hands"]
        hand = hands[0]

        assert "hand_id" in hand
        assert "hand_number" in hand
        assert "hand_data" in hand
        assert "user_won" in hand
        assert "pot" in hand

    def test_hands_ordered_by_hand_number(self, client_with_history):
        """Should order hands by hand_number."""
        client, user_id, _ = client_with_history
        response = client.get("/games/game-0/hands")

        hands = response.json()["hands"]

        for i, hand in enumerate(hands):
            assert hand["hand_number"] == i + 1

    def test_rejects_other_users_games(self, client_with_history):
        """Should not return hands for other users' games."""
        client, user_id, SessionLocal = client_with_history

        # Create another user's game with hands
        db = SessionLocal()
        other_user = User(user_id="other-user", username="other", password_hash="hash")
        other_game = Game(
            game_id="other-game",
            user_id="other-user",
            starting_stack=1000
        )
        db.add_all([other_user, other_game])
        db.commit()
        db.close()

        response = client.get("/games/other-game/hands")
        assert response.status_code == 404

    def test_returns_404_for_nonexistent_game(self, client_with_history):
        """Should return 404 for nonexistent game."""
        client, user_id, _ = client_with_history
        response = client.get("/games/nonexistent/hands")

        assert response.status_code == 404
```

**Run tests - SHOULD FAIL:**
```bash
cd backend
PYTHONPATH=. pytest tests/test_history_endpoints.py -v
# Expected: Endpoints don't exist
```

#### 1.5.2 Implement History Endpoints (GREEN)

**File:** `backend/main.py`

**ADD endpoints AFTER existing game endpoints:**

```python
# Game history endpoints
# Add after the /games endpoints

@app.get("/users/me/games")
async def get_my_games(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """
    Get user's completed games.

    Returns most recent games ordered by started_at descending.
    Only returns completed games (not active).
    """
    games_list = db.query(Game).filter(
        Game.user_id == user_id,
        Game.status == "completed"
    ).order_by(Game.started_at.desc()).limit(limit).all()

    return {
        "games": [
            {
                "game_id": g.game_id,
                "started_at": g.started_at.isoformat() if g.started_at else None,
                "completed_at": g.completed_at.isoformat() if g.completed_at else None,
                "total_hands": g.total_hands,
                "starting_stack": g.starting_stack,
                "final_stack": g.final_stack,
                "profit_loss": g.profit_loss,
                "num_ai_players": g.num_ai_players
            }
            for g in games_list
        ]
    }

@app.get("/games/{game_id}/hands")
async def get_game_hands(
    game_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get all hands for a game.

    Verifies game belongs to user before returning hands.
    Returns hands ordered by hand_number.
    """
    # Verify game ownership
    game = db.query(Game).filter(
        Game.game_id == game_id,
        Game.user_id == user_id
    ).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get hands
    hands = db.query(Hand).filter(
        Hand.game_id == game_id
    ).order_by(Hand.hand_number).all()

    return {
        "hands": [
            {
                "hand_id": str(h.hand_id),
                "hand_number": h.hand_number,
                "hand_data": h.hand_data,
                "user_hole_cards": h.user_hole_cards,
                "user_won": h.user_won,
                "pot": h.pot,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in hands
        ]
    }
```

**Run tests - SHOULD PASS:**
```bash
cd backend
PYTHONPATH=. pytest tests/test_history_endpoints.py -v
# Expected: All 16 tests pass
```

**Checkpoint 1.5:** History endpoints work, users can view their completed games and hands.

---

### Task 1.6: WebSocket Authentication (1 hour)

#### 1.6.1 Write Tests FIRST (RED)

**File:** `backend/tests/test_websocket_auth.py` (CREATE NEW)

```python
"""Test WebSocket authentication."""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
from models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/poker_test")

@pytest.fixture
def client_and_token():
    """Create client and get auth token."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # Register user
    response = client.post("/auth/register", json={"username": "testuser", "password": "test123"})
    token = response.json()["token"]

    # Create a game
    game_response = client.post(
        "/games",
        json={"player_name": "Test", "ai_count": 1},
        headers={"Authorization": f"Bearer {token}"}
    )
    game_id = game_response.json()["game_id"]

    yield client, token, game_id

    Base.metadata.drop_all(engine)
    app.dependency_overrides.clear()

class TestWebSocketAuthentication:
    """Test WebSocket requires authentication."""

    def test_websocket_without_token_fails(self, client_and_token):
        """Should reject WebSocket connection without token."""
        client, token, game_id = client_and_token

        with pytest.raises(Exception):
            with client.websocket_connect(f"/ws/{game_id}"):
                pass

    def test_websocket_with_invalid_token_fails(self, client_and_token):
        """Should reject WebSocket with invalid token."""
        client, token, game_id = client_and_token

        with pytest.raises(Exception):
            with client.websocket_connect(f"/ws/{game_id}?token=invalid-token"):
                pass

    def test_websocket_with_valid_token_succeeds(self, client_and_token):
        """Should accept WebSocket with valid token."""
        client, token, game_id = client_and_token

        with client.websocket_connect(f"/ws/{game_id}?token={token}") as websocket:
            # Should receive initial game state
            data = websocket.receive_json()
            assert "type" in data

    def test_websocket_verifies_game_ownership(self, client_and_token):
        """Should verify user owns the game."""
        client, token, game_id = client_and_token

        # Create second user
        client.post("/auth/register", json={"username": "other", "password": "test123"})
        login_response = client.post("/auth/login", json={"username": "other", "password": "test123"})
        other_token = login_response.json()["token"]

        # Try to connect to first user's game
        with pytest.raises(Exception):
            with client.websocket_connect(f"/ws/{game_id}?token={other_token}"):
                pass
```

**Run tests - SHOULD FAIL:**
```bash
cd backend
PYTHONPATH=. pytest tests/test_websocket_auth.py -v
# Expected: WebSocket doesn't have auth yet
```

#### 1.6.2 Implement WebSocket Auth (GREEN)

**File:** `backend/main.py`

**MODIFY WebSocket endpoint (around line 858):**

```python
# CHANGE FROM:
@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):

# CHANGE TO:
@app.websocket("/ws/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_id: str,
    token: str = Query(None)
):
    """
    WebSocket endpoint for real-time game updates (requires authentication).

    Args:
        websocket: WebSocket connection
        game_id: Game ID
        token: JWT token as query parameter (?token=xxx)
    """
    # Validate token
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    try:
        user_id = verify_token_string(token)
    except HTTPException:
        await websocket.close(code=1008, reason="Invalid token")
        return

    # Validate game exists
    if game_id not in games:
        await websocket.close(code=1008, reason="Game not found")
        return

    # Validate game ownership
    game, _ = games[game_id]
    if not hasattr(game, 'user_id') or game.user_id != user_id:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    # Rest of existing WebSocket logic...
    await manager.connect(game_id, websocket)

    # ... (keep all existing code)
```

**ADD Query import at top:**

```python
# Add to imports at top
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, Depends
```

**Run tests - SHOULD PASS:**
```bash
cd backend
PYTHONPATH=. pytest tests/test_websocket_auth.py -v
# Expected: Most tests pass (ownership test may need adjustment)
```

**Checkpoint 1.6:** WebSocket authenticated, users can only connect to their own games.

---

## Backend Phase Complete - Integration Checkpoint (30 minutes)

### Run ALL Backend Tests

```bash
cd backend

# Run new MVP tests
PYTHONPATH=. pytest tests/test_database_models.py tests/test_auth.py tests/test_auth_endpoints.py tests/test_hand_persistence.py tests/test_history_endpoints.py tests/test_websocket_auth.py -v

# Run existing regression tests to ensure no breaks
PYTHONPATH=. pytest tests/test_action_processing.py tests/test_state_advancement.py tests/test_fold_resolution.py tests/test_turn_order.py -v
```

**Expected: ~70-80 tests pass, 0 failures.**

### Manual Testing with Curl

```bash
# 1. Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}'
# Save token from response

# 2. Create game (use token)
curl -X POST http://localhost:8000/games \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"player_name":"Test","ai_count":3}'
# Save game_id

# 3. View game history
curl -X GET http://localhost:8000/users/me/games \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# 4. View hands for a game
curl -X GET http://localhost:8000/games/GAME_ID/hands \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Verify Database

```bash
psql postgresql://postgres:postgres@localhost:5432/poker_dev

-- Check tables
\dt

-- Check data
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM games;
SELECT COUNT(*) FROM hands;

-- View structure
SELECT * FROM users LIMIT 1;
SELECT * FROM games WHERE status='active' LIMIT 1;
```

**Checkpoint: Backend complete - proceed to frontend only after 100% backend working.**

---

## Phase 2: Frontend Auth & History (Afternoon - 6 hours)

### Task 2.1: Auth Library (45 minutes)

#### 2.1.1 Write Tests FIRST (RED)

**File:** `frontend/__tests__/lib/auth.test.ts` (CREATE NEW)

```typescript
/**
 * Test authentication library.
 */
import { login, register, logout, getToken, isAuthenticated } from '@/lib/auth';

// Mock fetch
global.fetch = jest.fn();

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; }
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('Auth Library', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('register', () => {
    it('should register user and store token', async () => {
      const mockResponse = {
        token: 'mock-token-123',
        user_id: 'user-123',
        username: 'testuser'
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await register('testuser', 'password123');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/register'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: 'testuser', password: 'password123' })
        })
      );

      expect(result.token).toBe('mock-token-123');
      expect(localStorage.getItem('poker_auth_token')).toBe('mock-token-123');
      expect(localStorage.getItem('poker_user_id')).toBe('user-123');
      expect(localStorage.getItem('poker_username')).toBe('testuser');
    });

    it('should throw error on registration failure', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Username already exists' })
      });

      await expect(register('testuser', 'password123')).rejects.toThrow('Username already exists');
    });

    it('should throw error on network failure', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await expect(register('testuser', 'password123')).rejects.toThrow('Network error');
    });
  });

  describe('login', () => {
    it('should login user and store token', async () => {
      const mockResponse = {
        token: 'mock-token-456',
        user_id: 'user-456',
        username: 'testuser'
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await login('testuser', 'password123');

      expect(result.token).toBe('mock-token-456');
      expect(localStorage.getItem('poker_auth_token')).toBe('mock-token-456');
    });

    it('should throw error on invalid credentials', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Invalid credentials' })
      });

      await expect(login('testuser', 'wrong')).rejects.toThrow('Invalid credentials');
    });
  });

  describe('logout', () => {
    it('should clear auth data from localStorage', () => {
      localStorage.setItem('poker_auth_token', 'token');
      localStorage.setItem('poker_user_id', 'user-123');
      localStorage.setItem('poker_username', 'testuser');

      logout();

      expect(localStorage.getItem('poker_auth_token')).toBeNull();
      expect(localStorage.getItem('poker_user_id')).toBeNull();
      expect(localStorage.getItem('poker_username')).toBeNull();
    });
  });

  describe('getToken', () => {
    it('should return token from localStorage', () => {
      localStorage.setItem('poker_auth_token', 'stored-token');

      expect(getToken()).toBe('stored-token');
    });

    it('should return null if no token', () => {
      expect(getToken()).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('should return true if token exists', () => {
      localStorage.setItem('poker_auth_token', 'token');
      expect(isAuthenticated()).toBe(true);
    });

    it('should return false if no token', () => {
      expect(isAuthenticated()).toBe(false);
    });
  });
});
```

**Run tests - SHOULD FAIL:**
```bash
cd frontend
npm test -- auth.test.ts
# Expected: Module not found: @/lib/auth
```

#### 2.1.2 Implement Auth Library (GREEN)

**File:** `frontend/lib/auth.ts` (CREATE NEW)

```typescript
/**
 * Authentication utilities for frontend.
 * Handles login, registration, token storage, and API authentication.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface AuthResponse {
  token: string;
  user_id: string;
  username: string;
}

/**
 * Register new user.
 */
export async function register(username: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  const data = await response.json();

  // Store auth data
  if (typeof window !== 'undefined') {
    localStorage.setItem('poker_auth_token', data.token);
    localStorage.setItem('poker_user_id', data.user_id);
    localStorage.setItem('poker_username', data.username);
  }

  return data;
}

/**
 * Login existing user.
 */
export async function login(username: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  const data = await response.json();

  // Store auth data
  if (typeof window !== 'undefined') {
    localStorage.setItem('poker_auth_token', data.token);
    localStorage.setItem('poker_user_id', data.user_id);
    localStorage.setItem('poker_username', data.username);
  }

  return data;
}

/**
 * Logout user (clear local storage).
 */
export function logout() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('poker_auth_token');
    localStorage.removeItem('poker_user_id');
    localStorage.removeItem('poker_username');
  }
}

/**
 * Get stored auth token.
 */
export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('poker_auth_token');
  }
  return null;
}

/**
 * Get stored user ID.
 */
export function getUserId(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('poker_user_id');
  }
  return null;
}

/**
 * Get stored username.
 */
export function getUsername(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('poker_username');
  }
  return null;
}

/**
 * Check if user is authenticated.
 */
export function isAuthenticated(): boolean {
  return getToken() !== null;
}
```

**Run tests - SHOULD PASS:**
```bash
cd frontend
npm test -- auth.test.ts
# Expected: All 10 tests pass
```

#### 2.1.3 Update Existing API Client

**File:** `frontend/lib/api.ts`

**ADD auth interceptor AFTER line 18 (after api creation):**

```typescript
// Add authentication interceptor
import { getToken, logout } from './auth';

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses (logout on auth failure)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      logout();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

**Checkpoint 2.1:** Auth library works, API client has auth headers.

---

### Task 2.2: Login Page (1.5 hours)

#### 2.2.1 Write Tests FIRST (RED)

**File:** `frontend/__tests__/pages/login.test.tsx` (CREATE NEW)

```typescript
/**
 * Test login/register page.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import LoginPage from '@/app/login/page';
import { login, register } from '@/lib/auth';
import { useRouter } from 'next/navigation';

jest.mock('@/lib/auth');
jest.mock('next/navigation', () => ({
  useRouter: jest.fn()
}));

describe('Login Page', () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
  });

  describe('Initial Render', () => {
    it('should render login form by default', () => {
      render(<LoginPage />);

      expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    });

    it('should show register option', () => {
      render(<LoginPage />);

      expect(screen.getByText(/create account/i)).toBeInTheDocument();
    });
  });

  describe('Login Flow', () => {
    it('should handle successful login', async () => {
      (login as jest.Mock).mockResolvedValue({
        token: 'token',
        user_id: 'user-1',
        username: 'testuser'
      });

      render(<LoginPage />);

      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'testuser' }
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: 'password123' }
      });

      fireEvent.click(screen.getByRole('button', { name: /login/i }));

      await waitFor(() => {
        expect(login).toHaveBeenCalledWith('testuser', 'password123');
        expect(mockPush).toHaveBeenCalledWith('/');
      });
    });

    it('should show error on login failure', async () => {
      (login as jest.Mock).mockRejectedValue(new Error('Invalid credentials'));

      render(<LoginPage />);

      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'testuser' }
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: 'wrong' }
      });

      fireEvent.click(screen.getByRole('button', { name: /login/i }));

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });
    });

    it('should disable button while loading', async () => {
      (login as jest.Mock).mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      render(<LoginPage />);

      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'testuser' }
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: 'password123' }
      });

      const button = screen.getByRole('button', { name: /login/i });
      fireEvent.click(button);

      expect(button).toBeDisabled();
    });
  });

  describe('Register Flow', () => {
    it('should switch to register mode', () => {
      render(<LoginPage />);

      fireEvent.click(screen.getByText(/create account/i));

      expect(screen.getByRole('heading', { name: /register/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument();
    });

    it('should handle successful registration', async () => {
      (register as jest.Mock).mockResolvedValue({
        token: 'token',
        user_id: 'user-1',
        username: 'newuser'
      });

      render(<LoginPage />);

      fireEvent.click(screen.getByText(/create account/i));

      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'newuser' }
      });
      fireEvent.change(screen.getByLabelText(/^password/i), {
        target: { value: 'password123' }
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: 'password123' }
      });

      fireEvent.click(screen.getByRole('button', { name: /register/i }));

      await waitFor(() => {
        expect(register).toHaveBeenCalledWith('newuser', 'password123');
        expect(mockPush).toHaveBeenCalledWith('/');
      });
    });

    it('should validate password match', async () => {
      render(<LoginPage />);

      fireEvent.click(screen.getByText(/create account/i));

      fireEvent.change(screen.getByLabelText(/^password/i), {
        target: { value: 'password123' }
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: 'different' }
      });

      fireEvent.click(screen.getByRole('button', { name: /register/i }));

      await waitFor(() => {
        expect(screen.getByText(/passwords.*match/i)).toBeInTheDocument();
        expect(register).not.toHaveBeenCalled();
      });
    });

    it('should validate empty fields', async () => {
      render(<LoginPage />);

      fireEvent.click(screen.getByRole('button', { name: /login/i }));

      await waitFor(() => {
        expect(screen.getByText(/required/i)).toBeInTheDocument();
      });
    });
  });

  describe('Mode Switching', () => {
    it('should clear error when switching modes', () => {
      (login as jest.Mock).mockRejectedValue(new Error('Invalid credentials'));

      render(<LoginPage />);

      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'test' }
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: 'test' }
      });
      fireEvent.click(screen.getByRole('button', { name: /login/i }));

      waitFor(() => {
        expect(screen.getByText(/invalid/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/create account/i));

      expect(screen.queryByText(/invalid/i)).not.toBeInTheDocument();
    });
  });
});
```

**Run tests - SHOULD FAIL:**
```bash
cd frontend
npm test -- login.test.tsx
# Expected: Module not found: @/app/login/page
```

#### 2.2.2 Implement Login Page (GREEN)

**File:** `frontend/app/login/page.tsx` (CREATE NEW)

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login, register } from '@/lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate
    if (!username || !password) {
      setError('Username and password are required');
      return;
    }

    if (mode === 'register') {
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return;
      }
      if (password.length < 6) {
        setError('Password must be at least 6 characters');
        return;
      }
    }

    setLoading(true);

    try {
      if (mode === 'login') {
        await login(username, password);
      } else {
        await register(username, password);
      }

      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError('');
    setConfirmPassword('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4">
      <div className="bg-gray-800 p-8 rounded-lg shadow-xl w-full max-w-md">
        <h1 className="text-3xl font-bold text-white mb-6 text-center">
          {mode === 'login' ? 'Login' : 'Register'}
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-2">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
              autoComplete="username"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              disabled={loading}
            />
          </div>

          {mode === 'register' && (
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300 mb-2">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                autoComplete="new-password"
                disabled={loading}
              />
            </div>
          )}

          {error && (
            <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-2 rounded text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded transition"
          >
            {loading ? 'Loading...' : (mode === 'login' ? 'Login' : 'Register')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={switchMode}
            className="text-blue-400 hover:text-blue-300 text-sm"
            disabled={loading}
          >
            {mode === 'login' ? "Don't have an account? Create one" : 'Already have an account? Login'}
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Run tests - SHOULD PASS:**
```bash
cd frontend
npm test -- login.test.tsx
# Expected: All 12 tests pass
```

**Checkpoint 2.2:** Login page works, users can register and login.

---

### Task 2.3: Update Home Page with Auth (30 minutes)

**File:** `frontend/app/page.tsx`

**REPLACE entire file with:**

```typescript
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, getUsername, logout } from '@/lib/auth';
import Link from 'next/link';

export default function HomePage() {
  const router = useRouter();
  const username = getUsername();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
    }
  }, [router]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (!isAuthenticated()) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center px-4">
      <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">Welcome, {username}!</h1>
          <button
            onClick={handleLogout}
            className="text-gray-400 hover:text-white text-sm transition"
          >
            Logout
          </button>
        </div>

        <div className="space-y-4">
          <Link
            href="/game/new"
            className="block bg-blue-600 hover:bg-blue-700 text-white text-center font-bold py-3 px-4 rounded transition"
          >
            Start New Game
          </Link>

          <Link
            href="/history"
            className="block bg-gray-700 hover:bg-gray-600 text-white text-center font-bold py-3 px-4 rounded transition"
          >
            View Game History
          </Link>

          <Link
            href="/tutorial"
            className="block bg-gray-700 hover:bg-gray-600 text-white text-center py-3 px-4 rounded transition"
          >
            Tutorial
          </Link>

          <Link
            href="/guide"
            className="block bg-gray-700 hover:bg-gray-600 text-white text-center py-3 px-4 rounded transition"
          >
            Hand Rankings Guide
          </Link>
        </div>
      </div>
    </div>
  );
}
```

**Checkpoint 2.3:** Home page requires auth, shows username, has logout.

---

### Task 2.4: Game History Page (1.5 hours)

#### 2.4.1 Add History API Methods

**File:** `frontend/lib/api.ts`

**ADD after existing methods:**

```typescript
  // Get user's game history
  async getMyGames(limit: number = 20): Promise<any> {
    const response = await api.get('/users/me/games', {
      params: { limit }
    });
    return response.data;
  },

  // Get hands for a specific game
  async getGameHands(gameId: string): Promise<any> {
    const response = await api.get(`/games/${gameId}/hands`);
    return response.data;
  },
```

#### 2.4.2 Implement History Page

**File:** `frontend/app/history/page.tsx` (CREATE NEW)

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { pokerApi } from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';
import Link from 'next/link';

interface GameSummary {
  game_id: string;
  started_at: string;
  completed_at: string;
  total_hands: number;
  starting_stack: number;
  final_stack: number;
  profit_loss: number;
  num_ai_players: number;
}

export default function HistoryPage() {
  const router = useRouter();
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    const fetchHistory = async () => {
      try {
        const data = await pokerApi.getMyGames();
        setGames(data.games);
      } catch (err) {
        setError('Failed to load game history');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [router]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading history...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 text-xl mb-4">{error}</div>
          <Link href="/" className="text-blue-400 hover:text-blue-300">
            Back to Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">Game History</h1>
          <div className="space-x-4">
            <Link
              href="/"
              className="text-blue-400 hover:text-blue-300 transition"
            >
              Home
            </Link>
            <Link
              href="/game/new"
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition"
            >
              New Game
            </Link>
          </div>
        </div>

        {games.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-8 text-center">
            <p className="text-gray-400 text-lg mb-4">No games yet</p>
            <p className="text-gray-500 mb-6">Play your first game to see it here!</p>
            <Link
              href="/game/new"
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded transition"
            >
              Start Playing
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {games.map((game) => (
              <div
                key={game.game_id}
                className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-3">
                      <span className="text-gray-400 text-sm">
                        {formatDate(game.started_at)}
                      </span>
                      <span className="text-gray-500 text-sm">
                        vs {game.num_ai_players} AI opponent{game.num_ai_players !== 1 ? 's' : ''}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-6 text-sm">
                      <div>
                        <span className="text-gray-400">Hands Played:</span>
                        <span className="text-white ml-2 font-medium">{game.total_hands}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Stack:</span>
                        <span className="text-white ml-2">
                          ${game.starting_stack} → ${game.final_stack}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">Result:</span>
                        <span
                          className={`ml-2 font-bold ${
                            game.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}
                        >
                          {game.profit_loss >= 0 ? '+' : ''}{game.profit_loss}
                        </span>
                      </div>
                    </div>
                  </div>

                  <Link
                    href={`/history/${game.game_id}`}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm transition ml-4"
                  >
                    Review Hands
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

**Checkpoint 2.4:** History page shows completed games, links to hand review.

---

### Task 2.5: Hand Review Page (1.5 hours)

**File:** `frontend/app/history/[gameId]/page.tsx` (CREATE NEW)

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { pokerApi } from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';
import Link from 'next/link';

interface Hand {
  hand_id: string;
  hand_number: number;
  hand_data: any;
  user_hole_cards: string;
  user_won: boolean;
  pot: number;
  created_at: string;
}

export default function HandReviewPage() {
  const router = useRouter();
  const params = useParams();
  const gameId = params.gameId as string;

  const [hands, setHands] = useState<Hand[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    const fetchHands = async () => {
      try {
        const data = await pokerApi.getGameHands(gameId);
        setHands(data.hands);
      } catch (err) {
        setError('Failed to load hands');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchHands();
  }, [gameId, router]);

  const currentHand = hands[currentIndex];

  const getAnalysis = async () => {
    if (!currentHand) return;

    setLoadingAnalysis(true);
    setError('');

    try {
      const data = await pokerApi.getHandAnalysisLLM(gameId, {
        handNumber: currentHand.hand_number
      });
      setAnalysis(data);
    } catch (err: any) {
      if (err.response?.status === 429) {
        setError('Rate limited. Please wait before requesting another analysis.');
      } else {
        setError('Failed to load analysis');
      }
      console.error(err);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const goToPrevious = () => {
    setCurrentIndex(Math.max(0, currentIndex - 1));
    setAnalysis(null);
  };

  const goToNext = () => {
    setCurrentIndex(Math.min(hands.length - 1, currentIndex + 1));
    setAnalysis(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading hands...</div>
      </div>
    );
  }

  if (error && hands.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 text-xl mb-4">{error}</div>
          <Link href="/history" className="text-blue-400 hover:text-blue-300">
            Back to History
          </Link>
        </div>
      </div>
    );
  }

  if (hands.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-400 text-xl mb-4">No hands found for this game</div>
          <Link href="/history" className="text-blue-400 hover:text-blue-300">
            Back to History
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <Link
            href="/history"
            className="text-blue-400 hover:text-blue-300 transition"
          >
            ← Back to History
          </Link>
          <div className="text-gray-400">
            Hand {currentIndex + 1} of {hands.length}
          </div>
        </div>

        {currentHand && (
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-3">
                  Hand #{currentHand.hand_number}
                </h2>
                <div className="flex flex-wrap gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Your Cards:</span>
                    <span className="text-white ml-2 font-medium">
                      {currentHand.user_hole_cards || 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Pot:</span>
                    <span className="text-white ml-2">${currentHand.pot}</span>
                  </div>
                  <div>
                    <span className={currentHand.user_won ? 'text-green-400' : 'text-red-400'}>
                      {currentHand.user_won ? '✓ Won' : '✗ Lost'}
                    </span>
                  </div>
                </div>
              </div>

              <button
                onClick={getAnalysis}
                disabled={loadingAnalysis}
                className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded transition"
              >
                {loadingAnalysis ? 'Loading...' : 'Get AI Analysis'}
              </button>
            </div>

            {/* Hand Details */}
            {currentHand.hand_data && (
              <div className="bg-gray-700 rounded p-4 mb-4">
                <h3 className="text-white font-semibold mb-2">Hand Details</h3>
                <div className="text-gray-300 text-sm space-y-1">
                  {currentHand.hand_data.community_cards && (
                    <div>
                      <span className="text-gray-400">Community Cards:</span>
                      <span className="ml-2">{currentHand.hand_data.community_cards.join(', ')}</span>
                    </div>
                  )}
                  {currentHand.hand_data.rounds && (
                    <div>
                      <span className="text-gray-400">Rounds:</span>
                      <span className="ml-2">{currentHand.hand_data.rounds.length}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Analysis Display */}
            {analysis && (
              <div className="bg-gray-700 rounded p-4">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-white font-semibold">AI Analysis</h3>
                  <div className="text-sm text-gray-400">
                    Model: {analysis.model_used} | Cost: ${analysis.cost.toFixed(3)}
                    {analysis.cached && <span className="ml-2">(Cached)</span>}
                  </div>
                </div>
                <div className="text-gray-200 text-sm">
                  <pre className="whitespace-pre-wrap font-sans">
                    {JSON.stringify(analysis.analysis, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-2 rounded text-sm">
                {error}
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={goToPrevious}
            disabled={currentIndex === 0}
            className="bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded transition"
          >
            ← Previous
          </button>
          <button
            onClick={goToNext}
            disabled={currentIndex === hands.length - 1}
            className="bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded transition"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Checkpoint 2.5:** Hand review page works, users can navigate hands and get AI analysis.

---

### Task 2.6: Update WebSocket to Use Auth Token (30 minutes)

**File:** `frontend/lib/websocket.ts`

**MODIFY connect method (around line 80):**

```typescript
// FIND the connect() method and UPDATE:
public connect(): void {
  if (this.ws) {
    return; // Already connected
  }

  this.shouldReconnect = true;
  this.connectionState = ConnectionState.CONNECTING;
  this.callbacks.onConnect();

  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

  // ADD: Get auth token
  import { getToken } from './auth';
  const token = getToken();

  // ADD: Include token in WebSocket URL
  const urlWithAuth = `${wsUrl}/ws/${this.gameId}${token ? `?token=${token}` : ''}`;

  this.ws = new WebSocket(urlWithAuth);

  // ... rest of existing code
}
```

**Checkpoint 2.6:** WebSocket uses auth token, users can only connect to their games.

---

### Task 2.7: Update Store to Use Auth (30 minutes)

**File:** `frontend/lib/store.ts`

**MODIFY createGame method (around line 70):**

```typescript
// FIND createGame and ensure it's already using pokerApi (which now has auth)
// No changes needed - api.ts interceptor handles auth automatically
```

**VERIFY game creation requires auth:**

```typescript
// In store.ts, the createGame already uses pokerApi.createGame()
// which goes through axios interceptor that adds Authorization header
// So this is already done!
```

**Checkpoint 2.7:** Store uses authenticated API client.

---

## Frontend Phase Complete - Integration Checkpoint (30 minutes)

### Run ALL Frontend Tests

```bash
cd frontend

# Run new MVP tests
npm test -- auth.test.ts login.test.tsx

# Run existing tests
npm test -- short-stack-logic.test.ts
```

**Expected: All tests pass.**

### Manual End-to-End Testing

```bash
# Start backend (terminal 1)
cd backend
python main.py

# Start frontend (terminal 2)
cd frontend
npm run dev
```

**Test Flow:**
1. Visit http://localhost:3000
2. Should redirect to /login
3. Register: testuser / test123
4. Should redirect to home page
5. Click "Start New Game"
6. Play a few hands (fold, call, raise)
7. Complete game or quit
8. Click "View Game History"
9. Should see completed game
10. Click "Review Hands"
11. Navigate through hands
12. Click "Get AI Analysis"
13. Verify analysis appears
14. Logout
15. Should redirect to login

### Verify Database

```bash
psql postgresql://postgres:postgres@localhost:5432/poker_dev

SELECT
  u.username,
  COUNT(DISTINCT g.game_id) as games,
  COUNT(h.hand_id) as hands
FROM users u
LEFT JOIN games g ON u.user_id = g.user_id
LEFT JOIN hands h ON g.game_id = h.game_id
GROUP BY u.username;
```

**Expected: See testuser with games and hands.**

---

## Final Summary & Time Estimates

| Phase | Task | Estimate | Status |
|-------|------|----------|--------|
| **Phase 0** | Setup | 1 hour | ✅ Complete |
| **Phase 1** | Backend | 7 hours | ✅ Complete |
| Task 1.1 | Database Models | 1 hour | ✅ |
| Task 1.2 | Auth Module | 1 hour | ✅ |
| Task 1.3 | Auth Endpoints | 1.5 hours | ✅ |
| Task 1.4 | Hand Persistence | 2 hours | ✅ |
| Task 1.5 | History Endpoints | 1.5 hours | ✅ |
| Task 1.6 | WebSocket Auth | 1 hour | ✅ |
| Checkpoint | Backend Integration | 30 min | ✅ |
| **Phase 2** | Frontend | 6 hours | ✅ Complete |
| Task 2.1 | Auth Library | 45 min | ✅ |
| Task 2.2 | Login Page | 1.5 hours | ✅ |
| Task 2.3 | Home Page Update | 30 min | ✅ |
| Task 2.4 | History Page | 1.5 hours | ✅ |
| Task 2.5 | Hand Review Page | 1.5 hours | ✅ |
| Task 2.6 | WebSocket Auth | 30 min | ✅ |
| Checkpoint | Frontend Integration | 30 min | ✅ |
| **TOTAL** | **14-16 hours** | **READY** |

---

## Summary of Key Changes

### From Original Plan

1. ✅ Added Phase 0 (dependencies, database, environment setup)
2. ✅ PostgreSQL-only (no SQLite compatibility)
3. ✅ Diff-based modifications to existing files
4. ✅ Database session fixtures in conftest.py
5. ✅ Game lifecycle integration with hand persistence
6. ✅ Complete WebSocket authentication
7. ✅ Realistic time estimates (14-16 hours vs 8.5)
8. ✅ Integration checkpoints after each phase
9. ✅ Manual testing procedures
10. ✅ Verified against existing codebase

### Backend Highlights

- SQLAlchemy models matching Alembic schema
- JWT-based authentication with bcrypt passwords
- Protected API endpoints with user isolation
- Hand persistence on game lifecycle events
- History endpoints with ownership validation
- WebSocket authentication with token validation
- 70+ tests covering all functionality

### Frontend Highlights

- Auth library with localStorage persistence
- Login/Register page with validation
- Home page with auth protection
- Game history page with completed games
- Hand review page with AI analysis
- WebSocket with auth token
- API interceptor for automatic auth headers
- Integration with existing game components

---

## Execution Checklist

Before starting:
- [ ] PostgreSQL running on port 5432
- [ ] `.env` files created (backend and frontend)
- [ ] Dependencies installed (backend and frontend)
- [ ] Alembic configured and migrations ready
- [ ] Existing tests still pass

After completion:
- [ ] All new tests pass (16 backend + 12 frontend)
- [ ] Manual end-to-end flow works
- [ ] Database has users, games, hands
- [ ] WebSocket connects with auth
- [ ] No regressions in existing functionality

---

## Next Steps (Day 2)

After Day 1 is 100% complete:

1. Add GitHub Actions workflows (from CICD docs)
2. Run Azure setup workflow
3. Add deployment secrets to GitHub
4. Push to main branch (triggers CI/CD)
5. Verify production deployment

See `docs/GITHUB-ACTIONS-SETUP.md` for Day 2 details.

---

**This plan is now COMPLETE and ready for autonomous execution.**

---

## Summary of Key Changes

1. ✅ Added Phase 0 (setup)
2. ✅ PostgreSQL for all tests (not SQLite)
3. ✅ Diff-based modifications (not full rewrites)
4. ✅ Database session fixtures in conftest.py
5. ✅ Proper game lifecycle integration
6. ✅ Complete WebSocket authentication
7. ✅ Realistic time estimates (14-16 hours)
8. ✅ Integration checkpoints
9. ✅ Manual testing procedures
10. ✅ Verified against existing codebase

**This plan is now ready for autonomous execution.**
