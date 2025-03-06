"""
Module for analyzing trends in poker decision quality over time.
"""
from typing import List, Dict, Any, Optional

class TrendAnalyzer:
    """
    Analyzes trends in poker decision quality over time.
    """
    
    @staticmethod
    def analyze_decision_quality_trend(recent_decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes the trend in decision quality over time.
        
        Args:
            recent_decisions: List of recent decision data, ordered from oldest to newest
            
        Returns:
            Dictionary with trend analysis
        """
        if len(recent_decisions) < 5:
            return {
                "trend": "not_enough_data",
                "description": "Need more decisions to analyze trends",
                "improvement_rate": 0
            }
        
        # Divide decisions into first half and second half
        midpoint = len(recent_decisions) // 2
        first_half = recent_decisions[:midpoint]
        second_half = recent_decisions[midpoint:]
        
        # Calculate accuracy for each half
        first_half_optimal = sum(1 for d in first_half if d.get("was_optimal", False))
        second_half_optimal = sum(1 for d in second_half if d.get("was_optimal", False))
        
        first_half_accuracy = (first_half_optimal / len(first_half)) * 100 if first_half else 0
        second_half_accuracy = (second_half_optimal / len(second_half)) * 100 if second_half else 0
        
        # Calculate improvement rate
        improvement_rate = second_half_accuracy - first_half_accuracy
        
        # Determine trend
        if improvement_rate > 5:
            trend = "improving"
            description = "Your decision making is showing clear improvement!"
        elif improvement_rate > 0:
            trend = "slightly_improving"
            description = "Your decision making is showing slight improvement."
        elif improvement_rate > -5:
            trend = "stable"
            description = "Your decision making has been consistent."
        else:
            trend = "declining"
            description = "Your recent decisions have been less optimal than before."
        
        # Look at the most recent decisions (last 5)
        very_recent = recent_decisions[-5:]
        very_recent_optimal = sum(1 for d in very_recent if d.get("was_optimal", False))
        very_recent_accuracy = (very_recent_optimal / len(very_recent)) * 100 if very_recent else 0
        
        # Check for recent improvement
        recent_trend = None
        if very_recent_accuracy > second_half_accuracy + 10:
            recent_trend = "recent_improvement"
            recent_description = "Your most recent decisions show significant improvement!"
        elif very_recent_accuracy < second_half_accuracy - 10:
            recent_trend = "recent_decline"
            recent_description = "Your most recent decisions have been less optimal."
        
        result = {
            "trend": trend,
            "description": description,
            "improvement_rate": round(improvement_rate, 1),
            "first_half_accuracy": round(first_half_accuracy, 1),
            "second_half_accuracy": round(second_half_accuracy, 1)
        }
        
        if recent_trend:
            result["recent_trend"] = recent_trend
            result["recent_description"] = recent_description
        
        return result