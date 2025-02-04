import unittest
from game_engine import Player, AIPlayer, PokerGame

class TestBlinds(unittest.TestCase):
    def setUp(self):
        """Initialize a test game instance before each test."""
        self.players = [
            AIPlayer("AI-1"),
            AIPlayer("AI-2"),
            AIPlayer("AI-3"),
            AIPlayer("AI-4"),
        ]
        self.game = PokerGame(self.players)
        self.game.hand_count = 1  # Ensure hand count starts at 1

    def test_post_blinds(self):
        """Test if small and big blinds are posted correctly."""
        initial_sb = self.game.small_blind
        initial_bb = self.game.big_blind
        
        self.game.post_blinds()
        print(f"Hand {self.game.hand_count}: Dealer {self.game.dealer_index}, SB {initial_sb}, BB {initial_bb}")
        self.assertEqual(self.game.pot, initial_sb + initial_bb)
        
        sb_index = (self.game.dealer_index + 1) % len(self.players)
        bb_index = (sb_index + 1) % len(self.players)
        
        print(f"Expected SB: Player {sb_index}, Expected BB: Player {bb_index}")
        self.assertEqual(self.players[sb_index].current_bet, initial_sb)
        self.assertEqual(self.players[bb_index].current_bet, initial_bb)

    def test_blind_progression(self):
        """Test if small and big blinds increase correctly every 2 hands."""
        initial_sb = self.game.small_blind
        initial_bb = self.game.big_blind

        for hand in range(1, 6):  # Simulate 5 hands
            self.game.hand_count = hand
            self.game.post_blinds()
            
            expected_sb = initial_sb + (5 * ((hand) // 2))
            expected_bb = expected_sb * 2
            
            print(f"Hand {hand}: Expected SB {expected_sb}, Actual SB {self.game.small_blind}, Expected BB {expected_bb}, Actual BB {self.game.big_blind}")
            self.assertEqual(self.game.small_blind, expected_sb, f"Incorrect SB on hand {hand}")
            self.assertEqual(self.game.big_blind, expected_bb, f"Incorrect BB on hand {hand}")

if __name__ == "__main__":
    unittest.main()
