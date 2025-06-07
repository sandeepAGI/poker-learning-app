"""
State Management System for poker game transactions.
Ensures atomic state transitions and rollback capability.
"""

import logging
import copy
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum

from models.game_state import GameState

logger = logging.getLogger(__name__)


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class IncompleteTransitionError(Exception):
    """Raised when a state transition is incomplete."""
    pass


class StateTransactionError(Exception):
    """Raised when a state transaction fails."""
    pass


@dataclass
class StateCheckpoint:
    """Represents a point-in-time snapshot of game state."""
    timestamp: float
    operation: str
    game_state: GameState
    pot: int
    current_bet: int
    player_states: Dict[str, Dict[str, Any]]
    community_cards: List[str]
    deck_size: int


class StateTransitionValidator:
    """Validates state transitions according to poker rules."""
    
    VALID_TRANSITIONS = {
        GameState.PRE_FLOP: [GameState.FLOP, GameState.SHOWDOWN],
        GameState.FLOP: [GameState.TURN, GameState.SHOWDOWN],
        GameState.TURN: [GameState.RIVER, GameState.SHOWDOWN],
        GameState.RIVER: [GameState.SHOWDOWN],
        GameState.SHOWDOWN: [GameState.PRE_FLOP]  # For next hand
    }
    
    @classmethod
    def is_valid_transition(cls, from_state: GameState, to_state: GameState) -> bool:
        """Check if a state transition is valid."""
        return to_state in cls.VALID_TRANSITIONS.get(from_state, [])
    
    @classmethod
    def get_valid_transitions(cls, from_state: GameState) -> List[GameState]:
        """Get all valid transitions from a given state."""
        return cls.VALID_TRANSITIONS.get(from_state, [])


