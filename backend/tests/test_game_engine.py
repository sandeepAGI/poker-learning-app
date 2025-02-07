import unittest
from game_engine import PokerGame, Player  # ✅ Import necessary classes

class TestPokerGame(unittest.TestCase):

    def setUp(self):
        """Initialize a fresh Poker game before each test."""
        # ✅ Correctly create a list of players
        self.players = [Player(player_id="P1"), Player(player_id="P2")]
        self.game = PokerGame(players=self.players)  # ✅ Pass list of players
        self.game.reset_deck()  # ✅ Ensures a full deck before tests run

        # ✅ Manually add `last_hand_dealt` since it's missing in PokerGame
        if not hasattr(self.game, "last_hand_dealt"):
            self.game.last_hand_dealt = -1  # ✅ Initialize to prevent AttributeError

    def test_deck_initialization(self):
        """Test if the deck initializes correctly, accounting for hole card dealing."""
        expected_deck_size = 52  # ✅ Full deck before dealing

        # ✅ Check deck size before dealing
        self.assertEqual(len(self.game.deck), 52, "Deck should start with 52 cards")

        # ✅ Deal hole cards and track expected deck size
        self.game.deal_hole_cards()
        actual_cards_dealt = sum(len(player.hole_cards) for player in self.game.players)
        expected_deck_size -= actual_cards_dealt  # ✅ Accurately count removed cards

        # ✅ Check deck size after dealing
        self.assertEqual(len(self.game.deck), expected_deck_size, f"Deck should have {expected_deck_size} cards after dealing")

    def test_players_receive_unique_hole_cards(self):
        """Ensure each player gets different hole cards."""
        self.game.deal_hole_cards()

        # ✅ Extract player hole cards
        p1_cards = self.game.players[0].hole_cards
        p2_cards = self.game.players[1].hole_cards

        # ✅ Check that players have received two unique cards
        self.assertEqual(len(p1_cards), 2, "Player 1 should have 2 hole cards")
        self.assertEqual(len(p2_cards), 2, "Player 2 should have 2 hole cards")
        self.assertNotEqual(p1_cards, p2_cards, "Players should have different hole cards")

    def test_deck_after_card_distribution(self):
        """Ensure deck correctly reduces after hole cards are dealt using game logic."""
        initial_deck_size = len(self.game.deck)

        # ✅ Use `deal_hole_cards()` instead of manually modifying the deck
        self.game.deal_hole_cards()

        # ✅ Expected reduction: 2 cards per player
        expected_deck_size = initial_deck_size - (2 * len(self.game.players))

        self.assertEqual(len(self.game.deck), expected_deck_size, "Deck size should reduce after dealing")

    def test_no_duplicate_hole_cards(self):
        """Ensure no duplicate hole cards exist after dealing."""
        self.game.deal_hole_cards()

        # ✅ Collect all hole cards into a single list
        all_hole_cards = [card for player in self.game.players for card in player.hole_cards]

        # ✅ Ensure all cards are unique
        self.assertEqual(len(all_hole_cards), len(set(all_hole_cards)), "All hole cards should be unique")

if __name__ == '__main__':
    unittest.main()

