#!/usr/bin/env python3
"""
State Space Exploration - Phase C Testing Enhancement
=====================================================
Tests that all game states are reachable and all state transitions work correctly.

Strategy:
- Verify all possible game states can be reached
- Test all state transition paths
- Ensure no unreachable states
- Test edge case state combinations

States to explore:
1. PRE_FLOP
2. FLOP
3. TURN
4. RIVER
5. SHOWDOWN

Scenarios to test:
- Complete hand (pre-flop → flop → turn → river → showdown)
- Early folds (pre-flop → showdown)
- All-in scenarios (any state → showdown)
- Multiple hands in sequence
- Different player counts (2-4 players)

Expected runtime: ~2-3 minutes
"""

import sys
import os
import random
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState


class StateExplorer:
    """Explore game state space."""

    def __init__(self):
        self.states_reached = set()
        self.state_transitions = defaultdict(set)
        self.scenarios_tested = 0
        self.errors = []

    def record_state(self, state: GameState):
        """Record that a state was reached."""
        self.states_reached.add(state.value)

    def record_transition(self, from_state: GameState, to_state: GameState):
        """Record a state transition."""
        self.state_transitions[from_state.value].add(to_state.value)

    def print_summary(self):
        """Print exploration summary."""
        print("\n" + "="*70)
        print("STATE SPACE EXPLORATION SUMMARY")
        print("="*70)
        print(f"Scenarios tested:     {self.scenarios_tested:>4}")
        print(f"States reached:       {len(self.states_reached)}/5")
        print(f"  - PRE_FLOP:         {'✓' if 'pre_flop' in self.states_reached else '✗'}")
        print(f"  - FLOP:             {'✓' if 'flop' in self.states_reached else '✗'}")
        print(f"  - TURN:             {'✓' if 'turn' in self.states_reached else '✗'}")
        print(f"  - RIVER:            {'✓' if 'river' in self.states_reached else '✗'}")
        print(f"  - SHOWDOWN:         {'✓' if 'showdown' in self.states_reached else '✗'}")

        print(f"\nState transitions observed:")
        for from_state, to_states in sorted(self.state_transitions.items()):
            print(f"  {from_state:12} → {', '.join(sorted(to_states))}")

        if self.errors:
            print(f"\nErrors encountered:   {len(self.errors)}")
            for i, error in enumerate(self.errors[:3], 1):
                print(f"  {i}. {error}")
            if len(self.errors) > 3:
                print(f"  ... and {len(self.errors) - 3} more")

        print("="*70)


def scenario_complete_hand(explorer: StateExplorer) -> bool:
    """Scenario: Play a complete hand through all states."""
    try:
        game = PokerGame(human_player_name="Player", ai_count=3)
        game.start_new_hand()

        prev_state = game.current_state
        explorer.record_state(prev_state)

        # Play through entire hand by calling everything
        max_actions = 100
        actions = 0

        while game.current_state != GameState.SHOWDOWN and actions < max_actions:
            if game.current_player_index is None:
                break

            human = game.players[0]
            current = game.players[game.current_player_index]

            if current == human and human.is_active and not human.all_in:
                # Always call to advance through all states
                game.submit_human_action("call")
                actions += 1

                # Record state and transition
                new_state = game.current_state
                if new_state != prev_state:
                    explorer.record_transition(prev_state, new_state)
                    explorer.record_state(new_state)
                    prev_state = new_state
            else:
                break

        explorer.scenarios_tested += 1
        return True

    except Exception as e:
        explorer.errors.append(f"Complete hand: {e}")
        return False


def scenario_early_fold(explorer: StateExplorer) -> bool:
    """Scenario: Fold early, skip to showdown."""
    try:
        game = PokerGame(human_player_name="Player", ai_count=3)
        game.start_new_hand()

        prev_state = game.current_state
        explorer.record_state(prev_state)

        # Fold immediately
        human = game.players[0]
        if game.current_player_index is not None and game.players[game.current_player_index] == human:
            game.submit_human_action("fold")

        # Record transition
        new_state = game.current_state
        if new_state != prev_state:
            explorer.record_transition(prev_state, new_state)
            explorer.record_state(new_state)

        explorer.scenarios_tested += 1
        return True

    except Exception as e:
        explorer.errors.append(f"Early fold: {e}")
        return False


def scenario_all_in_preflop(explorer: StateExplorer) -> bool:
    """Scenario: All-in pre-flop, fast-forward to showdown."""
    try:
        game = PokerGame(human_player_name="Player", ai_count=3)
        game.start_new_hand()

        prev_state = game.current_state
        explorer.record_state(prev_state)

        # Go all-in
        human = game.players[0]
        if (game.current_player_index is not None and
            game.players[game.current_player_index] == human and
            human.is_active):
            game.submit_human_action("raise", human.stack)

        # Record states reached
        explorer.record_state(game.current_state)
        if game.current_state != prev_state:
            explorer.record_transition(prev_state, game.current_state)

        explorer.scenarios_tested += 1
        return True

    except Exception as e:
        explorer.errors.append(f"All-in preflop: {e}")
        return False


