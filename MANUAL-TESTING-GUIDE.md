# Manual Testing Guide - Phase A+B Fixes
**Servers Running**:
- 🟢 Backend: http://localhost:8000
- 🟢 Frontend: http://localhost:3000

---

## Quick Start

### Option 1: Test via Frontend (Easiest)
1. Open browser: **http://localhost:3000**
2. Create a game
3. Play poker and observe the fixes

### Option 2: Test via API (More Control)
Use the curl commands below to test specific fixes

---

## Test Scenarios for Each Fix

### ✅ Test Fix A1: BB Option Not Honored

**What to Test**: Big Blind gets option to raise when everyone calls

**Via Frontend**:
1. Open http://localhost:3000
2. Create game
3. Watch pre-flop action closely
4. When all players call to BB, verify BB acts again
5. **Expected**: BB should get to act (call or raise)

**Via API**:
```bash
# Create game
GAME_ID=$(curl -s -X POST http://localhost:8000/games \
  -H "Content-Type: application/json" \
  -d '{"player_name": "TestPlayer", "ai_count": 3}' | jq -r '.game_id')

echo "Game ID: $GAME_ID"

# Get game state and watch for BB acting multiple times in pre-flop
curl -s http://localhost:8000/games/$GAME_ID | jq '.state, .current_player_index, .players[] | select(.name | contains("Mathematical")) | {name, current_bet, is_active}'
```

**What to Look For**:
- BB (AI Mathematical) should have `has_acted: true` after pre-flop
- BB should act even when all others just called
- Pre-flop should complete properly

---

### ✅ Test Fix A2: API Crashes When All-In

**What to Test**: API returns valid response when all players all-in (not 500 error)

**Via API** (Force all-in scenario):
```bash
# This would require manipulating game state
# Simpler: Just check that current_player_index can be null
curl -s http://localhost:8000/games/$GAME_ID | jq '.current_player_index'

# Should return either a number or null (not crash)
```

**What to Look For**:
- API returns 200 (not 500)
- `current_player_index` field accepts null
- No Pydantic validation errors

---

### ✅ Test Fix A3: All-Fold Bug

**What to Test**: Pot is awarded (not lost) when all players fold

**This is extremely rare**, but the fix ensures chip conservation.

**What to Look For**:
- Total chips always = $4000 across all players
- Pot never "disappears"

---

### ✅ Test Fix B1: Duplicate File Deleted

**What to Test**: Only correct poker_engine.py exists

**Via Terminal**:
```bash
# This should only show one file (in game/)
find /home/user/poker-learning-app -name "poker_engine.py" -type f

# Expected output:
# /home/user/poker-learning-app/backend/game/poker_engine.py
# (NOT: /home/user/poker-learning-app/backend/poker_engine.py)
```

**What to Look For**:
- Only ONE poker_engine.py file exists
- It's in the game/ directory
- It has 846 lines (not 572)

---

### ✅ Test Fix B2: Memory Leaks

**What to Test**:
1. Hand events capped at 1000
2. Old games cleaned up after 1 hour idle

**Test Hand Events Cap**:
```bash
# Play 50 hands and check memory doesn't grow unbounded
# (This would require a longer test session)
```

**Test Game Cleanup**:
```bash
# Create game
GAME_ID=$(curl -s -X POST http://localhost:8000/games \
  -H "Content-Type: application/json" \
  -d '{"player_name": "TestPlayer"}' | jq -r '.game_id')

# Game should exist
curl -s http://localhost:8000/games/$GAME_ID | jq '.game_id'

# After 1 hour of inactivity, game would be cleaned up
# (Can't test easily without waiting, but check logs)
```

**What to Look For**:
- Backend logs show: `[Startup] Periodic game cleanup enabled (every 300s, max idle 3600s)`
- No memory growing unbounded
- Games are stored with timestamps

---

### ✅ Test Fix B3: Player Count Dynamic

**What to Test**: API honors ai_count parameter (1, 2, or 3 AI)

**Via API**:
```bash
# Test with 1 AI opponent
GAME_1=$(curl -s -X POST http://localhost:8000/games \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Test1", "ai_count": 1}' | jq -r '.game_id')

curl -s http://localhost:8000/games/$GAME_1 | jq '.players | length'
# Expected: 2 (1 human + 1 AI)

# Test with 2 AI opponents
GAME_2=$(curl -s -X POST http://localhost:8000/games \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Test2", "ai_count": 2}' | jq -r '.game_id')

curl -s http://localhost:8000/games/$GAME_2 | jq '.players | length'
# Expected: 3 (1 human + 2 AI)

# Test with 3 AI opponents (default)
GAME_3=$(curl -s -X POST http://localhost:8000/games \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Test3", "ai_count": 3}' | jq -r '.game_id')

curl -s http://localhost:8000/games/$GAME_3 | jq '.players | length'
# Expected: 4 (1 human + 3 AI)
```

