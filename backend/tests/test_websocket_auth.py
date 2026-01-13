"""Test WebSocket authentication."""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
from models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://sandeepmangaraj@localhost:5432/poker_test")

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
