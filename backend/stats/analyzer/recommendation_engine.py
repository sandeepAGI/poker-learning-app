"""
Module for generating learning recommendations based on poker decision analysis.
"""
from typing import List, Dict, Any, Optional

class RecommendationEngine:
    """
    Generates personalized learning recommendations for improving poker play.
    """
    
    @staticmethod
    def generate_learning_recommendations(dominant_strategy: str, 
                                        recommended_strategy: str,
                                        improvement_areas: List[Dict[str, Any]],
                                        total_decisions: int) -> List[Dict[str, Any]]:
        """
        Generates personalized learning recommendations based on identified improvement areas.
        
        Args:
            dominant_strategy: Player's most frequently matched strategy
            recommended_strategy: Strategy that would improve their play
            improvement_areas: List of identified improvement areas
            total_decisions: Total number of decisions analyzed
            
        Returns:
            List of learning recommendations with titles and descriptions
        """
        recommendations = []
        
        # Strategy alignment recommendation
        if dominant_strategy != recommended_strategy and dominant_strategy and recommended_strategy:
            strategy_tips = {
                "Conservative": "Be more selective with your calls and more aggressive with your value hands",
                "Risk Taker": "Be more selective with your aggression - not every hand warrants a raise",
                "Probability-Based": "Calculate pot odds and expected value for more mathematical play",
                "Bluffer": "Mix in more straightforward play to balance your bluffs"
            }
            
            recommendation = {
                "focus": "strategy_alignment",
                "title": "Adapt Your Strategy Style",
                "description": f"Try {strategy_tips.get(recommended_strategy, 'adapting your play')} to align with a {recommended_strategy} style."
            }
            recommendations.append(recommendation)
        
        # Game state specific recommendations
        game_state_areas = [area for area in improvement_areas if area["type"] == "game_state"]
        for area in game_state_areas:
            game_state = area["area"]
            
            if game_state == "pre_flop":
                recommendations.append({
                    "focus": "pre_flop_play",
                    "title": "Improve Pre Flop Play",
                    "description": "Study starting hand selection charts and position-based play"
                })
            
            elif game_state == "flop":
                recommendations.append({
                    "focus": "flop_play",
                    "title": "Improve Flop Decision Making",
                    "description": "Practice evaluating hand strength on the flop and calculating pot odds for draws"
                })
            
            elif game_state == "turn":
                recommendations.append({
                    "focus": "turn_play",
                    "title": "Improve Turn Decision Making",
                    "description": "Focus on re-evaluating hand strength and pot odds with one more card revealed"
                })
            
            elif game_state == "river":
                recommendations.append({
                    "focus": "river_play",
                    "title": "Improve River Decision Making",
                    "description": "Work on value betting and identifying good bluffing opportunities"
                })
        
        # SPR specific recommendations
        spr_areas = [area for area in improvement_areas if area["type"] == "spr_range"]
        for area in spr_areas:
            spr_range = area["area"]
            
            if spr_range == "very_low" or spr_range == "low":
                recommendations.append({
                    "focus": "low_spr_play",
                    "title": "Improve Play with Low SPR",
                    "description": "With low SPR, focus on commitment decisions - are you willing to get all your chips in?"
                })
            
            elif spr_range == "medium":
                recommendations.append({
                    "focus": "medium_spr_play",
                    "title": "Improve Play with Medium SPR",
                    "description": "With medium SPR, practice balancing value bets and draws based on pot odds"
                })
            
            elif spr_range == "high":
                recommendations.append({
                    "focus": "high_spr_play",
                    "title": "Improve Play with High SPR",
                    "description": "With high SPR, work on playing more speculative hands for implied odds"
                })
        
        # Add beginner recommendation if player is new
        if total_decisions < 20:
            recommendations.append({
                "focus": "fundamentals",
                "title": "Master the Basics",
                "description": "Focus on understanding position, pot odds, and hand rankings"
            })
        
        # Limit to at most 3 recommendations to avoid overwhelming the player
        return recommendations[:3]