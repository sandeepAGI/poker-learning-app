# Re-export components from the refactored modules
# This file exists for backward compatibility
from enum import Enum
from typing import List, Dict, Set, Any, Optional, Tuple
from dataclasses import dataclass, field

import config
from treys import Evaluator, Card

from models.game_state import GameState
from models.player import Player, AIPlayer, HumanPlayer
from models.pot import PotInfo, PotManager
from game.poker_game import PokerGame
from utils.logger import get_logger

# Backward compatibility flag
try:
    from stats.ai_decision_analyzer import get_decision_analyzer
    from stats.statistics_manager import get_statistics_manager
    LEARNING_STATS_ENABLED = True
except ImportError:
    LEARNING_STATS_ENABLED = False

# Create a logger for the game engine
logger = get_logger("game_engine")

# This module has been refactored:
# - Player classes moved to models/player.py
# - GameState enum moved to models/game_state.py
# - PotInfo moved to models/pot.py
# - PokerGame moved to game/poker_game.py
# 
# For new code, please import from the specific modules.
# This file is kept for backward compatibility.

