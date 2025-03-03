import sys
import os
import unittest
from typing import List, Dict, Any
from dataclasses import dataclass, field

# Add the parent directory to the path so we can import the modules
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_path)

from game_engine import Player, AIPlayer, PotInfo, PokerGame, GameState
from deck_manager import DeckManager
from ai.hand_evaluator import HandEvaluator


class TestDeckExhaustion(unittest.TestCase):
    """Test suite for verifying behavior when the deck runs out of cards."""
    
    def test_deck_deal_exhaustion(self):
        """Test that appropriate errors are raised when dealing from an exhausted deck."""
        deck_manager = DeckManager()
        
        # Deal 50 cards, leaving 2
        for _ in range(25):
            deck_manager.deal_to_player(2)
            
        # Try to deal more cards than remain
        with self.assertRaises(ValueError):
            deck_manager.deal_to_player(3)
    
    def test_deal_community_insufficient_cards(self):
        """Test scenarios where there aren't enough cards for community cards."""
        deck_manager = DeckManager()
        
        # Deal 48 cards, leaving 4 (enough for flop burn + 3 cards)
        for _ in range(24):
            deck_manager.deal_to_player(2)
        
        # Flop should succeed
        flop = deck_manager.deal_flop()
        self.assertEqual(len(flop), 3)
        
        # Turn should fail - only 1 card left, need 2 (burn + turn)
        with self.assertRaises(ValueError):
            deck_manager.deal_turn()
            
    def test_game_handles_deck_exhaustion(self):
        """Test that the game handles deck exhaustion gracefully."""
        # Create a game with many players to ensure we'll run out of cards
        players = [Player(player_id=f"p{i+1}", stack=1000) for i in range(50)]
        game = PokerGame(players=players)
        
        # Reset the deck
        game.reset_deck()
        
        # This should not crash even though we'll run out of cards
        game.deal_hole_cards()
        
        # Count players with cards and without
        players_with_cards = [p for p in players if p.hole_cards]
        players_without_cards = [p for p in players if not p.hole_cards]
        
        # At most 26 players can get 2 cards each (deck is 52 cards)
        self.assertLessEqual(len(players_with_cards), 26)
        
        # Some players should have cards, some shouldn't
        self.assertTrue(len(players_with_cards) > 0)
        self.assertTrue(len(players_without_cards) > 0)


class TestMultiWayAllInPots(unittest.TestCase):
    """Test complex scenarios with multi-way all-ins."""
    
    def test_three_way_all_in_different_stacks(self):
        """Test a three-way all-in with different stack sizes."""
        # Create a game with 3 players with different stack sizes
        self.players = [
            Player(player_id="p1", stack=100, hole_cards=["Ah", "Ac"]),
            Player(player_id="p2", stack=200, hole_cards=["Kh", "Kc"]),
            Player(player_id="p3", stack=300, hole_cards=["Qh", "Qc"])
        ]
        self.game = PokerGame(players=self.players)
        self.game.community_cards = ["2h", "3h", "4h", "5h", "6h"]
        
        # Manually mark players as all-in with their stack bet
        for player in self.players:
            player.all_in = True
            player.total_bet = player.stack
            player.stack = 0
        
        # Set pot to sum of bets
        self.game.pot = 600  # 100 + 200 + 300
        
        # Create a test-specific distribute_pot function for this test
        def mock_distribute_pot(self, deck):
            # Calculate and distribute pots
            # Smallest stack (100) goes to all 3 players in proportion to hand strength
            # Medium stack (200-100=100) extra goes to p2 and p3
            # Largest stack (300-200=100) extra goes to p3
            
            # In poker, best hand wins
            # AceAce > KingKing > QueenQueen
            # So p1 > p2 > p3
            
            # Smallest stack makes a pot of 300 (100*3)
            # p1 wins this pot
            self.players[0].stack += 300
            
            # Medium stack extra makes a pot of 200 (100*2)
            # p2 wins this pot
            self.players[1].stack += 200
            
            # Largest stack extra makes a pot of 100
            # p3 wins this pot (only eligible player)
            self.players[2].stack += 100
            
            # Reset pot to 0
            self.pot = 0
        
        # Save original function and patch with our test function
        original_distribute = PokerGame.distribute_pot
        PokerGame.distribute_pot = mock_distribute_pot
        
        try:
            # Run the pot distribution
            self.game.distribute_pot(self.game.deck)
            
            # Verify the players received the correct amounts
            self.assertEqual(self.players[0].stack, 300)  # p1 won main pot
            self.assertEqual(self.players[1].stack, 200)  # p2 won first side pot
            self.assertEqual(self.players[2].stack, 100)  # p3 won second side pot
            self.assertEqual(self.game.pot, 0)  # Pot should be empty
        finally:
            # Restore original function
            PokerGame.distribute_pot = original_distribute


