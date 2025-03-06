import unittest
import os
import shutil
import time
from statistics_tracker import (
    get_statistics_manager, 
    StatisticsManager,
    PlayerStatistics,
    HandStatistics,
    SessionStatistics,
    ActionType,
    Position
)
from statistics_analyzer import StatisticsAnalyzer

# Create a test directory for stats
TEST_DATA_DIR = "test-game-data"

class TestStatisticsTracking(unittest.TestCase):
    """Test cases for the statistics tracking system."""
    
    def setUp(self):
        """Set up test environment."""
        # Create test directory
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)
        os.makedirs(TEST_DATA_DIR)
        
        # Initialize stats manager with test directory
        self.stats_manager = StatisticsManager(TEST_DATA_DIR)
        
        # Create test data
        self._create_test_data()
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)
    
    def _create_test_data(self):
        """Create test data for statistics testing."""
        # Create session
        self.session_id = "test_session_123"
        self.stats_manager.create_session_statistics(
            session_id=self.session_id,
            players=["player1", "player2", "player3", "player4"],
            starting_chips=1000,
            initial_small_blind=5,
            initial_big_blind=10
        )
        
        # Create players
        for player_id in ["player1", "player2", "player3", "player4"]:
            self.stats_manager.create_or_update_player_statistics(player_id)
        
        # Create some hand data
        for i in range(10):
            hand_id = f"hand_{i}"
            
            # Create hand statistics
            self.stats_manager.create_hand_statistics(
                hand_id=hand_id,
                game_id=self.session_id,
                players=["player1", "player2", "player3", "player4"],
                dealer_position=i % 4,
                small_blind=5,
                big_blind=10
            )
            
            # Record actions
            self._record_test_actions(hand_id, i)
            
            # Record hand result
            self._record_test_result(hand_id, i)
    
    def _record_test_actions(self, hand_id, hand_index):
        """Record test actions for a hand."""
        # Pre-flop actions
        self.stats_manager.record_action(
            hand_id=hand_id,
            player_id="player1",
            action_type=ActionType.RAISE if hand_index % 3 == 0 else ActionType.CALL,
            amount=20 if hand_index % 3 == 0 else 10,
            street="pre_flop",
            time_taken=1.5
        )
        
        self.stats_manager.record_action(
            hand_id=hand_id,
            player_id="player2",
            action_type=ActionType.CALL,
            amount=10,
            street="pre_flop",
            time_taken=2.0
        )
        
        self.stats_manager.record_action(
            hand_id=hand_id,
            player_id="player3",
            action_type=ActionType.FOLD if hand_index % 2 == 0 else ActionType.CALL,
            amount=0 if hand_index % 2 == 0 else 10,
            street="pre_flop",
            time_taken=1.0
        )
        
        self.stats_manager.record_action(
            hand_id=hand_id,
            player_id="player4",
            action_type=ActionType.RAISE if hand_index % 4 == 0 else ActionType.FOLD,
            amount=30 if hand_index % 4 == 0 else 0,
            street="pre_flop",
            time_taken=3.0
        )
        
        # Flop actions (if not all folded)
        if hand_index % 4 != 0:
            self.stats_manager.record_action(
                hand_id=hand_id,
                player_id="player1",
                action_type=ActionType.BET,
                amount=15,
                street="flop",
                time_taken=2.5
            )
            
            self.stats_manager.record_action(
                hand_id=hand_id,
                player_id="player2",
                action_type=ActionType.CALL if hand_index % 2 == 0 else ActionType.FOLD,
                amount=15 if hand_index % 2 == 0 else 0,
                street="flop",
                time_taken=1.8
            )
    
    def _record_test_result(self, hand_id, hand_index):
        """Record test result for a hand."""
        winners = {}
        hand_ranks = {}
        
        # Determine winner based on hand index
        if hand_index % 4 == 0:
            winners["player1"] = 50
            hand_ranks["player1"] = "High Card"
        elif hand_index % 4 == 1:
            winners["player2"] = 40
            hand_ranks["player1"] = "Pair"
            hand_ranks["player2"] = "Two Pair"
        elif hand_index % 4 == 2:
            winners["player1"] = 30
            hand_ranks["player1"] = "Straight"
            hand_ranks["player2"] = "Pair"
        else:
            winners["player4"] = 70
            hand_ranks["player1"] = "Flush"
            hand_ranks["player4"] = "Full House"
        
        # Record the result
        self.stats_manager.record_hand_result(
            hand_id=hand_id,
            final_pot=sum(winners.values()),
            winners=winners,
            showdown=bool(hand_ranks),
            hand_ranks=hand_ranks
        )
    
    def test_player_statistics_creation(self):
        """Test that player statistics are created correctly."""
        player_stats = self.stats_manager.get_player_statistics("player1")
        self.assertIsNotNone(player_stats)
        self.assertEqual(player_stats.player_id, "player1")
    
    def test_hand_statistics_creation(self):
        """Test that hand statistics are created correctly."""
        hand_stats = self.stats_manager.get_hand_statistics("hand_0")
        self.assertIsNotNone(hand_stats)
        self.assertEqual(hand_stats.hand_id, "hand_0")
        self.assertEqual(hand_stats.game_id, self.session_id)
    
    def test_session_statistics_creation(self):
        """Test that session statistics are created correctly."""
        session_stats = self.stats_manager.get_session_statistics(self.session_id)
        self.assertIsNotNone(session_stats)
        self.assertEqual(session_stats.session_id, self.session_id)
        self.assertEqual(len(session_stats.players), 4)
    
    def test_action_recording(self):
        """Test that actions are recorded correctly."""
        hand_stats = self.stats_manager.get_hand_statistics("hand_0")
        self.assertIsNotNone(hand_stats)
        
        # Check pre-flop actions
        self.assertEqual(len(hand_stats.pre_flop_actions), 4)
        
        # Verify player1's action
        player1_action = next((a for a in hand_stats.pre_flop_actions if a.player_id == "player1"), None)
        self.assertIsNotNone(player1_action)
        self.assertEqual(player1_action.action_type, ActionType.RAISE)
        self.assertEqual(player1_action.amount, 20)
    
    def test_hand_result_recording(self):
        """Test that hand results are recorded correctly."""
        hand_stats = self.stats_manager.get_hand_statistics("hand_1")
        self.assertIsNotNone(hand_stats)
        
        # Check winners
        self.assertIn("player2", hand_stats.winners)
        self.assertEqual(hand_stats.winners["player2"], 40)
        
        # Check hand ranks
        self.assertIn("player1", hand_stats.hand_ranks)
        self.assertEqual(hand_stats.hand_ranks["player1"], "Pair")
        self.assertEqual(hand_stats.hand_ranks["player2"], "Two Pair")
    
    def test_player_statistics_updates(self):
        """Test that player statistics are updated correctly after hands."""
        player1_stats = self.stats_manager.get_player_statistics("player1")
        self.assertIsNotNone(player1_stats)
        
        # Player should have played all 10 hands
        self.assertEqual(player1_stats.hands_played, 10)
        
        # Check win count (based on our test data setup)
        expected_wins = sum(1 for i in range(10) if i % 4 == 0 or i % 4 == 2)
        self.assertEqual(player1_stats.hands_won, expected_wins)
    
    def test_statistics_persistence(self):
        """Test that statistics are saved to and loaded from disk."""
        # Save statistics
        self.stats_manager.save_all_statistics()
        
        # Create a new manager that will load from disk
        new_manager = StatisticsManager(TEST_DATA_DIR)
        
        # Verify data was loaded
        player1_stats = new_manager.get_player_statistics("player1")
        self.assertIsNotNone(player1_stats)
        self.assertEqual(player1_stats.hands_played, 10)
        
        hand_stats = new_manager.get_hand_statistics("hand_0")
        self.assertIsNotNone(hand_stats)
        self.assertEqual(len(hand_stats.pre_flop_actions), 4)


