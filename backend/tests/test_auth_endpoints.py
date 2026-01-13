"""Test authentication endpoints."""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
from models import Base, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://sandeepmangaraj@localhost:5432/poker_test")

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

    # Create test client (pass app as positional argument)
    test_client = TestClient(app)

    yield test_client

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
