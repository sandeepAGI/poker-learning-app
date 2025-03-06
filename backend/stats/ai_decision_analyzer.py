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

class AIDecisionAnalyzer:
    """
    Analyzes player decisions by comparing them with AI strategies.
    Provides insights on decision quality and learning recommendations.
    """
    
    def __init__(self):
        """Initialize the AI decision analyzer."""
        self.stats_manager = get_statistics_manager()
        logger.info("AI decision analyzer initialized")
    
    def analyze_decision(self, player_id: str, player_decision: str, 
                        hole_cards: List[str], game_state: Dict[str, Any], 
                        deck: List[str], pot_size: int, spr: float) -> Dict[str, Any]:
        """
        Analyze a player's decision by comparing it with AI strategies.
        
        Args:
            player_id: ID of the player who made the decision
            player_decision: The decision made ("fold", "call", or "raise")
            hole_cards: Player's hole cards
            game_state: Current game state including community cards
            deck: Current deck state
            pot_size: Current pot size
            spr: Stack-to-pot ratio
            
        Returns:
            Dictionary containing decision analysis
        """
        # Compare with all AI strategies
        strategy_decisions = self._get_all_strategy_decisions(
            hole_cards, game_state, deck, pot_size, spr
        )
        
        # Find which strategy matches the player's decision
        matching_strategy = self._find_matching_strategy(player_decision, strategy_decisions)
        
        # Determine optimal strategy in this situation
        optimal_strategy, expected_value = self._find_optimal_strategy(
            strategy_decisions, hole_cards, game_state, pot_size, spr
        )
        
        # Determine if player's decision was optimal
        was_optimal = matching_strategy == optimal_strategy
        
        # Create decision data
        decision_data = {
            "hand_id": game_state.get("hand_id", "unknown"),
            "game_state": game_state.get("game_state", "unknown"),
            "decision": player_decision,
            "hole_cards": hole_cards,
            "community_cards": game_state.get("community_cards", []),
            "pot_size": pot_size,
            "spr": spr,
            "current_bet": game_state.get("current_bet", 0),
            "matching_strategy": matching_strategy,
            "optimal_strategy": optimal_strategy,
            "was_optimal": was_optimal,
            "expected_value": expected_value,
            "strategy_decisions": strategy_decisions
        }
        
        # Record the decision for later analysis
        self.stats_manager.record_decision(player_id, decision_data)
        
        # Log the analysis
        logger.info(
            f"Player {player_id} decision: {player_decision} | "
            f"Matching strategy: {matching_strategy} | "
            f"Optimal strategy: {optimal_strategy} | "
            f"Was optimal: {was_optimal}"
        )
        
        return decision_data
    
    def _get_all_strategy_decisions(self, hole_cards: List[str], game_state: Dict[str, Any], 
                                  deck: List[str], pot_size: int, spr: float) -> Dict[str, str]:
        """
        Get decisions from all AI strategies for the same situation.
        
        Args:
            hole_cards: Player's hole cards
            game_state: Current game state
            deck: Current deck state
            pot_size: Current pot size
            spr: Stack-to-pot ratio
            
        Returns:
            Dictionary mapping strategy names to decisions
        """
        strategies = ["Conservative", "Risk Taker", "Probability-Based", "Bluffer"]
        strategy_decisions = {}
        
        for strategy in strategies:
            try:
                decision = AIDecisionMaker.make_decision(
                    personality=strategy,
                    hole_cards=hole_cards,
                    game_state=game_state,
                    deck=deck,
                    pot_size=pot_size,
                    spr=spr
                )
                strategy_decisions[strategy] = decision
                logger.debug(f"Strategy {strategy} decision: {decision}")
            except Exception as e:
                logger.error(f"Error getting decision for strategy {strategy}: {e}")
                strategy_decisions[strategy] = "fold"  # Default to fold on error
        
        return strategy_decisions
    
    def _find_matching_strategy(self, player_decision: str, 
                              strategy_decisions: Dict[str, str]) -> str:
        """
        Find which AI strategy most closely matches the player's decision.
        
        Args:
            player_decision: The player's decision
            strategy_decisions: Dictionary of decisions from each strategy
            
        Returns:
            Name of the matching strategy
        """
        # Find exact matches first
        matching_strategies = [
            strategy for strategy, decision in strategy_decisions.items()
            if decision == player_decision
        ]
        
        if matching_strategies:
            # If multiple matches, prioritize in this order
            priority_order = ["Probability-Based", "Conservative", "Risk Taker", "Bluffer"]
            for strategy in priority_order:
                if strategy in matching_strategies:
                    return strategy
            return matching_strategies[0]
        
        # If no exact match, find closest (e.g., if player called and no strategy called)
        decision_strength = {"fold": 0, "call": 1, "raise": 2}
        player_strength = decision_strength.get(player_decision, 0)
        
        closest_strategy = None
        min_diff = float('inf')
        
        for strategy, decision in strategy_decisions.items():
            strategy_strength = decision_strength.get(decision, 0)
            diff = abs(player_strength - strategy_strength)
            
            if diff < min_diff:
                min_diff = diff
                closest_strategy = strategy
        
        return closest_strategy or "Conservative"
    
    def _find_optimal_strategy(self, strategy_decisions: Dict[str, str], 
                             hole_cards: List[str], game_state: Dict[str, Any],
                             pot_size: int, spr: float) -> Tuple[str, float]:
        """
        Determine which AI strategy would be optimal in the current situation.
        
        Args:
            strategy_decisions: Dictionary of decisions from each strategy
            hole_cards: Player's hole cards
            game_state: Current game state
            pot_size: Current pot size
            spr: Stack-to-pot ratio
            
        Returns:
            Tuple of (optimal strategy name, expected value)
        """
        # This is a simplified model to determine the optimal strategy
        # In a real implementation, you would calculate expected value for each decision
        
        # For now, we'll use a heuristic approach based on hand strength and SPR
        community_cards = game_state.get("community_cards", [])
        current_bet = game_state.get("current_bet", 0)
        
        # Determine game stage
        if not community_cards:
            stage = "pre_flop"
        elif len(community_cards) == 3:
            stage = "flop"
        elif len(community_cards) == 4:
            stage = "turn"
        else:
            stage = "river"
        
        # Use the decisions that the AIs actually made for deeper analysis
        fold_strategies = [s for s, d in strategy_decisions.items() if d == "fold"]
        call_strategies = [s for s, d in strategy_decisions.items() if d == "call"]
        raise_strategies = [s for s, d in strategy_decisions.items() if d == "raise"]
        
        # Simplified heuristic for optimal strategy based on SPR, stage and AI consensus
        
        # More AIs raising is a signal of a strong hand
        if len(raise_strategies) >= 2:
            # Multiple AIs think raising is correct
            if "Probability-Based" in raise_strategies:
                return "Probability-Based", 2.0
            else:
                return raise_strategies[0], 1.5
                
        # More AIs folding is a signal of a weak hand
        if len(fold_strategies) >= 2:
            # Multiple AIs think folding is correct
            if "Conservative" in fold_strategies:
                return "Conservative", -0.5
            else:
                return fold_strategies[0], -0.8
        
        # Mixed signals - use SPR-based heuristics
        if spr < 3:  # Low SPR favors Risk Taker or Conservative with strong hands
            if stage == "pre_flop":
                return "Risk Taker", 1.5
            else:
                return "Conservative", 1.0
        elif spr <= 6:  # Medium SPR favors Probability-Based
            return "Probability-Based", 0.8
        else:  # High SPR favors Conservative or Bluffer
            if stage == "pre_flop":
                return "Conservative", 0.6
            else:
                # Late stages with high SPR favor occasional bluffing
                return "Bluffer", 0.4
                
        # In a more sophisticated implementation, you would:
        # 1. Simulate outcomes for each decision
        # 2. Calculate expected value
        # 3. Return the strategy with highest EV
        
    def generate_feedback(self, decision_data: Dict[str, Any]) -> str:
        """
        Generate feedback for a player based on their decision.
        
        Args:
            decision_data: Dictionary containing decision analysis
            
        Returns:
            String containing feedback message
        """
        player_decision = decision_data["decision"]
        matching_strategy = decision_data["matching_strategy"]
        optimal_strategy = decision_data["optimal_strategy"]
        was_optimal = decision_data["was_optimal"]
        spr = decision_data["spr"]
        game_state = decision_data["game_state"]
        
        feedback = []
        
        # Strategy match feedback
        feedback.append(f"Your decision ({player_decision}) matches a {matching_strategy} playing style.")
        
        # Optimal strategy feedback
        if was_optimal:
            feedback.append(f"This was the optimal decision in this situation!")
        else:
            feedback.append(f"A {optimal_strategy} might have decided to {strategy_decisions[optimal_strategy]} in this situation.")
        
        # SPR-based feedback
        if spr < 3:
            feedback.append("With a low SPR, being aggressive with strong hands is generally optimal.")
        elif spr <= 6:
            feedback.append("With a medium SPR, balanced play based on hand strength is important.")
        else:
            feedback.append("With a high SPR, being selective and occasionally bluffing can be effective.")
        
        return "\n".join(feedback)
    
    def get_player_strategy_profile(self, player_id: str) -> Dict[str, Any]:
        """
        Get a player's strategy profile based on their decision history.
        
        Args:
            player_id: ID of the player
            
        Returns:
            Dictionary containing strategy profile information
        """
        learning_stats = self.stats_manager.get_learning_statistics(player_id)
        
        # Calculate strategy distribution
        strategy_distribution = learning_stats.get_strategy_distribution()
        
        # Get dominant and recommended strategies
        dominant_strategy = learning_stats.dominant_strategy
        recommended_strategy = learning_stats.recommended_strategy
        
        # Calculate decision accuracy
        accuracy = learning_stats.decision_accuracy
        
        # Get EV ratio
        ev_ratio = 0
        if learning_stats.total_decisions > 0:
            ev_ratio = (learning_stats.positive_ev_decisions / learning_stats.total_decisions) * 100
        
        return {
            "strategy_distribution": strategy_distribution,
            "dominant_strategy": dominant_strategy,
            "recommended_strategy": recommended_strategy,
            "decision_accuracy": accuracy,
            "ev_ratio": ev_ratio,
            "total_decisions": learning_stats.total_decisions
        }

# Create a singleton instance
_decision_analyzer = None

def get_decision_analyzer() -> AIDecisionAnalyzer:
    """
    Get the singleton instance of the AI decision analyzer.
    
    Returns:
        AIDecisionAnalyzer instance
    """
    global _decision_analyzer
    if _decision_analyzer is None:
        _decision_analyzer = AIDecisionAnalyzer()
    return _decision_analyzer