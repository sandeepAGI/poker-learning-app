"""
Shared Playwright fixtures for E2E tests
"""
import pytest
import os
from playwright.sync_api import sync_playwright, Page


# Test configuration
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"


@pytest.fixture(scope="function")
def page():
    """
    Playwright page fixture for E2E tests.

    Creates a browser page for each test and cleans up after.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        yield page
        page.close()
        context.close()
        browser.close()


@pytest.fixture(scope="function")
def browser_page():
    """
    Legacy fixture name for backwards compatibility with test_critical_flows.py

    This is the same as the 'page' fixture above.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        yield page
        page.close()
        context.close()
        browser.close()
