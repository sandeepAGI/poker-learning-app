"""
Integration tests for LLM Analysis API endpoints (Phase 4).

Tests API endpoint behavior WITHOUT making expensive LLM calls.
Uses mocking to test caching, rate limiting, error handling, and metrics.
"""

import pytest
import time
import requests
from unittest.mock import patch, Mock, MagicMock

# API base URL (assumes backend is running on localhost:8000)
BASE_URL = "http://localhost:8000"


def server_is_running():
    """Check if the server is running."""
    try:
        requests.get(f"{BASE_URL}/", timeout=1)
        return True
    except requests.exceptions.ConnectionError:
        return False


# Skip all tests if server isn't running
pytestmark = pytest.mark.skipif(
    not server_is_running(),
    reason="Server not running at localhost:8000. Start with: python main.py"
)


def api_request(method, endpoint, **kwargs):
    """Helper to make API requests."""
    url = f"{BASE_URL}{endpoint}"
    response = requests.request(method, url, **kwargs)
    return response


@pytest.fixture
def mock_llm_analyzer():
    """Mock LLM analyzer that returns fake analysis without API calls."""
    with patch('main.llm_analyzer') as mock:
        # Create a mock analysis response
        mock.analyze_hand.return_value = {
            "summary": "You folded pre-flop with a weak hand (2h 3c). This was the correct decision given your poor starting hand.",
            "round_by_round": [
                {
                    "round": "Pre-flop",
                    "pot": 15,
                    "your_action": "fold",
                    "analysis": "Correct fold with weak hand"
                }
            ],
            "player_analysis": {
                "good_decisions": ["Folding weak hand"],
                "questionable_decisions": []
            },
            "ai_opponent_insights": [],
            "concepts_to_study": [
                {
                    "concept": "Starting hand selection",
                    "explanation": "2-3 offsuit is one of the weakest starting hands"
                }
            ],
            "tips_for_improvement": [
                {
                    "category": "Pre-flop",
                    "observation": "You correctly identified a weak hand",
                    "actionable_step": "Continue folding hands below the top 50% range"
                }
            ],
            "discussion_questions": ["What would you do if you had pocket aces?"],
            "overall_assessment": "Good decision-making on this hand",
            "encouragement": "Keep up the disciplined folding!"
        }
        yield mock


class TestLLMAnalysisEndpoint:
    """Test /games/{id}/analysis-llm endpoint."""

    def test_analysis_endpoint_requires_game_id(self, mock_llm_analyzer):
        """Test that endpoint requires valid game ID."""
        response = requests.get(f"{BASE_URL}/games/nonexistent-game-id/analysis-llm")
        assert response.status_code == 404

    def test_analysis_endpoint_quick_depth(self, mock_llm_analyzer):
        """Test quick analysis (Haiku model)."""
        # Create a game
        response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
        assert response.status_code == 200
        game_id = response.json()["game_id"]

        # Play one hand (fold)
        response = requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})
        assert response.status_code == 200

        # Request quick analysis
        response = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?depth=quick&use_cache=false")
        assert response.status_code == 200

        data = response.json()
        assert "analysis" in data
        assert "model_used" in data
        assert "haiku" in data["model_used"].lower()
        assert "cost" in data
        assert data["cost"] < 0.02  # Haiku should be cheap
        assert "analysis_count" in data

        # Verify analyzer was called with correct parameters
        mock_llm_analyzer.analyze_hand.assert_called_once()
        call_args = mock_llm_analyzer.analyze_hand.call_args
        assert call_args.kwargs["depth"] == "quick"

    def test_analysis_endpoint_deep_depth(self, mock_llm_analyzer):
        """Test deep dive analysis (Sonnet model)."""
        # Create a game
        response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
        game_id = response.json()["game_id"]

        # Play one hand
        response = requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})

        # Request deep analysis
        response = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?depth=deep&use_cache=false")
        assert response.status_code == 200

        data = response.json()
        assert "sonnet" in data["model_used"].lower()
        assert data["cost"] > 0.02  # Sonnet should be more expensive
        assert data["cost"] < 0.05

        # Verify analyzer was called with deep depth
        call_args = mock_llm_analyzer.analyze_hand.call_args
        assert call_args.kwargs["depth"] == "deep"

    def test_analysis_endpoint_invalid_depth(self):
        """Test that invalid depth parameter is rejected."""
        # Create a game
        response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
        game_id = response.json()["game_id"]

        # Request with invalid depth
        response = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?depth=invalid")
        assert response.status_code == 422  # Validation error


