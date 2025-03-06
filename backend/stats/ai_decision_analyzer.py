from typing import List, Dict, Any, Tuple, Optional
import copy
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.ai_manager import AIDecisionMaker
from stats.statistics_manager import get_statistics_manager
from utils.logger import get_logger

# Create a logger for the AI decision analyzer
logger = get_logger("ai.decision_analyzer")

# Global singleton instance
_decision_analyzer = None

def get_decision_analyzer():
    """
    Returns a singleton instance of the AIDecisionAnalyzer.
    
    Returns:
        AIDecisionAnalyzer: The singleton instance
    """
    global _decision_analyzer
    if _decision_analyzer is None:
        _decision_analyzer = AIDecisionAnalyzer()
    return _decision_analyzer

class AIDecisionAnalyzer:
    """
    Analyzes poker decisions by comparing them with AI-driven strategies.
    Provides feedback and recommendations for improvement.
    """
    
    def __init__(self):
        """Initialize the AI decision analyzer."""
        self.stats_manager = get_statistics_manager()
        
        # Try to import the analyzer modules
        try:
            from stats.analyzer.feedback_generator import FeedbackGenerator
            from stats.analyzer.hand_analyzer import HandAnalyzer
            from stats.analyzer.pattern_analyzer import PatternAnalyzer
            from stats.analyzer.recommendation_engine import RecommendationEngine
            from stats.analyzer.trend_analyzer import TrendAnalyzer
            
            self.feedback_generator = FeedbackGenerator
            self.hand_analyzer = HandAnalyzer
            self.pattern_analyzer = PatternAnalyzer
            self.recommendation_engine = RecommendationEngine
            self.trend_analyzer = TrendAnalyzer
            self.using_analyzer_modules = True
            logger.info("Using analyzer modules for enhanced feedback")
        except ImportError as e:
            self.using_analyzer_modules = False
            logger.warning(f"Analyzer modules not available, using built-in methods: {e}")
    
    def analyze_decision(self, player_id: str, player_decision: str, 
                        hole_cards: List[str], game_state: Dict[str, Any],
                        deck: List[str], pot_size: float, spr: float) -> Dict[str, Any]:
        """
        Analyzes a player's poker decision by comparing it with AI strategies.
        
        Args:
            player_id: Unique player identifier
            player_decision: Player's decision (fold, call, raise)
            hole_cards: Player's hole cards
            game_state: Current game state information
            deck: Remaining deck for simulations
            pot_size: Current pot size
            spr: Stack-to-pot ratio
            
        Returns:
            Dictionary with decision analysis data
        """
        # Get decisions from different AI strategies
        ai_decision_maker = AIDecisionMaker()
        strategy_decisions = {
            "Conservative": ai_decision_maker.make_decision(
                "Conservative", hole_cards, game_state, deck, pot_size, spr
            ),
            "Risk Taker": ai_decision_maker.make_decision(
                "Risk Taker", hole_cards, game_state, deck, pot_size, spr
            ),
            "Probability-Based": ai_decision_maker.make_decision(
                "Probability-Based", hole_cards, game_state, deck, pot_size, spr
            ),
            "Bluffer": ai_decision_maker.make_decision(
                "Bluffer", hole_cards, game_state, deck, pot_size, spr
            )
        }
        
        # Find which strategy the player's decision most closely matches
        matching_strategy = self._find_matching_strategy(player_decision, strategy_decisions)
        
        # Find the optimal strategy for this situation
        optimal_strategy, expected_value = self._find_optimal_strategy(
            strategy_decisions, hole_cards, game_state, pot_size, spr
        )
        
        # Check if player's decision matches the optimal strategy's decision
        was_optimal = (strategy_decisions[optimal_strategy] == player_decision)
        
        # Record detailed game state and context
        decision_data = {
            "decision": player_decision,
            "matching_strategy": matching_strategy,
            "optimal_strategy": optimal_strategy,
            "was_optimal": was_optimal,
            "strategy_decisions": strategy_decisions,
            "expected_value": expected_value,
            "spr": spr,
            "game_state": game_state.get("game_state", "unknown"),
            "hole_cards": hole_cards,
            "community_cards": game_state.get("community_cards", []),
            "pot_size": pot_size,
            "current_bet": game_state.get("current_bet", 0)
        }
        
        # Record the decision in the player's statistics
        self.stats_manager.record_decision(player_id, decision_data)
        
        return decision_data
    
    def _find_matching_strategy(self, player_decision: str, 
                              strategy_decisions: Dict[str, str]) -> str:
        """
        Finds which strategy most closely matches the player's decision.
        
        Args:
            player_decision: Player's decision (fold, call, raise)
            strategy_decisions: Dictionary of decisions by strategy
            
        Returns:
            Name of the matching strategy
        """
        # Strategy priority order for tie-breaking
        strategy_priority = ["Probability-Based", "Conservative", "Risk Taker", "Bluffer"]
        
        # First, check for exact matches
        exact_matches = []
        for strategy, decision in strategy_decisions.items():
            if decision == player_decision:
                exact_matches.append(strategy)
        
        # If multiple exact matches, return the highest priority one
        if exact_matches:
            for strategy in strategy_priority:
                if strategy in exact_matches:
                    return strategy
        
        # If no exact match, find closest match based on "action strength"
        # Fold < Call < Raise
        action_strength = {"fold": 0, "call": 1, "raise": 2}
        player_strength = action_strength.get(player_decision, 1)  # Default to call
        
        best_match = None
        smallest_diff = float('inf')
        
        for strategy, decision in strategy_decisions.items():
            strategy_strength = action_strength.get(decision, 1)  # Default to call
            diff = abs(player_strength - strategy_strength)
            
            if diff < smallest_diff or (diff == smallest_diff and 
                                      strategy_priority.index(strategy) < strategy_priority.index(best_match)):
                smallest_diff = diff
                best_match = strategy
        
        return best_match
    
    def _find_optimal_strategy(self, strategy_decisions: Dict[str, str],
                             hole_cards: List[str], game_state: Dict[str, Any],
                             pot_size: float, spr: float) -> Tuple[str, float]:
        """
        Determines the optimal strategy based on the game context.
        
        Args:
            strategy_decisions: Decisions made by different strategies
            hole_cards: Player's hole cards
            game_state: Current game state information
            pot_size: Current pot size
            spr: Stack-to-pot ratio
            
        Returns:
            Tuple of (optimal strategy name, expected value)
        """
        # Different strategies perform better in different contexts
        # This is a simplified heuristic - could be enhanced with ML or more detailed heuristics
        
        game_stage = game_state.get("game_state", "unknown")
        community_cards = game_state.get("community_cards", [])
        
        # Low SPR scenarios (<3) favor aggressive play
        if spr < 3:
            if game_stage == "pre_flop":
                return "Risk Taker", 1.2
            else:
                return "Conservative", 0.9
                
        # Medium SPR scenarios (3-6) favor calculated play
        elif spr <= 6:
            if game_stage == "pre_flop":
                return "Conservative", 1.0
            else:
                return "Probability-Based", 1.1
                
        # High SPR scenarios (>6) favor conservative play pre-flop and calculated play post-flop
        else:
            if game_stage == "pre_flop":
                return "Conservative", 1.3
            else:
                return "Probability-Based", 1.2
    
    def generate_feedback(self, decision_data: Dict[str, Any]) -> str:
        """
        Generates detailed, educational feedback for a player based on their decision.
        
        Args:
            decision_data: Dictionary containing decision analysis
            
        Returns:
            String containing feedback message with actionable advice
        """
        if self.using_analyzer_modules:
            # Use the specialized feedback generator if available
            return self.feedback_generator.generate_feedback(decision_data)
        
        # Fallback implementation if the module isn't available
        feedback = []
        
        # Extract data
        player_decision = decision_data["decision"]
        matching_strategy = decision_data["matching_strategy"]
        optimal_strategy = decision_data["optimal_strategy"]
        was_optimal = decision_data["was_optimal"]
        spr = decision_data["spr"]
        
        # Basic feedback components
        feedback.append(f"Your decision to {player_decision} matches a {matching_strategy} playing style.")
        
        if was_optimal:
            feedback.append("This was the optimal decision for this situation.")
        else:
            feedback.append(f"A {optimal_strategy} player would have made a different decision here.")
        
        # SPR-based advice
        if spr < 3:
            feedback.append("With a low SPR, commitment decisions are critical.")
        elif spr <= 6:
            feedback.append("With a medium SPR, you have flexibility for different plays.")
        else:
            feedback.append("With a high SPR, premium hands and draws gain value.")
        
        return "\n".join(feedback)
    
    def get_player_strategy_profile(self, player_id: str) -> Dict[str, Any]:
        """
        Retrieves a player's strategy profile with strengths, weaknesses, and recommendations.
        
        Args:
            player_id: Unique player identifier
            
        Returns:
            Dictionary with strategy profile data
        """
        # Get player learning statistics
        learning_stats = self.stats_manager.get_learning_statistics(player_id)
        
        # Basic profile data
        profile = {
            "strategy_distribution": learning_stats.get_strategy_distribution(),
            "dominant_strategy": learning_stats.dominant_strategy,
            "recommended_strategy": learning_stats.recommended_strategy,
            "decision_accuracy": learning_stats.decision_accuracy,
            "ev_ratio": (learning_stats.positive_ev_decisions / learning_stats.total_decisions * 100 
                        if learning_stats.total_decisions > 0 else 0),
            "total_decisions": learning_stats.total_decisions
        }
        
        # Get recent decisions for trend analysis
        recent_decisions = learning_stats.get_recent_decisions(30)  # Last 30 decisions
        
        if self.using_analyzer_modules and recent_decisions:
            # Use the specialized analyzer modules if available
            game_state_patterns = self.pattern_analyzer.analyze_game_state_patterns(recent_decisions)
            spr_patterns = self.pattern_analyzer.analyze_spr_patterns(recent_decisions)
            
            improvement_areas = self.pattern_analyzer.identify_improvement_areas(
                recent_decisions,
                profile["dominant_strategy"],
                profile["recommended_strategy"],
                profile["decision_accuracy"],
                spr_patterns,
                game_state_patterns
            )
            
            profile["improvement_areas"] = improvement_areas
            
            profile["learning_recommendations"] = self.recommendation_engine.generate_learning_recommendations(
                profile["dominant_strategy"],
                profile["recommended_strategy"],
                improvement_areas,
                profile["total_decisions"]
            )
            
            profile["decision_trend"] = self.trend_analyzer.analyze_decision_quality_trend(recent_decisions)
            
        else:
            # Simplified fallback implementation
            profile["improvement_areas"] = []
            profile["learning_recommendations"] = []
            profile["decision_trend"] = {"trend": "not_enough_data", "description": "Need more data"}
        
        return profile