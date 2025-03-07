# backend/services/learning_service.py
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime, timedelta
import json

# Import error classes
from utils.errors import (
    PlayerNotFoundError
)

# Import learning tracker (similar to how game_service uses poker_game)
from game.learning_tracker import LearningTracker
from utils.logger import get_logger
from services.player_service import PlayerService

class LearningService:
    def __init__(self):
        self.learning_tracker = LearningTracker()
        self.player_service = PlayerService()
        self.logger = get_logger("learning_service")
    
    def get_learning_feedback(self, player_id: str, num_decisions: int = 1) -> Dict[str, Any]:
        """Get learning feedback for a player using the LearningTracker"""
        # Verify player exists
        try:
            self.player_service.get_player(player_id)
        except Exception as e:
            self.logger.warning(f"Player {player_id} not found")
            raise PlayerNotFoundError(player_id)
        
        try:
            # Get feedback from the learning tracker
            feedback_data = self.learning_tracker.get_learning_feedback(player_id, num_decisions)
            
            # Convert to API format
            feedback_items = []
            for item in feedback_data:
                # If we received a string, convert to dict (compatibility with different formats)
                if isinstance(item, str):
                    try:
                        item = json.loads(item)
                    except:
                        # If it's just a string message, wrap it in a simple structure
                        item = {
                            "decision_id": str(uuid.uuid4()),
                            "game_context": {},
                            "decision": "unknown",
                            "feedback_text": item,
                            "optimal_decision": "unknown",
                            "improvement_areas": [],
                            "timestamp": datetime.now()
                        }
                
                # Ensure all required fields are present
                if isinstance(item, dict):
                    if "decision_id" not in item:
                        item["decision_id"] = str(uuid.uuid4())
                    if "timestamp" not in item:
                        item["timestamp"] = datetime.now()
                    
                    feedback_items.append(item)
            
            return {
                "feedback": feedback_items
            }
        except Exception as e:
            self.logger.error(f"Error getting learning feedback: {e}")
            # Fallback to mock data if there's an error
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
                    "feedback_text": f"Learning system error: {str(e)}. Showing mock data.",
                    "optimal_decision": "raise",
                    "improvement_areas": ["system error"],
                    "timestamp": datetime.now() - timedelta(minutes=i*5)
                })
            
            return {
                "feedback": feedback_items
            }
    
    def get_strategy_profile(self, player_id: str) -> Dict[str, Any]:
        """Get player's strategic profile using the LearningTracker"""
        # Verify player exists
        try:
            self.player_service.get_player(player_id)
        except Exception as e:
            self.logger.warning(f"Player {player_id} not found")
            raise PlayerNotFoundError(player_id)
        
        try:
            # Get strategy profile from the learning tracker
            profile = self.learning_tracker.get_strategy_profile(player_id)
            
            # Ensure the profile has all required fields for the API
            required_fields = {
                "dominant_strategy": "Unknown",
                "strategy_distribution": {},
                "recommended_strategy": "Unknown",
                "decision_accuracy": 0.0,
                "total_decisions": 0,
                "improvement_areas": [],
                "learning_recommendations": [],
                "decision_trend": {"trend": "stable", "description": "No trend data available"}
            }
            
            # Fill in any missing fields with defaults
            for field, default in required_fields.items():
                if field not in profile:
                    profile[field] = default
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error getting strategy profile: {e}")
            # Return fallback mock data with error indication
            return {
                "dominant_strategy": "Unknown",
                "strategy_distribution": {
                    "Conservative": 25.0,
                    "Risk Taker": 25.0,
                    "Probability-Based": 25.0,
                    "Bluffer": 25.0
                },
                "recommended_strategy": "Unknown",
                "decision_accuracy": 0.0,
                "total_decisions": 0,
                "improvement_areas": [
                    {
                        "area": "system_error",
                        "description": f"Error retrieving profile: {str(e)}"
                    }
                ],
                "learning_recommendations": [
                    {
                        "focus": "System Error",
                        "title": "Learning System Error",
                        "description": "The learning system encountered an error. Please try again later."
                    }
                ],
                "decision_trend": {
                    "trend": "unknown",
                    "description": "Unable to determine trend due to system error"
                }
            }
    
    def get_decision_details(self, player_id: str, decision_id: str) -> Dict[str, Any]:
        """Get detailed analysis of a specific decision"""
        # Verify player exists
        try:
            self.player_service.get_player(player_id)
        except Exception as e:
            self.logger.warning(f"Player {player_id} not found")
            raise PlayerNotFoundError(player_id)
        
        try:
            # In a full implementation, we would call a method like:
            # self.learning_tracker.get_decision_details(player_id, decision_id)
            # But since that method doesn't exist in the current LearningTracker,
            # we'll use mock data for now
            
            # This would be replaced with actual data retrieval
            # For now we're returning mock data
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
            
        except Exception as e:
            self.logger.error(f"Error getting decision details: {e}")
            # Return fallback mock data with error indication
            return {
                "decision_id": decision_id,
                "timestamp": datetime.now(),
                "game_context": {},
                "player_decision": "unknown",
                "matching_strategy": "unknown",
                "optimal_strategy": "unknown",
                "was_optimal": False,
                "strategy_decisions": {},
                "expected_value": 0.0,
                "detailed_analysis": f"Error retrieving decision details: {str(e)}"
            }