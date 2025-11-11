#!/usr/bin/env python3
"""
Full Test Suite Runner
======================
Runs all comprehensive tests in order to verify all bug fixes and features.

Tests run:
1. Core regression tests (turn order, fold resolution, raise validation, side pots)
2. Phase C tests (marathon simulation, property-based, action fuzzing, state exploration)
3. Backend-specific tests (blind escalation, complete game)

Expected runtime: ~15-20 minutes
"""

import subprocess
import sys
import time
from datetime import datetime

class TestRunner:
    """Run all test suites and track results."""

    def __init__(self):
        self.results = []
        self.start_time = None
        self.total_duration = 0

    def run_test(self, name: str, command: str, timeout: int = 600) -> bool:
        """Run a single test file and track result."""
        print("\n" + "="*70)
        print(f"Running: {name}")
        print("="*70)

        start = time.time()
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd="/home/user/poker-learning-app"
            )
            duration = time.time() - start

            success = result.returncode == 0

            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr and not success:
                print("STDERR:", result.stderr)

            self.results.append({
                'name': name,
                'success': success,
                'duration': duration,
                'output': result.stdout
            })

            if success:
                print(f"\n✅ {name} PASSED ({duration:.1f}s)")
            else:
                print(f"\n❌ {name} FAILED ({duration:.1f}s)")

            return success

        except subprocess.TimeoutExpired:
            duration = time.time() - start
            print(f"\n⏱️  {name} TIMEOUT after {duration:.1f}s")
            self.results.append({
                'name': name,
                'success': False,
                'duration': duration,
                'output': 'TIMEOUT'
            })
            return False
        except Exception as e:
            duration = time.time() - start
            print(f"\n❌ {name} ERROR: {e}")
            self.results.append({
                'name': name,
                'success': False,
                'duration': duration,
                'output': str(e)
            })
            return False

    def print_summary(self):
        """Print final summary of all tests."""
        print("\n\n" + "="*70)
        print("FULL TEST SUITE SUMMARY")
        print("="*70)
        print(f"Started:  {self.start_time}")
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {self.total_duration:.1f}s ({self.total_duration/60:.1f} minutes)")
        print(f"\nTests run: {len(self.results)}")

        passed = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - passed

        print(f"Passed:    {passed}")
        print(f"Failed:    {failed}")

        print("\n" + "-"*70)
        print("Individual Test Results:")
        print("-"*70)

        for r in self.results:
            status = "✅ PASS" if r['success'] else "❌ FAIL"
            print(f"{status} | {r['duration']:>6.1f}s | {r['name']}")

        print("="*70)

        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! 🎉")
            print("Ready for user testing")
        else:
            print(f"\n⚠️  {failed} TEST(S) FAILED")
            print("Review failures above")

        print("="*70)

        return failed == 0

def main():
    """Run full test suite."""
    runner = TestRunner()
    runner.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    start = time.time()

    print("="*70)
    print("POKER LEARNING APP - FULL TEST SUITE")
    print("="*70)
    print(f"Started: {runner.start_time}")
    print("This will take approximately 15-20 minutes...")
    print("="*70)

    # Define tests in order of importance
    tests = [
        # Core regression tests (fast, critical)
        ("Core Regression Tests", "python backend/tests/run_all_tests.py"),

        # Comprehensive Phase C tests (slower but thorough)
        ("Marathon Simulation (1000 hands)", "python test_marathon_simulation.py"),
        ("Property-Based Testing (1000 scenarios)", "python test_property_based.py"),
        ("Action Fuzzing (10,000 actions)", "python test_action_fuzzing.py"),
        ("State Space Exploration", "python test_state_exploration.py"),

        # Additional backend tests
        ("Blind Escalation", "python test_blind_escalation.py"),
        ("Side Pots Comprehensive", "python backend/tests/test_side_pots.py"),
        ("Complete Game Flow", "python backend/tests/test_complete_game.py"),

        # AI tests
        ("AI SPR Decisions", "python backend/tests/test_ai_spr_decisions.py"),
    ]

    print(f"\nTotal tests to run: {len(tests)}\n")

    # Run all tests
    all_passed = True
    for name, command in tests:
        passed = runner.run_test(name, command, timeout=600)  # 10 min timeout per test
        if not passed:
            all_passed = False
            # Don't stop on failure - run all tests to see full picture

    # Calculate total duration
    runner.total_duration = time.time() - start

    # Print summary
    success = runner.print_summary()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
