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

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://sandeepmangaraj@localhost:5432/poker_test")

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
        from auth import hash_password
        other_user = User(user_id="other-user", username="other", password_hash=hash_password("password123"))
        db.add(other_user)
        db.commit()  # Commit user first

        other_game = Game(
            game_id="other-game",
            user_id="other-user",
            starting_stack=1000,
            status="completed",
            completed_at=datetime.utcnow()
        )
        db.add(other_game)
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
        from auth import hash_password
        other_user = User(user_id="other-user", username="other", password_hash=hash_password("password123"))
        db.add(other_user)
        db.commit()  # Commit user first

        other_game = Game(
            game_id="other-game",
            user_id="other-user",
            starting_stack=1000,
            status="active"
        )
        db.add(other_game)
        db.commit()
        db.close()

        response = client.get("/games/other-game/hands")
        assert response.status_code == 404

    def test_returns_404_for_nonexistent_game(self, client_with_history):
        """Should return 404 for nonexistent game."""
        client, user_id, _ = client_with_history
        response = client.get("/games/nonexistent/hands")

        assert response.status_code == 404
