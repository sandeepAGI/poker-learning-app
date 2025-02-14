import unittest
from unittest.mock import Mock, patch
from game_engine import PokerGame, Player, AIPlayer, GameState
import config

class TestRoundManagement(unittest.TestCase):
    def setUp(self):
        """Set up a game with 4 AI players for testing."""
        self.players = [
            AIPlayer(f"Player_{i}", personality="conservative")
            for i in range(4)
        ]
        self.game = PokerGame(players=self.players)
        self.game.reset_deck()

    def test_game_state_progression(self):
        """Test that game states progress correctly."""
        self.assertEqual(self.game.current_state, GameState.PRE_FLOP)
        
        self.game.advance_game_state()
        self.assertEqual(self.game.current_state, GameState.FLOP)
        
        self.game.advance_game_state()
        self.assertEqual(self.game.current_state, GameState.TURN)
        
        self.game.advance_game_state()
        self.assertEqual(self.game.current_state, GameState.RIVER)
        
        self.game.advance_game_state()
        self.assertEqual(self.game.current_state, GameState.SHOWDOWN)

    def test_community_card_dealing(self):
        """Test that community cards are dealt correctly in each round."""
        # Pre-flop (no community cards)
        self.assertEqual(len(self.game.community_cards), 0)
        
        # Flop (3 cards)
        self.game.current_state = GameState.FLOP
        self.game.deal_community_cards()
        self.assertEqual(len(self.game.community_cards), 3)
        
        # Turn (1 more card)
        self.game.current_state = GameState.TURN
        self.game.deal_community_cards()
        self.assertEqual(len(self.game.community_cards), 4)
        
        # River (1 more card)
        self.game.current_state = GameState.RIVER
        self.game.deal_community_cards()
        self.assertEqual(len(self.game.community_cards), 5)

    def test_duplicate_community_card_prevention(self):
        """Test that community cards aren't dealt twice in the same round."""
        self.game.current_state = GameState.FLOP
        
        # First deal should work
        self.game.deal_community_cards()
        initial_cards = self.game.community_cards.copy()
        
        # Second deal should not change anything
        self.game.deal_community_cards()
        self.assertEqual(self.game.community_cards, initial_cards)

    def test_betting_position_order(self):
        """Test that betting order changes appropriately after pre-flop."""
        with patch.object(AIPlayer, 'make_decision', return_value='call'):
            # Pre-flop betting (should start left of BB)
            self.game.current_state = GameState.PRE_FLOP
            self.game.betting_round()
            
            # Post-flop betting (should start left of dealer)
            self.game.current_state = GameState.FLOP
            self.game.betting_round()

    def test_hand_completion(self):
        """Test that a complete hand plays through all states correctly."""
        with patch.object(AIPlayer, 'make_decision', return_value='call'):
            initial_hand_count = self.game.hand_count
            self.game.play_hand()
            
            # Verify hand count increased
            self.assertEqual(self.game.hand_count, initial_hand_count + 1)
            
            # Verify cleanup
            self.assertEqual(len(self.game.community_cards), 0)
            for player in self.game.players:
                self.assertEqual(len(player.hole_cards), 0)
                self.assertEqual(player.current_bet, 0)

