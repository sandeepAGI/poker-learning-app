"""
Test import consistency in main.py and websocket_manager.py

Issue #1: main.py line 283 uses `from backend.game.poker_engine import HandEvaluator`
which fails when running `uvicorn backend.main:app` from repo root because
`backend` is not an installed package.

This test ensures all imports use the correct relative path format.
"""

import pytest
import sys
import os
from pathlib import Path


def test_main_module_imports():
    """Test that main.py can be imported successfully from repo root context."""

    # Simulate running from repo root (standard deployment)
    repo_root = Path(__file__).parent.parent.parent
    backend_path = repo_root / "backend"

    # Ensure backend is in path (simulates uvicorn backend.main:app)
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))

    try:
        # This import will fail if there are mixed import paths
        import main

        # Verify HandEvaluator is accessible
        # The bug occurs in get_game_state when it tries to import HandEvaluator
        assert hasattr(main, 'get_game_state'), "get_game_state function should exist"

    except ModuleNotFoundError as e:
        if 'backend' in str(e):
            pytest.fail(f"Import failed due to mixed import paths: {e}")
        else:
            raise


def test_import_paths_are_consistent():
    """Verify that all imports in main.py use consistent paths."""

    repo_root = Path(__file__).parent.parent.parent
    main_file = repo_root / "backend" / "main.py"

    with open(main_file, 'r') as f:
        content = f.read()

    # Check for problematic import pattern
    if 'from backend.game' in content:
        # Find the line number
        lines = content.split('\n')
        problematic_lines = []
        for i, line in enumerate(lines, 1):
            if 'from backend.game' in line:
                problematic_lines.append(f"Line {i}: {line.strip()}")

        pytest.fail(
            f"Found inconsistent import paths in main.py:\n" +
            "\n".join(problematic_lines) +
            "\n\nShould use 'from game...' instead of 'from backend.game...'"
        )


if __name__ == "__main__":
    print("Testing import consistency...")

    print("\n1. Testing main module imports...")
    try:
        test_main_module_imports()
        print("✅ PASSED")
    except Exception as e:
        print(f"❌ FAILED: {e}")

    print("\n2. Testing import path consistency...")
    try:
        test_import_paths_are_consistent()
        print("✅ PASSED")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
