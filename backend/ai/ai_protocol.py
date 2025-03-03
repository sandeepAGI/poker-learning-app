from typing import Protocol, List, Dict, Tuple, Any, Union


class AIStrategyProtocol(Protocol):
    """
    Protocol defining the interface that all AI poker strategies must implement.
    This ensures consistent behavior across different strategy implementations.
    """
    
    def evaluate_hand(self, hole_cards: List[str], community_cards: List[str], 
                     deck: List[str]) -> Tuple[float, str]:
        """
        Evaluates the strength of a poker hand.
        
        Args:
            hole_cards: Player's private cards
            community_cards: Shared community cards
            deck: Current deck state
            
        Returns:
            Tuple containing:
            - hand_score: Numerical score of the hand (lower is better)
            - hand_rank_str: String representation of the hand rank
        """
        ...
    
    def make_decision(self, hole_cards: List[str], game_state: Dict[str, Any], 
                     deck: List[str], pot_size: int, spr: float) -> str:
        """
        Determines the AI's poker action based on game state.
        
        Args:
            hole_cards: Player's private cards
            game_state: Current state of the game including community cards
            deck: Current deck state
            pot_size: Current size of the pot
            spr: Stack-to-pot ratio
            
        Returns:
            Decision string: "fold", "call", or "raise"
        """
        ...