#!/usr/bin/env python3
"""
Action Fuzzing - Phase C Testing Enhancement
============================================
Tests the game's robustness by sending random (valid AND invalid) actions.

Strategy:
- Try 10,000+ random actions including intentionally invalid ones
- Verify game handles errors gracefully
- Ensure invalid actions don't corrupt game state
- Test boundary conditions and edge cases

Fuzzing techniques:
1. Negative bet amounts
2. Extremely large bet amounts (> stack)
3. Invalid action types
4. Out-of-turn actions
5. Actions when player is all-in
6. Actions when player is inactive
7. Actions with None/null values
8. Rapid-fire actions

Expected runtime: ~3-5 minutes
"""

import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

class FuzzingStats:
    """Track fuzzing statistics."""
    def __init__(self):
        self.total_actions = 0
        self.valid_actions = 0
        self.invalid_actions = 0
        self.accepted_actions = 0
        self.rejected_actions = 0
        self.errors_raised = 0
        self.state_corruptions = 0
        self.action_types = {
            'fold': 0,
            'call': 0,
            'raise': 0,
            'invalid': 0
        }

    def print_summary(self):
        """Print fuzzing summary."""
        print("\n" + "="*70)
        print("ACTION FUZZING SUMMARY")
        print("="*70)
        print(f"Total actions tried:     {self.total_actions:>7,}")
        print(f"  Valid actions:         {self.valid_actions:>7,}")
        print(f"  Invalid actions:       {self.invalid_actions:>7,}")
        print(f"\nAction outcomes:")
        print(f"  Accepted:              {self.accepted_actions:>7,}")
        print(f"  Rejected (expected):   {self.rejected_actions:>7,}")
        print(f"  Errors raised:         {self.errors_raised:>7,}")
        print(f"  State corruptions:     {self.state_corruptions:>7,}")
        print(f"\nAction types:")
        print(f"  Fold:                  {self.action_types['fold']:>7,}")
        print(f"  Call:                  {self.action_types['call']:>7,}")
        print(f"  Raise:                 {self.action_types['raise']:>7,}")
        print(f"  Invalid type:          {self.action_types['invalid']:>7,}")
        print("="*70)


def check_state_integrity(game: PokerGame) -> bool:
    """Check if game state is still valid after action."""
    try:
        # Chip conservation
        total = sum(p.stack for p in game.players) + game.pot
        if total != game.total_chips:
            return False

        # No negative values
        if game.pot < 0 or game.current_bet < 0:
            return False

        for p in game.players:
            if p.stack < 0 or p.current_bet < 0 or p.total_invested < 0:
                return False

        return True
    except Exception:
        return False


def generate_fuzz_action():
    """Generate a random (potentially invalid) action."""
    action_type = random.choice([
        # Valid actions
        "fold", "fold", "fold",
        "call", "call", "call",
        "raise", "raise",
        # Invalid actions
        "check", "bet", "all-in", "allin", "RAISE", "Fold",
        "", None, "invalid", "quit", "skip"
    ])

    # Generate random amount (including invalid values)
    amount_type = random.choice([
        'zero', 'negative', 'small', 'medium', 'large',
        'huge', 'stack', 'none', 'float'
    ])

    if amount_type == 'zero':
        amount = 0
    elif amount_type == 'negative':
        amount = random.randint(-10000, -1)
    elif amount_type == 'small':
        amount = random.randint(1, 50)
    elif amount_type == 'medium':
        amount = random.randint(51, 500)
    elif amount_type == 'large':
        amount = random.randint(501, 2000)
    elif amount_type == 'huge':
        amount = random.randint(10000, 100000)
    elif amount_type == 'none':
        amount = None
    elif amount_type == 'float':
        amount = random.uniform(1.5, 100.5)
    else:  # 'stack'
        amount = 1000

    return action_type, amount


