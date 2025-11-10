#!/usr/bin/env python3
"""Quick test to reproduce the blind posting bug."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame

# Create game
game = PokerGame("Player", ai_count=3)

# Manually set stacks to reproduce issue: 2 busted, 2 with chips
game.players[0].stack = 0  # Player busted
game.players[1].stack = 1000  # AI-ce has chips
game.players[2].stack = 0  # AI-ron busted
game.players[3].stack = 1000  # AI-nstein has chips

print("Initial state:")
for i, p in enumerate(game.players):
    print(f"  P{i} {p.name}: ${p.stack}")

print(f"\nTotal chips: ${sum(p.stack for p in game.players)}")
print(f"Expected: $2000\n")

# Try to start new hand
try:
    game.start_new_hand()
    print(f"After start_new_hand():")
    for i, p in enumerate(game.players):
        print(f"  P{i} {p.name}: ${p.stack}, current_bet=${p.current_bet}")
    print(f"Pot: ${game.pot}")
    print(f"Total chips: ${sum(p.stack for p in game.players) + game.pot}")
except Exception as e:
    print(f"ERROR: {e}")
