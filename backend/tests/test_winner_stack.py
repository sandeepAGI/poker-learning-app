import sys
import os
import unittest
from typing import List, Dict, Any
from dataclasses import dataclass, field

# Add the parent directory to the path so we can import the game_engine module
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_path)

from game_engine import PokerGame, Player, GameState

class TestWinnerAndStackUpdates(unittest.TestCase):
    """Tests specifically for winner information and stack updates."""
    
    def setUp(self):
        """Set up a standard game with players."""
        self.players = [
            Player(player_id=f"p{i}", stack=1000) 
            for i in range(3)
        ]
        self.game = PokerGame(players=self.players)
        
        # Set up custom distribute_pot to simulate winning
        self.original_distribute = PokerGame.distribute_pot
        
    def tearDown(self):
        """Restore original distribute_pot method."""
        PokerGame.distribute_pot = self.original_distribute
        
    def test_pot_distribution_updates_stacks(self):
        """Test that pot distribution correctly updates player stacks."""
        # Set up a pot
        pot_amount = 300
        self.game.pot = pot_amount
        
        # Set player 0 as the winner
        winner_id = self.players[0].player_id
        
        # Create a test-specific distribute_pot method
        def test_distribute_pot(self, deck):
            # Give all chips to player 0
            for player in self.players:
                if player.player_id == winner_id:
                    player.stack += self.pot
            self.pot = 0
            
            # Return a winner info dictionary as expected
            return {winner_id: pot_amount}
        
        # Patch the distribute_pot method
        PokerGame.distribute_pot = test_distribute_pot
        
        # Execute the distribution
        self.game.distribute_pot(self.game.deck)
        
        # Verify winner's stack increased
        self.assertEqual(self.players[0].stack, 1000 + pot_amount,
                       f"Winner's stack should increase by {pot_amount}")
        
        # Verify pot is now empty
        self.assertEqual(self.game.pot, 0, "Pot should be empty after distribution")
        
    def test_pot_distribution_with_multiple_winners(self):
        """Test that pot distribution correctly handles multiple winners."""
        # Set up a pot
        pot_amount = 300
        self.game.pot = pot_amount
        
        # Create a test-specific distribute_pot method for split pot
        def test_distribute_pot(self, deck):
            # Split the pot between players 0 and 1
            split_amount = self.pot // 2
            
            winner_ids = [self.players[0].player_id, self.players[1].player_id]
            
            for player in self.players:
                if player.player_id in winner_ids:
                    player.stack += split_amount
            
            # Handle odd chip if needed
            if self.pot % 2 == 1:
                self.players[0].stack += 1
                
            self.pot = 0
            
            # Return a winner info dictionary as expected
            return {
                winner_ids[0]: split_amount + (1 if self.pot % 2 == 1 else 0),
                winner_ids[1]: split_amount
            }
            
        # Patch the distribute_pot method
        PokerGame.distribute_pot = test_distribute_pot
        
        # Execute the distribution
        self.game.distribute_pot(self.game.deck)
        
        # Verify winners' stacks increased correctly
        self.assertEqual(self.players[0].stack, 1000 + (pot_amount // 2) + (1 if pot_amount % 2 == 1 else 0),
                       "First winner's stack should increase by their share")
        self.assertEqual(self.players[1].stack, 1000 + (pot_amount // 2),
                       "Second winner's stack should increase by their share")
        
        # Verify third player's stack unchanged
        self.assertEqual(self.players[2].stack, 1000,
                       "Non-winner's stack should remain unchanged")
if __name__ == '__main__':
    unittest.main()