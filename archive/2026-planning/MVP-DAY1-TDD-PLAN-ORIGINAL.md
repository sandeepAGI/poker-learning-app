# MVP Day 1 Implementation - TDD Execution Plan

**Date:** 2026-01-13
**Target:** Complete Day 1 (Backend + Frontend) using Test-Driven Development
**Execution Mode:** Autonomous with clear checkpoints
**Estimated Time:** 8 hours (4 hours backend + 4 hours frontend)

---

## TDD Workflow

For each feature, follow this cycle:

1. **RED:** Write failing tests first
2. **GREEN:** Write minimal code to pass tests
3. **REFACTOR:** Clean up code while keeping tests green
4. **VERIFY:** Run full test suite to ensure no regressions

---

## Phase 1: Backend Auth & Database (Morning - 4 hours)

### Task 1.1: Auth Module - Password Hashing (30 minutes)

#### 1.1.1 Write Tests FIRST (RED)

**File:** `backend/tests/test_auth.py`

```python
import pytest
from auth import hash_password, verify_password

class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password_returns_different_hash_each_time(self):
        """Same password should produce different hashes (bcrypt salt)"""
        password = "test123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert len(hash1) == 60  # bcrypt hash length

    def test_verify_password_with_correct_password(self):
        """Correct password should verify successfully"""
        password = "test123"
        password_hash = hash_password(password)

        assert verify_password(password, password_hash) is True

    def test_verify_password_with_wrong_password(self):
        """Wrong password should fail verification"""
        password = "test123"
        wrong_password = "wrong456"
        password_hash = hash_password(password)

        assert verify_password(wrong_password, password_hash) is False

    def test_hash_password_with_empty_string(self):
        """Empty password should still hash (validation done elsewhere)"""
        password = ""
        password_hash = hash_password(password)

        assert password_hash is not None
        assert len(password_hash) == 60
```

