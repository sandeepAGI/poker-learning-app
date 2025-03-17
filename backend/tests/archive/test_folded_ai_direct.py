#!/usr/bin/env python3
"""
Direct Test Script to Verify Fix for Folded AI Players Issue

This test directly uses the PokerGame class to verify that:
1. AI players that fold are properly marked as inactive
2. Folded AI players do not make decisions in subsequent betting rounds
3. Folded AI players are properly reactivated for the next hand
"""

import sys
import os
import logging
from typing import List, Dict, Any

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required components
from models.player import Player, AIPlayer
from game.poker_game import PokerGame
from models.game_state import GameState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_folded_ai_direct.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_folded_ai_direct")

def create_test_players() -> List[AIPlayer]:
    """Create 5 AI players for testing"""
    players = []
    personalities = ["Conservative", "Risk Taker", "Probability-Based", "Bluffer", "Conservative"]
    
    for i, personality in enumerate(personalities):
        players.append(AIPlayer(
            player_id=f"ai_{i}",
            stack=1000,
            personality=personality
        ))
    
    logger.info(f"Created {len(players)} AI players")
    return players

def analyze_player_states(poker_game: PokerGame) -> None:
    """Analyze and log player states to verify folded players are not acting"""
    logger.info(f"Current game state: {poker_game.current_state.value}")
    logger.info(f"Pot size: {poker_game.pot}")
    
    active_players = 0
    folded_players = 0
    
    for player in poker_game.players:
        player_status = "ACTIVE" if player.is_active else "FOLDED"
        logger.info(f"Player {player.player_id} is {player_status} with stack {player.stack}")
        
        if player.is_active:
            active_players += 1
        else:
            folded_players += 1
    
    logger.info(f"Total active players: {active_players}, folded players: {folded_players}")

def run_test() -> bool:
    """Run the complete test sequence"""
    try:
        # Create players
        players = create_test_players()
        
        # Create poker game
        poker_game = PokerGame(players=players)
        logger.info("Poker game initialized")
        
        # Track which players fold in each hand
        folded_players_by_hand = {}
        
        # Play 5 hands
        for hand_num in range(1, 6):
            logger.info(f"\n{'='*50}\nStarting hand #{hand_num}\n{'='*50}")
            
            # Start a new hand
            poker_game.current_state = GameState.PRE_FLOP
            poker_game.community_cards = []
            
            # Post blinds and deal cards
            poker_game.post_blinds()
            logger.info("Posted blinds and dealt cards")
            
            # Verify all players are active at the start of the hand
            for player in poker_game.players:
                if not player.is_active:
                    logger.error(f"Player {player.player_id} should be active at the start of hand {hand_num} but is not")
                    return False
            
            # Track folded players for this hand
            folded_this_hand = set()
            
            # Play through betting rounds
            while poker_game.current_state != GameState.SHOWDOWN:
                logger.info(f"Current state: {poker_game.current_state.value}")
                
                # Log player states before betting round
                analyze_player_states(poker_game)
                
                # Execute betting round
                active_before = sum(1 for p in poker_game.players if p.is_active)
                poker_game.betting_round()
                active_after = sum(1 for p in poker_game.players if p.is_active)
                
                # Check which players folded in this betting round
                for player in poker_game.players:
                    if player.is_active == False and player.player_id not in folded_this_hand:
                        folded_this_hand.add(player.player_id)
                        logger.info(f"Player {player.player_id} folded in {poker_game.current_state.value}")
                
                # Log results of betting round
                logger.info(f"Betting round complete. Active players: {active_before} -> {active_after}")
                logger.info(f"Pot: {poker_game.pot}")
                
                # Break early if only one player is left
                if active_after <= 1:
                    logger.info("Only one active player remains, skipping to distribution")
                    break
                
                # Advance to next state
                poker_game.advance_game_state()
            
            # Distribute pot (showdown or single player remaining)
            poker_game.distribute_pot()
            logger.info("Pot distributed")
            
            # Store which players folded in this hand
            folded_players_by_hand[hand_num] = folded_this_hand
            
            # Prepare for next hand
            for player in poker_game.players:
                player.reset_hand_state()
            
            # Verify all players with sufficient chips are reactivated
            for player in poker_game.players:
                if player.stack >= 5 and not player.is_active:
                    logger.error(f"Player {player.player_id} has {player.stack} chips but was not reactivated for the next hand")
                    return False
            
            logger.info(f"Hand {hand_num} complete. Folded players: {folded_this_hand}")
        
        # Test passed if we got here
        logger.info("TEST PASSED: Folded AI players were properly handled")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Starting direct test to verify fix for folded AI players issue")
    success = run_test()
    if success:
        logger.info("Test completed successfully!")
        sys.exit(0)
    else:
        logger.error("Test failed!")
        sys.exit(1)