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
        # Log total pot for debugging
        logger.info(f"DISTRIBUTE POT: Total pot is {total_pot}")
        
        active_players = [player for player in players if player.is_active or player.all_in]
        winners = {}
        
        # Log player states before distribution for debugging
        for player in players:
            logger.info(f"PLAYER STATE: {player.player_id} - active: {player.is_active}, all-in: {player.all_in}, stack: {player.stack}")
        
        # Early return if only one player is active (everyone else folded)
        if len(active_players) == 1:
            winner = active_players[0]
            old_stack = winner.stack  # Log the old stack for debugging
            winner.stack += total_pot
            winners[winner.player_id] = total_pot
            logger.info(f"STACK UPDATE: Single winner {winner.player_id} stack changed from {old_stack} to {winner.stack} (+{total_pot})")
            
            # Extra verification
            if winner.stack != old_stack + total_pot:
                logger.error(f"STACK ERROR: Winner {winner.player_id} stack ({winner.stack}) does not match expected value ({old_stack + total_pot})")
                # Fix the stack if there's an error
                winner.stack = old_stack + total_pot
                logger.info(f"STACK CORRECTED: Fixed {winner.player_id} stack to {winner.stack}")
            
            return winners
        
        # Calculate main pot and side pots
        pots = PotManager.calculate_pots(players)
        
        # Log calculated pots for debugging
        pot_sum = sum(pot.amount for pot in pots)
        logger.info(f"POT CALCULATION: Found {len(pots)} pots totaling {pot_sum} chips")
        
        # Update the last pot with remaining chips to account for rounding errors
        remaining_chips = total_pot - pot_sum
        if pots and remaining_chips != 0:
            logger.info(f"POT ADJUSTMENT: Adding {remaining_chips} remaining chips to last pot")
            pots[-1].amount += remaining_chips
        
        # Early return if no pots (shouldn't happen but just in case)
        if not pots:
            logger.warning("No pots calculated despite having active players")
            return winners
            
        # Evaluate hands for all active players
        player_hands = self.evaluate_hands(players, community_cards, deck)
        
        # Log evaluated hands for debugging
        for pid, (score, rank, _) in player_hands.items():
            logger.info(f"HAND EVAL: Player {pid} has {rank} (score: {score})")
        
        # Track total chips distributed for verification
        total_distributed = 0
        
        # Distribute each pot to winner(s)
        for i, pot in enumerate(pots):
            logger.info(f"DISTRIBUTING POT {i+1}: Amount {pot.amount}, eligible players: {pot.eligible_players}")
            
            eligible_player_hands = {
                pid: player_hands[pid] for pid in pot.eligible_players 
                if pid in player_hands
            }
            
            if not eligible_player_hands:
                logger.warning(f"No eligible players found for pot {i+1}")
                continue
                
            # Find the best hand score among eligible players
            best_score = min(hand[0] for hand in eligible_player_hands.values())
            
            # Find all players with the best hand (to handle split pots)
            pot_winners = [
                player for pid, (score, _, player) in eligible_player_hands.items()
                if score == best_score
            ]
            
            # Log pot winners for debugging
            logger.info(f"POT {i+1} WINNERS: {[p.player_id for p in pot_winners]}")
            
            # Split the pot among winners
            if pot_winners:
                split_amount = pot.amount // len(pot_winners)
                remainder = pot.amount % len(pot_winners)
                
                logger.info(f"SPLIT AMOUNT: {split_amount} per winner, remainder: {remainder}")
                
                for winner in pot_winners:
                    old_stack = winner.stack  # Log old stack
                    winner.stack += split_amount
                    winners[winner.player_id] = winners.get(winner.player_id, 0) + split_amount
                    total_distributed += split_amount
                    
                    logger.info(f"STACK UPDATE: Winner {winner.player_id} stack changed from {old_stack} to {winner.stack} (+{split_amount})")
                    
                    # Verify stack update
                    if winner.stack != old_stack + split_amount:
                        logger.error(f"STACK ERROR: Winner {winner.player_id} stack ({winner.stack}) does not match expected value ({old_stack + split_amount})")
                        # Fix the stack if there's an error
                        winner.stack = old_stack + split_amount
                        logger.info(f"STACK CORRECTED: Fixed {winner.player_id} stack to {winner.stack}")
                    
                # Distribute remainder (1 chip per player until gone)
                if remainder > 0:
                    logger.info(f"DISTRIBUTING REMAINDER: {remainder} chips")
                    
                for i in range(remainder):
                    winner = pot_winners[i % len(pot_winners)]
                    old_stack = winner.stack  # Log old stack before adding chip
                    winner.stack += 1
                    winners[winner.player_id] = winners.get(winner.player_id, 0) + 1
                    total_distributed += 1
                    logger.info(f"STACK UPDATE: Winner {winner.player_id} gets +1 remainder chip, stack now {winner.stack}")
        
        # Verify total distribution matches total pot
        if total_distributed != total_pot:
            logger.error(f"DISTRIBUTION ERROR: Distributed {total_distributed} chips, but pot was {total_pot}")
            # Find a winner to fix the difference
            if winners:
                difference = total_pot - total_distributed
                first_winner_id = next(iter(winners))
                for player in players:
                    if player.player_id == first_winner_id:
                        old_stack = player.stack
                        player.stack += difference
                        winners[first_winner_id] += difference
                        logger.info(f"DISTRIBUTION CORRECTED: Added {difference} chips to {player.player_id}, stack now {player.stack}")
                        break
        
        # Log final winner distribution
        logger.info(f"FINAL DISTRIBUTION: Winners = {winners}, total distributed = {total_distributed}")
        
        return winners