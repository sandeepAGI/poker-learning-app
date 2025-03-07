# backend/services/learning_service.py
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime, timedelta

# Import error classes
from utils.errors import (
    PlayerNotFoundError
)

class LearningService:
    # Mock player storage for validation
    _players = {}  # In a real implementation, this would use PlayerService
    
    def get_learning_feedback(self, player_id: str, num_decisions: int = 1) -> Dict[str, Any]:
        """Get learning feedback for a player"""
        # In a real implementation, this would check if player exists
        # For now, we'll just generate mock feedback
        
        # Generate mock feedback items
        feedback_items = []
        for i in range(num_decisions):
            feedback_items.append({
                "decision_id": str(uuid.uuid4()),
                "game_context": {
                    "game_state": "pre_flop",
                    "hole_cards": ["Ah", "Kd"],
                    "community_cards": [],
                    "pot_size": 15,
                    "spr": 66.7
                },
                "decision": "raise",
                "feedback_text": "Your raise with premium holdings was optimal. Consider a larger sizing to extract more value.",
                "optimal_decision": "raise",
                "improvement_areas": ["bet sizing"],
                "timestamp": datetime.now() - timedelta(minutes=i*5)
            })
        
        return {
            "feedback": feedback_items
        }
    
    def get_strategy_profile(self, player_id: str) -> Dict[str, Any]:
        """Get player's strategic profile"""
        # In a real implementation, this would check if player exists
        # For now, we'll just return mock profile data
        
        return {
            "dominant_strategy": "Probability-Based",
            "strategy_distribution": {
                "Conservative": 15.5,
                "Risk Taker": 28.2,
                "Probability-Based": 46.3,
                "Bluffer": 10.0
            },
            "recommended_strategy": "Risk Taker",
            "decision_accuracy": 72.5,
            "total_decisions": 120,
            "improvement_areas": [
                {
                    "area": "pre_flop",
                    "description": "Tendency to play too many hands from early position"
                },
                {
                    "area": "aggression",
                    "description": "More aggression needed when drawing to strong hands"
                }
            ],
            "learning_recommendations": [
                {
                    "focus": "Position Play",
                    "title": "Playing from Early Position",
                    "description": "Tighten your opening range from early position to premium holdings"
                },
                {
                    "focus": "Bet Sizing",
                    "title": "Value Betting",
                    "description": "Increase bet sizing with strong hands to extract maximum value"
                }
            ],
            "decision_trend": {
                "trend": "improving",
                "description": "Your decision quality has improved 12% over the last 50 hands"
            }
        }
    
    def get_decision_details(self, player_id: str, decision_id: str) -> Dict[str, Any]:
        """Get detailed analysis of a specific decision"""
        # In a real implementation, this would check if player and decision exist
        # For now, we'll just return mock decision details
        
        return {
            "decision_id": decision_id,
            "timestamp": datetime.now() - timedelta(hours=1),
            "game_context": {
                "game_state": "flop",
                "hole_cards": ["Ah", "Kd"],
                "community_cards": ["Qh", "Jh", "7s"],
                "pot_size": 45,
                "current_bet": 15,
                "spr": 20.0
            },
            "player_decision": "call",
            "matching_strategy": "Conservative",
            "optimal_strategy": "Risk Taker",
            "was_optimal": False,
            "strategy_decisions": {
                "Conservative": "call",
                "Risk Taker": "raise",
                "Probability-Based": "raise",
                "Bluffer": "raise"
            },
            "expected_value": -2.5,
            "detailed_analysis": "With a strong draw to the nuts (royal flush), a raise would put maximum pressure on opponents and give you multiple ways to win. Calling gives your opponents a cheap opportunity to outdraw you or bluff you on later streets."
        }