class TestRegressionCore(unittest.TestCase):
    """Regression tests for core functionality."""
    
    def setUp(self):
        self.players = [
            AIPlayer(f"Player_{i}", personality="conservative")
            for i in range(4)
        ]
        self.game = PokerGame(players=self.players)
        self.game.reset_deck()

    def test_blind_posting(self):
        """Test that blinds are posted correctly."""
        initial_sb = self.game.small_blind
        initial_bb = self.game.big_blind
        
        self.game.post_blinds()
        
        # Verify blind amounts were posted
        sb_player = self.players[(self.game.dealer_index + 1) % len(self.players)]
        bb_player = self.players[(self.game.dealer_index + 2) % len(self.players)]
        
        self.assertEqual(sb_player.current_bet, initial_sb)
        self.assertEqual(bb_player.current_bet, initial_bb)
        self.assertEqual(self.game.pot, initial_sb + initial_bb)

    def test_blind_progression(self):
        """Test that blinds increase correctly."""
        initial_sb = self.game.small_blind
        
        # Play two hands to trigger blind increase
        self.game.hand_count = 2
        self.game.post_blinds()
        
        self.assertEqual(self.game.small_blind, initial_sb + 5)
        self.assertEqual(self.game.big_blind, (initial_sb + 5) * 2)

    def test_hole_card_dealing(self):
        """Test that hole cards are dealt correctly."""
        initial_deck_size = len(self.game.deck)
        self.game.deal_hole_cards()
        
        # Verify each player got exactly 2 cards
        for player in self.game.players:
            self.assertEqual(len(player.hole_cards), 2)
        
        # Verify correct number of cards were removed from deck
        expected_remaining = initial_deck_size - (len(self.players) * 2)
        self.assertEqual(len(self.game.deck), expected_remaining)

    def test_player_elimination(self):
        """Test that players are eliminated correctly."""
        player = self.players[0]
        player.stack = 4  # Below elimination threshold
        
        player.eliminate()
        self.assertFalse(player.is_active)

    def test_all_in_mechanics(self):
        """Test all-in betting mechanics."""
        player = self.players[0]
        initial_stack = 50
        player.stack = initial_stack
        
        # Try to bet more than stack
        bet_amount = player.bet(100)
        
        self.assertEqual(bet_amount, initial_stack)
        self.assertEqual(player.stack, 0)
        self.assertTrue(player.all_in)

class TestAIIntegration(unittest.TestCase):
    """Tests for AI decision-making integration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment with mocked config values."""
        cls.config_patcher = patch.multiple(
            'config',
            STARTING_CHIPS=200,
            SMALL_BLIND=5,
            BIG_BLIND=10
        )
        cls.mocked_config = cls.config_patcher.start()

    @classmethod
    def tearDownClass(cls):
        """Clean up the mock after all tests."""
        cls.config_patcher.stop()

    def setUp(self):
        """Set up individual test with a fresh game instance."""
        self.players = [
            AIPlayer(f"Player_{i}", personality="conservative")
            for i in range(4)
        ]
        self.game = PokerGame(players=self.players)
        self.game.reset_deck()

    def test_ai_decision_state_info(self):
        """Test that AI decisions receive correct game state information."""
        with patch('ai.ai_manager.AIDecisionMaker.make_decision', return_value='call') as mock_make_decision:
            self.game.current_state = GameState.FLOP
            self.game.betting_round()
            
            # Verify game state was passed to AI
            call_args = mock_make_decision.call_args.kwargs
            self.assertIn('game_state', call_args['game_state'])
            self.assertEqual(call_args['game_state']['game_state'], GameState.FLOP.value)

    def test_ai_stack_to_pot_calculation(self):
        """Test that SPR is calculated correctly for AI decisions."""
        with patch('game_engine.config.STARTING_CHIPS', 200), \
             patch('ai.ai_manager.AIDecisionMaker.make_decision', return_value='call') as mock_make_decision:
            
            # Set up initial state before betting round
            self.game.pot = 100
            self.game.current_bet = 0  # Important: set current bet to 0 to prevent calling
            for player in self.players:
                player.stack = 200
                player.current_bet = 0  # Reset any previous bets
                player.is_active = True
            
            # Mock player.bet to prevent stack changes
            with patch('game_engine.Player.bet', return_value=0):
                self.game.betting_round()
            
            # Get the FIRST call to make_decision, not the last
            first_call_args = mock_make_decision.call_args_list[0]
            actual_spr = first_call_args.kwargs['spr']
        
            # For debugging
            print(f"\nAll SPR values in order:")
            for call in mock_make_decision.call_args_list:
                print(f"SPR: {call.kwargs['spr']}")
            
            self.assertAlmostEqual(actual_spr, 2.0)

if __name__ == '__main__':
    unittest.main()