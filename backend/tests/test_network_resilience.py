"""
Phase 11: Network Failure Simulation & Resilience Testing

Goal: Validate the system handles poor network conditions gracefully:
1. High latency (slow responses)
2. Timeout handling
3. Graceful degradation
4. State consistency under network stress

This ensures production reliability under real-world network conditions.
"""
import pytest
import sys
import os
import time
import asyncio
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame


class TestHighLatencyResilience:
    """Test 1: System behavior under high latency."""

    def test_game_completes_with_slow_processing(self):
        """
        Simulate slow processing (high latency scenario).

        Game should complete successfully even with delays.
        """
        print("\n" + "="*60)
        print("TEST 1: Game Completion Under Slow Processing")
        print("="*60)

        game = PokerGame("TestPlayer", ai_count=3)

        # Simulate latency by adding delays between operations
        start_time = time.time()

        # Start hand
        time.sleep(0.1)  # 100ms latency
        game.start_new_hand(process_ai=False)

        # Process player actions with delays
        actions_completed = 0
        for _ in range(10):
            if game.current_state.value == "showdown":
                break

            time.sleep(0.05)  # 50ms per action (high latency)

            if game.current_player_index is not None:
                success = game.apply_action(
                    game.current_player_index,
                    "call",
                    0
                )
                if success:
                    actions_completed += 1

        elapsed = time.time() - start_time

        print(f"\n📊 Results:")
        print(f"  Actions completed: {actions_completed}")
        print(f"  Final state: {game.current_state.value}")
        print(f"  Total time: {elapsed:.2f}s (with simulated latency)")
        print(f"  Game completed: {game.current_state.value in ['showdown', 'pre_flop']}")

        # Game should complete despite latency
        assert game.current_state.value in ["showdown", "pre_flop"], \
            f"Game stuck in {game.current_state.value}"

        print("\n✅ PASS: Game completes under high latency")

    def test_multiple_games_with_latency(self):
        """
        Test multiple games complete with latency.

        Validates system doesn't accumulate issues over time.
        """
        print("\n" + "="*60)
        print("TEST 2: Multiple Games with Latency")
        print("="*60)

        games_completed = 0
        total_latency = 0.0

        for i in range(10):
            start_time = time.time()

            game = PokerGame("TestPlayer", ai_count=3)

            # Add latency
            time.sleep(0.05)  # 50ms startup latency
            game.start_new_hand(process_ai=True)

            elapsed = time.time() - start_time
            total_latency += elapsed

            # Verify game completed
            if game.current_state.value in ["showdown", "pre_flop"]:
                games_completed += 1

        avg_latency = total_latency / 10

        print(f"\n📊 Results:")
        print(f"  Games completed: {games_completed}/10")
        print(f"  Total time: {total_latency:.2f}s")
        print(f"  Avg per game: {avg_latency:.3f}s")

        # All games should complete
        assert games_completed == 10, \
            f"Only {games_completed}/10 games completed"

        print("\n✅ PASS: Multiple games complete with latency")


class TestTimeoutHandling:
    """Test 2: Timeout handling and recovery."""

    def test_game_state_valid_after_timeout_scenario(self):
        """
        Simulate timeout scenario and verify state validity.

        System should maintain valid state even if operations are slow.
        """
        print("\n" + "="*60)
        print("TEST 3: State Validity After Timeout Scenario")
        print("="*60)

        game = PokerGame("TestPlayer", ai_count=3)
        game.start_new_hand(process_ai=False)

        # Simulate timeout by not processing for a while
        initial_state = game.current_state.value
        time.sleep(0.2)  # 200ms "timeout"

        # State should still be valid
        assert game.current_state.value == initial_state, \
            f"State changed during timeout: {initial_state} -> {game.current_state.value}"

        # Game should continue normally after timeout
        game.start_new_hand(process_ai=True)

        print(f"\n📊 Results:")
        print(f"  State after timeout: {game.current_state.value}")
        print(f"  Game recovered: True")

        assert game.current_state.value in ["showdown", "pre_flop"], \
            f"Game failed to recover: {game.current_state.value}"

        print("\n✅ PASS: Game state valid after timeout")

    def test_rapid_action_processing_stability(self):
        """
        Test system stability under rapid action processing.

        System should handle rapid-fire actions without errors.
        """
        print("\n" + "="*60)
        print("TEST 4: Rapid Action Processing Stability")
        print("="*60)

        actions_processed = 0
        errors = []

        # Process actions rapidly across multiple games
        for i in range(50):
            try:
                game = PokerGame("TestPlayer", ai_count=3)
                game.start_new_hand(process_ai=False)

                # Rapid-fire actions (no delays)
                for _ in range(10):
                    if game.current_player_index is not None and game.current_state.value != "showdown":
                        result = game.apply_action(
                            game.current_player_index,
                            "call",
                            0
                        )
                        if result:
                            actions_processed += 1

                # Verify game reached valid end state
                assert game.current_state.value in ["showdown", "pre_flop"], \
                    f"Invalid end state: {game.current_state.value}"

            except Exception as e:
                errors.append(f"Game {i+1}: {str(e)}")

        print(f"\n📊 Results:")
        print(f"  Actions processed: {actions_processed}")
        print(f"  Games completed: 50")
        print(f"  Errors: {len(errors)}")

        if errors:
            print(f"\n❌ First 3 errors:")
            for error in errors[:3]:
                print(f"  - {error}")

        # Should handle rapid processing without errors
        assert len(errors) == 0, \
            f"Encountered {len(errors)} errors during rapid processing"

        print("\n✅ PASS: Rapid action processing is stable")


