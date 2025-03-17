from dataclasses import dataclass, field
from typing import Set, List, Dict, Any
import copy

@dataclass
class PotInfo:
    """Represents a pot (main or side) in the poker game."""
    amount: int = 0
    eligible_players: Set[str] = field(default_factory=set)


class PotManager:
    """Manages pot calculations and distribution."""
    
    @staticmethod
    def calculate_pots(players) -> List[PotInfo]:
        """
        Calculates main pot and side pots based on player contributions.
        
        Args:
            players: List of Player objects
            
        Returns:
            List of PotInfo objects representing main pot and side pots
        """
        import logging
        logger = logging.getLogger("pot_manager")
        
        # Get all active or all-in players (players who haven't folded)
        active_players = [p for p in players if p.is_active or p.all_in]
        
        # Log player contributions for debugging
        logger.info(f"Calculating pots with {len(active_players)} active/all-in players")
        for p in active_players:
            logger.info(f"Player {p.player_id}: total_bet={p.total_bet}, is_active={p.is_active}, all_in={p.all_in}")
        
        if not active_players:
            logger.warning("No active players found when calculating pots")
            return []
            
        # Track all player contributions for verification
        total_contributions = sum(p.total_bet for p in active_players)
        logger.info(f"Total player contributions: {total_contributions}")
            
        # Sort players by total contribution to the pot (lowest to highest)
        # Only include players who have actually bet something
        contributing_players = sorted(
            [p for p in active_players if p.total_bet > 0],
            key=lambda p: p.total_bet
        )
        
        if not contributing_players:
            logger.warning("No players have contributed to the pot")
            return []
        
        pots = []
        prev_bet = 0
        eligible_players = set()
        total_pot_amount = 0
        
        # Create pots based on bet differences
        for player in contributing_players:
            if player.total_bet > prev_bet:
                # Create a pot for the difference in bets
                current_pot_size = (player.total_bet - prev_bet) * len(eligible_players)
                
                if current_pot_size > 0:
                    pot = PotInfo(amount=current_pot_size)
                    # All players who contributed at least this much are eligible
                    pot.eligible_players = eligible_players.copy()
                    pots.append(pot)
                    total_pot_amount += current_pot_size
                    logger.info(f"Created pot of {current_pot_size} chips with {len(eligible_players)} eligible players: {eligible_players}")
                
                prev_bet = player.total_bet
            
            # Add current player to eligible players set
            eligible_players.add(player.player_id)
        
        # Final pot (includes all remaining bets from top contributors)
        if eligible_players and prev_bet > 0:
            final_pot_amount = total_contributions - total_pot_amount
            
            if final_pot_amount > 0:
                pot = PotInfo(amount=final_pot_amount)
                pot.eligible_players = eligible_players.copy()
                pots.append(pot)
                logger.info(f"Created final pot of {final_pot_amount} chips with {len(eligible_players)} eligible players: {eligible_players}")
            else:
                logger.info("No chips remaining for final pot")
        
        # Verify the sum of pots equals total contributions
        calculated_total = sum(pot.amount for pot in pots)
        if calculated_total != total_contributions:
            logger.error(f"POT CALCULATION ERROR: Sum of pots ({calculated_total}) doesn't match total contributions ({total_contributions})")
        else:
            logger.info(f"Pot calculation verified: {calculated_total} chips in {len(pots)} pots")
        
        return pots
    
    @staticmethod
    def verify_pots_distribution(players, pots: List[PotInfo], total_pot: int) -> bool:
        """
        Verify that all pots correctly account for the total pot amount.
        
        Args:
            players: List of Player objects
            pots: List of PotInfo objects
            total_pot: Total amount in the pot
            
        Returns:
            bool: True if pots are properly distributed, False otherwise
        """
        pot_sum = sum(pot.amount for pot in pots)
        return pot_sum == total_pot