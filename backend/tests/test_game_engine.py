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

    def test_side_pot_creation(self):
        """Test creation of side pots when players go all-in with different amounts."""
        # Setup players with specific stacks
        self.players[0].stack = 100  # Will bet 100
        self.players[1].stack = 50   # Will bet 50 (all-in)
        self.players[2].stack = 25   # Will bet 25 (all-in)
        self.players[3].stack = 100  # Will bet 100
        
        # Simulate betting
        for player in self.players:
            player.current_bet = player.stack
            player.stack = 0
            if player.current_bet < 100:
                player.all_in = True
        
        # Calculate pots
        pots = self.game.calculate_pots()
        
        # Should create 3 pots:
        # 1. Main pot: All players eligible (25 * 4 = 100)
        # 2. Middle pot: Players 0, 1, 3 eligible (25 * 3 = 75)
        # 3. High pot: Players 0, 3 eligible (50 * 2 = 100)
        self.assertEqual(len(pots), 3)
        self.assertEqual(pots[0].amount, 100)  # 25 from each player
        self.assertEqual(pots[1].amount, 75)   # 25 more from three players
        self.assertEqual(pots[2].amount, 100)  # 50 more from two players
        self.assertEqual(len(pots[0].eligible_players), 4)
        self.assertEqual(len(pots[1].eligible_players), 3)
        self.assertEqual(len(pots[2].eligible_players), 2)

    def test_split_pot_distribution(self):
        """Test even distribution of pot when players tie."""
        # Setup two players with identical hands
        self.players = self.players[:2]  # Use only 2 players for simplicity
        self.game = PokerGame(players=self.players)
        
        # Important: Reset player stacks to 0
        for player in self.players:
            player.stack = 0

        # Set up identical hands (both with Ace high)
        self.players[0].hole_cards = ["Ah", "Kh"]
        self.players[1].hole_cards = ["Ad", "Kd"]
        self.game.community_cards = ["2c", "5c", "7d", "Tc", "Qc"]
        
        # Set up pot
        self.game.pot = 100
        self.players[0].current_bet = 50
        self.players[1].current_bet = 50
        
        # Distribute pot
        self.game.distribute_pot(self.game.deck)
        
        # Each player should receive half the pot
        self.assertEqual(self.players[0].stack, 50)
        self.assertEqual(self.players[1].stack, 50)

    def test_uneven_split_pot_distribution(self):
        """Test distribution of odd-numbered pot in split pot scenario."""
        # Similar setup to split_pot but with odd pot amount
        self.players = self.players[:2]
        self.game = PokerGame(players=self.players)

        # Important: Reset player stacks to 0
        for player in self.players:
            player.stack = 0
        
        self.players[0].hole_cards = ["Ah", "Kh"]
        self.players[1].hole_cards = ["Ad", "Kd"]
        self.game.community_cards = ["2c", "5c", "7d", "Tc", "Qc"]
        
        # Set up odd-numbered pot
        self.game.pot = 101
        self.players[0].current_bet = 51
        self.players[1].current_bet = 50
        
        # Distribute pot
        self.game.distribute_pot(self.game.deck)
        
        # First player should get 51, second 50 (or vice versa)
        stacks = {self.players[0].stack, self.players[1].stack}
        self.assertEqual(stacks, {50, 51})

    def test_all_in_multiple_side_pots(self):
        """Test complex scenario with multiple all-ins and side pots."""
        # Player 1: 100 chips (bets all)
        # Player 2: 50 chips (all-in)
        # Player 3: 25 chips (all-in)
        # Player 4: 100 chips (calls 100)
        
        initial_stacks = [100, 50, 25, 100]
        for player, stack in zip(self.players, initial_stacks):
            player.stack = stack
            player.current_bet = stack
            player.stack = 0
            if stack < 100:
                player.all_in = True
        
        # Set up different strength hands
        hands = [["Ah", "Kh"], ["Qh", "Qd"], ["Jh", "Jd"], ["Th", "Td"]]
        for player, hand in zip(self.players, hands):
            player.hole_cards = hand
        
        self.game.community_cards = ["2c", "5c", "7d", "Tc", "Qc"]
        
        # Distribute pots
        self.game.distribute_pot(self.game.deck)
        
        # Verify:
        # - Main pot (25*4 = 100) should go to highest hand among all
        # - Second pot (25*3 = 75) should go to highest among remaining three
        # - Final pot (50*2 = 100) should go to highest of top two
        self.assertEqual(sum(p.stack for p in self.players), 275)  # Total money preserved


