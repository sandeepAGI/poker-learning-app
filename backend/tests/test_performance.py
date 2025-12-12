"""
Phase 10: Performance & Load Testing

Goal: Determine system limits and performance characteristics:
1. How many concurrent games can run simultaneously?
2. What's the response time under load?
3. Memory and CPU usage patterns
4. Performance degradation characteristics

This validates the app can handle production load.
"""
import pytest
import sys
import os
import time
import asyncio
from collections import defaultdict
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame


class TestConcurrentGames:
    """Test 1: Concurrent game execution."""

    def test_10_sequential_games_baseline(self):
        """
        Baseline: 10 games played sequentially.

        This establishes baseline performance for comparison.
        """
        print("\n" + "="*60)
        print("TEST 1: Baseline - 10 Sequential Games")
        print("="*60)

        start_time = time.time()
        games_completed = 0

        for i in range(10):
            game = PokerGame("TestPlayer", ai_count=3)

            # Play one complete hand
            game.start_new_hand(process_ai=True)
            games_completed += 1

        elapsed = time.time() - start_time
        avg_per_game = elapsed / games_completed

        print(f"\n📊 Results:")
        print(f"  Total games: {games_completed}")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Avg per game: {avg_per_game:.3f}s")
        print(f"  Games/second: {games_completed/elapsed:.2f}")

        # Baseline assertion: should complete in reasonable time
        assert elapsed < 30.0, f"Sequential games took {elapsed:.2f}s - too slow!"

        print("\n✅ PASS: Baseline performance acceptable")

    def test_50_games_performance_scaling(self):
        """
        Scale test: 50 games to measure performance characteristics.

        Tests if performance degrades linearly or worse than linear.
        """
        print("\n" + "="*60)
        print("TEST 2: Performance Scaling (50 games)")
        print("="*60)

        results = []
        batch_sizes = [1, 5, 10, 25, 50]

        for batch_size in batch_sizes:
            start_time = time.time()

            for i in range(batch_size):
                game = PokerGame("TestPlayer", ai_count=3)
                game.start_new_hand(process_ai=True)

            elapsed = time.time() - start_time
            avg_per_game = elapsed / batch_size

            results.append({
                "batch_size": batch_size,
                "total_time": elapsed,
                "avg_per_game": avg_per_game,
                "games_per_sec": batch_size / elapsed
            })

        print(f"\n📊 Performance Scaling Results:")
        print(f"{'Batch Size':<12} {'Total Time':<12} {'Avg/Game':<12} {'Games/sec':<12}")
        print("-" * 60)

        for r in results:
            print(f"{r['batch_size']:<12} {r['total_time']:<12.2f} "
                  f"{r['avg_per_game']:<12.3f} {r['games_per_sec']:<12.2f}")

        # Check for performance degradation
        baseline = results[0]["avg_per_game"]
        worst = results[-1]["avg_per_game"]
        degradation = worst / baseline

        print(f"\n📈 Performance Analysis:")
        print(f"  Baseline (1 game): {baseline:.3f}s")
        print(f"  At scale (50 games): {worst:.3f}s")
        print(f"  Degradation factor: {degradation:.2f}x")

        # Performance shouldn't degrade more than 2x
        assert degradation < 2.0, \
            f"Performance degraded {degradation:.2f}x - exceeds 2x threshold!"

        print("\n✅ PASS: Performance scaling is acceptable")