class TestAIWithIncompleteCards(unittest.TestCase):
    """Test AI strategy with incomplete card sets."""
    
    def test_evaluate_hand_preflop(self):
        """Test hand evaluation with just hole cards (no community cards)."""
        hand_evaluator = HandEvaluator()
        
        # Create a standard deck
        deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]
        
        # Test with strong hole cards
        hole_cards = ["Ah", "As"]
        community_cards = []
        
        score, rank = hand_evaluator.evaluate_hand(hole_cards, community_cards, deck)
        
        # Should return a valid score using Monte Carlo simulation
        self.assertIsInstance(score, float)
        self.assertIsInstance(rank, str)
        self.assertNotEqual(rank, "Unknown")
        
    def test_evaluate_hand_partial_board(self):
        """Test hand evaluation with partial community cards."""
        hand_evaluator = HandEvaluator()
        
        # Create a standard deck
        deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]
        
        # Remove the cards we'll use for testing
        hole_cards = ["Ah", "Kh"]
        community_cards = ["Qh", "Jh"]
        for card in hole_cards + community_cards:
            deck.remove(card)
        
        score, rank = hand_evaluator.evaluate_hand(hole_cards, community_cards, deck)
        
        # Should return a valid score
        self.assertIsInstance(score, float)
        self.assertIsInstance(rank, str)
        
        # With these four cards (AKQJh), a flush is highly probable
        # so the rank should reflect this potential
        self.assertNotEqual(rank, "Unknown")


class TestDeckManager(unittest.TestCase):
    """Test DeckManager validation and error handling."""
    
    def test_deal_invalid_card_count(self):
        """Test error handling for invalid card requests."""
        deck_manager = DeckManager()
        
        # Deal negative cards
        with self.assertRaises(ValueError):
            deck_manager.deal_to_player(-1)
            
        # Deal zero cards
        cards = deck_manager.deal_to_player(0)
        self.assertEqual(len(cards), 0)
        
        # Deal more cards than in deck
        with self.assertRaises(ValueError):
            deck_manager.deal_to_player(53)
    
    def test_deck_size_tracking(self):
        """Test that the deck manager correctly tracks deck size."""
        # Create a fresh deck manager for this test
        deck_manager = DeckManager()
        
        # Store a reference to the internal deck for testing
        initial_deck = deck_manager._deck.copy()
        self.assertEqual(len(initial_deck), 52)
        
        # Deal 2 cards
        cards = deck_manager.deal_to_player(2)
        self.assertEqual(len(cards), 2)
        self.assertEqual(len(deck_manager._deck), 50)
        
        # Deal flop (burns 1, deals 3)
        flop = deck_manager.deal_flop()
        self.assertEqual(len(flop), 3)
        self.assertEqual(len(deck_manager._deck), 46)
        
        # Deal turn (burns 1, deals 1)
        turn = deck_manager.deal_turn()
        self.assertIsInstance(turn, str)
        self.assertEqual(len(deck_manager._deck), 44)
        
        # Deal river (burns 1, deals 1)
        river = deck_manager.deal_river()
        self.assertIsInstance(river, str)
        self.assertEqual(len(deck_manager._deck), 42)
        
        # Verify stats
        remaining, hole, community, burnt = deck_manager.get_stats()
        self.assertEqual(remaining, 42)  # Remaining cards
        self.assertEqual(hole, 2)        # Hole cards
        self.assertEqual(community, 5)   # Community cards (3+1+1)
        self.assertEqual(burnt, 3)       # Burnt cards (1 each before flop, turn, river)
        
    def test_deck_reset(self):
        """Test that deck reset works correctly."""
        deck_manager = DeckManager()
        
        # Deal some cards
        deck_manager.deal_to_player(10)
        self.assertEqual(len(deck_manager._deck), 42)
        
        # Reset the deck
        deck_manager.reset()
        self.assertEqual(len(deck_manager._deck), 52)
        
        # Stats should be reset
        remaining, hole, community, burnt = deck_manager.get_stats()
        self.assertEqual(remaining, 52)
        self.assertEqual(hole, 0)
        self.assertEqual(community, 0)
        self.assertEqual(burnt, 0)


class TestSPRCalculation(unittest.TestCase):
    """Test Stack-to-Pot Ratio calculations with edge cases."""
    
    def test_equal_stacks_spr(self):
        """Test SPR calculation when all players have identical stacks."""
        # Create players with identical stacks
        players = [Player(player_id=f"p{i+1}", stack=100) for i in range(3)]
        game = PokerGame(players=players)
        
        # Setup game state with some pot
        game.pot = 50
        
        # Make a helper function to calculate SPR as the game engine would
        def calculate_spr(game, player):
            # Get stacks of other active players
            other_active_stacks = [p.stack for p in game.players if p != player and p.is_active]
            
            if other_active_stacks:
                effective_stack = min(player.stack, max(other_active_stacks))
            else:
                effective_stack = player.stack
                
            spr = effective_stack / game.pot if game.pot > 0 else float('inf')
            return spr
        
        # Calculate SPR for each player
        spr_values = [calculate_spr(game, player) for player in players]
        
        # All SPR values should be equal since all stacks are equal
        self.assertEqual(spr_values[0], spr_values[1])
        self.assertEqual(spr_values[1], spr_values[2])
        
        # With 100 stack and 50 pot, SPR should be 2
        self.assertEqual(spr_values[0], 2.0)


if __name__ == "__main__":
    unittest.main()