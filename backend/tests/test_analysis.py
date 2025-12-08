"""
Test hand analysis functionality - Bug UAT-11: Analysis shows player names correctly.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame, GameState


class TestHandAnalysis:
    """Test hand analysis functionality."""

    def test_analysis_returns_player_names(self):
        """
        Bug UAT-11: Analysis should show AI player names, not indices.
        """
        game = PokerGame("TestPlayer", ai_count=2)

        # Play a hand to completion
        game.start_new_hand(process_ai=True)

        # Analysis should be available
        analysis = game.analyze_last_hand()

        if analysis is None:
            pytest.skip("No analysis available (hand may not have completed)")

        # Check ai_thinking has proper structure
        if analysis.get('ai_thinking'):
            assert isinstance(analysis['ai_thinking'], list), \
                "ai_thinking should be a list"

            for ai_entry in analysis['ai_thinking']:
                # Each entry should have a name field
                assert 'name' in ai_entry, "AI entry should have 'name' field"

                # Name should not be a number (index)
                name = ai_entry['name']
                assert not name.isdigit(), \
                    f"AI name should not be an index: '{name}'"

                # Name should be a string
                assert isinstance(name, str) and len(name) > 0, \
                    f"AI name should be a non-empty string: '{name}'"

                print(f"AI Player: {name}")
                print(f"  Action: {ai_entry.get('action')}")
                print(f"  Reasoning: {ai_entry.get('reasoning', 'N/A')[:50]}...")

    def test_analysis_structure(self):
        """Verify analysis has correct structure."""
        game = PokerGame("TestPlayer", ai_count=2)
        game.start_new_hand(process_ai=True)

        analysis = game.analyze_last_hand()

        if analysis is None:
            pytest.skip("No analysis available")

        # Check required fields
        expected_fields = [
            'hand_number', 'your_action', 'your_cards', 'community_cards',
            'pot_size', 'you_won', 'winners', 'your_hand_strength',
            'insights', 'tips', 'ai_thinking'
        ]

        for field in expected_fields:
            assert field in analysis, f"Analysis should have '{field}' field"

        print(f"\nAnalysis structure verified:")
        print(f"  Hand #{analysis['hand_number']}")
        print(f"  Your action: {analysis['your_action']}")
        print(f"  Winners: {analysis['winners']}")
        print(f"  AI players in analysis: {len(analysis['ai_thinking'])}")

    def test_multiple_hands_analysis(self):
        """Verify analysis works across multiple hands."""
        game = PokerGame("TestPlayer", ai_count=2)

        for hand_num in range(3):
            # Start new hand
            game.start_new_hand(process_ai=True)

            # Get analysis
            analysis = game.analyze_last_hand()

            if analysis:
                print(f"\nHand {hand_num + 1} analysis:")
                print(f"  Hand number: {analysis['hand_number']}")
                print(f"  AI thinking count: {len(analysis.get('ai_thinking', []))}")

                # Verify names are correct
                for ai_entry in analysis.get('ai_thinking', []):
                    assert 'name' in ai_entry
                    assert not ai_entry['name'].isdigit()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
