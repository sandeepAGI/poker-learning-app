"""
Module for analyzing patterns in poker decisions.
"""
from typing import List, Dict, Any, Optional

class PatternAnalyzer:
    """
    Analyzes patterns in poker decisions to identify strengths and weaknesses.
    """
    
    @staticmethod
    def analyze_game_state_patterns(decisions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Analyzes player decisions across different game states.
        
        Args:
            decisions: List of decision data dictionaries
            
        Returns:
            Dictionary with analysis by game state
        """
        game_states = ["pre_flop", "flop", "turn", "river"]
        patterns = {state: {"count": 0, "optimal": 0, "actions": {"fold": 0, "call": 0, "raise": 0}} 
                  for state in game_states}
        
        for decision in decisions:
            state = decision.get("game_state", "unknown")
            if state in patterns:
                patterns[state]["count"] += 1
                if decision.get("was_optimal", False):
                    patterns[state]["optimal"] += 1
                
                action = decision.get("decision")
                if action in patterns[state]["actions"]:
                    patterns[state]["actions"][action] += 1
        
        # Calculate accuracy percentages
        for state, data in patterns.items():
            if data["count"] > 0:
                data["accuracy"] = (data["optimal"] / data["count"]) * 100
                # Convert action counts to percentages
                for action in data["actions"]:
                    if data["count"] > 0:
                        data["actions"][action] = (data["actions"][action] / data["count"]) * 100
            else:
                data["accuracy"] = 0
        
        return patterns
    
    @staticmethod
    def analyze_spr_patterns(decisions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Analyzes player decisions across different SPR ranges.
        
        Args:
            decisions: List of decision data dictionaries
            
        Returns:
            Dictionary with analysis by SPR range
        """
        # Define SPR ranges
        spr_ranges = {
            "very_low": {"range": (0, 1), "count": 0, "optimal": 0, "actions": {"fold": 0, "call": 0, "raise": 0}},
            "low": {"range": (1, 3), "count": 0, "optimal": 0, "actions": {"fold": 0, "call": 0, "raise": 0}},
            "medium": {"range": (3, 6), "count": 0, "optimal": 0, "actions": {"fold": 0, "call": 0, "raise": 0}},
            "high": {"range": (6, float('inf')), "count": 0, "optimal": 0, "actions": {"fold": 0, "call": 0, "raise": 0}}
        }
        
        for decision in decisions:
            spr = decision.get("spr", 0)
            action = decision.get("decision")
            was_optimal = decision.get("was_optimal", False)
            
            for range_name, range_data in spr_ranges.items():
                min_spr, max_spr = range_data["range"]
                if min_spr <= spr < max_spr:
                    range_data["count"] += 1
                    if was_optimal:
                        range_data["optimal"] += 1
                    if action in range_data["actions"]:
                        range_data["actions"][action] += 1
                    break
        
        # Calculate accuracy percentages
        for range_name, range_data in spr_ranges.items():
            if range_data["count"] > 0:
                range_data["accuracy"] = (range_data["optimal"] / range_data["count"]) * 100
                # Convert action counts to percentages
                for action in range_data["actions"]:
                    if range_data["count"] > 0:
                        range_data["actions"][action] = (range_data["actions"][action] / range_data["count"]) * 100
            else:
                range_data["accuracy"] = 0
        
        return spr_ranges
        
    @staticmethod
    def identify_improvement_areas(recent_decisions: List[Dict[str, Any]], 
                                 dominant_strategy: str, recommended_strategy: str,
                                 accuracy: float, spr_patterns: Dict[str, Dict[str, Any]],
                                 game_state_patterns: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identifies specific areas where the player can improve based on their decision patterns.
        
        Args:
            recent_decisions: List of recent decision data
            dominant_strategy: Player's most frequently matched strategy
            recommended_strategy: Strategy that would improve their play
            accuracy: Overall decision accuracy
            spr_patterns: Analysis of decisions by SPR range
            game_state_patterns: Analysis of decisions by game state
            
        Returns:
            List of improvement areas with descriptions
        """
        improvement_areas = []
        
        # Check game state performance
        for state, data in game_state_patterns.items():
            # Only consider states with enough data
            if data["count"] >= 3:
                # If accuracy in this state is significantly below overall accuracy
                if data.get("accuracy", 0) < accuracy - 10:
                    improvement_areas.append({
                        "type": "game_state",
                        "area": state,
                        "description": f"Your decisions in the {state.replace('_', ' ')} are less optimal than your overall average."
                    })
        
        # Check SPR performance
        for spr_range, data in spr_patterns.items():
            # Only consider ranges with enough data
            if data["count"] >= 3:
                # If accuracy in this SPR range is significantly below overall accuracy
                if data.get("accuracy", 0) < accuracy - 10:
                    readable_range = spr_range.replace("_", " ")
                    improvement_areas.append({
                        "type": "spr_range",
                        "area": spr_range,
                        "description": f"Your decisions with {readable_range} SPR could be improved."
                    })
        
        # Check strategy alignment
        if dominant_strategy != recommended_strategy and dominant_strategy and recommended_strategy:
            improvement_areas.append({
                "type": "strategy_alignment",
                "area": "strategy_shift",
                "description": f"Your play currently aligns with a {dominant_strategy} style, but a {recommended_strategy} approach might be more effective."
            })
        
        # If no specific areas found but accuracy is below 70%, suggest general improvement
        if not improvement_areas and accuracy < 70:
            improvement_areas.append({
                "type": "general",
                "area": "overall_play",
                "description": "Your overall decision-making could benefit from more consistent application of basic poker strategy concepts."
            })
        
        return improvement_areas