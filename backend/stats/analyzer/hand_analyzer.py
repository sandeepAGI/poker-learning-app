"""
Module for analyzing poker hand strength and related metrics.
"""
from typing import List, Dict, Any, Optional

class HandAnalyzer:
    """
    Analyzes poker hand strength and provides related feedback.
    """
    
    @staticmethod
    def analyze_hand_strength(hole_cards: List[str], community_cards: List[str], game_state: str) -> str:
        """
        Analyzes the strength of the player's hand and provides feedback.
        
        Args:
            hole_cards: Player's hole cards
            community_cards: Community cards
            game_state: Current game state (pre_flop, flop, turn, river)
            
        Returns:
            String with hand strength analysis
        """
        if not hole_cards:
            return ""
        
        # Detect premium starting hands
        premium_hands = [
            ["A", "A"], ["K", "K"], ["Q", "Q"], ["J", "J"], ["10", "10"],
            ["A", "K"], ["A", "Q"], ["A", "J"], ["K", "Q"]
        ]
        
        # Extract ranks from hole cards
        ranks = [card[0] if card[0] != "1" else "10" for card in hole_cards]
        suits = [card[-1] for card in hole_cards]
        suited = suits[0] == suits[1] if len(suits) == 2 else False
        
        # Pre-flop analysis
        if game_state == "pre_flop":
            # Check for premium hands
            for hand in premium_hands:
                if sorted(ranks) == sorted(hand):
                    return f"Your starting hand ({', '.join(hole_cards)}) is considered premium - strong enough to play from any position."
            
            # Check for suited cards
            if suited:
                return f"Your starting hand ({', '.join(hole_cards)}) is suited, giving you flush potential."
            
            # Check for connected cards (straight potential)
            rank_values = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, 
                          "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
            if len(ranks) == 2 and abs(rank_values.get(ranks[0], 0) - rank_values.get(ranks[1], 0)) <= 3:
                return f"Your starting hand ({', '.join(hole_cards)}) has straight potential with connected cards."
                
            return f"Your starting hand ({', '.join(hole_cards)}) is relatively weak. Position and opponent tendencies become more important."
        
        # Post-flop analysis would require more complex evaluation with community cards
        # This is simplified for the example
        if community_cards:
            return f"With {', '.join(hole_cards)} and {', '.join(community_cards)} on the board, consider how your hand ranks against likely opponent holdings."
            
        return ""
    
    @staticmethod
    def get_strategy_reasoning(strategy: str, decision: str, game_state: str, 
                             spr: float, hole_cards: List[str], community_cards: List[str]) -> str:
        """
        Provides reasoning for why a particular strategy would make a specific decision.
        
        Args:
            strategy: Strategy name
            decision: The decision made by the strategy
            game_state: Current game state
            spr: Stack-to-pot ratio
            hole_cards: Player's hole cards
            community_cards: Community cards
            
        Returns:
            String with reasoning
        """
        if strategy == "Conservative":
            if decision == "fold":
                return "Conservative players prefer to fold marginal hands and only continue with strong holdings, especially when facing aggression."
            elif decision == "call":
                return "Conservative players call when they have a solid hand but not strong enough to raise, minimizing risk while staying in the hand."
            else:  # raise
                return "Conservative players raise with strong hands to protect their equity and build the pot when they're likely ahead."
                
        elif strategy == "Risk Taker":
            if decision == "raise":
                return "Risk Takers use aggression to put pressure on opponents and take control of the hand, often raising to force opponents to make difficult decisions."
            else:
                return "Risk Takers will occasionally slow down with very strong hands (trapping) or when aggression isn't advantageous."
                
        elif strategy == "Probability-Based":
            if decision == "fold":
                return "Probability-Based players calculate that the expected value of continuing is negative, so folding is mathematically correct."
            elif decision == "call":
                return "Probability-Based players call when the pot odds justify continuing but don't warrant a raise."
            else:  # raise
                return "Probability-Based players raise when they have positive expected value from building the pot, considering their equity and fold equity."
                
        elif strategy == "Bluffer":
            if decision == "raise":
                return "Bluffers raise to represent strength regardless of their actual hand, making it difficult for opponents to put them on a range."
            else:
                return "Bluffers mix their play to remain unpredictable, sometimes playing straightforwardly to set up future bluffs."
                
        return f"The {strategy} strategy bases decisions on a balanced approach considering hand strength, position, and opponent tendencies."
    
    @staticmethod
    def get_spr_based_tip(spr: float, game_state: str) -> str:
        """
        Provides educational tips based on stack-to-pot ratio.
        
        Args:
            spr: Stack-to-pot ratio
            game_state: Current game state
            
        Returns:
            String with SPR-based tip
        """
        if spr < 1:
            return "With very low SPR (<1), you're essentially committed to the pot. This is often an all-in situation where folding sacrifices too much equity."
        
        elif spr < 3:
            if game_state == "pre_flop":
                return "With low SPR (<3), you should play a 'push or fold' strategy - either commit with strong hands or fold marginal ones."
            else:
                return "With low SPR (<3), top pair or better is often worth committing to, but drawing hands lose value without proper pot odds."
        
        elif spr <= 6:
            return "With medium SPR (3-6), you have flexibility to play more hand types. Strong draws and pairs gain value, and set mining becomes viable."
        
        else:  # spr > 6
            if game_state == "pre_flop":
                return "With high SPR (>6), premium pairs and high-card hands gain value. You can play more speculative hands like suited connectors looking for big payoffs."
            else:
                return "With high SPR (>6), be cautious with one pair hands. Strong draws and sets/two pairs+ gain significant value for implied odds."