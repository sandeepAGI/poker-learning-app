"""
Stress Test: Run many AI-only games to find edge cases and crashes.

This test runs a large number of complete poker games with AI-only players
to stress test the game engine and catch rare edge cases.

Configuration:
- NUM_GAMES: Number of complete games to run (default: 100)
- NUM_AI_PLAYERS: Number of AI players per game (default: 3)
- MAX_HANDS_PER_GAME: Safety limit to prevent infinite loops (default: 200)

Tests:
1. No crashes or exceptions during gameplay
2. Chip conservation maintained throughout
3. Games reach completion (someone wins all chips)
4. No infinite loops (max hands limit)

Phase 4 of refactoring plan - Comprehensive stress testing.
"""
import pytest
import sys
import os
import time
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame, GameState


# Configuration - Test Tiers
# Tier 1 (Smoke):          50 games,   ~2 min  - Quick validation
# Tier 2 (Regression):    500 games,  ~10 min  - Pre-PR validation
# Tier 3 (Comprehensive): 2000 games, ~40 min  - Release validation

NUM_GAMES = 100  # Number of games to run (default for standard tests)
NUM_AI_PLAYERS = 3  # Fixed 3 AI players (backward compatibility)
VARY_PLAYER_COUNT = False  # Set True to randomize player count 2-6
MAX_HANDS_PER_GAME = 200  # Safety limit
VERBOSE = False  # Set True for debugging


class StressTestStats:
    """Track statistics across all stress test games."""

    def __init__(self):
        self.games_completed = 0
        self.games_crashed = 0
        self.total_hands = 0
        self.total_actions = 0
        self.chip_violations = 0
        self.infinite_loop_hits = 0
        self.errors: List[str] = []
        self.crash_details: List[Dict] = []
        self.game_durations: List[float] = []

        # Enhanced tracking
        self.player_count_distribution: Dict[int, int] = {}
        self.allin_scenarios = 0
        self.side_pot_scenarios = 0
        self.showdown_scenarios = 0
        self.fold_victories = 0

    def report(self) -> str:
        """Generate summary report."""
        total_games = self.games_completed + self.games_crashed
        success_rate = (self.games_completed / total_games * 100) if total_games > 0 else 0
        avg_hands = self.total_hands / self.games_completed if self.games_completed > 0 else 0
        avg_duration = sum(self.game_durations) / len(self.game_durations) if self.game_durations else 0

        report = f"""
================================================================================
STRESS TEST SUMMARY
================================================================================
Games Attempted:     {total_games}
Games Completed:     {self.games_completed} ({success_rate:.1f}%)
Games Crashed:       {self.games_crashed}
Total Hands Played:  {self.total_hands}
Avg Hands/Game:      {avg_hands:.1f}
Total Actions:       {self.total_actions}
Chip Violations:     {self.chip_violations}
Infinite Loop Hits:  {self.infinite_loop_hits}
Avg Game Duration:   {avg_duration:.2f}s

EDGE CASE COVERAGE:
All-In Scenarios:    {self.allin_scenarios}
Side Pot Scenarios:  {self.side_pot_scenarios}
Showdown Victories:  {self.showdown_scenarios}
Fold Victories:      {self.fold_victories}
================================================================================
"""
        if self.player_count_distribution:
            report += f"\nPLAYER COUNT DISTRIBUTION:\n"
            for count in sorted(self.player_count_distribution.keys()):
                games = self.player_count_distribution[count]
                pct = (games / total_games * 100) if total_games > 0 else 0
                report += f"  {count} players: {games} games ({pct:.1f}%)\n"

        if self.errors:
            report += f"\nERRORS ({len(self.errors)}):\n"
            for i, err in enumerate(self.errors[:10], 1):  # Show first 10
                report += f"  {i}. {err[:100]}...\n" if len(err) > 100 else f"  {i}. {err}\n"
            if len(self.errors) > 10:
                report += f"  ... and {len(self.errors) - 10} more errors\n"

        return report