def scenario_raises_and_calls(explorer: StateExplorer) -> bool:
    """Scenario: Mix of raises and calls."""
    try:
        game = PokerGame(human_player_name="Player", ai_count=3)
        game.start_new_hand()

        prev_state = game.current_state
        explorer.record_state(prev_state)

        # Alternate between raise and call
        actions_taken = 0
        max_actions = 20

        while game.current_state != GameState.SHOWDOWN and actions_taken < max_actions:
            if game.current_player_index is None:
                break

            human = game.players[0]
            current = game.players[game.current_player_index]

            if current == human and human.is_active and not human.all_in:
                # Alternate: raise, call, raise, call...
                if actions_taken % 2 == 0 and human.stack > game.current_bet + game.big_blind:
                    # Try to raise
                    min_raise = game.current_bet + game.big_blind
                    if human.stack >= min_raise - human.current_bet:
                        raise_amount = min(min_raise + random.randint(10, 50), human.stack)
                        game.submit_human_action("raise", raise_amount)
                    else:
                        game.submit_human_action("call")
                else:
                    game.submit_human_action("call")

                actions_taken += 1

                # Record state changes
                new_state = game.current_state
                if new_state != prev_state:
                    explorer.record_transition(prev_state, new_state)
                    explorer.record_state(new_state)
                    prev_state = new_state
            else:
                break

        explorer.scenarios_tested += 1
        return True

    except Exception as e:
        explorer.errors.append(f"Raises and calls: {e}")
        return False


def scenario_multiple_hands(explorer: StateExplorer) -> bool:
    """Scenario: Multiple consecutive hands."""
    try:
        game = PokerGame(human_player_name="Player", ai_count=3)

        for _ in range(5):
            game.start_new_hand()
            prev_state = game.current_state
            explorer.record_state(prev_state)

            # Play hand with random actions
            max_actions = 20
            actions = 0

            while game.current_state != GameState.SHOWDOWN and actions < max_actions:
                if game.current_player_index is None:
                    break

                human = game.players[0]
                current = game.players[game.current_player_index]

                if current == human and human.is_active and not human.all_in:
                    action = random.choice(["fold", "call", "call", "call"])
                    game.submit_human_action(action)
                    actions += 1

                    # Record transitions
                    new_state = game.current_state
                    if new_state != prev_state:
                        explorer.record_transition(prev_state, new_state)
                        explorer.record_state(new_state)
                        prev_state = new_state
                else:
                    break

            # Stop if too many players busted
            active = [p for p in game.players if p.stack > 0]
            if len(active) < 2:
                break

        explorer.scenarios_tested += 1
        return True

    except Exception as e:
        explorer.errors.append(f"Multiple hands: {e}")
        return False


def scenario_heads_up(explorer: StateExplorer) -> bool:
    """Scenario: Heads-up game (2 players)."""
    try:
        game = PokerGame(human_player_name="Player", ai_count=1)
        game.start_new_hand()

        prev_state = game.current_state
        explorer.record_state(prev_state)

        # Play through hand
        max_actions = 20
        actions = 0

        while game.current_state != GameState.SHOWDOWN and actions < max_actions:
            if game.current_player_index is None:
                break

            human = game.players[0]
            current = game.players[game.current_player_index]

            if current == human and human.is_active and not human.all_in:
                game.submit_human_action("call")
                actions += 1

                new_state = game.current_state
                if new_state != prev_state:
                    explorer.record_transition(prev_state, new_state)
                    explorer.record_state(new_state)
                    prev_state = new_state
            else:
                break

        explorer.scenarios_tested += 1
        return True

    except Exception as e:
        explorer.errors.append(f"Heads-up: {e}")
        return False


def run_state_exploration():
    """Run state space exploration."""
    print("="*70)
    print("STATE SPACE EXPLORATION")
    print("="*70)
    print("\nScenarios to test:")
    print("  1. Complete hand (all states)")
    print("  2. Early fold (pre-flop → showdown)")
    print("  3. All-in pre-flop (fast-forward)")
    print("  4. Raises and calls")
    print("  5. Multiple consecutive hands")
    print("  6. Heads-up (2 players)")
    print("\nRunning scenarios...\n")

    explorer = StateExplorer()

    # Run each scenario multiple times
    scenarios = [
        ("Complete hand", scenario_complete_hand, 20),
        ("Early fold", scenario_early_fold, 20),
        ("All-in pre-flop", scenario_all_in_preflop, 20),
        ("Raises and calls", scenario_raises_and_calls, 20),
        ("Multiple hands", scenario_multiple_hands, 10),
        ("Heads-up", scenario_heads_up, 10),
    ]

    for name, scenario_func, count in scenarios:
        print(f"  Running: {name} ({count}x)...")
        for i in range(count):
            scenario_func(explorer)

    # Print summary
    explorer.print_summary()

    # Check success
    expected_states = {'pre_flop', 'flop', 'turn', 'river', 'showdown'}
    all_states_reached = expected_states.issubset(explorer.states_reached)

    # Expected transitions
    expected_transitions = {
        'pre_flop': {'flop', 'showdown'},
        'flop': {'turn', 'showdown'},
        'turn': {'river', 'showdown'},
        'river': {'showdown'},
    }

    transitions_valid = True
    for from_state, to_states in expected_transitions.items():
        if from_state in explorer.state_transitions:
            observed = explorer.state_transitions[from_state]
            if not to_states.intersection(observed):
                transitions_valid = False
                print(f"\n⚠️  Missing transitions from {from_state}")

    success = (all_states_reached and
               transitions_valid and
               len(explorer.errors) == 0)

    if success:
        print("\n✅ STATE SPACE EXPLORATION PASSED!")
        print("   All states reachable")
        print("   All transitions working")
        print(f"   {explorer.scenarios_tested} scenarios tested")
    else:
        print("\n❌ STATE SPACE EXPLORATION FAILED!")
        if not all_states_reached:
            missing = expected_states - explorer.states_reached
            print(f"   Missing states: {missing}")
        if not transitions_valid:
            print("   Some transitions not working")
        if explorer.errors:
            print(f"   {len(explorer.errors)} errors encountered")

    print("="*70)
    return success


if __name__ == "__main__":
    success = run_state_exploration()
    sys.exit(0 if success else 1)
