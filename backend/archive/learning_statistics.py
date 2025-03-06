from typing import Dict, List, Any, Optional
import time


class LearningStatistics:
    """
    Tracks a player's decision quality and learning progress over time.
    Stores detailed decision history, strategy alignments, and improvement metrics.
    """
    
    # Constants for storage management
    MAX_DETAILED_DECISIONS = 100  # Only store last 100 detailed decisions
    
    def __init__(self, player_id: str):
        """
        Initialize learning statistics for a player.
        
        Args:
            player_id: Unique identifier for the player
        """
        self.player_id = player_id
        self.total_decisions = 0
        self.correct_decisions = 0
        self.decisions_by_strategy = {
            "Conservative": 0,
            "Risk Taker": 0, 
            "Probability-Based": 0,
            "Bluffer": 0
        }
        self.optimal_strategies = {
            "Conservative": 0,
            "Risk Taker": 0,
            "Probability-Based": 0,
            "Bluffer": 0
        }
        self.decision_history: List[Dict[str, Any]] = []
        self.current_session_id: Optional[str] = None
        
        # EV tracking
        self.positive_ev_decisions = 0
        self.negative_ev_decisions = 0
        
        # SPR-based improvement tracking
        self.improvement_by_spr = {
            "low": [],    # SPR < 3
            "medium": [], # 3 <= SPR <= 6
            "high": []    # SPR > 6
        }
    
    def add_decision(self, decision_data: Dict[str, Any]) -> None:
        """
        Add a new decision, managing the history size.
        
        Args:
            decision_data: Dictionary containing decision context and analysis
        """
        self.total_decisions += 1
        
        # Update strategy alignment counter
        matching_strategy = decision_data.get("matching_strategy")
        if matching_strategy in self.decisions_by_strategy:
            self.decisions_by_strategy[matching_strategy] += 1
        
        # Update optimal strategy counter
        optimal_strategy = decision_data.get("optimal_strategy")
        if optimal_strategy in self.optimal_strategies:
            self.optimal_strategies[optimal_strategy] += 1
            
        # Check if decision was optimal
        if decision_data.get("was_optimal", False):
            self.correct_decisions += 1
            
        # Update EV tracking
        if decision_data.get("expected_value", 0) > 0:
            self.positive_ev_decisions += 1
        else:
            self.negative_ev_decisions += 1
            
        # Add to history, maintaining size limit
        self.decision_history.append(decision_data)
        if len(self.decision_history) > self.MAX_DETAILED_DECISIONS:
            self.decision_history.pop(0)  # Remove oldest entry
    
    @property
    def decision_accuracy(self) -> float:
        """Returns the percentage of correct decisions."""
        if self.total_decisions == 0:
            return 0.0
        return (self.correct_decisions / self.total_decisions) * 100
    
    @property
    def dominant_strategy(self) -> str:
        """Returns the strategy that best matches the player's decisions."""
        if not any(self.decisions_by_strategy.values()):
            return "Unknown"
        return max(self.decisions_by_strategy.items(), key=lambda x: x[1])[0]
    
    @property
    def recommended_strategy(self) -> str:
        """
        Returns the strategy that would have been optimal most often,
        indicating what the player should aim for.
        """
        if not any(self.optimal_strategies.values()):
            return "Unknown"
        return max(self.optimal_strategies.items(), key=lambda x: x[1])[0]
    
    def get_recent_decisions(self, num_decisions: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent decisions with full context.
        
        Args:
            num_decisions: Number of recent decisions to return
            
        Returns:
            List of recent decision data dictionaries
        """
        return self.decision_history[-num_decisions:]
    
    def get_strategy_distribution(self) -> Dict[str, float]:
        """
        Calculate the percentage distribution of decisions by strategy.
        
        Returns:
            Dictionary mapping strategy names to percentage of decisions
        """
        if self.total_decisions == 0:
            return {strategy: 0.0 for strategy in self.decisions_by_strategy}
            
        return {
            strategy: (count / self.total_decisions) * 100
            for strategy, count in self.decisions_by_strategy.items()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert object to dictionary for serialization.
        
        Returns:
            Dictionary representation of learning statistics
        """
        return {
            "player_id": self.player_id,
            "total_decisions": self.total_decisions,
            "correct_decisions": self.correct_decisions,
            "decisions_by_strategy": self.decisions_by_strategy,
            "optimal_strategies": self.optimal_strategies,
            "decision_history": self.decision_history,
            "current_session_id": self.current_session_id,
            "positive_ev_decisions": self.positive_ev_decisions,
            "negative_ev_decisions": self.negative_ev_decisions,
            "improvement_by_spr": self.improvement_by_spr
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningStatistics':
        """
        Create a LearningStatistics object from dictionary data.
        
        Args:
            data: Dictionary containing learning statistics data
            
        Returns:
            New LearningStatistics object
        """
        stats = cls(data["player_id"])
        
        stats.total_decisions = data.get("total_decisions", 0)
        stats.correct_decisions = data.get("correct_decisions", 0)
        stats.decisions_by_strategy = data.get("decisions_by_strategy", {})
        stats.optimal_strategies = data.get("optimal_strategies", {})
        stats.decision_history = data.get("decision_history", [])
        stats.current_session_id = data.get("current_session_id")
        stats.positive_ev_decisions = data.get("positive_ev_decisions", 0)
        stats.negative_ev_decisions = data.get("negative_ev_decisions", 0)
        stats.improvement_by_spr = data.get("improvement_by_spr", {})
        
        return stats