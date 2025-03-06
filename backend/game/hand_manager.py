from typing import List, Dict, Tuple, Any
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.pot import PotInfo, PotManager
from ai.hand_evaluator import HandEvaluator
from utils.logger import get_logger

logger = get_logger("game.hand_manager")

class HandManager:
    """Manages hand evaluation and distribution of pots."""
    
    def __init__(self):
        """Initialize the hand manager."""
        self.hand_evaluator = HandEvaluator()
    
    def evaluate_hands(self, players, community_cards: List[str], 
                     deck: List[str]) -> Dict[str, Tuple[int, str, Any]]:
        """
        Evaluates all player hands and returns scores.
        
        Args:
            players: List of Player objects
            community_cards: List of community cards
            deck: Current deck state
            
        Returns:
            Dict mapping player_id to (hand_score, hand_rank, player_obj)
        """
        active_players = [player for player in players if player.is_active or player.all_in]
        player_hands = {}
        
        for player in active_players:
            if player.hole_cards:
                hand_score, hand_rank = self.hand_evaluator.evaluate_hand(
                    hole_cards=player.hole_cards,
                    community_cards=community_cards,
                    deck=deck
                )
                player_hands[player.player_id] = (hand_score, hand_rank, player)
                logger.info(f"Player {player.player_id} hand: {', '.join(player.hole_cards)} - {hand_rank} ({hand_score})")
                
        return player_hands
    
    def distribute_pot(self, players, community_cards: List[str], 
                      total_pot: int, deck: List[str]) -> Dict[str, int]:
        """
        Enhanced pot distribution that handles:
        - Split pots (equal hand strength)
        - Side pots (all-in with different stack sizes)
        - Multiple all-in scenarios
        
        Args:
            players: List of Player objects
            community_cards: List of community cards
            total_pot: Total pot amount
            deck: Current deck state
            
        Returns:
            Dictionary mapping player_id to amount won
        """
        active_players = [player for player in players if player.is_active or player.all_in]
        winners = {}
        
        # Early return if only one player is active (everyone else folded)
        if len(active_players) == 1:
            winner = active_players[0]
            winner.stack += total_pot
            winners[winner.player_id] = total_pot
            return winners
        
        # Calculate main pot and side pots
        pots = PotManager.calculate_pots(players)
        
        # Update the last pot with remaining chips (rounding errors, etc.)
        if pots:
            remaining_chips = total_pot - sum(pot.amount for pot in pots)
            pots[-1].amount += remaining_chips
        
        # Early return if no pots (shouldn't happen but just in case)
        if not pots:
            return winners
            
        # Evaluate hands for all active players
        player_hands = self.evaluate_hands(players, community_cards, deck)
        
        # Distribute each pot to winner(s)
        for pot in pots:
            eligible_player_hands = {
                pid: player_hands[pid] for pid in pot.eligible_players 
                if pid in player_hands
            }
            
            if not eligible_player_hands:
                continue
                
            # Find the best hand score among eligible players
            best_score = min(hand[0] for hand in eligible_player_hands.values())
            
            # Find all players with the best hand (to handle split pots)
            pot_winners = [
                player for pid, (score, _, player) in eligible_player_hands.items()
                if score == best_score
            ]
            
            # Split the pot among winners
            if pot_winners:
                split_amount = pot.amount // len(pot_winners)
                remainder = pot.amount % len(pot_winners)
                
                for winner in pot_winners:
                    winner.stack += split_amount
                    winners[winner.player_id] = winners.get(winner.player_id, 0) + split_amount
                    
                # Distribute remainder (1 chip per player until gone)
                for i in range(remainder):
                    pot_winners[i % len(pot_winners)].stack += 1
                    winners[pot_winners[i % len(pot_winners)].player_id] = winners.get(
                        pot_winners[i % len(pot_winners)].player_id, 0) + 1
        
        return winners