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
        # Get all active or all-in players (players who haven't folded)
        active_players = [p for p in players if p.is_active or p.all_in]
        
        if not active_players:
            return []
            
        # Sort players by total contribution to the pot (lowest to highest)
        contributing_players = sorted(
            active_players, 
            key=lambda p: p.total_bet
        )
        
        pots = []
        prev_bet = 0
        eligible_players = set()
        
        # Create pots based on bet differences
        for player in contributing_players:
            if player.total_bet > prev_bet:
                # Create a new pot for the difference
                current_pot_size = (player.total_bet - prev_bet) * len(eligible_players)
                
                if current_pot_size > 0:
                    pot = PotInfo(amount=current_pot_size)
                    # All players who contributed at least this much are eligible
                    pot.eligible_players = eligible_players.copy()
                    pots.append(pot)
                    
                prev_bet = player.total_bet
                
            # Add current player to eligible players set
            eligible_players.add(player.player_id)
        
        # Final pot (includes all players)
        if eligible_players:
            pot = PotInfo(amount=0)  # Amount will be updated later
            pot.eligible_players = eligible_players
            pots.append(pot)
        
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