"""
AI-Only Game Test: 4 AI players compete until 1 winner remains
Tests game flow, decision validity, and reasoning consistency
"""
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame, GameState

# Log file for detailed decision tracking
LOG_FILE = "ai_game_decisions.log"

def log(message, to_file=True, to_console=True):
    """Log to both file and console."""
    if to_console:
        print(message)
    if to_file:
        with open(LOG_FILE, 'a') as f:
            f.write(message + '\n')

def check_decision_validity(decision):
    """
    Basic sanity checks for AI decisions.
    Returns (is_valid, error_messages)
    """
    errors = []

    # 1. Action validity
    if decision.action not in ['fold', 'call', 'raise']:
        errors.append(f"Invalid action: {decision.action}")

    # 2. Basic amount checks
    if decision.action == 'fold' and decision.amount != 0:
        errors.append(f"Fold should have amount=0, got {decision.amount}")

    if decision.amount < 0:
        errors.append(f"Negative amount: {decision.amount}")

    # 3. Required fields present
    if not decision.reasoning:
        errors.append("Missing reasoning")

    return len(errors) == 0, errors

def play_ai_only_game(game_number):
    """
    Play one complete game with 4 AI players until 1 winner remains.
    Returns winner name and game statistics.
    """
    log(f"\n{'='*80}")
    log(f"GAME {game_number}: Starting AI-Only Game")
    log(f"{'='*80}")

    # Create game with 4 AI players (no human)
    # We'll modify the game to have all AI players
    game = PokerGame("AI Player 1")  # Temp human

    # Convert all players to AI
    for i, player in enumerate(game.players):
        player.is_human = False
        if i == 0:
            player.name = "AI Conservative"
            player.personality = "Conservative"
        elif i == 1:
            player.name = "AI Aggressive"
            player.personality = "Aggressive"
        elif i == 2:
            player.name = "AI Mathematical"
            player.personality = "Mathematical"
        else:
            player.name = "AI Conservative 2"
            player.personality = "Conservative"

    # Game statistics
    stats = {
        'hands_played': 0,
        'decisions_made': 0,
        'validations_passed': 0,
        'validations_failed': 0,
        'errors': []
    }

    # Play until only 1 player has chips
    max_hands = 100  # Safety limit
    hand_num = 0

    while hand_num < max_hands:
        # Count players with chips
        players_with_chips = [p for p in game.players if p.stack > 0]
        if len(players_with_chips) <= 1:
            log(f"\nGame Over! Winner: {players_with_chips[0].name if players_with_chips else 'No winner'}")
            log(f"Total hands played: {hand_num}")
            break

        hand_num += 1
        stats['hands_played'] = hand_num

        log(f"\n--- Hand {hand_num} ---")
        log(f"Players:")
        for p in game.players:
            if p.stack > 0:
                log(f"  {p.name}: ${p.stack}")

        # Start new hand
        game.start_new_hand()

        log(f"\nPre-flop (Pot: ${game.pot}, Current Bet: ${game.current_bet})")

        # Play through the hand
        max_iterations = 200
        iterations = 0

        while game.current_state != GameState.SHOWDOWN and iterations < max_iterations:
            iterations += 1

            # Capture decisions made before processing
            decisions_before = set(game.last_ai_decisions.keys())

            # Process AI actions
            game._process_remaining_actions()

            # Check for new decisions
            new_decisions = {pid: decision for pid, decision in game.last_ai_decisions.items()
                           if pid not in decisions_before}

            # Log and validate new decisions
            for player_id, decision in new_decisions.items():
                stats['decisions_made'] += 1

                # Find the player
                player = next((p for p in game.players if p.player_id == player_id), None)
                if not player:
                    continue

                # Log decision with full context for manual review
                log(f"\n  {player.name} ({game.current_state.value}):")
                log(f"    Cards: {player.hole_cards}, Community: {game.community_cards}")
                log(f"    Stack: ${player.stack}, Bet: ${player.current_bet}, Pot: ${game.pot}, Current Bet: ${game.current_bet}")
                log(f"    Decision: {decision.action.upper()} ${decision.amount}")
                log(f"    SPR: {decision.spr:.2f}, Pot Odds: {decision.pot_odds:.1%}, Hand Strength: {decision.hand_strength:.1%}, Confidence: {decision.confidence:.1%}")
                log(f"    Reasoning: {decision.reasoning}")

                # Basic sanity checks only (not state-dependent validation)
                is_valid, errors = check_decision_validity(decision)

                if is_valid:
                    stats['validations_passed'] += 1
                else:
                    stats['validations_failed'] += 1
                    log(f"    ⚠️  SANITY CHECK FAILED: {errors}", to_console=True, to_file=True)
                    stats['errors'].extend(errors)

            # Advance game state
            game._maybe_advance_state()

            # Log state transitions
            if game.current_state == GameState.FLOP and iterations == 1:
                log(f"\n  Flop: {game.community_cards[:3]}")
            elif game.current_state == GameState.TURN:
                log(f"\n  Turn: {game.community_cards[3]}")
            elif game.current_state == GameState.RIVER:
                log(f"\n  River: {game.community_cards[4]}")

        # Showdown
        if game.current_state == GameState.SHOWDOWN:
            results = game.get_showdown_results()
            log(f"\nShowdown Results:")
            for pot in results['pots']:
                log(f"  Pot ${pot['amount']}: Winners = {pot['winners']}")

            # Verify chip conservation
            total_chips = sum(p.stack for p in game.players) + game.pot
            if total_chips != 4000:
                error_msg = f"❌ CHIP CONSERVATION FAILED: Total = ${total_chips}, Expected = $4000"
                log(error_msg)
                stats['errors'].append(error_msg)
        else:
            error_msg = f"❌ Hand {hand_num} did not reach showdown (stuck at {game.current_state.value})"
            log(error_msg)
            stats['errors'].append(error_msg)

    # Final standings
    log(f"\n{'='*80}")
    log(f"GAME {game_number} COMPLETE")
    log(f"{'='*80}")
    log(f"Final Standings:")
    sorted_players = sorted(game.players, key=lambda p: p.stack, reverse=True)
    for i, p in enumerate(sorted_players):
        log(f"  {i+1}. {p.name}: ${p.stack}")

    winner = sorted_players[0] if sorted_players[0].stack > 0 else None

    return winner, stats

