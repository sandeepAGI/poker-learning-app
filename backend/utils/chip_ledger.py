"""
Chip Ledger System for tracking and validating all chip movements in poker games.
Ensures chip conservation and provides audit trail for debugging.
"""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChipMovement:
    """Record of a chip movement transaction."""
    timestamp: float
    source: str
    destination: str
    amount: int
    operation: str
    before_balance: Optional[int] = None
    after_balance: Optional[int] = None


class ChipConservationError(Exception):
    """Raised when chip conservation is violated."""
    pass


class ChipLedger:
    """
    Track and validate all chip movements in the game.
    Ensures total chips remain constant throughout the game.
    """
    
    def __init__(self, initial_chips_per_player: int, num_players: int):
        """
        Initialize the chip ledger.
        
        Args:
            initial_chips_per_player: Starting chips for each player
            num_players: Number of players in the game
        """
        self.total_expected_chips = initial_chips_per_player * num_players
        self.movements: List[ChipMovement] = []
        self.logger = logger
        
    def record_movement(self, source: str, destination: str, amount: int, 
                       operation: str, before_balance: Optional[int] = None,
                       after_balance: Optional[int] = None) -> None:
        """
        Record a chip movement with validation.
        
        Args:
            source: Where chips came from (player_id, "pot", "blinds", etc.)
            destination: Where chips went to (player_id, "pot", "winnings", etc.)
            amount: Number of chips moved
            operation: Description of the operation (e.g., "bet", "call", "pot_distribution")
            before_balance: Balance before movement (if available)
            after_balance: Balance after movement (if available)
        """
        if amount <= 0:
            raise ValueError(f"Chip movement amount must be positive: {amount}")
            
        movement = ChipMovement(
            timestamp=time.time(),
            source=source,
            destination=destination,
            amount=amount,
            operation=operation,
            before_balance=before_balance,
            after_balance=after_balance
        )
        
        self.movements.append(movement)
        
        self.logger.debug(f"CHIP MOVEMENT: {source} -> {destination}: {amount} chips ({operation})")
        
    def validate_game_state(self, players: List[Any], pot: int) -> bool:
        """
        Validate total chips in the system match expected amount.
        
        Args:
            players: List of player objects with .stack attribute
            pot: Current pot amount
            
        Returns:
            True if chips are conserved
            
        Raises:
            ChipConservationError: If chip conservation is violated
        """
        player_chips = sum(getattr(player, 'stack', 0) for player in players)
        total_chips = player_chips + pot
        
        if total_chips != self.total_expected_chips:
            error_msg = (f"Chip conservation error: Expected {self.total_expected_chips}, "
                        f"found {total_chips} (players: {player_chips}, pot: {pot})")
            self.logger.error(error_msg)
            
            # Log recent movements for debugging
            self._log_recent_movements(5)
            
            raise ChipConservationError(error_msg)
        
        self.logger.debug(f"CHIP VALIDATION: Total chips preserved: {total_chips}")
        return True
    
    def validate_player_stacks(self, players: List[Any]) -> bool:
        """
        Validate that no player has negative chips.
        
        Args:
            players: List of player objects with .stack attribute
            
        Returns:
            True if all stacks are valid
            
        Raises:
            ChipConservationError: If any player has invalid stack
        """
        for player in players:
            stack = getattr(player, 'stack', 0)
            if stack < 0:
                error_msg = f"Player {getattr(player, 'player_id', 'unknown')} has negative stack: {stack}"
                self.logger.error(error_msg)
                raise ChipConservationError(error_msg)
        
        return True
    
    def get_movement_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all chip movements.
        
        Returns:
            Dictionary with movement statistics
        """
        if not self.movements:
            return {"total_movements": 0, "total_chips_moved": 0}
            
        total_moved = sum(m.amount for m in self.movements)
        operations = {}
        
        for movement in self.movements:
            op = movement.operation
            if op not in operations:
                operations[op] = {"count": 0, "total_amount": 0}
            operations[op]["count"] += 1
            operations[op]["total_amount"] += movement.amount
        
        return {
            "total_movements": len(self.movements),
            "total_chips_moved": total_moved,
            "operations": operations,
            "first_movement": self.movements[0].timestamp if self.movements else None,
            "last_movement": self.movements[-1].timestamp if self.movements else None
        }
    
    def _log_recent_movements(self, count: int = 10) -> None:
        """Log recent chip movements for debugging."""
        recent = self.movements[-count:] if len(self.movements) > count else self.movements
        
        self.logger.info(f"RECENT CHIP MOVEMENTS ({len(recent)} of {len(self.movements)}):")
        for movement in recent:
            self.logger.info(f"  {movement.operation}: {movement.source} -> {movement.destination} "
                           f"({movement.amount} chips) at {movement.timestamp}")
    
    def audit_pot_distribution(self, pot_before: int, pot_after: int, 
                              winners: Dict[str, int]) -> bool:
        """
        Audit a pot distribution to ensure it's valid.
        
        Args:
            pot_before: Pot size before distribution
            pot_after: Pot size after distribution (should be 0)
            winners: Dictionary of winner_id -> chips_won
            
        Returns:
            True if distribution is valid
            
        Raises:
            ChipConservationError: If distribution is invalid
        """
        total_distributed = sum(winners.values())
        
        if pot_after != 0:
            error_msg = f"Pot not fully distributed: {pot_after} chips remaining"
            self.logger.error(error_msg)
            raise ChipConservationError(error_msg)
            
        if total_distributed != pot_before:
            error_msg = (f"Pot distribution mismatch: pot was {pot_before}, "
                        f"distributed {total_distributed}")
            self.logger.error(error_msg)
            raise ChipConservationError(error_msg)
        
        # Record the distribution
        for winner_id, amount in winners.items():
            self.record_movement("pot", winner_id, amount, "pot_distribution")
        
        self.logger.info(f"POT DISTRIBUTION AUDIT: {pot_before} chips distributed to {len(winners)} winners")
        return True
    
    def create_checkpoint(self, players: List[Any], pot: int, 
                         operation: str) -> Dict[str, Any]:
        """
        Create a checkpoint of current chip state for rollback purposes.
        
        Args:
            players: List of player objects
            pot: Current pot amount
            operation: Description of operation being performed
            
        Returns:
            Checkpoint data that can be used for rollback
        """
        checkpoint = {
            "timestamp": time.time(),
            "operation": operation,
            "pot": pot,
            "player_stacks": {
                getattr(player, 'player_id', f'player_{i}'): getattr(player, 'stack', 0)
                for i, player in enumerate(players)
            },
            "total_chips": sum(getattr(player, 'stack', 0) for player in players) + pot
        }
        
        # Validate before creating checkpoint
        self.validate_game_state(players, pot)
        
        self.logger.debug(f"CHECKPOINT CREATED: {operation} - Total chips: {checkpoint['total_chips']}")
        return checkpoint
    
    def validate_against_checkpoint(self, checkpoint: Dict[str, Any], 
                                   players: List[Any], pot: int) -> bool:
        """
        Validate current state against a checkpoint.
        
        Args:
            checkpoint: Previously created checkpoint
            players: Current list of player objects
            pot: Current pot amount
            
        Returns:
            True if state is consistent with checkpoint expectations
        """
        current_total = sum(getattr(player, 'stack', 0) for player in players) + pot
        expected_total = checkpoint["total_chips"]
        
        if current_total != expected_total:
            error_msg = (f"Checkpoint validation failed for {checkpoint['operation']}: "
                        f"expected {expected_total}, found {current_total}")
            self.logger.error(error_msg)
            raise ChipConservationError(error_msg)
        
        self.logger.debug(f"CHECKPOINT VALIDATION: {checkpoint['operation']} - Chips preserved")
        return True