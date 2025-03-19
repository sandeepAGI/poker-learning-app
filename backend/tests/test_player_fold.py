import sys
import os
import unittest
from typing import List, Dict, Any
from dataclasses import dataclass, field

# Add the parent directory to the path so we can import the game_engine module
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_path)

from game_engine import PokerGame, Player, GameState

class TestPlayerStatusAndFolding(unittest.TestCase):
    """Tests specifically for player status and folding behavior fixes."""
    
    def setUp(self):
        """Set up a standard game with players."""
        self.players = [
            Player(player_id=f"p{i}", stack=1000) 
            for i in range(4)
        ]
        self.game = PokerGame(players=self.players)
        
    def test_folded_player_reactivation(self):
        """Test that folded players are properly reactivated in the next hand."""
        # Mark some players as folded
        self.players[1].is_active = False
        self.players[2].is_active = False
        
        # Verify initial state
        self.assertTrue(self.players[0].is_active)
        self.assertFalse(self.players[1].is_active)
        self.assertFalse(self.players[2].is_active)
        self.assertTrue(self.players[3].is_active)
        
        # Simulate end of hand and start of new hand
        for player in self.players:
            player.reset_hand_state()
            
        # Verify all players were reactivated
        for i, player in enumerate(self.players):
            self.assertTrue(player.is_active, 
                          f"Player {i} should be reactivated for the new hand")
            
    def test_eliminated_player_stays_inactive(self):
        """Test that players with insufficient chips stay inactive."""
        # Set player 2 with insufficient chips
        self.players[2].stack = 3  # Below minimum (5)
        
        # Simulate end of hand and start of new hand
        for player in self.players:
            player.reset_hand_state()
            
        # Check that player 2 stays inactive
        self.assertFalse(self.players[2].is_active,
                       "Player with insufficient chips should stay inactive")
        
        # Other players should be active
        self.assertTrue(self.players[0].is_active)
        self.assertTrue(self.players[1].is_active)
        self.assertTrue(self.players[3].is_active)
        
    def test_game_advances_when_all_but_one_fold(self):
        """Test that game properly advances to showdown when all but one player fold."""
        # Deal cards and set up the game
        self.game.deal_hole_cards()
        self.game.current_state = GameState.FLOP
        self.game.deal_community_cards()
        
        # Mark all players except one as folded
        for i in range(1, len(self.players)):
            self.players[i].is_active = False
            
        # Verify initial state
        self.assertEqual(self.game.current_state, GameState.FLOP)
        
        # Advance game state
        self.game.advance_game_state()
        
        # Game should skip to showdown since only one player is active
        self.assertEqual(self.game.current_state, GameState.SHOWDOWN,
                       "Game should advance to showdown when only one player remains")
        
if __name__ == '__main__':
    unittest.main()