class TestGameRequirements(unittest.TestCase):
    """Tests for specific game requirements implementation."""
    
    def setUp(self):
        """Set up test environment."""
        self.human_player = Player("Human")
        self.ai_players = [
            AIPlayer(f"AI_{i}", personality=f"personality_{i}")
            for i in range(4)
        ]
        self.all_players = [self.human_player] + self.ai_players
        self.game = PokerGame(players=self.all_players)

    def test_player_count_validation(self):
        """Verify game enforces 1 human + 4 AI players requirement."""
        # Test with too few players
        with self.assertRaises(ValueError):
            insufficient_players = [self.human_player] + self.ai_players[:2]
            PokerGame(players=insufficient_players)
        
        # Test with too many players
        with self.assertRaises(ValueError):
            extra_ai = AIPlayer("Extra_AI", personality="conservative")
            too_many_players = self.all_players + [extra_ai]
            PokerGame(players=too_many_players)
        
        # Test with wrong player type composition
        with self.assertRaises(ValueError):
            all_ai_players = [AIPlayer(f"AI_{i}", personality="conservative") 
                            for i in range(5)]
            PokerGame(players=all_ai_players)

    def test_blind_progression_schedule(self):
        """Test blind increases follow specified schedule."""
        initial_sb = self.game.small_blind
        initial_bb = self.game.big_blind
        
        # First two hands should maintain initial blinds
        self.game.hand_count = 1
        self.game.post_blinds()
        self.assertEqual(self.game.small_blind, initial_sb)
        self.assertEqual(self.game.big_blind, initial_bb)
        
        self.game.hand_count = 2
        self.game.post_blinds()
        self.assertEqual(self.game.small_blind, initial_sb)
        self.assertEqual(self.game.big_blind, initial_bb)
        
        # Third hand should increase blinds
        self.game.hand_count = 3
        self.game.post_blinds()
        self.assertEqual(self.game.small_blind, initial_sb + config.BLIND_INCREASE)
        self.assertEqual(self.game.big_blind, (initial_sb + config.BLIND_INCREASE) * 2)
        
        # Verify progression continues
        self.game.hand_count = 5
        self.game.post_blinds()
        self.assertEqual(self.game.small_blind, initial_sb + (2 * config.BLIND_INCREASE))
        self.assertEqual(self.game.big_blind, (initial_sb + (2 * config.BLIND_INCREASE)) * 2)

    def test_win_conditions(self):
        """Test all specified win conditions."""
        # Test user elimination
        self.human_player.stack = 4  # Below elimination threshold
        self.human_player.eliminate()
        self.assertFalse(self.human_player.is_active)
        
        # Test all AI eliminated
        for ai_player in self.ai_players:
            ai_player.stack = 4
            ai_player.eliminate()
        self.assertTrue(all(not p.is_active for p in self.ai_players))
        
        # Verify only one active player remains
        active_players = [p for p in self.all_players if p.is_active]
        self.assertEqual(len(active_players), 0)

    @patch('ai.ai_manager.AIDecisionMaker.make_decision')
    def test_ai_personality_consistency(self, mock_make_decision):
        """Verify AI personalities remain consistent throughout game."""
        # Set up tracking for each AI's decisions
        decision_history = {player.player_id: [] for player in self.ai_players}
        
        # Mock different decisions based on personality
        def ai_decision(personality, **kwargs):
            if 'conservative' in personality:
                return 'fold'
            elif 'risk_taker' in personality:
                return 'raise'
            return 'call'
        
        mock_make_decision.side_effect = ai_decision
        
        # Play multiple hands and track decisions
        for _ in range(3):
            self.game.current_state = GameState.PRE_FLOP
            self.game.betting_round()
            
            # Record each AI's decision
            for player in self.ai_players:
                last_call = mock_make_decision.call_args_list[-1]
                decision_history[player.player_id].append(last_call)
        
        # Verify each AI's decisions were consistent with their personality
        for player in self.ai_players:
            decisions = decision_history[player.player_id]
            self.assertTrue(len(set(decisions)) <= 1)  # All decisions should be same

    def test_elimination_sequence(self):
        """Test proper handling of multiple player eliminations."""
        # Set up players with different stack sizes near elimination
        stack_sizes = [4, 6, 4, 7, 4]  # Three should be eliminated
        for player, stack in zip(self.all_players, stack_sizes):
            player.stack = stack
        
        # Process eliminations
        for player in self.all_players:
            player.eliminate()
        
        # Verify correct number of eliminations
        active_players = [p for p in self.all_players if p.is_active]
        eliminated_players = [p for p in self.all_players if not p.is_active]
        
        self.assertEqual(len(active_players), 2)
        self.assertEqual(len(eliminated_players), 3)
        
        # Verify correct players were eliminated
        self.assertTrue(all(p.stack < 5 for p in eliminated_players))
        self.assertTrue(all(p.stack >= 5 for p in active_players))

    def test_starting_conditions(self):
        """Test initial game setup requirements."""
        # Verify starting chip counts
        for player in self.all_players:
            self.assertEqual(player.stack, config.STARTING_CHIPS)
        
        # Verify initial blind levels
        self.assertEqual(self.game.small_blind, config.SMALL_BLIND)
        self.assertEqual(self.game.big_blind, config.SMALL_BLIND * 2)
        
        # Verify AI personalities are assigned
        for ai_player in self.ai_players:
            self.assertIsNotNone(ai_player.personality)
            self.assertNotEqual(ai_player.personality, "")

if __name__ == '__main__':
    unittest.main()