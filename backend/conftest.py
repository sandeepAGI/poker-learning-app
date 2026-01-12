"""
Pytest configuration for backend tests.

Defines custom markers for test categorization.
"""

import pytest


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselected by default, run in nightly CI)"
    )