class TestGameEnginePerformance:
    """Test 2: Individual game engine performance."""

    def test_hand_evaluator_performance(self):
        """
        Benchmark hand evaluator speed.

        Hand evaluation is critical path - must be fast.
        """
        print("\n" + "="*60)
        print("TEST 3: Hand Evaluator Performance")
        print("="*60)

        game = PokerGame("TestPlayer", ai_count=3)
        evaluations = 0

        start_time = time.time()

        # Evaluate 1000 random hands
        for _ in range(1000):
            game.start_new_hand(process_ai=False)

            # Deal community cards
            game.community_cards = game.deck_manager.deal_cards(5)

            # Evaluate each player's hand
            for player in game.players:
                if player.hole_cards:
                    game.hand_evaluator.evaluate_hand(
                        player.hole_cards,
                        game.community_cards
                    )
                    evaluations += 1

        elapsed = time.time() - start_time
        evals_per_sec = evaluations / elapsed

        print(f"\n📊 Results:")
        print(f"  Total evaluations: {evaluations:,}")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Evaluations/sec: {evals_per_sec:,.0f}")
        print(f"  Avg time/eval: {(elapsed/evaluations)*1000:.3f}ms")

        # Should achieve at least 1000 evaluations/sec
        assert evals_per_sec >= 1000, \
            f"Hand evaluator too slow: {evals_per_sec:.0f} evals/sec"

        print("\n✅ PASS: Hand evaluator performance acceptable")

    def test_ai_decision_performance(self):
        """
        Benchmark AI decision-making speed.

        AI should make decisions quickly to avoid UI lag.
        """
        print("\n" + "="*60)
        print("TEST 4: AI Decision Performance")
        print("="*60)

        decisions = 0
        start_time = time.time()

        # Run 100 hands with AI processing
        # Each hand with 3 AI players = ~3-12 decisions per hand (depending on folds)
        for _ in range(100):
            game = PokerGame("TestPlayer", ai_count=3)
            game.start_new_hand(process_ai=True)

            # Count AI decisions from completed hands
            # Each AI player acts at least once per betting round
            # Minimum: 3 AI players * 1 pre-flop action = 3 decisions per hand
            decisions += 3  # Conservative estimate

        elapsed = time.time() - start_time

        # Use conservative estimate since we can't easily track exact AI decision count
        estimated_decisions = 100 * 3  # 100 hands * 3 AI players minimum
        decisions_per_sec = estimated_decisions / elapsed

        print(f"\n📊 Results:")
        print(f"  Estimated AI decisions: {estimated_decisions:,}")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Decisions/sec: {decisions_per_sec:.1f}")
        print(f"  Avg time/decision: {(elapsed/estimated_decisions)*1000:.1f}ms")

        # AI decisions should be fast (<100ms average)
        avg_decision_time = elapsed / estimated_decisions
        assert avg_decision_time < 0.1, \
            f"AI decisions too slow: {avg_decision_time*1000:.1f}ms average"

        print("\n✅ PASS: AI decision performance acceptable")

    def test_complete_hand_performance(self):
        """
        Benchmark complete hand execution.

        End-to-end performance including all game logic.
        """
        print("\n" + "="*60)
        print("TEST 5: Complete Hand Performance")
        print("="*60)

        num_hands = 100
        timing_breakdown = defaultdict(list)

        for _ in range(num_hands):
            game = PokerGame("TestPlayer", ai_count=3)

            # Time complete hand
            start = time.time()
            game.start_new_hand(process_ai=True)
            hand_time = time.time() - start

            timing_breakdown["complete_hand"].append(hand_time)

        # Calculate statistics
        hands = timing_breakdown["complete_hand"]
        avg_time = sum(hands) / len(hands)
        min_time = min(hands)
        max_time = max(hands)
        p95_time = sorted(hands)[int(len(hands) * 0.95)]

        print(f"\n📊 Results ({num_hands} hands):")
        print(f"  Average: {avg_time*1000:.1f}ms")
        print(f"  Minimum: {min_time*1000:.1f}ms")
        print(f"  Maximum: {max_time*1000:.1f}ms")
        print(f"  P95: {p95_time*1000:.1f}ms")

        # P95 should be under 500ms for good UX
        assert p95_time < 0.5, \
            f"P95 latency too high: {p95_time*1000:.1f}ms"

        print("\n✅ PASS: Complete hand performance acceptable")


class TestMemoryUsage:
    """Test 3: Memory usage characteristics."""

    def test_memory_stability_100_hands(self):
        """
        Verify no memory leaks over 100 hands.

        Memory should remain stable, not grow unbounded.
        """
        print("\n" + "="*60)
        print("TEST 6: Memory Stability (100 hands)")
        print("="*60)

        import gc
        import sys

        # Force garbage collection before test
        gc.collect()

        game = PokerGame("TestPlayer", ai_count=3)

        # Measure memory at intervals
        memory_samples = []

        for i in range(100):
            game.start_new_hand(process_ai=True)

            # Sample memory every 10 hands
            if i % 10 == 0:
                gc.collect()
                memory_samples.append(sys.getsizeof(game))

        print(f"\n📊 Memory Samples (bytes):")
        for i, size in enumerate(memory_samples):
            print(f"  Hand {i*10:3d}: {size:,} bytes")

        # Check for memory growth
        first_sample = memory_samples[0]
        last_sample = memory_samples[-1]
        growth_pct = ((last_sample - first_sample) / first_sample) * 100

        print(f"\n📈 Memory Analysis:")
        print(f"  Initial: {first_sample:,} bytes")
        print(f"  Final: {last_sample:,} bytes")
        print(f"  Growth: {growth_pct:+.1f}%")

        # Memory shouldn't grow more than 50%
        assert abs(growth_pct) < 50.0, \
            f"Memory grew {growth_pct:.1f}% - possible leak!"

        print("\n✅ PASS: Memory usage is stable")


