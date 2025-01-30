import unittest
from game_engine import PokerGame, AIPlayer, Player
import config

class TestPokerGame(unittest.TestCase):
    def setUp(self):
        self.players = [
            Player("User"),
            AIPlayer("AI-1", personality="Conservative"),
            AIPlayer("AI-2", personality="Risk Taker"),
            AIPlayer("AI-3", personality="Probability-Based"),
            AIPlayer("AI-4", personality="Bluffer"),
        ]
        self.game = PokerGame(self.players)

    def test_blinds_progression(self):
        """Test that blinds increase every two hands and move correctly."""
        initial_sb = self.game.small_blind
        initial_bb = self.game.big_blind
        self.game.post_blinds()
        self.assertEqual(self.game.small_blind, initial_sb)
        self.assertEqual(self.game.big_blind, initial_bb)
        
        self.game.hand_count = 2  # Simulate two hands played
        self.game.post_blinds()
        self.assertEqual(self.game.small_blind, initial_sb + 5)
        self.assertEqual(self.game.big_blind, (initial_sb + 5) * 2)

    def test_betting_logic(self):
        """Test that AI players correctly match, raise, or fold based on the highest bet."""
        self.game.post_blinds()
        self.game.betting_round()
        
        active_players = [p for p in self.players if p.is_active]
        self.assertGreaterEqual(len(active_players), 1, "At least one player should remain active")
        
        max_bet = max(p.current_bet for p in self.players)
        for player in self.players:
            if player.is_active:
                self.assertTrue(player.current_bet >= max_bet or player.stack == 0)

    def test_pot_distribution(self):
        """Test that the best hand wins and the pot is distributed correctly."""
        self.game.community_cards = ['2h', '5d', '9c', 'Jc', 'Qd']
        for player in self.players:
            player.receive_cards(['Ah', 'Ad'])  # Simulated strong hands for everyone
        self.game.pot = 500
        self.game.distribute_pot()
        
        winner = max(self.players, key=lambda p: p.stack)
        self.assertEqual(winner.stack, config.STARTING_CHIPS + 500)
        self.assertEqual(self.game.pot, 0)

    def test_player_elimination(self):
        """Test that players with zero chips are eliminated from the game."""
        for player in self.players:
            player.stack = 0
        
        self.game.betting_round()
        active_players = [p for p in self.players if p.is_active]
        self.assertEqual(len(active_players), 0, "All players should be eliminated if they have zero chips.")

if __name__ == '__main__':
    unittest.main()
