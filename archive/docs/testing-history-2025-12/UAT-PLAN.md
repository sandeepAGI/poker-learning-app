# User Acceptance Testing (UAT) Plan

**Date**: December 8, 2025
**Version**: 3.3 (Post All-In & Analysis Bug Fixes)
**Tester**: Sandeep

---

## Bugs Fixed Since Last UAT

| Bug | Description | Fix Applied | Status |
|-----|-------------|-------------|--------|
| Bug #9 | Game starts with completed hand (1-2 players) | Use `process_ai=False` in game creation | **FIXED** |
| Bug #10 | Game hangs after all-in elimination | Added `isWaitingAllIn` state, fixed `isEliminated` logic | **FIXED** |
| UAT-11 | Analysis shows player indices (0,1,2) instead of names | Fixed array iteration in AnalysisModal | **FIXED** |
| All-In UI | Shows "Game Over" immediately when going all-in | Fixed `isEliminated` to check `all_in` flag | **FIXED** |

### Test Coverage
- 32 critical backend tests passing
- 178,060 property-based checks passing (1,000 scenarios)
- 21 new tests added for all-in scenarios, game start, and analysis
- Frontend build verified

---

## Pre-Test Setup

### Start Backend
```bash
cd backend && python main.py
```
**Status**: [X] PASS  [ ] FAIL
**Notes**: _________________________________________________

### Start Frontend
```bash
cd frontend && npm run dev
```
**Status**: [X] PASS  [ ] FAIL
**Notes**: _________________________________________________

### Verify Connection
- Open http://localhost:3000
- Check WebSocket status shows "Connected" (green dot) after starting game

**Status**: [X] PASS  [ ] FAIL
**Notes**: _________________________________________________

---

## Test Cases

### UAT-1: Game Creation (BUG #9 FIX VERIFICATION)
**Steps**:
1. Click "New Game" or start button
2. **Test with 1 AI opponent** (heads-up)
3. **Test with 2 AI opponents**
4. **Test with 3 AI opponents**
5. Verify game starts in PRE_FLOP state (not showdown)

**Expected**:
- Game starts with cards dealt
- You see your hole cards
- Game does NOT start at showdown
- Current player is set (either you or AI)

**Status**: [ ] PASS  [X] FAIL
**Notes**:
```
Again, for 1 and 2 players it goes straight to showdown but I know why it is happening.  It is because the AI player is losing and folds but as the game play is very fast, you see Player winning.  I think we need to think of what we want to do here - maybe drop having 1 or 2 player option?
```
---

### UAT-2: Basic Actions - Call
**Steps**:
1. Wait for your turn (yellow highlight)
2. Click "Call" button
3. Observe chips move to pot

**Expected**: Your bet is placed, turn advances to next player
**Status**: [X] PASS  [ ] FAIL
**Notes**:
```
```

---

### UAT-3: Basic Actions - Fold
**Steps**:
1. On your turn, click "Fold"
2. Observe your cards gray out
3. **Verify game continues** (AI players keep acting OR winner announced)
4. Hand completes to showdown or last player wins

**Expected**: Game does NOT hang; hand completes correctly
**Status**: [X] PASS  [ ] FAIL
**Notes**:
```
```

---

### UAT-4: Raise Slider UX
**Steps**:
1. On your turn, look at the raise section
2. **Test slider**: Move it - should increment by big blind ($10)
3. **Test quick buttons**: Click "Min", "1/2 Pot", "Pot", "2x Pot"
4. **Test number input**: Type a specific amount (e.g., 75)
5. Click "Raise" button

**Expected**:
- Slider moves in $10 increments
- Quick buttons set correct amounts
- Can type exact amount in input field
- Raise button shows amount: "Raise $XX"

**Status**: [X] PASS  [ ] FAIL
**Notes**:
```
```

---

### UAT-5: All-In Flow (BUG #10 FIX VERIFICATION)
**Steps**:
1. On your turn, click "All-In" button
2. **Verify "All-In! Waiting..." message appears** (not "Game Over")
3. Watch AI players respond
4. If opponent(s) match, game advances to showdown
5. Winner is announced with chips awarded

**Scenario A - You Win**:
- Winner modal shows
- Your stack increases
- "Next Hand" button appears

