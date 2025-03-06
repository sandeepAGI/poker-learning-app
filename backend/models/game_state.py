from enum import Enum
from typing import List

class GameState(Enum):
    """Represents the different states of a poker game."""
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    
    @classmethod
    def get_state_sequence(cls) -> List['GameState']:
        """Returns the standard sequence of game states in order."""
        return [
            cls.PRE_FLOP,
            cls.FLOP,
            cls.TURN,
            cls.RIVER,
            cls.SHOWDOWN
        ]
    
    @classmethod
    def next_state(cls, current_state: 'GameState') -> 'GameState':
        """Returns the next game state in the sequence."""
        sequence = cls.get_state_sequence()
        current_index = sequence.index(current_state)
        
        if current_index < len(sequence) - 1:
            return sequence[current_index + 1]
        
        return current_state  # Return the same state if we're at the end