from typing import Dict, List, Any, Type
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logger import get_logger
from ai.ai_protocol import AIStrategyProtocol
from ai.strategies.conservative import ConservativeStrategy
from ai.strategies.risk_taker import RiskTakerStrategy
from ai.strategies.probability_based import ProbabilityBasedStrategy
from ai.strategies.bluffer import BlufferStrategy

# Create a logger for AI decisions
logger = get_logger("ai.manager")

class AIDecisionMaker:
    """Manages AI decision-making based on assigned personality."""

    # Map personality types to strategy implementations
    STRATEGY_MAP: Dict[str, Type[AIStrategyProtocol]] = {
        "Conservative": ConservativeStrategy,
        "Risk Taker": RiskTakerStrategy,
        "Probability-Based": ProbabilityBasedStrategy,
        "Bluffer": BlufferStrategy,
    }

    @staticmethod
    def make_decision(personality: str, hole_cards: List[str], 
                     game_state: Dict[str, Any], deck: List[str], 
                     pot_size: int, spr: float) -> str:
        """
        Determines the AI's poker action based on personality and game state.
        
        Args:
            personality: The AI personality type
            hole_cards: Player's private cards
            game_state: Current state of the game including community cards
            deck: Current deck state
            pot_size: Current size of the pot
            spr: Stack-to-pot ratio
            
        Returns:
            Decision string: "fold", "call", or "raise"
            
        Raises:
            ValueError: If the personality type is not recognized
        """
        logger.debug(f"Making decision for {personality} AI with SPR {spr}")
        
        if personality not in AIDecisionMaker.STRATEGY_MAP:
            logger.error(f"Unknown personality type: {personality}")
            raise ValueError(f"Unknown personality type: {personality}")

        strategy_class = AIDecisionMaker.STRATEGY_MAP[personality]()
        
        # Evaluate hand and get decision
        hand_score, hand_rank = strategy_class.evaluate_hand(
            hole_cards, 
            game_state["community_cards"], 
            deck
        )
        
        decision = strategy_class.make_decision(
            hole_cards,
            game_state,
            deck,
            pot_size,
            spr
        )
        
        # Log the decision and relevant context
        logger.debug(
            f"AI {personality} Decision: {decision} | "
            f"Hand: {', '.join(hole_cards)} | "
            f"Community: {', '.join(game_state['community_cards'])} | "
            f"Hand Score: {hand_score} ({hand_rank}) | "
            f"Pot: {pot_size} | SPR: {spr}"
        )
        
        return decision