class GameStateManager:
    """
    Manages atomic state transitions for poker games.
    Ensures consistency and provides rollback capability.
    """
    
    def __init__(self, game):
        """
        Initialize the state manager.
        
        Args:
            game: The poker game instance to manage
        """
        self.game = game
        self.logger = logger
        self.checkpoints: List[StateCheckpoint] = []
        self.validator = StateTransitionValidator()
        
    def create_checkpoint(self, operation: str) -> StateCheckpoint:
        """
        Create a checkpoint of the current game state.
        
        Args:
            operation: Description of the operation being performed
            
        Returns:
            StateCheckpoint: The created checkpoint
        """
        import time
        
        # Capture player states
        player_states = {}
        for player in self.game.players:
            player_states[player.player_id] = {
                "stack": player.stack,
                "current_bet": player.current_bet,
                "total_bet": player.total_bet,
                "is_active": player.is_active,
                "all_in": player.all_in,
                "hole_cards": player.hole_cards.copy() if player.hole_cards else []
            }
        
        checkpoint = StateCheckpoint(
            timestamp=time.time(),
            operation=operation,
            game_state=self.game.current_state,
            pot=self.game.pot,
            current_bet=self.game.current_bet,
            player_states=player_states,
            community_cards=self.game.community_cards.copy(),
            deck_size=len(self.game.deck)
        )
        
        self.checkpoints.append(checkpoint)
        self.logger.debug(f"CHECKPOINT CREATED: {operation} - State: {self.game.current_state}")
        return checkpoint
    
    def transition_state(self, to_state: GameState, operation: Callable[[], Any], 
                        operation_name: str) -> Any:
        """
        Perform an atomic state transition with validation and rollback capability.
        
        Args:
            to_state: Target state to transition to
            operation: Function to execute for the transition
            operation_name: Description of the operation
            
        Returns:
            Result of the operation
            
        Raises:
            InvalidStateTransitionError: If transition is not valid
            StateTransactionError: If the transaction fails
        """
        from_state = self.game.current_state
        
        # Validate transition
        if not self.validator.is_valid_transition(from_state, to_state):
            raise InvalidStateTransitionError(
                f"Invalid transition from {from_state} to {to_state}")
        
        # Create checkpoint before transition
        checkpoint = self.create_checkpoint(f"{operation_name}_before")
        
        try:
            # Execute the operation
            self.logger.info(f"STATE TRANSITION: {from_state} -> {to_state} ({operation_name})")
            result = operation()
            
            # Update state
            self.game.current_state = to_state
            
            # Verify successful transition
            if self.game.current_state != to_state:
                raise IncompleteTransitionError(
                    f"Failed to transition to {to_state}, current state is {self.game.current_state}")
            
            # Validate game consistency after transition
            self._validate_game_consistency(operation_name)
            
            self.logger.info(f"STATE TRANSITION COMPLETE: {from_state} -> {to_state}")
            return result
            
        except Exception as e:
            self.logger.error(f"STATE TRANSITION FAILED: {operation_name} - {e}")
            # Rollback to checkpoint
            try:
                self._rollback_to_checkpoint(checkpoint)
                self.logger.info(f"STATE ROLLBACK SUCCESSFUL: Restored to {checkpoint.game_state}")
            except Exception as rollback_error:
                self.logger.error(f"STATE ROLLBACK FAILED: {rollback_error}")
                raise StateTransactionError(
                    f"Transaction failed and rollback failed: {e}, {rollback_error}")
            
            raise StateTransactionError(f"Transaction failed and was rolled back: {e}")
    
    def execute_atomic_operation(self, operation: Callable[[], Any], 
                                operation_name: str) -> Any:
        """
        Execute an operation atomically without state transition.
        
        Args:
            operation: Function to execute
            operation_name: Description of the operation
            
        Returns:
            Result of the operation
        """
        checkpoint = self.create_checkpoint(f"{operation_name}_before")
        
        try:
            self.logger.debug(f"ATOMIC OPERATION: {operation_name}")
            result = operation()
            
            # Validate game consistency after operation
            self._validate_game_consistency(operation_name)
            
            self.logger.debug(f"ATOMIC OPERATION COMPLETE: {operation_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"ATOMIC OPERATION FAILED: {operation_name} - {e}")
            # Rollback to checkpoint
            try:
                self._rollback_to_checkpoint(checkpoint)
                self.logger.info(f"ROLLBACK SUCCESSFUL: {operation_name}")
            except Exception as rollback_error:
                self.logger.error(f"ROLLBACK FAILED: {rollback_error}")
                raise StateTransactionError(
                    f"Operation failed and rollback failed: {e}, {rollback_error}")
            
            raise StateTransactionError(f"Operation failed and was rolled back: {e}")
    
    def _rollback_to_checkpoint(self, checkpoint: StateCheckpoint) -> None:
        """
        Restore game state to a checkpoint.
        
        Args:
            checkpoint: The checkpoint to restore to
        """
        # Restore game state
        self.game.current_state = checkpoint.game_state
        self.game.pot = checkpoint.pot
        self.game.current_bet = checkpoint.current_bet
        self.game.community_cards = checkpoint.community_cards.copy()
        
        # Restore player states
        for player in self.game.players:
            if player.player_id in checkpoint.player_states:
                player_state = checkpoint.player_states[player.player_id]
                player.stack = player_state["stack"]
                player.current_bet = player_state["current_bet"]
                player.total_bet = player_state["total_bet"]
                player.is_active = player_state["is_active"]
                player.all_in = player_state["all_in"]
                player.hole_cards = player_state["hole_cards"].copy()
        
        self.logger.debug(f"ROLLBACK COMPLETE: Restored to {checkpoint.operation}")
    
    def _validate_game_consistency(self, operation_name: str) -> None:
        """
        Validate game state consistency after an operation.
        
        Args:
            operation_name: Name of the operation for logging
        """
        try:
            # Validate chip conservation if chip ledger is available
            if hasattr(self.game, 'chip_ledger'):
                self.game.chip_ledger.validate_game_state(self.game.players, self.game.pot)
                self.game.chip_ledger.validate_player_stacks(self.game.players)
            
            # Validate basic game rules
            self._validate_basic_rules()
            
        except Exception as e:
            raise StateTransactionError(f"Game consistency validation failed after {operation_name}: {e}")
    
    def _validate_basic_rules(self) -> None:
        """Validate basic poker game rules."""
        # Check that pot is non-negative
        if self.game.pot < 0:
            raise ValueError(f"Pot cannot be negative: {self.game.pot}")
        
        # Check that current bet is non-negative
        if self.game.current_bet < 0:
            raise ValueError(f"Current bet cannot be negative: {self.game.current_bet}")
        
        # Check that all player stacks are non-negative
        for player in self.game.players:
            if player.stack < 0:
                raise ValueError(f"Player {player.player_id} has negative stack: {player.stack}")
        
        # Check community cards count based on state
        max_community_cards = {
            GameState.PRE_FLOP: 0,
            GameState.FLOP: 3,
            GameState.TURN: 4,
            GameState.RIVER: 5,
            GameState.SHOWDOWN: 5
        }
        
        expected_max = max_community_cards.get(self.game.current_state, 5)
        if len(self.game.community_cards) > expected_max:
            raise ValueError(f"Too many community cards for state {self.game.current_state}: "
                           f"expected max {expected_max}, found {len(self.game.community_cards)}")
    
    def get_transaction_history(self) -> List[Dict[str, Any]]:
        """
        Get a summary of all transactions.
        
        Returns:
            List of transaction summaries
        """
        return [
            {
                "timestamp": cp.timestamp,
                "operation": cp.operation,
                "game_state": cp.game_state.value if cp.game_state else None,
                "pot": cp.pot,
                "current_bet": cp.current_bet,
                "players": len(cp.player_states),
                "community_cards": len(cp.community_cards)
            }
            for cp in self.checkpoints
        ]
    
    def cleanup_old_checkpoints(self, keep_last_n: int = 10) -> None:
        """
        Remove old checkpoints to prevent memory bloat.
        
        Args:
            keep_last_n: Number of recent checkpoints to keep
        """
        if len(self.checkpoints) > keep_last_n:
            removed = len(self.checkpoints) - keep_last_n
            self.checkpoints = self.checkpoints[-keep_last_n:]
            self.logger.debug(f"CHECKPOINT CLEANUP: Removed {removed} old checkpoints")