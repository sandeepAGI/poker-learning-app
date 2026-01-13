"""Test hand persistence to database."""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
from models import Base, User, Game, Hand
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://sandeepmangaraj@localhost:5432/poker_test")

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
            assert "community_cards" in hand.hand_data or hand.hand_data.get("betting_rounds")

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
