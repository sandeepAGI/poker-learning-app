"""
Debug script to investigate all-in state advancement bug.

Simulates the failing test scenario to see why the game gets stuck in pre_flop.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame, GameState

# Create a game with 1 human + 2 AI (same as test)
game = PokerGame("TestPlayer", ai_count=2)
game.start_new_hand(process_ai=False)

print("="*80)
print("INITIAL STATE")
print("="*80)
print(f"Game state: {game.current_state.value}")
print(f"Current player index: {game.current_player_index}")
print(f"Current bet: {game.current_bet}")
print(f"Pot: {game.pot}")
print("\nPlayers:")
for i, p in enumerate(game.players):
    print(f"  [{i}] {p.name}: stack={p.stack}, current_bet={p.current_bet}, is_active={p.is_active}, all_in={p.all_in}, has_acted={p.has_acted}, is_human={p.is_human}")

# Find human player
human_player = next((p for p in game.players if p.is_human), None)
human_index = game.players.index(human_player)
print(f"\nHuman player: {human_player.name} (index {human_index})")

# Simulate AI turns (before human acts)
print("\n" + "="*80)
print("SIMULATING AI TURNS (before human)")
print("="*80)

iteration = 0
while game.current_player_index is not None:
    iteration += 1
    if iteration > 20:
        print("ERROR: Too many iterations, breaking")
        break

    current_player = game.players[game.current_player_index]

    # Stop at human player
    if current_player.is_human:
        print(f"\nReached human player at index {game.current_player_index}")
        break

    # Skip inactive/all-in/already-acted
    if not current_player.is_active or current_player.all_in or current_player.has_acted:
        print(f"Skipping player {current_player.name}: is_active={current_player.is_active}, all_in={current_player.all_in}, has_acted={current_player.has_acted}")
        game.current_player_index = game._get_next_active_player_index(game.current_player_index + 1)
        continue

    print(f"\n[{iteration}] AI turn: {current_player.name} (index {game.current_player_index})")

    # AI makes decision
    from game.poker_engine import AIStrategy
    decision = AIStrategy.make_decision_with_reasoning(
        current_player.personality,
        current_player.hole_cards,
        game.community_cards,
        game.current_bet,
        game.pot,
        current_player.stack,
        current_player.current_bet,
        game.big_blind
    )

    print(f"  Decision: {decision.action} {decision.amount if decision.amount else ''}")

    # Apply action
    result = game.apply_action(
        player_index=game.current_player_index,
        action=decision.action,
        amount=decision.amount,
        hand_strength=decision.hand_strength,
        reasoning=decision.reasoning
    )

    print(f"  After action: stack={current_player.stack}, current_bet={current_player.current_bet}, game.current_bet={game.current_bet}, pot={game.pot}")

    # Check if round complete
    if game._betting_round_complete():
        print("  Betting round COMPLETE")
        break

    # Move to next player
    game.current_player_index = game._get_next_active_player_index(game.current_player_index + 1)

# Now human goes all-in
print("\n" + "="*80)
print("HUMAN GOES ALL-IN")
print("="*80)
print(f"Human stack before all-in: {human_player.stack}")
all_in_amount = human_player.stack

result = game.apply_action(
    player_index=human_index,
    action="raise",
    amount=all_in_amount
)

print(f"Applied action result: {result}")
print(f"\nAfter human all-in:")
print(f"  Human: stack={human_player.stack}, current_bet={human_player.current_bet}, all_in={human_player.all_in}, has_acted={human_player.has_acted}")
print(f"  Game: current_bet={game.current_bet}, pot={game.pot}")
print(f"  Current player index: {game.current_player_index}")

# Check betting round complete
print(f"\nBetting round complete? {game._betting_round_complete()}")

# Analyze why
active_players = [p for p in game.players if p.is_active and not p.all_in]
all_active_players = [p for p in game.players if p.is_active]

print(f"\nActive non-all-in players: {len(active_players)}")
for p in active_players:
    print(f"  {p.name}: has_acted={p.has_acted}, current_bet={p.current_bet}, game.current_bet={game.current_bet}")

print(f"\nAll active players (including all-in): {len(all_active_players)}")
for p in all_active_players:
    print(f"  {p.name}: all_in={p.all_in}, has_acted={p.has_acted}, current_bet={p.current_bet}")

# Check the specific logic
if len(active_players) == 0:
    print("\n→ Should be complete: 0 active non-all-in players")
elif len(active_players) == 1:
    if len(all_active_players) > 1:
        print(f"\n→ One player left, but others are all-in. Betting complete? {active_players[0].has_acted}")
    else:
        print("\n→ Should be complete: Only one player left, others folded")
else:
    print(f"\n→ {len(active_players)} active players, checking if all have acted and matched bet...")
    for p in active_players:
        if not p.has_acted:
            print(f"  {p.name} has NOT acted yet")
        if p.current_bet != game.current_bet:
            print(f"  {p.name} current_bet ({p.current_bet}) != game.current_bet ({game.current_bet})")
