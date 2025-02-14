import unittest
from unittest.mock import patch, Mock
from game_engine import PokerGame, AIPlayer, GameState

class TestSPRCalculation(unittest.TestCase):
    """
    Isolated test suite for Stack-to-Pot Ratio (SPR) calculations.
    This follows the principle of focused testing that has proven 
    successful in complex system migrations.
    """
    
    def setUp(self):
        """
        Initialize test environment with controlled state.
        Similar to how organizations create sanitized test environments
        for critical system components.
        """
        # Create players with predetermined stack sizes
        self.players = [
            AIPlayer(
                player_id=f"Player_{i}",
                personality="conservative",
                stack=200  # Controlled stack size for predictable SPR
            ) for i in range(4)
        ]
        
        # Initialize game with controlled state
        self.game = PokerGame(players=self.players)
        self.game.pot = 100  # Set pot for 2.0 SPR target
        self.game.current_state = GameState.FLOP
        
        # Reset deck to ensure clean state
        self.game.reset_deck()

    def test_spr_calculation_basic(self):
        """
        Test basic SPR calculation with controlled inputs.
        This represents a fundamental system validation, similar to
        testing core business logic during digital transformation.
        """
        # Mock AI decision making to isolate SPR calculation
        with patch('ai.ai_manager.AIDecisionMaker.make_decision', return_value='call') as mock_decision:
            # Execute betting round
            self.game.betting_round()
            
            # Capture and analyze decision parameters
            call_args = mock_decision.call_args
            
            # Verify decision was made
            self.assertIsNotNone(
                call_args,
                "AI decision maker was not called"
            )
            
            # Extract and verify SPR value
            actual_spr = call_args[0][4]
            print(f"\nTest Results:")
            print(f"Target SPR: 2.0")
            print(f"Actual SPR: {actual_spr}")
            print(f"Player Stacks: {[p.stack for p in self.players]}")
            print(f"Pot Size: {self.game.pot}")
            
            # Verify SPR calculation accuracy
            self.assertAlmostEqual(
                actual_spr,
                2.0,
                places=2,
                msg="SPR calculation deviation detected"
            )

if __name__ == '__main__':
    unittest.main()