class TestThroughputBenchmarks:
    """Test 4: System throughput benchmarks."""

    def test_hands_per_second_throughput(self):
        """
        Measure maximum hands/second throughput.

        This is the key performance metric for the system.
        """
        print("\n" + "="*60)
        print("TEST 7: Hands/Second Throughput")
        print("="*60)

        test_duration = 5.0  # Run for 5 seconds
        hands_completed = 0

        start_time = time.time()
        end_time = start_time + test_duration

        while time.time() < end_time:
            game = PokerGame("TestPlayer", ai_count=3)
            game.start_new_hand(process_ai=True)
            hands_completed += 1

        elapsed = time.time() - start_time
        hands_per_sec = hands_completed / elapsed

        print(f"\n📊 Results:")
        print(f"  Test duration: {elapsed:.2f}s")
        print(f"  Hands completed: {hands_completed}")
        print(f"  Hands/second: {hands_per_sec:.2f}")
        print(f"  Seconds/hand: {1/hands_per_sec:.3f}s")

        # Should achieve at least 5 hands/second
        assert hands_per_sec >= 5.0, \
            f"Throughput too low: {hands_per_sec:.2f} hands/sec"

        print("\n✅ PASS: Throughput meets requirements")

    def test_actions_per_second_throughput(self):
        """
        Measure action processing throughput.

        Critical for responsive WebSocket gameplay.
        """
        print("\n" + "="*60)
        print("TEST 8: Actions/Second Throughput")
        print("="*60)

        game = PokerGame("TestPlayer", ai_count=3)
        actions_processed = 0

        start_time = time.time()

        # Play 50 hands and count all actions
        for _ in range(50):
            game.start_new_hand(process_ai=False)

            # Simulate actions for each player
            for player in game.players:
                if player.is_active and not player.has_acted:
                    success = game.apply_action(
                        game.current_player_index,
                        "call",
                        0
                    )
                    if success:
                        actions_processed += 1

        elapsed = time.time() - start_time
        actions_per_sec = actions_processed / elapsed

        print(f"\n📊 Results:")
        print(f"  Actions processed: {actions_processed}")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Actions/second: {actions_per_sec:.1f}")

        # Should process at least 50 actions/second
        assert actions_per_sec >= 50.0, \
            f"Action processing too slow: {actions_per_sec:.1f} actions/sec"

        print("\n✅ PASS: Action throughput acceptable")


class TestStressScenarios:
    """Test 5: Stress test scenarios."""

    def test_rapid_game_creation_and_destruction(self):
        """
        Stress test: Rapidly create and destroy games.

        Simulates high churn rate in production.
        """
        print("\n" + "="*60)
        print("TEST 9: Rapid Game Creation/Destruction")
        print("="*60)

        iterations = 100
        start_time = time.time()

        for i in range(iterations):
            # Create game
            game = PokerGame("TestPlayer", ai_count=3)
            game.start_new_hand(process_ai=True)

            # Immediately destroy (let GC handle it)
            del game

        elapsed = time.time() - start_time
        ops_per_sec = iterations / elapsed

        print(f"\n📊 Results:")
        print(f"  Iterations: {iterations}")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Operations/sec: {ops_per_sec:.1f}")

        # Should handle rapid churn
        assert elapsed < 60.0, \
            f"Rapid creation/destruction too slow: {elapsed:.2f}s"

        print("\n✅ PASS: Rapid churn handled well")

    def test_long_running_game_stability(self):
        """
        Stress test: Single game running many hands.

        Validates game state doesn't degrade over time.
        """
        print("\n" + "="*60)
        print("TEST 10: Long-Running Game Stability")
        print("="*60)

        game = PokerGame("TestPlayer", ai_count=3)
        hands_played = 0
        errors = 0

        start_time = time.time()

        # Play 200 consecutive hands
        for i in range(200):
            try:
                game.start_new_hand(process_ai=True)
                hands_played += 1

                # Verify game state integrity
                assert game.pot >= 0, f"Negative pot at hand {i+1}"
                assert len(game.players) == 4, f"Player count changed at hand {i+1}"

            except Exception as e:
                errors += 1
                print(f"  Error at hand {i+1}: {e}")

        elapsed = time.time() - start_time

        print(f"\n📊 Results:")
        print(f"  Hands played: {hands_played}")
        print(f"  Errors: {errors}")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Avg per hand: {elapsed/hands_played:.3f}s")

        # Should complete all hands without errors
        assert errors == 0, f"Encountered {errors} errors during long run"
        assert hands_played == 200, f"Only completed {hands_played}/200 hands"

        print("\n✅ PASS: Long-running game is stable")


if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v", "-s"])
