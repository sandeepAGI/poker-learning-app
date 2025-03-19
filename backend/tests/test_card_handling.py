import sys
import os
import unittest
from typing import List, Dict, Any
from dataclasses import dataclass, field

# Add the parent directory to the path so we can import the game_engine module
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_path)

from game_engine import PokerGame, Player, GameState

class TestCardHandling(unittest.TestCase):
    """Tests specifically for the card handling fixes."""
    
    def setUp(self):
        """Set up a standard game with players."""
        self.players = [
            Player(player_id=f"p{i}", stack=1000) 
            for i in range(4)
        ]
        self.game = PokerGame(players=self.players)
        
    def test_hole_cards_cleared_between_hands(self):
        """Test that hole cards are properly cleared between hands."""
        # Deal initial hole cards
        self.game.deal_hole_cards()
        
        # Store the initial cards
        initial_cards = {}
        for player in self.players:
            self.assertEqual(len(player.hole_cards), 2, 
                           f"Player {player.player_id} should have 2 hole cards")
            initial_cards[player.player_id] = player.hole_cards.copy()
        
        # Simulate end of hand and reset
        for player in self.players:
            player.reset_hand_state()
            
        # Verify cards are cleared
        for player in self.players:
            self.assertEqual(len(player.hole_cards), 0, 
                          f"Player {player.player_id} should have cards cleared after reset")
        
        # Deal new hole cards
        self.game.reset_deck()
        self.game.deal_hole_cards()
        
        # Verify cards are different
        for player in self.players:
            self.assertEqual(len(player.hole_cards), 2, 
                           f"Player {player.player_id} should have 2 new hole cards")
            if player.player_id in initial_cards:
                self.assertNotEqual(player.hole_cards, initial_cards[player.player_id],
                                 f"Player {player.player_id} should have different cards in new hand")
    
    def test_no_duplicate_cards(self):
        """Test that no duplicate cards are dealt across players and community."""
        self.game.deal_hole_cards()
        
        # Collect all dealt cards
        all_cards = []
        for player in self.players:
            all_cards.extend(player.hole_cards)
        
        # Deal community cards
        self.game.current_state = GameState.FLOP
        self.game.deal_community_cards()
        all_cards.extend(self.game.community_cards)
        
        # Verify no duplicates
        self.assertEqual(len(all_cards), len(set(all_cards)),
                       "There should be no duplicate cards dealt")

if __name__ == '__main__':
    unittest.main()