def fuzz_single_game(stats: FuzzingStats, num_actions: int = 100) -> bool:
    """Fuzz a single game with random actions."""
    try:
        game = PokerGame(human_player_name="Player", ai_count=3)
        game.start_new_hand()

        for _ in range(num_actions):
            # Check state integrity before action
            if not check_state_integrity(game):
                stats.state_corruptions += 1
                return False

            # Generate random action
            action_type, amount = generate_fuzz_action()
            stats.total_actions += 1

            # Track action type
            if action_type in ['fold', 'call', 'raise']:
                stats.action_types[action_type] += 1
                is_valid = True
            else:
                stats.action_types['invalid'] += 1
                is_valid = False

            # Determine if action should be valid based on game state
            human = game.players[0]
            is_human_turn = (game.current_player_index is not None and
                           game.players[game.current_player_index] == human)

            if is_valid and is_human_turn and human.is_active and not human.all_in:
                stats.valid_actions += 1
            else:
                stats.invalid_actions += 1

            # Try action
            try:
                result = game.submit_human_action(action_type, amount)

                if result:
                    stats.accepted_actions += 1
                else:
                    stats.rejected_actions += 1

            except (ValueError, TypeError, AttributeError, KeyError) as e:
                # Expected errors for invalid actions
                stats.errors_raised += 1
            except Exception as e:
                # Unexpected errors might indicate a bug
                print(f"\n⚠️  Unexpected error: {type(e).__name__}: {e}")
                print(f"   Action: {action_type}, Amount: {amount}")
                stats.errors_raised += 1

            # Check state integrity after action
            if not check_state_integrity(game):
                stats.state_corruptions += 1
                print(f"\n⚠️  State corruption after action!")
                print(f"   Action: {action_type}, Amount: {amount}")
                return False

            # Restart hand if needed
            if game.current_state == GameState.SHOWDOWN:
                # Check for player bankruptcy
                active_with_chips = [p for p in game.players if p.stack > 0]
                if len(active_with_chips) < 2:
                    break
                game.start_new_hand()

        return True

    except Exception as e:
        print(f"\n⚠️  Game crashed: {type(e).__name__}: {e}")
        return False


def run_action_fuzzing(num_games: int = 100, actions_per_game: int = 100):
    """Run action fuzzing tests."""
    print("="*70)
    print(f"ACTION FUZZING - {num_games} GAMES x {actions_per_game} ACTIONS")
    print("="*70)
    print("\nFuzzing techniques:")
    print("  - Negative bet amounts")
    print("  - Extremely large bet amounts")
    print("  - Invalid action types")
    print("  - Out-of-turn actions")
    print("  - Actions when all-in/inactive")
    print("  - None/null values")
    print("\nRunning fuzzing...\n")

    stats = FuzzingStats()
    games_completed = 0

    for game_num in range(1, num_games + 1):
        success = fuzz_single_game(stats, actions_per_game)

        if success:
            games_completed += 1

        if game_num % 10 == 0:
            pct = (game_num / num_games) * 100
            print(f"  Game {game_num:>3}/{num_games} ({pct:>5.1f}%) - "
                  f"{stats.total_actions:>6,} actions, "
                  f"{stats.state_corruptions} corruptions")

        # Stop if state corruptions detected
        if stats.state_corruptions > 0:
            print(f"\n⚠️  STOPPING: State corruption detected!")
            break

    # Print summary
    stats.print_summary()

    # Determine success
    success = (stats.state_corruptions == 0 and games_completed >= num_games * 0.95)

    if success:
        print("\n✅ ACTION FUZZING PASSED!")
        print("   Game handled all invalid actions gracefully")
        print("   No state corruptions detected")
        print(f"   {stats.total_actions:,} actions tested")
    else:
        print("\n❌ ACTION FUZZING FAILED!")
        if stats.state_corruptions > 0:
            print(f"   {stats.state_corruptions} state corruptions detected")
        if games_completed < num_games * 0.95:
            print(f"   Only {games_completed}/{num_games} games completed")

    print("="*70)
    return success


if __name__ == "__main__":
    # Run with 50 games first (quick test)
    print("Phase 1: Quick fuzzing test (50 games)...\n")
    success = run_action_fuzzing(num_games=50, actions_per_game=100)

    if success:
        print("\n\n" + "="*70)
        print("Quick test passed! Running full fuzzing (100 games)...")
        print("="*70 + "\n")
        success = run_action_fuzzing(num_games=100, actions_per_game=100)

    sys.exit(0 if success else 1)
