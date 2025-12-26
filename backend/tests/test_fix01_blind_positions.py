"""
Unit tests for FIX-01: Blind Position Tracking

Tests that backend correctly tracks and exposes dealer, SB, and BB positions
to the frontend via API.
"""
import pytest
from game.poker_engine import PokerGame


class TestBlindPositionTracking:
    """Test that blind positions are tracked correctly in backend"""

    def test_4_player_blind_positions_initial_hand(self):
        """Test blind positions are correct in 4-player game on first hand"""
        game = PokerGame(human_player_name="Human", ai_count=3)
        game.start_new_hand()

        # Verify dealer position
        assert game.dealer_index == 1, "Dealer should be at position 1 on first hand"

        # Verify blind positions (consecutive after dealer)
        expected_sb = (game.dealer_index + 1) % 4
        expected_bb = (game.dealer_index + 2) % 4

        assert game.small_blind_index == expected_sb, \
            f"SB should be at {expected_sb}, got {game.small_blind_index}"
        assert game.big_blind_index == expected_bb, \
            f"BB should be at {expected_bb}, got {game.big_blind_index}"

        # Verify blinds are consecutive
        assert (game.small_blind_index + 1) % 4 == game.big_blind_index, \
            "SB and BB must be consecutive positions"

    def test_6_player_blind_positions_initial_hand(self):
        """Test blind positions are correct in 6-player game on first hand"""
        game = PokerGame(human_player_name="Human", ai_count=5)
        game.start_new_hand()

        # Verify dealer position
        assert game.dealer_index is not None, "Dealer position should be set"

        # Verify blind positions (consecutive after dealer)
        expected_sb = (game.dealer_index + 1) % 6
        expected_bb = (game.dealer_index + 2) % 6

        assert game.small_blind_index == expected_sb, \
            f"SB should be at {expected_sb}, got {game.small_blind_index}"
        assert game.big_blind_index == expected_bb, \
            f"BB should be at {expected_bb}, got {game.big_blind_index}"

        # Verify blinds are consecutive (THIS WAS THE BUG!)
        assert (game.small_blind_index + 1) % 6 == game.big_blind_index, \
            "SB and BB must be consecutive positions (not skipping a player)"

    def test_blind_positions_rotate_correctly_4_player(self):
        """Test that blind positions rotate correctly over multiple hands (4-player)"""
        game = PokerGame(human_player_name="Human", ai_count=3)

        for hand_num in range(5):
            game.start_new_hand()

            # Verify consecutive blinds
            assert (game.small_blind_index + 1) % 4 == game.big_blind_index, \
                f"Hand {hand_num + 1}: SB and BB must be consecutive"

            # Verify positions relative to dealer
            assert game.small_blind_index == (game.dealer_index + 1) % 4, \
                f"Hand {hand_num + 1}: SB should be dealer + 1"
            assert game.big_blind_index == (game.dealer_index + 2) % 4, \
                f"Hand {hand_num + 1}: BB should be dealer + 2"

            # Complete hand quickly (fold until showdown/complete)
            for _ in range(20):  # Safety limit
                current = game.get_current_player()
                if current and current.is_active and not current.all_in:
                    game.apply_action(game.current_player_index, "fold")
                else:
                    break

    def test_blind_positions_rotate_correctly_6_player(self):
        """Test that blind positions rotate correctly over multiple hands (6-player)"""
        game = PokerGame(human_player_name="Human", ai_count=5)

        for hand_num in range(7):  # Full rotation + 1
            game.start_new_hand()

            # Verify consecutive blinds (THE CRITICAL TEST!)
            assert (game.small_blind_index + 1) % 6 == game.big_blind_index, \
                f"Hand {hand_num + 1}: SB and BB must be consecutive (dealer={game.dealer_index}, sb={game.small_blind_index}, bb={game.big_blind_index})"

            # Verify positions relative to dealer
            assert game.small_blind_index == (game.dealer_index + 1) % 6, \
                f"Hand {hand_num + 1}: SB should be dealer + 1"
            assert game.big_blind_index == (game.dealer_index + 2) % 6, \
                f"Hand {hand_num + 1}: BB should be dealer + 2"

            # Complete hand quickly (fold until showdown/complete)
            for _ in range(20):  # Safety limit
                current = game.get_current_player()
                if current and current.is_active and not current.all_in:
                    game.apply_action(game.current_player_index, "fold")
                else:
                    break

    def test_blind_positions_match_actual_bets_4_player(self):
        """Test that blind positions match who actually posted blinds (4-player)"""
        game = PokerGame(human_player_name="Human", ai_count=3)
        game.start_new_hand()

        # Find who posted blinds by checking current_bet
        players_with_sb = [i for i, p in enumerate(game.players) if p.current_bet == game.small_blind]
        players_with_bb = [i for i, p in enumerate(game.players) if p.current_bet == game.big_blind]

        assert len(players_with_sb) == 1, "Exactly one player should have SB bet"
        assert len(players_with_bb) == 1, "Exactly one player should have BB bet"

        assert players_with_sb[0] == game.small_blind_index, \
            "small_blind_index should match player who posted SB"
        assert players_with_bb[0] == game.big_blind_index, \
            "big_blind_index should match player who posted BB"

    def test_blind_positions_match_actual_bets_6_player(self):
        """Test that blind positions match who actually posted blinds (6-player)"""
        game = PokerGame(human_player_name="Human", ai_count=5)
        # Don't process AI actions - we want to check blinds immediately after posting
        game.start_new_hand(process_ai=False)

        # Find who posted blinds by checking current_bet
        players_with_sb = [i for i, p in enumerate(game.players) if p.current_bet == game.small_blind]
        players_with_bb = [i for i, p in enumerate(game.players) if p.current_bet == game.big_blind]

        assert len(players_with_sb) == 1, "Exactly one player should have SB bet"
        assert len(players_with_bb) == 1, f"Exactly one player should have BB bet, found {len(players_with_bb)} at positions {players_with_bb}"

        assert players_with_sb[0] == game.small_blind_index, \
            "small_blind_index should match player who posted SB"
        assert players_with_bb[0] == game.big_blind_index, \
            "big_blind_index should match player who posted BB"

    def test_blind_positions_none_before_first_hand(self):
        """Test that blind positions are None before first hand starts"""
        game = PokerGame(human_player_name="Human", ai_count=3)

        # Before first hand
        assert game.small_blind_index is None, "SB position should be None before first hand"
        assert game.big_blind_index is None, "BB position should be None before first hand"
        assert game.dealer_index is not None, "Dealer position is initialized"

        # After first hand
        game.start_new_hand()
        assert game.small_blind_index is not None, "SB position should be set after first hand"
        assert game.big_blind_index is not None, "BB position should be set after first hand"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
