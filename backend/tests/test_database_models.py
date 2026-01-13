"""Test database models and session management."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Game, Hand, AnalysisCache
from datetime import datetime
import uuid
import os

# Use test database from environment
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://sandeepmangaraj@localhost:5432/poker_test")

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
        # Setup user first
        user = User(user_id="user-1", username="test", password_hash="hash")
        db_session.add(user)
        db_session.commit()

        # Then game
        game = Game(game_id="game-1", user_id="user-1", starting_stack=1000)
        db_session.add(game)
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
        db_session.add(user)
        db_session.commit()

        game = Game(game_id="game-1", user_id="user-1", starting_stack=1000)
        db_session.add(game)
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
        db_session.add(user)
        db_session.commit()

        game = Game(game_id="game-1", user_id="user-1", starting_stack=1000)
        db_session.add(game)
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
        db_session.add(user)
        db_session.commit()

        game = Game(game_id="game-1", user_id="user-1", starting_stack=1000)
        db_session.add(game)
        db_session.commit()

        hand = Hand(
            game_id="game-1",
            user_id="user-1",
            hand_number=1,
            hand_data={},
            pot=100
        )
        db_session.add(hand)
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