class TestCaching:
    """Test analysis caching behavior."""

    def test_cached_analysis_returns_immediately(self, mock_llm_analyzer):
        """Test that cached analysis doesn't call LLM again."""
        # Create game and play hand
        response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
        game_id = response.json()["game_id"]
        requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})

        # First request (not cached)
        response1 = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?depth=quick")
        assert response1.status_code == 200
        assert response1.json().get("cached", False) is False

        # Verify LLM was called once
        assert mock_llm_analyzer.analyze_hand.call_count == 1

        # Second request (should be cached)
        response2 = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?depth=quick")
        assert response2.status_code == 200
        assert response2.json()["cached"] is True

        # Verify LLM was NOT called again
        assert mock_llm_analyzer.analyze_hand.call_count == 1

        # Verify response is identical
        assert response1.json()["analysis"] == response2.json()["analysis"]

    def test_different_depths_not_cached_together(self, mock_llm_analyzer):
        """Test that quick and deep analyses are cached separately."""
        # Create game and play hand
        response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
        game_id = response.json()["game_id"]
        requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})

        # Request quick analysis
        response1 = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?depth=quick")
        assert response1.json()["cached"] is False

        # Request deep analysis (different depth, not cached)
        response2 = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?depth=deep")
        assert response2.json()["cached"] is False

        # Verify LLM was called twice (once for each depth)
        assert mock_llm_analyzer.analyze_hand.call_count == 2

    def test_use_cache_false_bypasses_cache(self, mock_llm_analyzer):
        """Test that use_cache=false forces fresh analysis."""
        # Create game and play hand
        response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
        game_id = response.json()["game_id"]
        requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})

        # First request
        response1 = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?depth=quick")
        assert response1.status_code == 200

        # Second request with use_cache=false
        response2 = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?depth=quick&use_cache=false")
        assert response2.status_code == 200
        assert response2.json()["cached"] is False

        # Verify LLM was called twice
        assert mock_llm_analyzer.analyze_hand.call_count == 2


class TestRateLimiting:
    """Test rate limiting behavior."""

    def test_rate_limiting_enforced(self, mock_llm_analyzer):
        """Test that rapid requests are rate limited."""
        # Create game and play hand
        response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
        game_id = response.json()["game_id"]
        requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})

        # Play another hand
        requests.post(f"{BASE_URL}/games/{game_id}/next", json={})
        requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})

        # First analysis succeeds
        response1 = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?hand_number=2&use_cache=false")
        assert response1.status_code == 200

        # Immediate second analysis is rate limited (same game, different hand)
        requests.post(f"{BASE_URL}/games/{game_id}/next", json={})
        requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})

        response2 = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?hand_number=3&use_cache=false")
        assert response2.status_code == 429  # Too Many Requests
        assert "Rate limit" in response2.json()["detail"]

    def test_rate_limit_bypass_with_cache(self, mock_llm_analyzer):
        """Test that cached requests bypass rate limiting."""
        # Create game and play hand
        response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
        game_id = response.json()["game_id"]
        requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})

        # First request
        response1 = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?depth=quick")
        assert response1.status_code == 200

        # Immediate cached request succeeds (no rate limit)
        response2 = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?depth=quick")
        assert response2.status_code == 200
        assert response2.json()["cached"] is True


class TestAdminMetrics:
    """Test admin metrics endpoint."""

    def test_metrics_endpoint_exists(self):
        """Test that metrics endpoint is accessible."""
        response = requests.get(f"{BASE_URL}/admin/analysis-metrics")
        assert response.status_code == 200

    def test_metrics_structure(self):
        """Test that metrics have correct structure."""
        response = requests.get(f"{BASE_URL}/admin/analysis-metrics")
        data = response.json()

        # Check required fields
        assert "total_analyses" in data
        assert "haiku_analyses" in data
        assert "sonnet_analyses" in data
        assert "total_cost" in data
        assert "cost_today" in data
        assert "cache_hits" in data
        assert "cache_misses" in data

        # All values should be numbers
        assert isinstance(data["total_analyses"], int)
        assert isinstance(data["haiku_analyses"], int)
        assert isinstance(data["sonnet_analyses"], int)
        assert isinstance(data["total_cost"], (int, float))
        assert isinstance(data["cost_today"], (int, float))

    def test_metrics_tracking(self, mock_llm_analyzer):
        """Test that metrics are updated after analysis."""
        # Get initial metrics
        response1 = requests.get(f"{BASE_URL}/admin/analysis-metrics")
        initial_total = response1.json()["total_analyses"]
        initial_haiku = response1.json()["haiku_analyses"]

        # Perform quick analysis
        response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
        game_id = response.json()["game_id"]
        requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})
        requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?depth=quick&use_cache=false")

        # Check metrics increased
        response2 = requests.get(f"{BASE_URL}/admin/analysis-metrics")
        final_total = response2.json()["total_analyses"]
        final_haiku = response2.json()["haiku_analyses"]

        assert final_total == initial_total + 1
        assert final_haiku == initial_haiku + 1


class TestErrorHandling:
    """Test error handling and fallback behavior."""

    def test_llm_error_returns_fallback(self):
        """Test that LLM errors trigger fallback to rule-based analysis."""
        # Mock LLM to raise an error
        with patch('main.llm_analyzer') as mock:
            mock.analyze_hand.side_effect = Exception("API Error")

            # Create game and play hand
            response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
            game_id = response.json()["game_id"]
            requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})

            # Request analysis
            response = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?depth=quick&use_cache=false")
            assert response.status_code == 200

            data = response.json()
            # Should have error field
            assert "error" in data
            assert "API Error" in data["error"]
            # Should still have analysis (fallback)
            assert "analysis" in data

    def test_no_completed_hands_returns_error(self):
        """Test that analysis fails gracefully when no hands completed."""
        # Create game but don't play any hands
        response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
        game_id = response.json()["game_id"]

        # Try to analyze (should fail)
        response = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm")
        assert response.status_code == 404
        assert "No completed hands" in response.json()["detail"]

    def test_specific_hand_number_not_found(self):
        """Test requesting analysis for non-existent hand number."""
        # Create game and play 1 hand
        response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
        game_id = response.json()["game_id"]
        requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})

        # Request analysis for hand #5 (doesn't exist)
        response = requests.get(f"{BASE_URL}/games/{game_id}/analysis-llm?hand_number=5")
        assert response.status_code == 404
        assert "Hand #5 not found" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
