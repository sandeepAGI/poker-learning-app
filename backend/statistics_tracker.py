from typing import Dict, List, Optional, Any, Tuple
import math
from statistics_tracker import (
    get_statistics_manager, 
    PlayerStatistics, 
    HandStatistics, 
    SessionStatistics,
    LearningStatistics,
    Position
)
from logger import get_logger

# Create a logger for the statistics analyzer
logger = get_logger("statistics_analyzer")

class StatisticsAnalyzer:
    """
    Analyzes poker statistics to provide insights and recommendations.
    Identifies patterns, leaks, and areas for improvement.
    """
    
    def __init__(self):
        """Initialize the statistics analyzer with reference to the statistics manager."""
        self.stats_manager = get_statistics_manager()
        logger.info("Statistics analyzer initialized")
        
    def analyze_player(self, player_id: str) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis of a player's performance.
        
        Args:
            player_id: ID of the player to analyze
            
        Returns:
            Dictionary containing analysis results including:
            - Basic metrics (win rate, VPIP, PFR, etc.)
            - Positional performance
            - Identified leaks
            - Recommendations
        """
        player_stats = self.stats_manager.get_player_statistics(player_id)
        if not player_stats:
            logger.warning(f"No statistics found for player: {player_id}")
            return {"error": "Player not found"}
        
        # Basic metrics
        basic_metrics = self._get_basic_metrics(player_stats)
        
        # Positional analysis
        positional_analysis = self._analyze_positional_play(player_stats)
        
        # Leak detection
        leaks = self._detect_leaks(player_stats)
        
        # Recommendations
        recommendations = self._generate_recommendations(player_stats, leaks)
        
        return {
            "player_id": player_id,
            "basic_metrics": basic_metrics,
            "positional_analysis": positional_analysis,
            "leaks": leaks,
            "recommendations": recommendations
        }
    
    def _get_basic_metrics(self, player_stats: PlayerStatistics) -> Dict[str, Any]:
        """Extract basic performance metrics from player statistics."""
        return {
            "hands_played": player_stats.hands_played,
            "win_rate": player_stats.win_rate,
            "vpip": player_stats.vpip,
            "pfr": player_stats.pfr,
            "aggression_factor": player_stats.aggression_factor,
            "showdown_success": player_stats.showdown_success,
            "total_winnings": player_stats.total_winnings,
            "total_losses": player_stats.total_losses,
            "net_profit": player_stats.total_winnings - player_stats.total_losses
        }
    
    def _analyze_positional_play(self, player_stats: PlayerStatistics) -> Dict[str, Any]:
        """Analyze performance by position."""
        position_analysis = {}
        
        for position in Position:
            position_value = position.value
            
            # Skip positions with no hands played
            if player_stats.position_hands.get(position_value, 0) == 0:
                continue
                
            hands_in_position = player_stats.position_hands.get(position_value, 0)
            wins_in_position = player_stats.position_wins.get(position_value, 0)
            win_rate_in_position = (wins_in_position / hands_in_position * 100) if hands_in_position > 0 else 0
            
            position_analysis[position_value] = {
                "hands_played": hands_in_position,
                "hands_won": wins_in_position,
                "win_rate": win_rate_in_position
            }
        
        # Identify strongest and weakest positions
        if position_analysis:
            strongest_position = max(position_analysis.items(), 
                                    key=lambda x: x[1]["win_rate"] if x[1]["hands_played"] >= 5 else 0)
            weakest_position = min(position_analysis.items(), 
                                  key=lambda x: x[1]["win_rate"] if x[1]["hands_played"] >= 5 else 100)
            
            return {
                "by_position": position_analysis,
                "strongest_position": strongest_position[0] if strongest_position[1]["hands_played"] >= 5 else None,
                "weakest_position": weakest_position[0] if weakest_position[1]["hands_played"] >= 5 else None
            }
        
        return {"by_position": {}}
    
    def _detect_leaks(self, player_stats: PlayerStatistics) -> List[Dict[str, Any]]:
        """
        Identify potential leaks in a player's game.
        
        A leak is a weakness in a player's strategy that consistently costs them chips.
        """
        leaks = []
        
        # Check for play style leaks
        if player_stats.hands_played >= 20:  # Minimum sample size
            # Too tight (low VPIP)
            if player_stats.vpip < 15:
                leaks.append({
                    "type": "too_tight",
                    "description": "Playing too few hands (low VPIP)",
                    "severity": "high" if player_stats.vpip < 10 else "medium",
                    "metric": "vpip",
                    "value": player_stats.vpip
                })
            
            # Too loose (high VPIP)
            if player_stats.vpip > 35:
                leaks.append({
                    "type": "too_loose",
                    "description": "Playing too many hands (high VPIP)",
                    "severity": "high" if player_stats.vpip > 45 else "medium",
                    "metric": "vpip",
                    "value": player_stats.vpip
                })
            
            # Passive preflop (low PFR/VPIP ratio)
            if player_stats.vpip > 0 and player_stats.pfr / player_stats.vpip < 0.5:
                leaks.append({
                    "type": "passive_preflop",
                    "description": "Too much calling, not enough raising preflop",
                    "severity": "medium",
                    "metric": "pfr_vpip_ratio",
                    "value": player_stats.pfr / player_stats.vpip if player_stats.vpip > 0 else 0
                })
            
            # Too passive postflop (low aggression factor)
            if player_stats.aggression_factor < 1.0:
                leaks.append({
                    "type": "passive_postflop",
                    "description": "Too passive postflop (low aggression factor)",
                    "severity": "high" if player_stats.aggression_factor < 0.5 else "medium",
                    "metric": "aggression_factor",
                    "value": player_stats.aggression_factor
                })
            
            # Too aggressive postflop (very high aggression factor)
            if player_stats.aggression_factor > 4.0:
                leaks.append({
                    "type": "too_aggressive",
                    "description": "Possibly too aggressive postflop",
                    "severity": "medium",
                    "metric": "aggression_factor",
                    "value": player_stats.aggression_factor
                })
            
            # Poor showdown success
            if player_stats.showdown_count >= 10 and player_stats.showdown_success < 40:
                leaks.append({
                    "type": "poor_showdown",
                    "description": "Low success rate at showdowns",
                    "severity": "high" if player_stats.showdown_success < 30 else "medium",
                    "metric": "showdown_success",
                    "value": player_stats.showdown_success
                })
        
        return leaks
    
    def _generate_recommendations(self, player_stats: PlayerStatistics, 
                                 leaks: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on detected leaks."""
        recommendations = []
        
        for leak in leaks:
            if leak["type"] == "too_tight":
                recommendations.append(
                    "Expand your starting hand range, especially in late position."
                )
            elif leak["type"] == "too_loose":
                recommendations.append(
                    "Tighten your starting hand requirements, particularly in early position."
                )
            elif leak["type"] == "passive_preflop":
                recommendations.append(
                    "Raise more frequently with your playable hands instead of just calling."
                )
            elif leak["type"] == "passive_postflop":
                recommendations.append(
                    "Be more aggressive with your strong hands and drawing hands postflop."
                )
            elif leak["type"] == "too_aggressive":
                recommendations.append(
                    "Mix in more calls and checks to balance your aggression."
                )
            elif leak["type"] == "poor_showdown":
                recommendations.append(
                    "Fold more marginal hands or improve hand reading to avoid showdowns with weaker hands."
                )
        
        # Add general recommendations based on positional play
        positional_analysis = self._analyze_positional_play(player_stats)
        if positional_analysis.get("weakest_position"):
            weak_pos = positional_analysis["weakest_position"]
            if weak_pos == Position.EARLY.value:
                recommendations.append(
                    "Tighten your early position range to improve performance."
                )
            elif weak_pos in [Position.SMALL_BLIND.value, Position.BIG_BLIND.value]:
                recommendations.append(
                    "Study blind defense strategies to improve your performance from the blinds."
                )
        
        return recommendations
    
    def analyze_hand_type_performance(self, player_id: str) -> Dict[str, Any]:
        """
        Analyze player performance with different hand types.
        
        Args:
            player_id: ID of the player to analyze
            
        Returns:
            Dictionary mapping hand ranks to performance metrics
        """
        hand_stats = self._get_player_hand_stats(player_id)
        if not hand_stats:
            return {}
        
        # Group performance by hand rank
        hand_type_performance = {}
        
        for hand_id, stats in hand_stats.items():
            if player_id not in stats.hand_ranks:
                continue
                
            hand_rank = stats.hand_ranks[player_id]
            
            if hand_rank not in hand_type_performance:
                hand_type_performance[hand_rank] = {
                    "count": 0,
                    "wins": 0,
                    "total_won": 0
                }
            
            hand_type_performance[hand_rank]["count"] += 1
            
            if player_id in stats.winners:
                hand_type_performance[hand_rank]["wins"] += 1
                hand_type_performance[hand_rank]["total_won"] += stats.winners[player_id]
        
        # Calculate win rates
        for hand_rank, perf in hand_type_performance.items():
            if perf["count"] > 0:
                perf["win_rate"] = (perf["wins"] / perf["count"]) * 100
                perf["avg_win"] = perf["total_won"] / perf["wins"] if perf["wins"] > 0 else 0
            else:
                perf["win_rate"] = 0
                perf["avg_win"] = 0
        
        return hand_type_performance
    
    def _get_player_hand_stats(self, player_id: str) -> Dict[str, HandStatistics]:
        """Get all hand statistics for a specific player."""
        all_hand_stats = self.stats_manager._hand_stats  # Access private field directly
        
        return {
            hand_id: stats for hand_id, stats in all_hand_stats.items()
            if player_id in stats.players
        }
    
    def analyze_decision_quality(self, player_id: str) -> Dict[str, Any]:
        """
        Analyze the quality of a player's decisions.
        
        Args:
            player_id: ID of the player to analyze
            
        Returns:
            Dictionary with decision quality metrics
        """
        learning_stats = self.stats_manager.get_learning_statistics(player_id)
        if not learning_stats:
            return {}
        
        decision_quality = {
            "total_decisions": learning_stats.total_decisions,
            "correct_decisions": learning_stats.correct_decisions,
            "accuracy": learning_stats.decision_accuracy,
            "positive_ev_decisions": learning_stats.positive_ev_decisions,
            "negative_ev_decisions": learning_stats.negative_ev_decisions,
            "ev_ratio": (learning_stats.positive_ev_decisions / learning_stats.total_decisions * 100) 
                       if learning_stats.total_decisions > 0 else 0
        }
        
        return decision_quality
    
    def get_personalized_learning_path(self, player_id: str) -> List[str]:
        """
        Generate a personalized learning path based on the player's statistics.
        
        Args:
            player_id: ID of the player
            
        Returns:
            List of learning recommendations in priority order
        """
        player_stats = self.stats_manager.get_player_statistics(player_id)
        if not player_stats or player_stats.hands_played < 20:
            return ["Play more hands to generate meaningful statistics for analysis."]
        
        # Detect leaks
        leaks = self._detect_leaks(player_stats)
        
        # Convert leaks to learning topics by severity
        learning_path = []
        
        high_severity_leaks = [leak for leak in leaks if leak["severity"] == "high"]
        medium_severity_leaks = [leak for leak in leaks if leak["severity"] == "medium"]
        
        # Add high severity topics first
        for leak in high_severity_leaks:
            if leak["type"] == "too_tight":
                learning_path.append("Study starting hand selection in different positions")
            elif leak["type"] == "too_loose":
                learning_path.append("Learn about hand ranges and preflop selection criteria")
            elif leak["type"] == "passive_preflop":
                learning_path.append("Develop a balanced preflop raising strategy")
            elif leak["type"] == "passive_postflop":
                learning_path.append("Study postflop aggression and betting strategies")
            elif leak["type"] == "poor_showdown":
                learning_path.append("Improve hand reading skills and understanding of showdown value")
                
        # Then add medium severity topics
        for leak in medium_severity_leaks:
            if leak["type"] == "too_aggressive":
                learning_path.append("Study when to slow play and balance your ranges")
        
        # Add positional play recommendations
        positional_analysis = self._analyze_positional_play(player_stats)
        if positional_analysis.get("weakest_position"):
            weak_pos = positional_analysis["weakest_position"]
            if weak_pos == Position.EARLY.value:
                learning_path.append("Study early position strategy and hand selection")
            elif weak_pos == Position.MIDDLE.value:
                learning_path.append("Improve middle position play and reading opponents")
            elif weak_pos == Position.LATE.value:
                learning_path.append("Learn to exploit positional advantage in late position")
            elif weak_pos in [Position.SMALL_BLIND.value, Position.BIG_BLIND.value]:
                learning_path.append("Master blind defense and stealing strategies")
                
        # If no specific leaks found, add general improvement topics
        if not learning_path:
            learning_path = [
                "Study hand reading and opponent tendencies",
                "Learn about pot odds and implied odds",
                "Improve understanding of betting patterns and sizing",
                "Study advanced concepts like balanced ranges"
            ]
            
        return learning_path
    
    def compare_players(self, player_ids: List[str]) -> Dict[str, Any]:
        """
        Compare performance metrics between multiple players.
        
        Args:
            player_ids: List of player IDs to compare
            
        Returns:
            Dictionary with comparative metrics
        """
        if len(player_ids) < 2:
            return {"error": "Need at least two players to compare"}
            
        comparison = {
            "players": {},
            "rankings": {}
        }
        
        # Collect metrics for each player
        for player_id in player_ids:
            player_stats = self.stats_manager.get_player_statistics(player_id)
            if not player_stats:
                continue
                
            comparison["players"][player_id] = self._get_basic_metrics(player_stats)
        
        # Generate rankings for key metrics
        key_metrics = ["win_rate", "vpip", "pfr", "aggression_factor", "showdown_success", "net_profit"]
        
        for metric in key_metrics:
            # Skip metrics that don't exist for some players
            if not all(metric in player_data for player_data in comparison["players"].values()):
                continue
                
            # Rank players by this metric (higher is better, except for some metrics)
            reverse_order = metric not in ["vpip"]  # For VPIP, lower might be better
            
            ranked_players = sorted(
                comparison["players"].items(),
                key=lambda x: x[1].get(metric, 0),
                reverse=reverse_order
            )
            
            comparison["rankings"][metric] = [player_id for player_id, _ in ranked_players]
        
        return comparison
    
    def generate_session_report(self, session_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive report for a game session.
        
        Args:
            session_id: ID of the session to analyze
            
        Returns:
            Dictionary with session analysis and player performances
        """
        session_stats = self.stats_manager.get_session_statistics(session_id)
        if not session_stats:
            logger.warning(f"No statistics found for session: {session_id}")
            return {"error": "Session not found"}
            
        # Session overview
        session_duration = (session_stats.end_time or 0) - session_stats.start_time
        
        overview = {
            "session_id": session_id,
            "duration_seconds": session_duration,
            "hands_played": session_stats.hands_played,
            "players": session_stats.players,
            "eliminated_order": session_stats.elimination_order
        }
        
        # Player performances
        performances = {}
        
        for player_id in session_stats.players:
            player_stats = self.stats_manager.get_player_statistics(player_id)
            if not player_stats:
                continue
                
            initial_chips = session_stats.starting_chips
            final_chips = session_stats.final_chip_counts.get(player_id, 0)
            
            performances[player_id] = {
                "initial_chips": initial_chips,
                "final_chips": final_chips,
                "net_change": final_chips - initial_chips,
                "win_rate": player_stats.win_rate,
                "hands_won": player_stats.hands_won,
                "eliminated": player_id in session_stats.elimination_order
            }
            
            if player_id in session_stats.elimination_order:
                performances[player_id]["elimination_position"] = session_stats.elimination_order.index(player_id) + 1
        
        # Determine winner
        if session_stats.final_chip_counts:
            winner_id = max(session_stats.final_chip_counts.items(), key=lambda x: x[1])[0]
            overview["winner"] = winner_id
        
        return {
            "overview": overview,
            "player_performances": performances
        }
    
    def get_trending_statistics(self, player_id: str, num_hands: int = 20) -> Dict[str, Any]:
        """
        Analyze trends in a player's recent performance.
        
        Args:
            player_id: ID of the player to analyze
            num_hands: Number of recent hands to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        player_hand_stats = self._get_player_hand_stats(player_id)
        if not player_hand_stats:
            return {}
            
        # Sort hands by timestamp (most recent first)
        recent_hands = sorted(
            player_hand_stats.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )[:num_hands]
        
        if not recent_hands:
            return {}
            
        # Calculate trends
        wins = []
        vpip_trend = []
        pfr_trend = []
        aggression_trend = []
        
        for i, hand in enumerate(reversed(recent_hands)):
            # Win/loss trend
            won = player_id in hand.winners
            wins.append(1 if won else 0)
            
            # VPIP trend (did player voluntarily put money in pot preflop?)
            vpip_action = False
            for action in hand.pre_flop_actions:
                if action.player_id == player_id and action.action_type.value in ["call", "bet", "raise", "all_in"]:
                    vpip_action = True
                    break
            vpip_trend.append(1 if vpip_action else 0)
            
            # PFR trend (did player raise preflop?)
            pfr_action = False
            for action in hand.pre_flop_actions:
                if action.player_id == player_id and action.action_type.value in ["bet", "raise"]:
                    pfr_action = True
                    break
            pfr_trend.append(1 if pfr_action else 0)
            
            # Aggression trend
            aggressive_actions = 0
            passive_actions = 0
            
            for street in [hand.pre_flop_actions, hand.flop_actions, hand.turn_actions, hand.river_actions]:
                for action in street:
                    if action.player_id == player_id:
                        if action.action_type.value in ["bet", "raise"]:
                            aggressive_actions += 1
                        elif action.action_type.value == "call":
                            passive_actions += 1
            
            aggression = aggressive_actions / passive_actions if passive_actions > 0 else float('inf')
            aggression_trend.append(min(aggression, 5.0))  # Cap at 5.0 for charting purposes
        
        # Calculate moving averages
        window_size = min(5, len(wins))
        win_rate_ma = self._calculate_moving_average(wins, window_size)
        vpip_ma = self._calculate_moving_average(vpip_trend, window_size)
        pfr_ma = self._calculate_moving_average(pfr_trend, window_size)
        
        return {
            "last_n_hands": num_hands,
            "win_trend": wins,
            "win_rate_moving_avg": win_rate_ma,
            "vpip_trend": vpip_trend,
            "vpip_moving_avg": vpip_ma,
            "pfr_trend": pfr_trend,
            "pfr_moving_avg": pfr_ma,
            "aggression_trend": aggression_trend,
            "overall_trend": "improving" if win_rate_ma[-1] > win_rate_ma[0] else "declining"
        }
    
    def _calculate_moving_average(self, data: List[float], window_size: int) -> List[float]:
        """Calculate moving average with specified window size."""
        results = []
        for i in range(len(data)):
            window_start = max(0, i - window_size + 1)
            window = data[window_start:i+1]
            avg = sum(window) / len(window)
            results.append(avg)
        return results