def create_ai_only_game(player_count=None) -> PokerGame:
    """Create a game with only AI players (no human)."""
    import random

    # Determine player count
    if player_count is None:
        if VARY_PLAYER_COUNT:
            # Weighted distribution: favor 3-4 players, test 2-4 (engine limit)
            player_count = random.choice([2, 3, 3, 3, 4, 4])
        else:
            player_count = NUM_AI_PLAYERS

    # Create game with a "human" that we'll convert to AI behavior
    game = PokerGame("AI-Human", ai_count=player_count - 1)

    # The first player is technically "human" but we'll control it as AI
    return game


def play_single_hand(game: PokerGame, stats: StressTestStats) -> bool:
    """
    Play a single hand to completion.
    Returns True if hand completed successfully, False if error.
    """
    try:
        # Start new hand
        game.start_new_hand(process_ai=False)

        # Safety counter for actions within a hand
        action_count = 0
        max_actions = 100  # Max actions per hand

        while game.current_state != GameState.SHOWDOWN and action_count < max_actions:
            current = game.get_current_player()

            if current is None:
                # No current player - check if we should advance state
                if game._betting_round_complete():
                    game._advance_state_core(process_ai=False)
                else:
                    # Stuck state - break
                    break
                continue

            # Use game's current player index directly
            player_idx = game.current_player_index
            if player_idx is None:
                stats.errors.append(f"Hand {hand_num}: No valid current player index")
                break

            # Verify index matches the current player
            if game.players[player_idx] != current:
                stats.errors.append(
                    f"Hand {hand_num}: Index mismatch - current player is "
                    f"{current.name} but index {player_idx} points to {game.players[player_idx].name}"
                )
                break

            # Make AI decision (even for "human" player in this test)
            if current.is_active and not current.all_in:
                from game.poker_engine import AIStrategy

                decision = AIStrategy.make_decision_with_reasoning(
                    current.personality or "Balanced",
                    current.hole_cards,
                    game.community_cards,
                    game.current_bet,
                    game.pot,
                    current.stack,
                    current.current_bet,
                    game.big_blind
                )

                # Apply the action
                result = game.apply_action(
                    player_idx,
                    decision.action,
                    decision.amount,
                    decision.hand_strength,
                    decision.reasoning
                )

                stats.total_actions += 1
                action_count += 1

                if result.get("triggers_showdown"):
                    break

                # Check if we need to advance state
                if game._betting_round_complete():
                    game._advance_state_core(process_ai=False)
            else:
                # Player can't act, move to next
                game.current_player_index = game._get_next_active_player_index(
                    game.current_player_index + 1 if game.current_player_index is not None else 0
                )
                if game.current_player_index is None:
                    break

        # Verify chip conservation
        total = sum(p.stack for p in game.players) + game.pot
        if total != game.total_chips:
            stats.chip_violations += 1
            stats.errors.append(f"Chip violation: {total} != {game.total_chips}")
            return False

        return True

    except Exception as e:
        stats.errors.append(f"Hand exception: {str(e)}")
        return False


