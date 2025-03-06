"""
Module for generating educational feedback for poker decisions.
"""
from typing import List, Dict, Any, Optional
from .hand_analyzer import HandAnalyzer

class FeedbackGenerator:
    """
    Generates detailed, educational feedback for poker decisions.
    """
    
    @staticmethod
    def generate_feedback(decision_data: Dict[str, Any]) -> str:
        """
        Generates detailed, educational feedback for a player based on their decision.
        Tailored for novice players to understand poker concepts and improve decision-making.
        
        Args:
            decision_data: Dictionary containing decision analysis including hand context,
                         player's decision, matched strategy, and optimal strategy
            
        Returns:
            String containing feedback message with actionable advice
        """
        # Extract key information
        player_decision = decision_data["decision"]
        matching_strategy = decision_data["matching_strategy"]
        optimal_strategy = decision_data["optimal_strategy"]
        was_optimal = decision_data["was_optimal"]
        spr = decision_data["spr"]
        game_state = decision_data.get("game_state", "unknown")
        hole_cards = decision_data.get("hole_cards", [])
        community_cards = decision_data.get("community_cards", [])
        pot_size = decision_data.get("pot_size", 0)
        current_bet = decision_data.get("current_bet", 0)
        strategy_decisions = decision_data.get("strategy_decisions", {})
        expected_value = decision_data.get("expected_value", 0)
        
        feedback = []
        
        # 1. Acknowledge the player's decision with style explanation
        strategy_descriptions = {
            "Conservative": "cautious and selective with strong hands",
            "Risk Taker": "aggressive and willing to put pressure on opponents",
            "Probability-Based": "mathematical and focused on expected value",
            "Bluffer": "deceptive and unpredictable"
        }
        
        style_desc = strategy_descriptions.get(matching_strategy, "balanced")
        feedback.append(f"Your decision to {player_decision} matches a {matching_strategy} playing style ({style_desc}).")
        
        # 2. Give positive reinforcement if optimal
        if was_optimal:
            feedback.append(f"👍 Great job! This was the optimal decision for this situation.")
            if expected_value > 1.0:
                feedback.append(f"This decision has high expected value, meaning it should be profitable in the long run.")
        
        # 3. Hand strength and position analysis
        hand_feedback = HandAnalyzer.analyze_hand_strength(hole_cards, community_cards, game_state)
        if hand_feedback:
            feedback.append(hand_feedback)
        
        # 4. Offer alternative perspective if not optimal
        if not was_optimal and optimal_strategy in strategy_decisions:
            optimal_decision = strategy_decisions[optimal_strategy]
            feedback.append(f"A {optimal_strategy} player would have decided to {optimal_decision} here. Here's why:")
            
            # Add reasoning based on strategy
            reason = HandAnalyzer.get_strategy_reasoning(
                optimal_strategy, 
                optimal_decision, 
                game_state, 
                spr, 
                hole_cards, 
                community_cards
            )
            feedback.append(reason)
        
        # 5. Educational tip based on SPR
        spr_tip = HandAnalyzer.get_spr_based_tip(spr, game_state)
        if spr_tip:
            feedback.append(f"SPR Tip: {spr_tip}")
        
        # 6. Game state specific advice
        stage_tip = FeedbackGenerator.get_game_stage_tip(game_state, player_decision, was_optimal)
        if stage_tip:
            feedback.append(stage_tip)
        
        # 7. Forward-looking advice
        improvement_tip = FeedbackGenerator.get_improvement_tip(
            matching_strategy, 
            optimal_strategy, 
            was_optimal,
            player_decision
        )
        if improvement_tip:
            feedback.append(f"For improvement: {improvement_tip}")
        
        return "\n".join(feedback)
    
    @staticmethod
    def get_game_stage_tip(game_state: str, decision: str, was_optimal: bool) -> str:
        """
        Provides stage-specific poker tips.
        
        Args:
            game_state: Current game state
            decision: Player's decision
            was_optimal: Whether the decision was optimal
            
        Returns:
            String with game stage tip
        """
        if game_state == "pre_flop":
            if not was_optimal and decision == "call":
                return "Pre-flop tip: Consider being more selective with calling. Many beginners call too often - raising or folding is often better."
            elif not was_optimal and decision == "fold":
                return "Pre-flop tip: Position is crucial - you can play more hands in late position than early position."
            return "Pre-flop tip: Starting hand selection is fundamental to poker success. Focus on playing strong hands and gradually expand your range."
            
        elif game_state == "flop":
            return "Flop tip: The flop is where your hand makes a significant improvement or misses. With a strong hand, consider how to extract value. With a draw, calculate pot odds."
            
        elif game_state == "turn":
            return "Turn tip: The turn is often a decision point for draws. If you're on a draw, make sure you're getting the right pot odds to continue."
            
        elif game_state == "river":
            return "River tip: On the river, you're either value betting or bluffing. Ask yourself: 'What hands can my opponent call with that I beat?'"
            
        return ""
    
    @staticmethod
    def get_improvement_tip(matching_strategy: str, optimal_strategy: str, 
                          was_optimal: bool, decision: str) -> str:
        """
        Provides forward-looking advice for player improvement.
        
        Args:
            matching_strategy: Strategy that matches player's decision
            optimal_strategy: Optimal strategy for the situation
            was_optimal: Whether the decision was optimal
            decision: Player's decision
            
        Returns:
            String with improvement tip
        """
        if was_optimal:
            return "Continue to focus on making decisions that align with the current game context - you did well here!"
        
        if matching_strategy == "Conservative" and optimal_strategy in ["Risk Taker", "Bluffer"]:
            return "Try to incorporate more aggression in your game, especially when the conditions favor putting pressure on opponents."
            
        elif matching_strategy == "Risk Taker" and optimal_strategy in ["Conservative", "Probability-Based"]:
            return "Consider being more selective with your aggression. Calculate pot odds and hand equity to inform your decisions."
            
        elif matching_strategy == "Bluffer" and optimal_strategy in ["Conservative", "Probability-Based"]:
            return "While mixing in bluffs is important, make sure they're strategically timed. Bluff when the board and betting pattern make your story credible."
            
        elif matching_strategy == "Probability-Based" and optimal_strategy in ["Risk Taker", "Bluffer"]:
            return "Sometimes the mathematically 'correct' play can be exploited. Consider mixing in more aggressive or deceptive plays to be less predictable."
            
        return "Focus on understanding why the optimal strategy was different in this scenario - this awareness will improve your decision-making."