**Expected:** Tests fail (auth.py doesn't exist)

#### 1.1.2 Implement (GREEN)

**File:** `backend/auth.py`

```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode(), password_hash.encode())
```

**Expected:** Tests pass

---

### Task 1.2: Auth Module - JWT Tokens (30 minutes)

#### 1.2.1 Write Tests FIRST (RED)

**File:** `backend/tests/test_auth.py` (append)

```python
from auth import create_token, verify_token
from datetime import datetime, timedelta
import jwt
import os

class TestJWTTokens:
    """Test JWT token creation and verification"""

    def test_create_token_returns_valid_jwt(self):
        """Token should be a valid JWT string"""
        user_id = "test-user-123"
        token = create_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0
        # Should have 3 parts separated by dots (header.payload.signature)
        assert len(token.split('.')) == 3

    def test_create_token_includes_user_id(self):
        """Token payload should contain user_id in 'sub' claim"""
        user_id = "test-user-123"
        token = create_token(user_id)

        # Decode without verification to check payload
        secret = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION")
        payload = jwt.decode(token, secret, algorithms=["HS256"])

        assert payload["sub"] == user_id

    def test_create_token_sets_expiration(self):
        """Token should expire in 30 days"""
        user_id = "test-user-123"
        token = create_token(user_id)

        secret = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION")
        payload = jwt.decode(token, secret, algorithms=["HS256"])

        # Check expiration is ~30 days from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + timedelta(days=30)
        time_diff = abs((exp_time - expected_exp).total_seconds())

        assert time_diff < 5  # Within 5 seconds

    def test_verify_token_with_valid_token(self):
        """Valid token should return user_id"""
        user_id = "test-user-123"
        token = create_token(user_id)

        # Mock HTTPAuthorizationCredentials
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )

        result = verify_token(credentials)
        assert result == user_id

    def test_verify_token_with_expired_token(self):
        """Expired token should raise HTTPException with 401"""
        from fastapi import HTTPException

        user_id = "test-user-123"
        # Create token with -1 day expiration
        secret = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION")
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() - timedelta(days=1)
        }
        expired_token = jwt.encode(payload, secret, algorithm="HS256")

        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=expired_token
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_token(credentials)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_verify_token_with_invalid_signature(self):
        """Token with wrong signature should raise HTTPException with 401"""
        from fastapi import HTTPException

        # Create token with wrong secret
        user_id = "test-user-123"
        wrong_secret = "wrong-secret"
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(days=30)
        }
        invalid_token = jwt.encode(payload, wrong_secret, algorithm="HS256")

        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=invalid_token
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_token(credentials)

        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()
```

**Expected:** Tests fail (create_token, verify_token don't exist)

#### 1.2.2 Implement (GREEN)

**File:** `backend/auth.py` (append)

```python
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION")
security = HTTPBearer()

def create_token(user_id: str) -> str:
    """Create JWT token for user"""
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Expected:** Tests pass

---

### Task 1.3: Database Models (45 minutes)

#### 1.3.1 Write Tests FIRST (RED)

**File:** `backend/tests/test_models.py`

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User, Game, Hand, AnalysisCache
from datetime import datetime
import uuid

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)
    session = TestSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)

class TestUserModel:
    """Test User model"""

    def test_create_user(self, db_session: Session):
        """Should create user with all required fields"""
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

    def test_username_unique_constraint(self, db_session: Session):
        """Should prevent duplicate usernames"""
        user1 = User(user_id="user-1", username="testuser", password_hash="hash1")
        user2 = User(user_id="user-2", username="testuser", password_hash="hash2")

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

class TestGameModel:
    """Test Game model"""

    def test_create_game(self, db_session: Session):
        """Should create game linked to user"""
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

    def test_game_cascade_delete(self, db_session: Session):
        """Deleting user should delete their games"""
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

class TestHandModel:
    """Test Hand model"""

    def test_create_hand(self, db_session: Session):
        """Should create hand with JSONB data"""
        # Setup user and game
        user = User(user_id="user-1", username="test", password_hash="hash")
        game = Game(game_id="game-1", user_id="user-1", starting_stack=1000)
        db_session.add_all([user, game])
        db_session.commit()

        # Create hand
        hand_data = {
            "rounds": [{"actions": [{"action": "fold"}]}],
            "pot": 150
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

        # Query back
        saved_hand = db_session.query(Hand).first()
        assert saved_hand is not None
        assert saved_hand.hand_data["pot"] == 150
        assert saved_hand.user_hole_cards == "AsKs"

class TestAnalysisCacheModel:
    """Test AnalysisCache model"""

    def test_create_analysis_cache(self, db_session: Session):
        """Should cache analysis with cost tracking"""
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

        # Get hand_id
        hand_id = db_session.query(Hand).first().hand_id

        # Create cache entry
        analysis = AnalysisCache(
            user_id="user-1",
            hand_id=hand_id,
            analysis_type="quick",
            model_used="haiku-4.5",
            cost=0.016,
            analysis_data={"verdict": "good play"}
        )
        db_session.add(analysis)
        db_session.commit()

        # Query back
        saved = db_session.query(AnalysisCache).first()
        assert saved is not None
        assert saved.cost == 0.016
        assert saved.model_used == "haiku-4.5"
```

**Expected:** Tests fail (models.py doesn't exist)

#### 1.3.2 Implement (GREEN)

**File:** `backend/models.py`

```python
from sqlalchemy import Column, String, Integer, Float, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    user_id = Column(String(50), primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    last_login = Column(TIMESTAMP)

class Game(Base):
    __tablename__ = 'games'

    game_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    started_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    completed_at = Column(TIMESTAMP)
    num_ai_players = Column(Integer)
    starting_stack = Column(Integer)
    final_stack = Column(Integer)
    profit_loss = Column(Integer)
    total_hands = Column(Integer, server_default='0')
    status = Column(String(20), server_default='active')

class Hand(Base):
    __tablename__ = 'hands'

    hand_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    game_id = Column(String(50), ForeignKey('games.game_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    hand_number = Column(Integer, nullable=False)
    hand_data = Column(JSONB, nullable=False)
    user_hole_cards = Column(String(10))
    user_won = Column(Boolean)
    pot = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

class AnalysisCache(Base):
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

**Expected:** Tests pass

---

### Task 1.4: Auth Endpoints (1 hour)

#### 1.4.1 Write Tests FIRST (RED)

**File:** `backend/tests/test_auth_endpoints.py`

```python
import pytest
from fastapi.testclient import TestClient
from main import app
from models import Base, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from auth import hash_password

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def client():
    """Create test client with test database"""
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

    from main import get_db
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    client = TestClient(app)

    yield client

    # Cleanup
    Base.metadata.drop_all(engine)
    app.dependency_overrides.clear()

class TestRegisterEndpoint:
    """Test /auth/register endpoint"""

    def test_register_new_user(self, client):
        """Should register new user and return token"""
        response = client.post(
            "/auth/register",
            json={"username": "testuser", "password": "test123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user_id" in data
        assert data["username"] == "testuser"
        assert len(data["token"]) > 0

    def test_register_duplicate_username(self, client):
        """Should reject duplicate usernames"""
        # Register first user
        client.post("/auth/register", json={"username": "testuser", "password": "test123"})

        # Try to register again
        response = client.post(
            "/auth/register",
            json={"username": "testuser", "password": "different"}
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_missing_fields(self, client):
        """Should reject requests with missing fields"""
        response = client.post("/auth/register", json={"username": "testuser"})
        assert response.status_code == 422  # Validation error

class TestLoginEndpoint:
    """Test /auth/login endpoint"""

    def test_login_with_correct_credentials(self, client):
        """Should login and return token"""
        # Register user first
        client.post("/auth/register", json={"username": "testuser", "password": "test123"})

        # Login
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "test123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["username"] == "testuser"

    def test_login_with_wrong_password(self, client):
        """Should reject wrong password"""
        # Register user
        client.post("/auth/register", json={"username": "testuser", "password": "test123"})

        # Try wrong password
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "wrong"}
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Should reject nonexistent user"""
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "test123"}
        )

        assert response.status_code == 401
```

**Expected:** Tests fail (endpoints don't exist)

#### 1.4.2 Implement (GREEN)

**File:** `backend/main.py` (add after imports)

```python
from auth import hash_password, verify_password, create_token, verify_token
from models import User, Game, Hand, AnalysisCache, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import uuid

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/poker_dev")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth endpoints
@app.post("/auth/register")
async def register(username: str, password: str, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if username exists
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create user
    user = User(
        user_id=str(uuid.uuid4()),
        username=username,
        password_hash=hash_password(password)
    )
    db.add(user)
    db.commit()

    return {
        "token": create_token(user.user_id),
        "user_id": user.user_id,
        "username": username
    }

@app.post("/auth/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return {
        "token": create_token(user.user_id),
        "user_id": user.user_id,
        "username": username
    }
```

**Expected:** Tests pass

**Checkpoint 1.4: Run all backend tests**
```bash
cd backend
PYTHONPATH=. pytest tests/test_auth*.py -v
```

---

### Task 1.5: Game Persistence - Save Hands to Database (1 hour)

#### 1.5.1 Write Tests FIRST (RED)

**File:** `backend/tests/test_game_persistence.py`

```python
import pytest
from fastapi.testclient import TestClient
from main import app, get_db
from models import Base, User, Game, Hand
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def auth_client():
    """Create authenticated test client"""
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

    # Register and get token
    response = client.post("/auth/register", json={"username": "testuser", "password": "test123"})
    token = response.json()["token"]

    # Set auth header
    client.headers = {"Authorization": f"Bearer {token}"}

    yield client

    Base.metadata.drop_all(engine)
    app.dependency_overrides.clear()

class TestGameCreationWithAuth:
    """Test game creation requires auth"""

    def test_create_game_with_auth(self, auth_client):
        """Should create game for authenticated user"""
        response = auth_client.post("/games", json={"player_name": "Test", "ai_count": 3})

        assert response.status_code == 200
        assert "game_id" in response.json()

    def test_create_game_without_auth(self):
        """Should reject game creation without auth"""
        client = TestClient(app)
        response = client.post("/games", json={"player_name": "Test", "ai_count": 3})

        assert response.status_code == 401

class TestHandPersistence:
    """Test hands are saved to database"""

    def test_completed_hand_saves_to_database(self, auth_client):
        """When hand completes, should save to database"""
        # Create game
        game_response = auth_client.post("/games", json={"player_name": "Test", "ai_count": 1})
        game_id = game_response.json()["game_id"]

        # Play hand to completion (fold to finish quickly)
        auth_client.post(f"/games/{game_id}/actions", json={"action": "fold"})

        # Check database has hand record
        # Note: This requires a helper endpoint or direct DB query
        # For now, verify via game state
        state = auth_client.get(f"/games/{game_id}").json()
        assert state["hand_count"] >= 1

    def test_hand_includes_required_fields(self, auth_client):
        """Saved hand should have all required fields"""
        # This test will verify the structure once we add a history endpoint
        pass  # TODO: Implement after history endpoint

class TestGameCompletion:
    """Test game completion updates database"""

    def test_game_completion_saves_final_stack(self, auth_client):
        """When game ends, should save final stack and profit/loss"""
        # This will be tested once we have game-over scenarios
        pass  # TODO: Implement after game completion logic
```

**Expected:** Tests fail (game creation doesn't require auth yet)

#### 1.5.2 Implement (GREEN)

**File:** `backend/main.py` (update create_game and game lifecycle)

```python
# Update create_game endpoint
@app.post("/games", response_model=Dict[str, str])
async def create_game(
    request: CreateGameRequest,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create a new poker game (requires auth)"""
    if request.ai_count < 1 or request.ai_count > 5:
        raise HTTPException(status_code=400, detail="AI count must be between 1 and 5")

    game_id = str(uuid.uuid4())
    game = PokerGame(request.player_name, request.ai_count)
    game.start_new_hand(process_ai=False)

    # Save game to database
    db_game = Game(
        game_id=game_id,
        user_id=user_id,
        num_ai_players=request.ai_count,
        starting_stack=game.players[0].stack,
        status="active"
    )
    db.add(db_game)
    db.commit()

    # Store in memory
    games[game_id] = (game, time.time())

    return {"game_id": game_id}

# Add hand completion hook
def save_completed_hand(game_id: str, game: PokerGame, db: Session):
    """Save completed hand to database"""
    if not game.last_hand_summary:
        return

    hand_summary = game.last_hand_summary
    human_player = next(p for p in game.players if p.is_human)

    # Serialize hand data
    hand_data = {
        "rounds": hand_summary.rounds,
        "pot": hand_summary.pot,
        "winner": hand_summary.winner,
        "community_cards": game.community_cards
    }

    # Create hand record
    hand = Hand(
        game_id=game_id,
        user_id=db.query(Game).filter(Game.game_id == game_id).first().user_id,
        hand_number=hand_summary.hand_number,
        hand_data=hand_data,
        user_hole_cards=",".join(hand_summary.showdown_hands.get(human_player.player_id, [])),
        user_won=hand_summary.winner == human_player.player_id,
        pot=hand_summary.pot
    )
    db.add(hand)

    # Update game total_hands
    db_game = db.query(Game).filter(Game.game_id == game_id).first()
    db_game.total_hands += 1

    db.commit()
```

**Expected:** Tests pass

---

### Task 1.6: History Endpoints (45 minutes)

#### 1.6.1 Write Tests FIRST (RED)

**File:** `backend/tests/test_history_endpoints.py`

```python
import pytest
from fastapi.testclient import TestClient
from main import app, get_db
from models import Base, User, Game, Hand
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def auth_client_with_history():
    """Create authenticated client with game history"""
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
            starting_stack=1000,
            final_stack=1200 + (i * 100),
            profit_loss=200 + (i * 100),
            total_hands=10 + i,
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
                    hand_data={"pot": 100 * (j + 1)},
                    user_hole_cards="AsKs",
                    user_won=(j % 2 == 0),
                    pot=100 * (j + 1)
                )
                db.add(hand)

    db.commit()
    db.close()

    yield client, user_id

    Base.metadata.drop_all(engine)
    app.dependency_overrides.clear()

class TestGetMyGamesEndpoint:
    """Test /users/me/games endpoint"""

    def test_get_my_games_requires_auth(self):
        """Should require authentication"""
        client = TestClient(app)
        response = client.get("/users/me/games")
        assert response.status_code == 401

    def test_get_my_games_returns_completed_games(self, auth_client_with_history):
        """Should return user's completed games"""
        client, user_id = auth_client_with_history
        response = client.get("/users/me/games")

        assert response.status_code == 200
        data = response.json()
        assert "games" in data
        assert len(data["games"]) == 3

        # Verify game structure
        game = data["games"][0]
        assert "game_id" in game
        assert "started_at" in game
        assert "total_hands" in game
        assert "profit_loss" in game

    def test_get_my_games_ordered_by_date(self, auth_client_with_history):
        """Should return games ordered by most recent first"""
        client, user_id = auth_client_with_history
        response = client.get("/users/me/games")

        games = response.json()["games"]
        # Verify descending order (most recent first)
        for i in range(len(games) - 1):
            assert games[i]["started_at"] >= games[i + 1]["started_at"]

    def test_get_my_games_limit(self, auth_client_with_history):
        """Should respect limit parameter"""
        client, user_id = auth_client_with_history
        response = client.get("/users/me/games?limit=2")

        games = response.json()["games"]
        assert len(games) == 2

class TestGetGameHandsEndpoint:
    """Test /games/{game_id}/hands endpoint"""

    def test_get_game_hands_requires_auth(self):
        """Should require authentication"""
        client = TestClient(app)
        response = client.get("/games/game-0/hands")
        assert response.status_code == 401

    def test_get_game_hands_returns_all_hands(self, auth_client_with_history):
        """Should return all hands for a game"""
        client, user_id = auth_client_with_history
        response = client.get("/games/game-0/hands")

        assert response.status_code == 200
        data = response.json()
        assert "hands" in data
        assert len(data["hands"]) == 5

        # Verify hand structure
        hand = data["hands"][0]
        assert "hand_number" in hand
        assert "hand_data" in hand
        assert "user_won" in hand
        assert "pot" in hand

    def test_get_game_hands_ownership_check(self, auth_client_with_history):
        """Should only return hands for user's own games"""
        client, user_id = auth_client_with_history

        # Try to access another user's game (doesn't exist in test)
        response = client.get("/games/other-user-game/hands")
        assert response.status_code == 404

    def test_get_game_hands_ordered_by_hand_number(self, auth_client_with_history):
        """Should return hands in order"""
        client, user_id = auth_client_with_history
        response = client.get("/games/game-0/hands")

        hands = response.json()["hands"]
        for i in range(len(hands)):
            assert hands[i]["hand_number"] == i + 1
```

**Expected:** Tests fail (endpoints don't exist)

#### 1.6.2 Implement (GREEN)

**File:** `backend/main.py` (add endpoints)

```python
@app.get("/users/me/games")
async def get_my_games(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """Get user's completed games"""
    games = db.query(Game).filter(
        Game.user_id == user_id,
        Game.status == "completed"
    ).order_by(Game.started_at.desc()).limit(limit).all()

    return {
        "games": [
            {
                "game_id": game.game_id,
                "started_at": game.started_at.isoformat() if game.started_at else None,
                "completed_at": game.completed_at.isoformat() if game.completed_at else None,
                "total_hands": game.total_hands,
                "starting_stack": game.starting_stack,
                "final_stack": game.final_stack,
                "profit_loss": game.profit_loss,
                "num_ai_players": game.num_ai_players
            }
            for game in games
        ]
    }

@app.get("/games/{game_id}/hands")
async def get_game_hands(
    game_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all hands for a game"""
    # Verify game belongs to user
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
                "hand_id": str(hand.hand_id),
                "hand_number": hand.hand_number,
                "hand_data": hand.hand_data,
                "user_hole_cards": hand.user_hole_cards,
                "user_won": hand.user_won,
                "pot": hand.pot,
                "created_at": hand.created_at.isoformat() if hand.created_at else None
            }
            for hand in hands
        ]
    }
```

**Expected:** Tests pass

**Checkpoint 1.6: Run ALL backend tests**
```bash
cd backend
PYTHONPATH=. pytest tests/ -v
```

---

## Phase 2: Frontend Auth & History (Afternoon - 4 hours)

### Task 2.1: Auth Library (30 minutes)

#### 2.1.1 Write Tests FIRST (RED)

**File:** `frontend/__tests__/lib/auth.test.ts`

```typescript
import { login, register, logout, getToken, apiClient, isAuthenticated } from '@/lib/auth';

// Mock fetch
global.fetch = jest.fn();

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
          body: JSON.stringify({ username: 'testuser', password: 'password123' })
        })
      );

      expect(result.token).toBe('mock-token-123');
      expect(localStorage.getItem('poker_auth_token')).toBe('mock-token-123');
      expect(localStorage.getItem('poker_user_id')).toBe('user-123');
    });

    it('should throw error on registration failure', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Username already exists' })
      });

      await expect(register('testuser', 'password123')).rejects.toThrow('Username already exists');
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
  });

  describe('logout', () => {
    it('should clear auth data from localStorage', () => {
      localStorage.setItem('poker_auth_token', 'token');
      localStorage.setItem('poker_user_id', 'user-123');

      logout();

      expect(localStorage.getItem('poker_auth_token')).toBeNull();
      expect(localStorage.getItem('poker_user_id')).toBeNull();
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

  describe('apiClient', () => {
    it('should add auth header to requests', async () => {
      localStorage.setItem('poker_auth_token', 'token-789');

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'success' })
      });

      await apiClient('/api/test', { method: 'GET' });

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer token-789'
          })
        })
      );
    });

    it('should redirect to login on 401', async () => {
      const mockPush = jest.fn();
      jest.mock('next/navigation', () => ({
        useRouter: () => ({ push: mockPush })
      }));

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' })
      });

      await expect(apiClient('/api/test')).rejects.toThrow();
      // Token should be cleared on 401
      expect(localStorage.getItem('poker_auth_token')).toBeNull();
    });
  });
});
```

**Expected:** Tests fail (auth.ts doesn't exist)

#### 2.1.2 Implement (GREEN)

**File:** `frontend/lib/auth.ts`

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface AuthResponse {
  token: string;
  user_id: string;
  username: string;
}

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
  localStorage.setItem('poker_auth_token', data.token);
  localStorage.setItem('poker_user_id', data.user_id);
  localStorage.setItem('poker_username', data.username);

  return data;
}

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
  localStorage.setItem('poker_auth_token', data.token);
  localStorage.setItem('poker_user_id', data.user_id);
  localStorage.setItem('poker_username', data.username);

  return data;
}

export function logout() {
  localStorage.removeItem('poker_auth_token');
  localStorage.removeItem('poker_user_id');
  localStorage.removeItem('poker_username');
}

export function getToken(): string | null {
  return localStorage.getItem('poker_auth_token');
}

export function getUserId(): string | null {
  return localStorage.getItem('poker_user_id');
}

export function getUsername(): string | null {
  return localStorage.getItem('poker_username');
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}

export async function apiClient(url: string, options: RequestInit = {}) {
  const token = getToken();

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${url}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    // Token expired or invalid
    logout();
    throw new Error('Authentication required');
  }

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Request failed');
  }

  return response.json();
}
```

**Expected:** Tests pass

---

### Task 2.2: Login Page (1 hour)

#### 2.2.1 Write Tests FIRST (RED)

**File:** `frontend/__tests__/pages/login.test.tsx`

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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

  it('should render login form by default', () => {
    render(<LoginPage />);

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

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

  it('should switch to register mode', () => {
    render(<LoginPage />);

    fireEvent.click(screen.getByText(/create account/i));

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
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' }
    });

    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(register).toHaveBeenCalledWith('newuser', 'password123');
      expect(mockPush).toHaveBeenCalledWith('/');
    });
  });

  it('should require password confirmation in register mode', () => {
    render(<LoginPage />);

    fireEvent.click(screen.getByText(/create account/i));

    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
  });

  it('should validate password match in register mode', async () => {
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
});
```

**Expected:** Tests fail (page doesn't exist)

#### 2.2.2 Implement (GREEN)

**File:** `frontend/app/login/page.tsx`

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

    if (mode === 'register' && password !== confirmPassword) {
      setError('Passwords do not match');
      return;
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 p-8 rounded-lg shadow-xl w-96">
        <h1 className="text-3xl font-bold text-white mb-6 text-center">
          {mode === 'login' ? 'Login' : 'Create Account'}
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
              />
            </div>
          )}

          {error && (
            <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-2 rounded">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded transition"
          >
            {loading ? 'Loading...' : (mode === 'login' ? 'Login' : 'Register')}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={() => {
              setMode(mode === 'login' ? 'register' : 'login');
              setError('');
              setConfirmPassword('');
            }}
            className="text-blue-400 hover:text-blue-300 text-sm"
          >
            {mode === 'login' ? 'Need an account? Create one' : 'Have an account? Login'}
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Expected:** Tests pass

---

### Task 2.3: Game History Page (1.5 hours)

#### 2.3.1 Write Tests FIRST (RED)

**File:** `frontend/__tests__/pages/history.test.tsx`

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import HistoryPage from '@/app/history/page';
import { apiClient } from '@/lib/auth';

jest.mock('@/lib/auth');
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({ push: jest.fn() }))
}));

describe('History Page', () => {
  const mockGames = [
    {
      game_id: 'game-1',
      started_at: '2026-01-13T10:00:00Z',
      completed_at: '2026-01-13T11:00:00Z',
      total_hands: 15,
      starting_stack: 1000,
      final_stack: 1300,
      profit_loss: 300,
      num_ai_players: 3
    },
    {
      game_id: 'game-2',
      started_at: '2026-01-12T10:00:00Z',
      completed_at: '2026-01-12T10:30:00Z',
      total_hands: 8,
      starting_stack: 1000,
      final_stack: 800,
      profit_loss: -200,
      num_ai_players: 2
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should display loading state initially', () => {
    (apiClient as jest.Mock).mockImplementation(() => new Promise(() => {}));

    render(<HistoryPage />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should fetch and display game history', async () => {
    (apiClient as jest.Mock).mockResolvedValue({ games: mockGames });

    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText(/game history/i)).toBeInTheDocument();
      expect(screen.getByText(/15 hands/i)).toBeInTheDocument();
      expect(screen.getByText(/8 hands/i)).toBeInTheDocument();
    });
  });

  it('should display profit/loss with correct styling', async () => {
    (apiClient as jest.Mock).mockResolvedValue({ games: mockGames });

    render(<HistoryPage />);

    await waitFor(() => {
      const profitElement = screen.getByText(/\+300/);
      const lossElement = screen.getByText(/-200/);

      expect(profitElement).toHaveClass('text-green-400');
      expect(lossElement).toHaveClass('text-red-400');
    });
  });

  it('should show empty state when no games', async () => {
    (apiClient as jest.Mock).mockResolvedValue({ games: [] });

    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText(/no games yet/i)).toBeInTheDocument();
    });
  });

  it('should link to hand review page', async () => {
    (apiClient as jest.Mock).mockResolvedValue({ games: mockGames });

    render(<HistoryPage />);

    await waitFor(() => {
      const reviewLinks = screen.getAllByText(/review hands/i);
      expect(reviewLinks[0]).toHaveAttribute('href', '/history/game-1');
    });
  });

  it('should format dates correctly', async () => {
    (apiClient as jest.Mock).mockResolvedValue({ games: mockGames });

    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText(/Jan 13, 2026/i)).toBeInTheDocument();
      expect(screen.getByText(/Jan 12, 2026/i)).toBeInTheDocument();
    });
  });

  it('should show error state on fetch failure', async () => {
    (apiClient as jest.Mock).mockRejectedValue(new Error('Failed to fetch'));

    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText(/error loading history/i)).toBeInTheDocument();
    });
  });
});
```

**Expected:** Tests fail (page doesn't exist)

#### 2.3.2 Implement (GREEN)

**File:** `frontend/app/history/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, isAuthenticated } from '@/lib/auth';
import Link from 'next/link';

interface Game {
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
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Check auth
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    // Fetch game history
    const fetchHistory = async () => {
      try {
        const data = await apiClient('/users/me/games');
        setGames(data.games);
      } catch (err) {
        setError('Error loading history');
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
        <div className="text-red-400 text-xl">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">Game History</h1>
          <Link
            href="/"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
          >
            New Game
          </Link>
        </div>

        {games.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-8 text-center">
            <p className="text-gray-400 text-lg">No games yet</p>
            <p className="text-gray-500 mt-2">Play your first game to see it here!</p>
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
                    <div className="flex items-center gap-4 mb-2">
                      <span className="text-gray-400 text-sm">
                        {formatDate(game.started_at)}
                      </span>
                      <span className="text-gray-500 text-sm">
                        {game.num_ai_players} AI opponents
                      </span>
                    </div>

                    <div className="flex gap-6 text-sm">
                      <div>
                        <span className="text-gray-400">Hands:</span>
                        <span className="text-white ml-2">{game.total_hands} hands</span>
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
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm"
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

**Expected:** Tests pass

---

### Task 2.4: Hand Review Page (1 hour)

#### 2.4.1 Write Tests FIRST (RED)

**File:** `frontend/__tests__/pages/history/[gameId].test.tsx`

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import HandReviewPage from '@/app/history/[gameId]/page';
import { apiClient } from '@/lib/auth';

jest.mock('@/lib/auth');
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({ push: jest.fn(), back: jest.fn() })),
  useParams: jest.fn(() => ({ gameId: 'game-1' }))
}));

describe('Hand Review Page', () => {
  const mockHands = [
    {
      hand_id: 'hand-1',
      hand_number: 1,
      hand_data: { pot: 150, rounds: [{ actions: [] }] },
      user_hole_cards: 'AsKs',
      user_won: true,
      pot: 150
    },
    {
      hand_id: 'hand-2',
      hand_number: 2,
      hand_data: { pot: 100, rounds: [{ actions: [] }] },
      user_hole_cards: 'QhJh',
      user_won: false,
      pot: 100
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch and display hands', async () => {
    (apiClient as jest.Mock).mockResolvedValue({ hands: mockHands });

    render(<HandReviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/hand #1/i)).toBeInTheDocument();
      expect(screen.getByText(/hand #2/i)).toBeInTheDocument();
    });
  });

  it('should display hand details', async () => {
    (apiClient as jest.Mock).mockResolvedValue({ hands: mockHands });

    render(<HandReviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/pot: \$150/i)).toBeInTheDocument();
      expect(screen.getByText(/won/i)).toBeInTheDocument();
    });
  });

  it('should navigate between hands', async () => {
    (apiClient as jest.Mock).mockResolvedValue({ hands: mockHands });

    render(<HandReviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/hand #1/i)).toBeInTheDocument();
    });

    const nextButton = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextButton);

    expect(screen.getByText(/hand #2/i)).toBeInTheDocument();
  });

  it('should show analysis button', async () => {
    (apiClient as jest.Mock).mockResolvedValue({ hands: mockHands });

    render(<HandReviewPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /get analysis/i })).toBeInTheDocument();
    });
  });

  it('should fetch and display AI analysis', async () => {
    (apiClient as jest.Mock)
      .mockResolvedValueOnce({ hands: mockHands })
      .mockResolvedValueOnce({
        analysis: { verdict: 'good play' },
        model_used: 'haiku-4.5',
        cost: 0.016
      });

    render(<HandReviewPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /get analysis/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /get analysis/i }));

    await waitFor(() => {
      expect(screen.getByText(/good play/i)).toBeInTheDocument();
      expect(apiClient).toHaveBeenCalledWith('/games/game-1/analysis-llm?hand_number=1');
    });
  });

  it('should show back button', async () => {
    (apiClient as jest.Mock).mockResolvedValue({ hands: mockHands });
    const mockBack = jest.fn();
    jest.spyOn(require('next/navigation'), 'useRouter').mockReturnValue({ back: mockBack });

    render(<HandReviewPage />);

    await waitFor(() => {
      const backButton = screen.getByText(/back to history/i);
      fireEvent.click(backButton);
      expect(mockBack).toHaveBeenCalled();
    });
  });
});
```

**Expected:** Tests fail (page doesn't exist)

#### 2.4.2 Implement (GREEN)

**File:** `frontend/app/history/[gameId]/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apiClient, isAuthenticated } from '@/lib/auth';

interface Hand {
  hand_id: string;
  hand_number: number;
  hand_data: any;
  user_hole_cards: string;
  user_won: boolean;
  pot: number;
  created_at?: string;
}

export default function HandReviewPage() {
  const router = useRouter();
  const params = useParams();
  const gameId = params.gameId as string;

  const [hands, setHands] = useState<Hand[]>([]);
  const [currentHandIndex, setCurrentHandIndex] = useState(0);
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
        const data = await apiClient(`/games/${gameId}/hands`);
        setHands(data.hands);
      } catch (err) {
        setError('Error loading hands');
      } finally {
        setLoading(false);
      }
    };

    fetchHands();
  }, [gameId, router]);

  const currentHand = hands[currentHandIndex];

  const getAnalysis = async () => {
    if (!currentHand) return;

    setLoadingAnalysis(true);
    try {
      const data = await apiClient(
        `/games/${gameId}/analysis-llm?hand_number=${currentHand.hand_number}`
      );
      setAnalysis(data);
    } catch (err) {
      setError('Error loading analysis');
    } finally {
      setLoadingAnalysis(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading hands...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-red-400 text-xl">{error}</div>
      </div>
    );
  }

  if (hands.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-gray-400 text-xl">No hands found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <button
            onClick={() => router.back()}
            className="text-blue-400 hover:text-blue-300"
          >
            ← Back to History
          </button>
          <div className="text-gray-400">
            Hand {currentHandIndex + 1} of {hands.length}
          </div>
        </div>

        {currentHand && (
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  Hand #{currentHand.hand_number}
                </h2>
                <div className="flex gap-4 text-sm">
                  <span className="text-gray-400">
                    Your cards: <span className="text-white">{currentHand.user_hole_cards}</span>
                  </span>
                  <span className="text-gray-400">
                    Pot: <span className="text-white">${currentHand.pot}</span>
                  </span>
                  <span className={currentHand.user_won ? 'text-green-400' : 'text-red-400'}>
                    {currentHand.user_won ? 'Won' : 'Lost'}
                  </span>
                </div>
              </div>

              <button
                onClick={getAnalysis}
                disabled={loadingAnalysis}
                className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white px-4 py-2 rounded"
              >
                {loadingAnalysis ? 'Loading...' : 'Get AI Analysis'}
              </button>
            </div>

            {analysis && (
              <div className="bg-gray-700 rounded p-4 mt-4">
                <div className="text-sm text-gray-400 mb-2">
                  Analysis by {analysis.model_used} (${analysis.cost})
                </div>
                <div className="text-white">
                  <pre className="whitespace-pre-wrap">
                    {JSON.stringify(analysis.analysis, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="flex justify-between">
          <button
            onClick={() => setCurrentHandIndex(Math.max(0, currentHandIndex - 1))}
            disabled={currentHandIndex === 0}
            className="bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 text-white px-6 py-2 rounded"
          >
            ← Previous
          </button>
          <button
            onClick={() => setCurrentHandIndex(Math.min(hands.length - 1, currentHandIndex + 1))}
            disabled={currentHandIndex === hands.length - 1}
            className="bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 text-white px-6 py-2 rounded"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Expected:** Tests pass

---

### Task 2.5: Update Existing Game Flow (30 minutes)

#### 2.5.1 Write Tests FIRST (RED)

**File:** `frontend/__tests__/integration/auth-game-flow.test.tsx`

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import HomePage from '@/app/page';
import { isAuthenticated, apiClient } from '@/lib/auth';

jest.mock('@/lib/auth');
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({ push: jest.fn() }))
}));

describe('Auth-Game Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should redirect unauthenticated users to login', () => {
    (isAuthenticated as jest.Mock).mockReturnValue(false);
    const mockPush = jest.fn();
    jest.spyOn(require('next/navigation'), 'useRouter').mockReturnValue({ push: mockPush });

    render(<HomePage />);

    expect(mockPush).toHaveBeenCalledWith('/login');
  });

  it('should allow authenticated users to create game', async () => {
    (isAuthenticated as jest.Mock).mockReturnValue(true);
    (apiClient as jest.Mock).mockResolvedValue({ game_id: 'game-123' });

    render(<HomePage />);

    const createButton = await screen.findByRole('button', { name: /start game/i });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(apiClient).toHaveBeenCalledWith(
        '/games',
        expect.objectContaining({
          method: 'POST'
        })
      );
    });
  });
});
```

**Expected:** Tests fail (auth integration not implemented)

#### 2.5.2 Implement (GREEN)

**File:** `frontend/app/page.tsx` (update)

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
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center">
      <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">Welcome, {username}!</h1>
          <button
            onClick={handleLogout}
            className="text-gray-400 hover:text-white text-sm"
          >
            Logout
          </button>
        </div>

        <div className="space-y-4">
          <Link
            href="/game/new"
            className="block bg-blue-600 hover:bg-blue-700 text-white text-center font-bold py-3 px-4 rounded"
          >
            Start New Game
          </Link>

          <Link
            href="/history"
            className="block bg-gray-700 hover:bg-gray-600 text-white text-center font-bold py-3 px-4 rounded"
          >
            View Game History
          </Link>
        </div>
      </div>
    </div>
  );
}
```

**File:** `frontend/lib/websocket.ts` (update to add auth)

```typescript
// Add auth token to WebSocket connection
export class PokerWebSocket {
  // ... existing code ...

  connect() {
    const token = getToken(); // Import from auth.ts
    const wsUrl = `${WS_URL}/${this.gameId}${token ? `?token=${token}` : ''}`;
    this.ws = new WebSocket(wsUrl);
    // ... rest of existing code ...
  }
}
```

**Expected:** Tests pass

**Checkpoint 2.5: Run all frontend tests**
```bash
cd frontend
npm test
```

---

## Final Verification (30 minutes)

### Manual End-to-End Test

1. **Start services**
```bash
# Terminal 1: Database
docker run --name postgres-dev -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=poker_dev -p 5432:5432 -d postgres:15

# Terminal 2: Run migrations
cd backend
export DATABASE_URL="postgresql://postgres:postgres@localhost/poker_dev"
alembic upgrade head

# Terminal 3: Start backend
cd backend
python main.py

# Terminal 4: Start frontend
cd frontend
npm run dev
```

2. **Test flow**
   - Visit http://localhost:3000
   - Should redirect to /login
   - Register new account
   - Create new game
   - Play a few hands
   - Check /history
   - Review hands
   - Get AI analysis

3. **Verify database**
```bash
psql postgresql://postgres:postgres@localhost/poker_dev

SELECT COUNT(*) FROM users;      -- Should have 1+
SELECT COUNT(*) FROM games;      -- Should have 1+
SELECT COUNT(*) FROM hands;      -- Should have hands played
SELECT COUNT(*) FROM analysis_cache; -- Should have 1 if analysis requested
```

---

## Success Criteria

Day 1 is complete when:

**Backend:**
- [ ] All auth tests pass (password hashing, JWT tokens)
- [ ] All database model tests pass
- [ ] All auth endpoint tests pass (register, login)
- [ ] All game persistence tests pass (save hands)
- [ ] All history endpoint tests pass (get games, get hands)
- [ ] Manual test: Can register, login, play game, view history

**Frontend:**
- [ ] All auth library tests pass
- [ ] All login page tests pass
- [ ] All history page tests pass
- [ ] All hand review page tests pass
- [ ] All integration tests pass
- [ ] Manual test: Full user flow works end-to-end

---

## Dependencies Needed

**Backend:**
```bash
cd backend
pip install bcrypt pyjwt alembic psycopg2-binary sqlalchemy
```

**Frontend:**
```bash
cd frontend
npm install --save-dev @testing-library/react @testing-library/jest-dom jest-environment-jsdom
```

---

## Time Estimates by Task

| Task | Estimated Time | Type |
|------|---------------|------|
| 1.1 Auth - Password Hashing | 30 min | Test + Impl |
| 1.2 Auth - JWT Tokens | 30 min | Test + Impl |
| 1.3 Database Models | 45 min | Test + Impl |
| 1.4 Auth Endpoints | 1 hour | Test + Impl |
| 1.5 Game Persistence | 1 hour | Test + Impl |
| 1.6 History Endpoints | 45 min | Test + Impl |
| **Backend Subtotal** | **4 hours** | |
| 2.1 Auth Library | 30 min | Test + Impl |
| 2.2 Login Page | 1 hour | Test + Impl |
| 2.3 Game History Page | 1.5 hours | Test + Impl |
| 2.4 Hand Review Page | 1 hour | Test + Impl |
| 2.5 Update Game Flow | 30 min | Test + Impl |
| **Frontend Subtotal** | **4 hours** | |
| Final Verification | 30 min | Manual |
| **TOTAL** | **8.5 hours** | |

---

## Execution Notes

1. **Follow TDD strictly**: Write test → Watch it fail → Implement → Watch it pass
2. **Run tests frequently**: After each implementation, verify tests pass
3. **Commit after each task**: Small commits make it easy to rollback
4. **Test integrations**: After backend done, test with curl/Postman before starting frontend
5. **Use checkpoints**: The marked checkpoints are good places to pause and verify

---

## Next Steps (Day 2)

After Day 1 is complete and all tests pass:

1. Add GitHub Actions workflows
2. Run Azure setup workflow
3. Push code to trigger deployment
4. Verify production deployment

See `docs/MVP-DEPLOYMENT-CHECKLIST.md` for Day 2 details.