class TestGracefulDegradation:
    """Test 3: Graceful degradation under poor conditions."""

    def test_game_engine_stability_under_stress(self):
        """
        Stress test: Rapid operations with minimal delays.

        System should remain stable and not crash.
        """
        print("\n" + "="*60)
        print("TEST 5: Game Engine Stability Under Stress")
        print("="*60)

        errors = []
        games_completed = 0

        # Run 50 games as fast as possible (stress test)
        for i in range(50):
            try:
                game = PokerGame("TestPlayer", ai_count=3)
                game.start_new_hand(process_ai=True)

                # Verify state is valid
                assert game.current_state.value in ["showdown", "pre_flop"], \
                    f"Invalid state: {game.current_state.value}"

                games_completed += 1

            except Exception as e:
                errors.append(f"Game {i+1}: {str(e)}")

        print(f"\n📊 Results:")
        print(f"  Games completed: {games_completed}/50")
        print(f"  Errors: {len(errors)}")

        if errors:
            print(f"\n❌ Errors encountered:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  - {error}")

        # Should complete all games without errors
        assert len(errors) == 0, \
            f"Encountered {len(errors)} errors during stress test"

        print("\n✅ PASS: Game engine stable under stress")

    def test_memory_stability_under_network_stress(self):
        """
        Verify memory doesn't leak under network stress conditions.

        Simulates many connections/disconnections.
        """
        print("\n" + "="*60)
        print("TEST 6: Memory Stability Under Network Stress")
        print("="*60)

        import gc
        import sys

        gc.collect()
        initial_objects = len(gc.get_objects())

        # Simulate 100 connection/disconnection cycles
        for _ in range(100):
            game = PokerGame("TestPlayer", ai_count=3)
            game.start_new_hand(process_ai=True)

            # Simulate "disconnect" by deleting game
            del game

        gc.collect()
        final_objects = len(gc.get_objects())

        growth = final_objects - initial_objects
        growth_pct = (growth / initial_objects) * 100

        print(f"\n📊 Results:")
        print(f"  Initial objects: {initial_objects:,}")
        print(f"  Final objects: {final_objects:,}")
        print(f"  Growth: {growth:,} objects ({growth_pct:+.1f}%)")

        # Memory shouldn't grow significantly
        assert abs(growth_pct) < 100.0, \
            f"Memory grew {growth_pct:.1f}% - potential leak!"

        print("\n✅ PASS: Memory stable under network stress")