def play_full_game(game_num: int, stats: StressTestStats, player_count=None) -> bool:
    """
    Play a complete game until one player has all chips.
    Returns True if game completed successfully.
    """
    start_time = time.time()

    try:
        game = create_ai_only_game(player_count)
        hands_played = 0

        # Track player count distribution
        num_players = len(game.players)
        stats.player_count_distribution[num_players] = stats.player_count_distribution.get(num_players, 0) + 1

        while hands_played < MAX_HANDS_PER_GAME:
            # Check if game is over (one player has all chips)
            active_with_chips = [p for p in game.players if p.stack > 0]
            if len(active_with_chips) <= 1:
                # Game over!
                stats.games_completed += 1
                stats.total_hands += hands_played
                stats.game_durations.append(time.time() - start_time)

                if VERBOSE:
                    winner = active_with_chips[0] if active_with_chips else None
                    print(f"  Game {game_num}: {hands_played} hands, {num_players} players, winner: {winner.name if winner else 'None'}")

                return True

            # Play a hand
            if not play_single_hand(game, stats):
                stats.games_crashed += 1
                return False

            hands_played += 1

        # Hit max hands limit
        stats.infinite_loop_hits += 1
        stats.errors.append(f"Game {game_num}: Hit {MAX_HANDS_PER_GAME} hands limit ({num_players} players)")
        stats.games_crashed += 1
        return False

    except Exception as e:
        import traceback
        stats.games_crashed += 1
        stats.errors.append(f"Game {game_num} crashed: {str(e)}")
        stats.crash_details.append({
            "game": game_num,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        return False


@pytest.mark.slow
class TestStressAIGames:
    """Stress test with many AI-only games."""

    @pytest.mark.monthly  # Marathon: 100 games, 10-15 minutes
    def test_run_100_ai_games(self):
        """Run 100 complete AI-only games and verify no crashes."""
        stats = StressTestStats()

        player_desc = f"{NUM_AI_PLAYERS} players each" if not VARY_PLAYER_COUNT else "2-6 players (varied)"

        print(f"\n{'='*60}")
        print(f"STRESS TEST: {NUM_GAMES} AI-only games, {player_desc}")
        print(f"{'='*60}")

        for game_num in range(1, NUM_GAMES + 1):
            play_full_game(game_num, stats)

            # Progress indicator
            if game_num % 10 == 0:
                print(f"  Progress: {game_num}/{NUM_GAMES} games ({stats.games_completed} completed, {stats.games_crashed} crashed)")

        print(stats.report())

        # Assertions
        assert stats.games_crashed == 0, f"Games crashed: {stats.games_crashed}\nErrors: {stats.errors[:5]}"
        assert stats.chip_violations == 0, f"Chip conservation violations: {stats.chip_violations}"
        assert stats.infinite_loop_hits == 0, f"Infinite loops detected: {stats.infinite_loop_hits}"
        assert stats.games_completed == NUM_GAMES, f"Not all games completed: {stats.games_completed}/{NUM_GAMES}"

    def test_run_10_quick_games(self):
        """Quick sanity check with 10 games."""
        stats = StressTestStats()

        for game_num in range(1, 11):
            play_full_game(game_num, stats)

        assert stats.games_crashed == 0, f"Games crashed: {stats.games_crashed}"
        assert stats.games_completed == 10, f"Games completed: {stats.games_completed}/10"

    def test_chip_conservation_across_games(self):
        """Verify chip conservation is maintained across multiple games."""
        stats = StressTestStats()

        for game_num in range(1, 21):
            game = create_ai_only_game()
            initial_chips = game.total_chips

            # Play 10 hands
            for _ in range(10):
                play_single_hand(game, stats)

                # Check conservation after each hand
                total = sum(p.stack for p in game.players) + game.pot
                assert total == initial_chips, f"Chip violation in game {game_num}: {total} != {initial_chips}"

        assert stats.chip_violations == 0

    @pytest.mark.monthly  # Marathon: 200 games, 15-30 minutes
    def test_run_200_ai_games_varied_players(self):
        """
        TIER 2: Regression test with 200 games and varied player counts.
        Runtime: ~4 minutes (local), ~65 minutes (CI - GitHub Actions ubuntu-latest).

        Note: CI environment runs 8-9x slower than local (~19.5 sec/game observed).
        Reduced from 500 to 200 games to fit within 180-minute nightly timeout.
        Full suite (all 6 tests) takes ~157 minutes, leaves 23-minute buffer.

        Coverage: 200 games with varied player counts (2-4 players) still provides
        excellent stress testing alongside other tests (total: 530 games).
        """
        # Temporarily enable player count variation
        global VARY_PLAYER_COUNT
        original_vary = VARY_PLAYER_COUNT
        VARY_PLAYER_COUNT = True

        try:
            stats = StressTestStats()
            num_games = 200

            print(f"\n{'='*70}")
            print(f"TIER 2 REGRESSION TEST: {num_games} games with varied player counts")
            print(f"{'='*70}")

            for game_num in range(1, num_games + 1):
                play_full_game(game_num, stats)

                # Progress indicator every 25 games (4 updates for 200 games)
                if game_num % 25 == 0:
                    print(f"  Progress: {game_num}/{num_games} games ({stats.games_completed} completed, {stats.games_crashed} crashed)")

            print(stats.report())

            # Assertions
            assert stats.games_crashed == 0, f"Games crashed: {stats.games_crashed}\nErrors: {stats.errors[:5]}"
            assert stats.chip_violations == 0, f"Chip conservation violations: {stats.chip_violations}"
            assert stats.infinite_loop_hits == 0, f"Infinite loops detected: {stats.infinite_loop_hits}"
            assert stats.games_completed == num_games, f"Not all games completed: {stats.games_completed}/{num_games}"

            # Verify we tested multiple player counts
            assert len(stats.player_count_distribution) >= 3, f"Should test at least 3 different player counts, got {len(stats.player_count_distribution)}"

        finally:
            VARY_PLAYER_COUNT = original_vary

    @pytest.mark.monthly  # Marathon: 100 heads-up games, 10-15 minutes
    def test_run_heads_up_intensive(self):
        """
        Test heads-up (2 player) games intensively.
        100 games to verify heads-up specific rules.
        """
        stats = StressTestStats()
        num_games = 100

        print(f"\n{'='*70}")
        print(f"HEADS-UP INTENSIVE TEST: {num_games} 2-player games")
        print(f"{'='*70}")

        for game_num in range(1, num_games + 1):
            play_full_game(game_num, stats, player_count=2)

            if game_num % 20 == 0:
                print(f"  Progress: {game_num}/{num_games} games")

        print(stats.report())

        # Assertions
        assert stats.games_crashed == 0, f"Games crashed: {stats.games_crashed}"
        assert stats.chip_violations == 0, f"Chip violations: {stats.chip_violations}"
        assert stats.games_completed == num_games, f"Completed: {stats.games_completed}/{num_games}"

        # Verify all games were 2-player
        assert stats.player_count_distribution.get(2, 0) == num_games, "All games should be 2-player"

    @pytest.mark.monthly  # Marathon: 100 multi-player games, 10-15 minutes
    def test_run_multi_player_intensive(self):
        """
        Test 4 player games intensively.
        100 games to verify multi-player scenarios (more complex side pots, etc.)
        """
        stats = StressTestStats()
        num_games = 100

        print(f"\n{'='*70}")
        print(f"MULTI-PLAYER INTENSIVE TEST: {num_games} 4-player games")
        print(f"{'='*70}")

        for game_num in range(1, num_games + 1):
            player_count = 4  # Maximum supported by poker engine
            play_full_game(game_num, stats, player_count=player_count)

            if game_num % 20 == 0:
                print(f"  Progress: {game_num}/{num_games} games")

        print(stats.report())

        # Assertions
        assert stats.games_crashed == 0, f"Games crashed: {stats.games_crashed}"
        assert stats.chip_violations == 0, f"Chip violations: {stats.chip_violations}"
        assert stats.games_completed == num_games, f"Completed: {stats.games_completed}/{num_games}"

        # Verify all games were 4-player
        assert stats.player_count_distribution.get(4, 0) == num_games, "All games should be 4-player"


def run_stress_test_standalone():
    """Run stress test directly (not via pytest)."""
    stats = StressTestStats()

    print(f"\n{'='*60}")
    print(f"STRESS TEST: {NUM_GAMES} AI-only games")
    print(f"{'='*60}")

    for game_num in range(1, NUM_GAMES + 1):
        play_full_game(game_num, stats)
        if game_num % 10 == 0:
            print(f"  Progress: {game_num}/{NUM_GAMES}")

    print(stats.report())

    return stats.games_crashed == 0


if __name__ == "__main__":
    success = run_stress_test_standalone()
    sys.exit(0 if success else 1)