**What to Look For**:
- Game with ai_count=1 has 2 total players
- Game with ai_count=2 has 3 total players
- Game with ai_count=3 has 4 total players

---

## Full Game Test (All Fixes)

**Complete Test Script**:
```bash
#!/bin/bash

echo "=== Testing All Fixes ==="

# Create game
echo -e "\n1. Creating game..."
GAME_ID=$(curl -s -X POST http://localhost:8000/games \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Tester", "ai_count": 3}' | jq -r '.game_id')
echo "Game ID: $GAME_ID"

# Get initial state
echo -e "\n2. Initial state:"
curl -s http://localhost:8000/games/$GAME_ID | jq '{
  state,
  pot,
  current_bet,
  current_player_index,
  player_count: (.players | length)
}'

# Submit human action (call)
echo -e "\n3. Human calls..."
curl -s -X POST http://localhost:8000/games/$GAME_ID/actions \
  -H "Content-Type: application/json" \
  -d '{"action": "call"}' | jq '{state, pot, current_bet}'

# Get updated state
echo -e "\n4. After human call:"
curl -s http://localhost:8000/games/$GAME_ID | jq '{
  state,
  pot,
  current_player_index,
  bb_player: (.players[] | select(.name | contains("Mathematical")))
}'

# Verify chip conservation
echo -e "\n5. Chip conservation:"
curl -s http://localhost:8000/games/$GAME_ID | jq '
  .players | map(.stack) | add as $total_stacks |
  ($total_stacks + .pot) as $total_chips |
  {
    total_stacks: $total_stacks,
    pot: .pot,
    total_chips: $total_chips,
    should_be: 4000
  }' | jq '. + {pot: 0}'  # Adjust for actual pot

echo -e "\n=== All Tests Complete ==="
```

**Run it**:
```bash
chmod +x test-all-fixes.sh
./test-all-fixes.sh
```

---

## What to Look For (Summary)

### ✅ Fix A1 (BB Option)
- BB acts after everyone calls pre-flop
- No premature betting round completion

### ✅ Fix A2 (All-In Crash)
- API returns 200 (not 500)
- `current_player_index` can be null

### ✅ Fix A3 (All-Fold)
- Total chips = $4000 always
- Pot never disappears

### ✅ Fix B1 (Duplicate File)
- Only one poker_engine.py exists
- In game/ directory

### ✅ Fix B2 (Memory Leaks)
- Cleanup task running (check logs)
- Memory doesn't grow unbounded

### ✅ Fix B3 (Player Count)
- ai_count=1 → 2 players
- ai_count=2 → 3 players
- ai_count=3 → 4 players

---

## Troubleshooting

### Backend not responding
```bash
# Check if running
curl http://localhost:8000/

# Restart if needed
pkill -f "python main.py"
cd backend && python main.py
```

### Frontend not loading
```bash
# Check if running
curl http://localhost:3000/

# Restart if needed
cd frontend && npm run dev
```

### View logs
```bash
# Backend logs
tail -f /tmp/backend.log

# Frontend logs
tail -f /tmp/frontend.log
```

---

## Quick API Reference

### Create Game
```bash
curl -X POST http://localhost:8000/games \
  -H "Content-Type: application/json" \
  -d '{"player_name": "YourName", "ai_count": 3}'
```

### Get Game State
```bash
curl http://localhost:8000/games/{GAME_ID}
```

### Submit Action
```bash
# Fold
curl -X POST http://localhost:8000/games/{GAME_ID}/actions \
  -H "Content-Type: application/json" \
  -d '{"action": "fold"}'

# Call
curl -X POST http://localhost:8000/games/{GAME_ID}/actions \
  -H "Content-Type: application/json" \
  -d '{"action": "call"}'

# Raise
curl -X POST http://localhost:8000/games/{GAME_ID}/actions \
  -H "Content-Type: application/json" \
  -d '{"action": "raise", "amount": 20}'
```

### Next Hand
```bash
curl -X POST http://localhost:8000/games/{GAME_ID}/next
```

---

**Servers Running**:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

**Both servers are LIVE and ready for testing!**