**Scenario B - You Lose** (BUG #10 specific):
- Winner modal shows who won
- "Game Over" message appears AFTER showdown (not during)
- "New Game" button is available
- Game does NOT hang

**Expected**: Clean flow from all-in to showdown to result
**Status**: [ ] PASS  [X] FAIL
**Notes**:
```
I went all in and so did 2 other players and then it hung

3ad
[WebSocket] Received: {'type': 'next_hand', 'show_ai_thinking': False}
[WebSocket] Client disconnected from game 07dcedb2-319c-4d39-b845-724fba5533ad
[WebSocket] Client disconnected from game 07dcedb2-319c-4d39-b845-724fba5533ad
INFO:     connection closed
INFO:     127.0.0.1:52035 - "POST /games HTTP/1.1" 200 OK
INFO:     ('127.0.0.1', 52037) - "WebSocket /ws/4f2604a7-3bc6-4d4e-ad4c-dc2d0a147428" [accepted]
[WebSocket] Client connected to game 4f2604a7-3bc6-4d4e-ad4c-dc2d0a147428
INFO:     connection open
[WebSocket] Client connected to game 4f2604a7-3bc6-4d4e-ad4c-dc2d0a147428, awaiting actions...
[WebSocket] Received: {'type': 'action', 'action': 'raise', 'amount': 1000, 'show_ai_thinking': False}
[WebSocket] Processing AI turns for game 4f2604a7-3bc6-4d4e-ad4c-dc2d0a147428
[WebSocket] Processing AI turn: AI-ce
[WebSocket] Processing AI turn: Lady Luck
[WebSocket] Processing AI turn: AI-nstein
[WebSocket] Betting round complete, advancing state
[WebSocket] AI turn processing complete for game 4f2604a7-3bc6-4d4e-ad4c-dc2d0a147428


```

---

### UAT-6: AI Actions Visible (Show AI Thinking)
**Steps**:
1. Click "Show AI Thinking" button in header
2. Observe AI players' turns
3. Look for reasoning text under each AI player

**Expected**: See AI decision reasoning (e.g., "High SPR - need premium hand")
**Status**: [X] PASS  [ ] FAIL
**Notes**:
```
But to be honest, not very helpful.  Maybe this is not a good functionality to have as AI players move quickly.  Maybe have the human have an ability to pause between AI players?
```

---

### UAT-7: Hand Completion & Next Hand
**Steps**:
1. Play through a complete hand to showdown
2. Verify winner announced
3. Click "Next Hand" button
4. Verify new hand starts

**Expected**:
- Winner modal shows
- Chips awarded correctly
- Next hand deals new cards
- No JSON errors in console

**Status**: [X] PASS  [ ] FAIL
**Notes**:
```
```

---

### UAT-8: Multiple Hands (Chip Conservation)
**Steps**:
1. Note starting chip totals ($1000 per player)
2. Play 5+ hands
3. After each hand, verify total chips are conserved

**How to check**: Add up all player stacks + pot (if mid-hand)

**Expected**: Total chips always conserved (no chip creation/loss)
**Status**: [X] PASS  [ ] FAIL
**Notes**:
```
```

---

### UAT-9: BB Option (Pre-flop Only)
**Steps**:
1. When you're the Big Blind, wait for all players to call
2. **Verify you get a chance to act** (raise or check)
3. This should only happen pre-flop

**Expected**: BB gets option to raise even when everyone just called
**Status**: [X] PASS  [ ] FAIL
**Notes**:
```
```

---

### UAT-10: Console Error Check
**Steps**:
1. Open browser DevTools (F12 or Cmd+Option+I)
2. Go to Console tab
3. Play 3-5 hands
4. Check for any red errors

**Expected**: No errors, especially no "Infinity" JSON errors
**Status**: [X] PASS  [ ] FAIL
**Notes**:
```
```

---

### UAT-11: Hand Analysis (BUG FIX VERIFICATION)
**Steps**:
1. Complete at least one hand
2. Click "Analyze Hand" button in header
3. Review the analysis modal

**Verify these specific fixes**:
- [ ] AI player names shown (e.g., "Binary Bob", "Call Carl") - NOT indices (0, 1, 2)
- [ ] Each AI shows their personality in parentheses
- [ ] Hand strength and confidence percentages displayed
- [ ] Reasoning quotes shown for each AI

**Expected**:
- Shows AI names like "Binary Bob (Aggressive)"
- Shows hand strength percentages
- Shows reasoning quotes

**Status**: [ ] PASS  [X] FAIL
**Notes**:
```
Maybe a stabiity issues.  There were a number of games where I could not see it and then I did.  When it shows - all good.
```

---

### UAT-12: Quit Game
**Steps**:
1. During a game, click "Quit" button
2. Verify return to lobby/start screen

**Expected**: Game ends, returns to new game screen
**Status**: [X] PASS  [ ] FAIL
**Notes**:
```
```

---

### UAT-13: Heads-Up All-In Scenario (NEW)
**Steps**:
1. Start a new game with **1 AI opponent only** (heads-up)
2. Go all-in on your first turn
3. Observe AI response
4. **Verify one of these outcomes**:
   - AI folds: You win, can start next hand
   - AI calls: Showdown occurs, winner announced

**Expected**: No hanging, no premature "Game Over"
**Status**: [X] PASS  [ ] FAIL
**Notes**:
```
```

---

## Summary

| Test | Status | Notes |
|------|--------|-------|
| UAT-1: Game Creation (Bug #9) | | |
| UAT-2: Call Action | | |
| UAT-3: Fold Action | | |
| UAT-4: Raise Slider UX | | |
| UAT-5: All-In Flow (Bug #10) | | |
| UAT-6: AI Thinking | | |
| UAT-7: Hand Completion | | |
| UAT-8: Chip Conservation | | |
| UAT-9: BB Option | | |
| UAT-10: Console Errors | | |
| UAT-11: Hand Analysis (Fixed) | | |
| UAT-12: Quit Game | | |
| UAT-13: Heads-Up All-In | | |

**Overall Result**: [ ] ALL PASS  [ ] HAS FAILURES

**Additional Notes**:
```
```

---

## Bug Report Template

If you find a bug, please fill out:

**Bug ID**: UAT-XX
**Severity**: [ ] Critical  [ ] High  [ ] Medium  [ ] Low
**Steps to Reproduce**:
1.
2.
3.

**Expected Behavior**:

**Actual Behavior**:

**Console Errors**:
```
(paste here)
```

**Screenshot**: (if applicable)
