"""
Pytest configuration for backend tests.

Defines custom markers for test categorization.
"""

import pytest
import os
import uuid
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselected by default, run in nightly CI)"
    )


# Database test fixture
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://sandeepmangaraj@localhost:5432/poker_test")


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


# ============================================================
# Shared auth helpers for integration tests
# ============================================================

async def register_and_get_token(port: int) -> str:
    """Register a unique test user and return a JWT token."""
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}") as client:
        resp = await client.post("/auth/register", json={
            "username": username,
            "password": "testpass123"
        })
        assert resp.status_code == 200, f"Registration failed: {resp.text}"
        return resp.json()["token"]


async def create_authed_game(port: int, token: str, ai_count: int = 3) -> str:
    """Create a game with auth and return game_id."""
    async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}") as client:
        resp = await client.post(
            "/games",
            json={"player_name": "TestPlayer", "ai_count": ai_count},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200, f"Game creation failed: {resp.text}"
        return resp.json()["game_id"]
