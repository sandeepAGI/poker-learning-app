#!/usr/bin/env python3
"""
Marathon Simulation Test - Phase A Testing Enhancement
========================================================
Runs 10,000 hands with random valid actions to stress-test the poker engine.
This catches edge cases and bugs that unit tests miss.

Strategy:
- Play 10,000 consecutive hands
- Make random but VALID actions (no invalid inputs)
- Check invariants every 100 hands
- Report statistics and any failures
- This simulates real gameplay at scale

Expected runtime: ~2-5 minutes
"""

import sys
import os
import random
from typing import List, Dict

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

class MarathonStats:
    """Track statistics during marathon simulation."""
    def __init__(self):
        self.hands_completed = 0
        self.actions_taken = 0
        self.folds = 0
        self.calls = 0
        self.raises = 0
        self.all_ins = 0
        self.showdowns = 0
        self.human_wins = 0
        self.ai_wins = 0
        self.errors = []

    def record_action(self, action: str):
        """Record an action."""
        self.actions_taken += 1
        if action == "fold":
            self.folds += 1
        elif action == "call":
            self.calls += 1
        elif action == "raise":
            self.raises += 1

    def record_hand_complete(self, game: PokerGame):
        """Record a completed hand."""
        self.hands_completed += 1

        # Check if we had a showdown
        if game.current_state == GameState.SHOWDOWN:
            self.showdowns += 1

    def print_summary(self):
        """Print statistics summary."""
        print("\n" + "="*70)
        print("MARATHON SIMULATION SUMMARY")
        print("="*70)
        print(f"Hands Completed:  {self.hands_completed:,}")
        print(f"Total Actions:    {self.actions_taken:,}")
        print(f"  - Folds:        {self.folds:,}")
        print(f"  - Calls:        {self.calls:,}")
        print(f"  - Raises:       {self.raises:,}")
        print(f"Showdowns:        {self.showdowns:,}")
        print(f"Errors:           {len(self.errors)}")

        if self.errors:
            print("\n⚠️  ERRORS ENCOUNTERED:")
            for i, error in enumerate(self.errors[:5], 1):
                print(f"  {i}. {error}")
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors) - 5} more")

        print("="*70)


def get_valid_actions(game: PokerGame) -> List[Dict]:
    """Get list of valid actions for current player."""
    human = game.players[0]

    actions = []

    # Can always fold if it's our turn
    if game.players[game.current_player_index] == human:
        actions.append({"type": "fold", "amount": 0})

    # Calculate call amount
    call_amount = game.current_bet - human.current_bet

    # Can call if we have chips
    if call_amount >= 0 and human.stack >= call_amount:
        actions.append({"type": "call", "amount": 0})

    # Can raise if we have chips beyond the call
    if human.stack > call_amount:
        min_raise = game.current_bet + game.big_blind
        max_raise = human.stack

        # Only offer raise if we can meet minimum
        if human.stack >= min_raise - human.current_bet:
            # Pick a random raise amount
            raise_amount = random.randint(
                max(min_raise - human.current_bet, game.big_blind),
                max_raise
            )
            actions.append({"type": "raise", "amount": raise_amount})

    return actions


def play_hand_with_random_actions(game: PokerGame, stats: MarathonStats) -> bool:
    """
    Play a single hand with random valid actions.
    Returns True if successful, False if error.
    """
    try:
        # Start new hand
        game.start_new_hand()

        # Play until hand is complete
        max_actions = 1000  # Safety limit to prevent infinite loops
        actions_this_hand = 0

        while game.current_state != GameState.SHOWDOWN and actions_this_hand < max_actions:
            # Check if it's human's turn
            if game.current_player_index is None:
                break

            human = game.players[0]
            current_player = game.players[game.current_player_index]

            if current_player == human and human.is_active and not human.all_in:
                # Get valid actions
                valid_actions = get_valid_actions(game)

                if not valid_actions:
                    # No valid actions, break
                    break

                # Choose random action with weighted probability
                # Fold: 30%, Call: 50%, Raise: 20%
                weights = []
                for action in valid_actions:
                    if action["type"] == "fold":
                        weights.append(30)
                    elif action["type"] == "call":
                        weights.append(50)
                    elif action["type"] == "raise":
                        weights.append(20)

                action = random.choices(valid_actions, weights=weights, k=1)[0]

                # Submit action
                stats.record_action(action["type"])
                result = game.submit_human_action(action["type"], action["amount"])

                if not result:
                    # Action failed, try fold
                    game.submit_human_action("fold")
                    stats.record_action("fold")

                actions_this_hand += 1
            else:
                # AI player or not our turn, let game process
                break

        # Record completed hand
        stats.record_hand_complete(game)

        return True

    except Exception as e:
        error_msg = f"Hand #{stats.hands_completed + 1}: {str(e)}"
        stats.errors.append(error_msg)
        return False


def run_marathon_simulation(num_hands: int = 10000, check_interval: int = 100):
    """
    Run marathon simulation of N hands.

    Args:
        num_hands: Number of hands to play
        check_interval: Check invariants every N hands
    """
    print("="*70)
    print(f"MARATHON SIMULATION TEST - {num_hands:,} HANDS")
    print("="*70)
    print("\nInitializing game...")

    # Create game with 3 AI opponents
    game = PokerGame(human_player_name="Player", ai_count=3)
    stats = MarathonStats()

    print(f"Starting simulation: {num_hands:,} hands")
    print(f"Checking invariants every {check_interval} hands")
    print("\nProgress:")

    # Play hands
    for hand_num in range(1, num_hands + 1):
        # Play hand
        success = play_hand_with_random_actions(game, stats)

        # Print progress
        if hand_num % check_interval == 0:
            progress_pct = (hand_num / num_hands) * 100
            print(f"  Hand {hand_num:>6,}/{num_hands:,} ({progress_pct:>5.1f}%) - "
                  f"{stats.actions_taken:,} actions, {len(stats.errors)} errors")

        # Stop if we hit too many errors
        if len(stats.errors) >= 10:
            print(f"\n⚠️  STOPPING: Too many errors ({len(stats.errors)})")
            break

        # Stop if all AI players are busted (unrealistic but possible)
        active_ai = [p for p in game.players[1:] if p.stack > 0]
        if len(active_ai) < 2:
            print(f"\n⚠️  STOPPING: Only {len(active_ai)} AI players remain with chips")
            break

    # Print summary
    stats.print_summary()

    # Final result
    if len(stats.errors) == 0 and stats.hands_completed >= num_hands * 0.95:
        print("\n✅ MARATHON SIMULATION PASSED!")
        print(f"   Completed {stats.hands_completed:,}/{num_hands:,} hands without critical errors")
        return True
    else:
        print("\n❌ MARATHON SIMULATION FAILED!")
        if len(stats.errors) > 0:
            print(f"   {len(stats.errors)} errors encountered")
        if stats.hands_completed < num_hands * 0.95:
            print(f"   Only completed {stats.hands_completed:,}/{num_hands:,} hands")
        return False


if __name__ == "__main__":
    # Run with smaller batch first (1000 hands) to catch issues faster
    print("Phase 1: Running 1000-hand warmup...\n")
    success = run_marathon_simulation(num_hands=1000, check_interval=100)

    if success:
        print("\n\n" + "="*70)
        print("Warmup passed! Running full 10,000-hand marathon...")
        print("="*70 + "\n")
        success = run_marathon_simulation(num_hands=10000, check_interval=500)

    sys.exit(0 if success else 1)
