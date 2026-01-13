"""
Pytest configuration for backend tests.

Defines custom markers for test categorization.
"""

import pytest
import os
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
