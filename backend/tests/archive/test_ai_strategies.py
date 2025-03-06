import unittest
from unittest.mock import patch, Mock
from game_engine import PokerGame, AIPlayer, GameState

class TestSPRCalculation(unittest.TestCase):
    """Focused test suite for SPR calculations with improved visibility."""
    
    def setUp(self):
        """Initialize test environment with controlled state."""
        self.players = [
            AIPlayer(
                player_id=f"Player_{i}",
                personality="conservative",
                stack=200
            ) for i in range(4)
        ]
        
        self.game = PokerGame(players=self.players)
        self.game.current_state = GameState.FLOP
        self.game.reset_deck()

    def test_spr_calculation_with_monitoring(self):
        """Test SPR calculation with enhanced state monitoring."""
        with patch('ai.ai_manager.AIDecisionMaker.make_decision', return_value='call') as mock_decision:
            # Set and verify initial state
            self.game.pot = 100
            print("\nInitial State:")
            print(f"Initial Pot: {self.game.pot}")
            print(f"Initial Stacks: {[p.stack for p in self.players]}")
            
            # Monitor pot changes during betting round
            self.game.betting_round()
            
            print("\nPost-Betting State:")
            print(f"Final Pot: {self.game.pot}")
            print(f"Final Stacks: {[p.stack for p in self.players]}")
            
            # Analyze decision parameters
            call_args = mock_decision.call_args
            self.assertIsNotNone(call_args, "AI decision maker was not called")
            
            actual_spr = call_args[0][4]
            print(f"\nSPR Calculation:")
            print(f"Actual SPR: {actual_spr}")
            print(f"Expected SPR: 2.0 (200/100)")
            
            # Verify SPR calculation
            self.assertAlmostEqual(
                actual_spr,
                2.0,
                places=2,
                msg="SPR calculation deviation detected"
            )