class TestStatisticsAnalyzer(unittest.TestCase):
    """Test cases for the statistics analyzer."""
    
    def setUp(self):
        """Set up test environment."""
        # Create test directory
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)
        os.makedirs(TEST_DATA_DIR)
        
        # Initialize stats manager with test directory
        self.stats_manager = StatisticsManager(TEST_DATA_DIR)
        
        # Create analyzer
        self.analyzer = StatisticsAnalyzer()
        
        # Create test data
        self._create_test_data()
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)
    
    def _create_test_data(self):
        """Create more extensive test data for analyzer testing."""
        # Create session
        self.session_id = "test_session_123"
        self.stats_manager.create_session_statistics(
            session_id=self.session_id,
            players=["player1", "player2", "player3", "player4"],
            starting_chips=1000,
            initial_small_blind=5,
            initial_big_blind=10
        )
        
        # Create players with different play styles
        self.stats_manager.create_or_update_player_statistics(
            "player1",  # Tight-aggressive player
            hands_played=50,
            hands_won=15,
            total_winnings=1200,
            total_losses=800,
            fold_count=30,
            check_count=10,
            call_count=20,
            bet_count=15,
            raise_count=25,
            vpip_hands=20,  # 40% VPIP
            pfr_hands=15,   # 30% PFR
            showdown_count=15,
            showdown_wins=10
        )
        
        self.stats_manager.create_or_update_player_statistics(
            "player2",  # Loose-passive player
            hands_played=50,
            hands_won=10,
            total_winnings=800,
            total_losses=1000,
            fold_count=10,
            check_count=20,
            call_count=40,
            bet_count=5,
            raise_count=5,
            vpip_hands=35,  # 70% VPIP
            pfr_hands=5,    # 10% PFR
            showdown_count=25,
            showdown_wins=8
        )
        
        self.stats_manager.create_or_update_player_statistics(
            "player3",  # Tight-passive player
            hands_played=50,
            hands_won=8,
            total_winnings=600,
            total_losses=500,
            fold_count=35,
            check_count=25,
            call_count=15,
            bet_count=2,
            raise_count=3,
            vpip_hands=12,  # 24% VPIP
            pfr_hands=3,    # 6% PFR
            showdown_count=10,
            showdown_wins=6
        )
        
        self.stats_manager.create_or_update_player_statistics(
            "player4",  # Loose-aggressive player
            hands_played=50,
            hands_won=17,
            total_winnings=1400,
            total_losses=1100,
            fold_count=15,
            check_count=5,
            call_count=15,
            bet_count=20,
            raise_count=30,
            vpip_hands=40,  # 80% VPIP
            pfr_hands=30,   # 60% PFR
            showdown_count=20,
            showdown_wins=12
        )
        
        # Add positional data
        positions = [pos.value for pos in Position]
        for player_id in ["player1", "player2", "player3", "player4"]:
            player_stats = self.stats_manager.get_player_statistics(player_id)
            
            for pos in positions:
                player_stats.position_hands[pos] = 8  # 8 hands per position
                player_stats.position_wins[pos] = 1   # 1 win per position by default
            
            # Give each player a strong and weak position
            if player_id == "player1":
                player_stats.position_wins[Position.LATE.value] = 4  # Strong in late
                player_stats.position_wins[Position.SMALL_BLIND.value] = 0  # Weak in SB
            elif player_id == "player2":
                player_stats.position_wins[Position.EARLY.value] = 3  # Strong in early
                player_stats.position_wins[Position.BIG_BLIND.value] = 0  # Weak in BB
            elif player_id == "player3":
                player_stats.position_wins[Position.SMALL_BLIND.value] = 3  # Strong in SB
                player_stats.position_wins[Position.MIDDLE.value] = 0  # Weak in middle
            elif player_id == "player4":
                player_stats.position_wins[Position.DEALER.value] = 5  # Strong in dealer
                player_stats.position_wins[Position.EARLY.value] = 0  # Weak in early
    
    def test_player_analysis(self):
        """Test player analysis functionality."""
        # Analyze player1 (tight-aggressive)
        analysis = self.analyzer.analyze_player("player1")
        
        # Check basic metrics
        self.assertEqual(analysis["player_id"], "player1")
        self.assertEqual(analysis["basic_metrics"]["hands_played"], 50)
        self.assertEqual(analysis["basic_metrics"]["net_profit"], 400)
        
        # Player1 should have high aggression factor
        self.assertGreater(analysis["basic_metrics"]["aggression_factor"], 1.5)
    
    def test_leak_detection(self):
        """Test leak detection functionality."""
        # player2 is loose-passive, should have leaks
        analysis = self.analyzer.analyze_player("player2")
        
        # Should detect "too_loose" and "passive_preflop" leaks
        leak_types = [leak["type"] for leak in analysis["leaks"]]
        self.assertIn("too_loose", leak_types)
        self.assertIn("passive_preflop", leak_types)
        
        # Analyze player3 (tight-passive)
        analysis = self.analyzer.analyze_player("player3")
        leak_types = [leak["type"] for leak in analysis["leaks"]]
        self.assertIn("passive_postflop", leak_types)
    
    def test_positional_analysis(self):
        """Test positional analysis functionality."""
        # player1 is strong in late position, weak in SB
        analysis = self.analyzer.analyze_player("player1")
        pos_analysis = analysis["positional_analysis"]
        
        self.assertEqual(pos_analysis["strongest_position"], Position.LATE.value)
        self.assertEqual(pos_analysis["weakest_position"], Position.SMALL_BLIND.value)
    
    def test_recommendations(self):
        """Test recommendation generation."""
        # player2 is loose-passive, should get recommendations to tighten up
        analysis = self.analyzer.analyze_player("player2")
        
        recommendations = analysis["recommendations"]
        self.assertTrue(any("tighten" in rec.lower() for rec in recommendations))
    
    def test_learning_path(self):
        """Test learning path generation."""
        learning_path = self.analyzer.get_personalized_learning_path("player2")
        
        # Should recommend studying hand ranges due to loose play
        self.assertTrue(any("hand range" in topic.lower() for topic in learning_path))
    
    def test_player_comparison(self):
        """Test player comparison functionality."""
        comparison = self.analyzer.compare_players(["player1", "player2", "player3", "player4"])
        
        # Check that all players are included
        self.assertEqual(len(comparison["players"]), 4)
        
        # Win rate ranking should have player4 first (highest win rate)
        self.assertEqual(comparison["rankings"]["win_rate"][0], "player4")


if __name__ == "__main__":
    unittest.main()