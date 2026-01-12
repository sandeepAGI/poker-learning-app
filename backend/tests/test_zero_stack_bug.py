"""
Test for bug: Players with $0 stacks being dealt into new hands.

USER REPORTED BUG (Jan 12, 2026):
- Screenshot shows Hand #7 with two players showing Stack: $0
- These players have cards dealt to them
- This violates poker rules - eliminated players shouldn't be in the hand

Expected behavior:
- Players with stack = 0 at end of hand should have is_active = False
- is_active = False players should NOT be dealt cards in new hand
- Only players with stack > 0 should receive hole cards
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame


class TestZeroStackBug:
    """Test that players with $0 stacks are not dealt into new hands."""

    def test_zero_stack_players_not_dealt_cards(self):
        """
        Reproduces user bug: Players with stack = 0 should not receive cards.

        Steps:
        1. Create game with 4 players
        2. Set 2 players to stack = 0 (simulating they busted out)
        3. Start new hand
        4. Verify zero-stack players have is_active = False
        5. Verify zero-stack players have no hole cards
        """
        print("\n[ZERO STACK BUG] Testing players with $0 not dealt cards...")
        game = PokerGame("Human", ai_count=3)

        # Simulate 2 players busting out
        game.players[1].stack = 0  # "Cool Hand Luke"
        game.players[2].stack = 0  # "Data Dealer"
        game.players[0].stack = 2000  # Human
        game.players[3].stack = 2000  # One AI remains

        # Update total chips
        game.total_chips = sum(p.stack for p in game.players)

        # Start new hand - this should NOT deal to players with stack = 0
        game.start_new_hand(process_ai=False)

        print(f"\n=== After new hand started ===")
        for i, player in enumerate(game.players):
            print(f"Player {i} ({player.name}):")
            print(f"  Stack: ${player.stack}")
            print(f"  is_active: {player.is_active}")
            print(f"  Cards dealt: {len(player.hole_cards)} cards")
            print(f"  Cards: {player.hole_cards}")

        # CRITICAL ASSERTIONS
        # Players with stack = 0 should NOT be active
        assert game.players[1].is_active == False, \
            f"Player 1 has $0 stack but is_active={game.players[1].is_active} (should be False)"
        assert game.players[2].is_active == False, \
            f"Player 2 has $0 stack but is_active={game.players[2].is_active} (should be False)"

        # Players with stack = 0 should NOT have cards
        assert len(game.players[1].hole_cards) == 0, \
            f"Player 1 has $0 stack but was dealt {len(game.players[1].hole_cards)} cards"
        assert len(game.players[2].hole_cards) == 0, \
            f"Player 2 has $0 stack but was dealt {len(game.players[2].hole_cards)} cards"

        # Players with stack > 0 should be active and have cards
        assert game.players[0].is_active == True, \
            f"Player 0 has ${game.players[0].stack} but is_active={game.players[0].is_active}"
        assert len(game.players[0].hole_cards) == 2, \
            f"Player 0 has ${game.players[0].stack} but was dealt {len(game.players[0].hole_cards)} cards"

        assert game.players[3].is_active == True, \
            f"Player 3 has ${game.players[3].stack} but is_active={game.players[3].is_active}"
        assert len(game.players[3].hole_cards) == 2, \
            f"Player 3 has ${game.players[3].stack} but was dealt {len(game.players[3].hole_cards)} cards"

        print("\n✅ Zero-stack players correctly NOT dealt cards")

    def test_zero_stack_after_all_in_loss(self):
        """
        Test realistic scenario: Player goes all-in, loses, next hand starts.

        This simulates the exact flow that would cause the user's bug:
        1. Player all-in with full stack
        2. Player loses (stack becomes 0)
        3. Next hand starts
        4. Player should NOT be dealt cards
        """
        print("\n[ZERO STACK BUG] Testing all-in loss → new hand flow...")
        game = PokerGame("Human", ai_count=3)

        # Manually simulate a player losing all-in and ending with stack = 0
        # (We don't run a full hand simulation, just set the end state)
        game.players[1].stack = 0
        game.players[1].is_active = False  # Should be set by reset_for_new_hand
        game.players[1].all_in = False

        initial_stack_0 = game.players[0].stack
        initial_stack_2 = game.players[2].stack
        initial_stack_3 = game.players[3].stack

        # CRITICAL: Update total_chips to match actual chip distribution
        game.total_chips = sum(p.stack for p in game.players)

        # Start next hand
        game.start_new_hand(process_ai=False)

        print(f"\n=== After new hand ===")
        for i, player in enumerate(game.players):
            print(f"Player {i}: stack=${player.stack}, active={player.is_active}, cards={len(player.hole_cards)}")

        # Player 1 should remain inactive with no cards
        assert game.players[1].stack == 0
        assert game.players[1].is_active == False
        assert len(game.players[1].hole_cards) == 0

        # Other players should be active with cards
        assert game.players[0].is_active == True
        assert len(game.players[0].hole_cards) == 2

        print("✅ Player with $0 correctly not dealt into next hand")

    def test_get_game_state_zero_stack_players(self):
        """
        Test that get_game_state() doesn't expose busted players as active.

        This tests what the frontend receives via WebSocket/API.
        """
        print("\n[ZERO STACK BUG] Testing get_game_state() with busted players...")
        game = PokerGame("Human", ai_count=3)

        # Bust 2 players
        game.players[1].stack = 0
        game.players[2].stack = 0

        # Update total chips to prevent conservation violation
        game.total_chips = sum(p.stack for p in game.players)

        # Start new hand
        game.start_new_hand(process_ai=False)

        # Get state that would be sent to frontend
        state = game.get_game_state()

        print(f"\n=== Game State ===")
        for player_state in state['players']:
            name = player_state['name']
            stack = player_state['stack']
            is_active = player_state['is_active']
            cards = player_state.get('hole_cards', [])

            print(f"{name}: stack=${stack}, active={is_active}, cards={len(cards)}")

            # If stack is 0, should not be active and should not have cards
            if stack == 0:
                assert is_active == False, \
                    f"{name} has $0 stack but is_active=True in game state"
                assert len(cards) == 0, \
                    f"{name} has $0 stack but has {len(cards)} cards in game state"

        print("✅ Game state correctly shows busted players as inactive")

    def test_frontend_display_bug_scenario(self):
        """
        Exact reproduction of user's screenshot scenario.

        User saw:
        - Hand #7
        - "Cool Hand Luke" - Stack: $0, cards visible
        - "Data Dealer" - Stack: $0, cards visible
        - Two other players with normal stacks
        """
        print("\n[ZERO STACK BUG] Exact reproduction of user scenario...")
        game = PokerGame("Human", ai_count=3)

        # Set up exact scenario from screenshot
        # Position 0: "The Rock" (Human) - has chips
        # Position 1: "Cool Hand Luke" - $0
        # Position 2: "Data Dealer" - $0
        # Position 3: AI - has chips
        game.players[0].name = "The Rock"
        game.players[1].name = "Cool Hand Luke"
        game.players[2].name = "Data Dealer"
        game.players[3].name = "Binary Bob"

        # Simulate they busted in previous hand
        game.players[1].stack = 0
        game.players[2].stack = 0
        game.players[0].stack = 2880  # From screenshot
        game.players[3].stack = 1000

        game.total_chips = 3880
        game.hand_count = 6  # So next will be hand #7

        # Start hand #7
        game.start_new_hand(process_ai=False)

        print(f"\n=== Hand #{game.hand_count} ===")

        # Get state as frontend would see it
        state = game.get_game_state()

        for player_state in state['players']:
            name = player_state['name']
            stack = player_state['stack']
            is_active = player_state['is_active']
            hole_cards = player_state.get('hole_cards', [])

            print(f"{name}:")
            print(f"  Stack: ${stack}")
            print(f"  Active: {is_active}")
            print(f"  Cards: {hole_cards}")

            # REPRODUCE THE BUG
            if name in ["Cool Hand Luke", "Data Dealer"]:
                # These should NOT have cards or be active
                assert stack == 0, f"{name} should have $0"
                assert is_active == False, f"{name} should be inactive (BUG if True!)"
                assert len(hole_cards) == 0, f"{name} should have no cards (BUG if they have cards!)"

        print("\n✅ Bug NOT reproduced - backend correctly excludes $0 players")
        print("   → Bug is likely in FRONTEND display logic")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
