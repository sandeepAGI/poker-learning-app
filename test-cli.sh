#!/bin/bash
# Poker Learning App - CLI Test Script

echo "================================================"
echo "POKER LEARNING APP - CLI TEST"
echo "================================================"
echo ""

# 1. Check backend health
echo "1. Testing Backend Health..."
curl -s http://localhost:8000/ | python -m json.tool
echo ""

# 2. Create a new game
echo "2. Creating New Game..."
GAME_ID=$(curl -s -X POST http://localhost:8000/games \
  -H "Content-Type: application/json" \
  -d '{"player_name":"CLIPlayer","ai_count":3}' | python -c "import sys, json; print(json.load(sys.stdin)['game_id'])")

echo "Game ID: $GAME_ID"
echo ""

# 3. Get initial game state
echo "3. Getting Initial Game State..."
curl -s http://localhost:8000/games/$GAME_ID | python -m json.tool | head -50
echo ""

# 4. Make a decision (let's call)
echo "4. Human Player Action: CALL"
curl -s -X POST http://localhost:8000/games/$GAME_ID/actions \
  -H "Content-Type: application/json" \
  -d '{"action":"call"}' | python -m json.tool | head -80
echo ""

echo "================================================"
echo "Test Complete! Game is now at FLOP/TURN"
echo "================================================"
echo ""
echo "To see full game state:"
echo "  curl -s http://localhost:8000/games/$GAME_ID | python -m json.tool"
echo ""
echo "To make another action:"
echo "  curl -s -X POST http://localhost:8000/games/$GAME_ID/actions -H 'Content-Type: application/json' -d '{\"action\":\"fold\"}'"
echo ""
