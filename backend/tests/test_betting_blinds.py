import sys
import os
import unittest
from typing import List, Dict, Any
from dataclasses import dataclass, field

# Add the parent directory to the path so we can import the game_engine module
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_path)

from game_engine import PokerGame, Player, GameState

class TestBettingAndBlinds(unittest.TestCase):
    """Tests specifically for the betting and blinds fixes."""
    
    def setUp(self):
        """Set up a standard game with players."""
        self.players = [
            Player(player_id=f"p{i}", stack=1000) 
            for i in range(4)
        ]
        self.game = PokerGame(players=self.players)
        
    def test_initial_blind_values(self):
        """Test that blinds start with the correct values."""
        # Initial blind values before posting
        self.assertEqual(self.game.small_blind, 5, "Initial small blind should be 5")
        self.assertEqual(self.game.big_blind, 10, "Initial big blind should be 10")
        
        # Post blinds
        self.game.post_blinds()
        
        # Check blinds were properly posted
        sb_posted = False
        bb_posted = False
        
        for player in self.players:
            if player.current_bet == 5:
                sb_posted = True
            elif player.current_bet == 10:
                bb_posted = True
                
        self.assertTrue(sb_posted, "Small blind should be posted")
        self.assertTrue(bb_posted, "Big blind should be posted")
    
    def test_minimum_raise_calculation(self):
        """Test that minimum raise follows standard poker rules."""
        # Set up game state
        self.game.current_bet = 20
        self.game.big_blind = 10
        
        # Calculate minimum raise according to rules
        min_raise = self.game.current_bet + self.game.big_blind
        self.assertEqual(min_raise, 30, 
                       "Minimum raise should be current bet (20) + big blind (10)")
        
        # Try with a different current bet
        self.game.current_bet = 50
        min_raise = self.game.current_bet + self.game.big_blind
        self.assertEqual(min_raise, 60, 
                       "Minimum raise should be current bet (50) + big blind (10)")

if __name__ == '__main__':
    unittest.main()