def test_ai_only_tournament():
    """Run 5 complete AI-only games and validate all decisions."""

    # Clear log file
    with open(LOG_FILE, 'w') as f:
        f.write(f"AI-Only Game Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")

    print("\n" + "="*80)
    print("AI-ONLY TOURNAMENT: 5 Games, 4 AI Players Each")
    print("="*80)

    tournament_stats = {
        'games_completed': 0,
        'total_hands': 0,
        'total_decisions': 0,
        'total_validations_passed': 0,
        'total_validations_failed': 0,
        'all_errors': [],
        'winners': []
    }

    # Play 5 games
    for game_num in range(1, 6):
        try:
            winner, stats = play_ai_only_game(game_num)

            tournament_stats['games_completed'] += 1
            tournament_stats['total_hands'] += stats['hands_played']
            tournament_stats['total_decisions'] += stats['decisions_made']
            tournament_stats['total_validations_passed'] += stats['validations_passed']
            tournament_stats['total_validations_failed'] += stats['validations_failed']
            tournament_stats['all_errors'].extend(stats['errors'])
            tournament_stats['winners'].append(winner.name if winner else "No winner")

        except Exception as e:
            error_msg = f"❌ Game {game_num} crashed: {str(e)}"
            log(error_msg)
            tournament_stats['all_errors'].append(error_msg)
            import traceback
            log(traceback.format_exc())

    # Tournament Summary
    log(f"\n\n{'='*80}")
    log(f"TOURNAMENT SUMMARY")
    log(f"{'='*80}")
    log(f"Games Completed: {tournament_stats['games_completed']}/5")
    log(f"Total Hands Played: {tournament_stats['total_hands']}")
    log(f"Total Decisions Made: {tournament_stats['total_decisions']}")
    log(f"Validations Passed: {tournament_stats['total_validations_passed']}")
    log(f"Validations Failed: {tournament_stats['total_validations_failed']}")
    log(f"\nWinners:")
    for i, winner in enumerate(tournament_stats['winners'], 1):
        log(f"  Game {i}: {winner}")

    if tournament_stats['all_errors']:
        log(f"\n❌ SANITY CHECK FAILURES ({len(tournament_stats['all_errors'])}):")
        for i, error in enumerate(tournament_stats['all_errors'][:20], 1):  # Limit to first 20
            log(f"  {i}. {error}")
        if len(tournament_stats['all_errors']) > 20:
            log(f"  ... and {len(tournament_stats['all_errors']) - 20} more errors")
    else:
        log(f"\n✅ ALL SANITY CHECKS PASSED! All decisions have valid format.")

    log(f"\n📋 MANUAL REVIEW REQUIRED:")
    log(f"   Review {LOG_FILE} to verify decisions follow poker rules")
    log(f"   Check: SPR usage, pot odds reasoning, action consistency")
    log(f"\nDetailed log saved to: {LOG_FILE}")
    log(f"{'='*80}\n")

    # Assertions for test pass/fail
    assert tournament_stats['games_completed'] == 5, f"Only {tournament_stats['games_completed']} games completed"
    assert tournament_stats['total_validations_failed'] == 0, f"{tournament_stats['total_validations_failed']} sanity checks failed"
    assert len(tournament_stats['all_errors']) == 0, f"{len(tournament_stats['all_errors'])} errors found"

    print("\n✅ ALL AI-ONLY GAMES COMPLETED!")
    print(f"📋 Review {LOG_FILE} for poker rules consistency")

if __name__ == "__main__":
    test_ai_only_tournament()