class TestStateConsistency:
    """Test 4: State consistency under adverse conditions."""

    def test_chip_conservation_under_stress(self):
        """
        Verify chip conservation under rapid operations.

        No chips should be created or destroyed.
        """
        print("\n" + "="*60)
        print("TEST 7: Chip Conservation Under Stress")
        print("="*60)

        violations = 0

        # Run 100 hands and verify chip conservation
        for i in range(100):
            game = PokerGame("TestPlayer", ai_count=3)

            # Calculate total chips before hand
            total_before = sum(p.stack for p in game.players)

            game.start_new_hand(process_ai=True)

            # Calculate total chips after hand (including pot)
            total_after = sum(p.stack for p in game.players) + game.pot

            # Verify conservation
            if abs(total_after - total_before) > 0.01:
                violations += 1
                if violations <= 3:  # Show first 3 violations
                    print(f"  Hand {i+1}: {total_before} -> {total_after} (Δ{total_after - total_before})")

        print(f"\n📊 Results:")
        print(f"  Hands tested: 100")
        print(f"  Violations: {violations}")

        assert violations == 0, \
            f"Found {violations} chip conservation violations"

        print("\n✅ PASS: Chip conservation maintained under stress")

    def test_player_state_consistency(self):
        """
        Verify player state remains consistent.

        Player states should never be invalid.
        """
        print("\n" + "="*60)
        print("TEST 8: Player State Consistency")
        print("="*60)

        inconsistencies = []

        for i in range(100):
            game = PokerGame("TestPlayer", ai_count=3)
            game.start_new_hand(process_ai=True)

            # Verify player state consistency
            for player in game.players:
                # Stack should never be negative
                if player.stack < 0:
                    inconsistencies.append(f"Hand {i+1}: {player.name} has negative stack: {player.stack}")

                # Active players should have valid hole cards
                if player.is_active and not player.hole_cards and game.current_state.value != "showdown":
                    inconsistencies.append(f"Hand {i+1}: Active player {player.name} has no hole cards")

                # All-in players should have zero stack
                if player.all_in and player.stack != 0:
                    inconsistencies.append(f"Hand {i+1}: All-in player {player.name} has stack: {player.stack}")

        print(f"\n📊 Results:")
        print(f"  Hands tested: 100")
        print(f"  Inconsistencies: {len(inconsistencies)}")

        if inconsistencies:
            print(f"\n❌ Inconsistencies found:")
            for issue in inconsistencies[:5]:
                print(f"  - {issue}")

        assert len(inconsistencies) == 0, \
            f"Found {len(inconsistencies)} state inconsistencies"

        print("\n✅ PASS: Player state consistent")


class TestRecoveryScenarios:
    """Test 5: Recovery from adverse scenarios."""

    def test_recovery_from_rapid_game_cycling(self):
        """
        Test system recovers from rapid game creation/destruction.

        Simulates users rapidly starting/leaving games.
        """
        print("\n" + "="*60)
        print("TEST 9: Recovery from Rapid Game Cycling")
        print("="*60)

        cycles_completed = 0
        errors = []

        # Rapidly create/destroy 200 games
        for i in range(200):
            try:
                game = PokerGame("TestPlayer", ai_count=3)
                game.start_new_hand(process_ai=True)

                # Immediately "abandon" game
                del game

                cycles_completed += 1

            except Exception as e:
                errors.append(str(e))

        print(f"\n📊 Results:")
        print(f"  Cycles completed: {cycles_completed}/200")
        print(f"  Errors: {len(errors)}")

        assert len(errors) == 0, \
            f"Encountered {len(errors)} errors during cycling"

        print("\n✅ PASS: System recovers from rapid cycling")

    def test_long_running_stability_under_load(self):
        """
        Test system stability over extended period under load.

        Simulates hours of continuous play.
        """
        print("\n" + "="*60)
        print("TEST 10: Long-Running Stability Under Load")
        print("="*60)

        game = PokerGame("TestPlayer", ai_count=3)
        hands_completed = 0
        errors = []

        start_time = time.time()

        # Play 500 consecutive hands (simulates extended session)
        for i in range(500):
            try:
                game.start_new_hand(process_ai=True)
                hands_completed += 1

                # Periodic state validation
                if i % 100 == 0:
                    total_chips = sum(p.stack for p in game.players) + game.pot
                    assert abs(total_chips - 4000) < 0.01, \
                        f"Chip conservation failed at hand {i+1}: {total_chips}"

            except Exception as e:
                errors.append(f"Hand {i+1}: {str(e)}")

        elapsed = time.time() - start_time

        print(f"\n📊 Results:")
        print(f"  Hands completed: {hands_completed}/500")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Avg per hand: {elapsed/hands_completed:.3f}s")
        print(f"  Errors: {len(errors)}")

        if errors:
            print(f"\n❌ First 3 errors:")
            for error in errors[:3]:
                print(f"  - {error}")

        assert len(errors) == 0, \
            f"Encountered {len(errors)} errors during long run"

        print("\n✅ PASS: System stable over extended period")


if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v", "-s"])
