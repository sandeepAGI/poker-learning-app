# User Acceptance Testing (UAT) Plan

**Date**: December 7, 2025
**Version**: Post Bug-Fix (commit b49d457f)
**Tester**: _______________

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
- Check WebSocket status shows "Connected" (green dot)

**Status**: [X] PASS  [ ] FAIL
**Notes**: Not sure where to see the "Connected" green dot.  Atleast it doesn'ts show in the signining page.

---

## Test Cases

### UAT-1: Game Creation
**Steps**:
1. Click "New Game" or start button
2. Select number of AI opponents (3)
3. Verify game loads with poker table

**Expected**: Game starts, you see your cards, AI players visible
**Status**: [ ] PASS  [X] FAIL
**Error Details**:
```
I choose only 1 AI player and the first thing that happened is a game got played, even before we could get started
```

---

### UAT-2: Basic Actions - Call
**Steps**:
1. Wait for your turn (yellow highlight)
2. Click "Call" button
3. Observe chips move to pot

**Expected**: Your bet is placed, turn advances to next player
**Status**: [ ] PASS  [ ] FAIL
**Error Details**:
```
(paste any errors here)
```

---

### UAT-3: Basic Actions - Fold
**Steps**:
1. On your turn, click "Fold"
2. Observe your cards gray out
3. **Verify game continues** (AI players keep acting)
4. Hand completes to showdown or last player wins

**Expected**: Game does NOT hang; hand completes correctly
**Status**: [ ] PASS  [ ] FAIL
**Error Details**:
```
(paste any errors here)
```

---

### UAT-4: Raise Slider UX (BUG FIX VERIFICATION)
**Steps**:
1. On your turn, look at the raise section
2. **Test slider**: Move it - should increment by big blind ($10)
3. **Test quick buttons**: Click "Min", "½ Pot", "Pot", "2x Pot"
4. **Test number input**: Type a specific amount (e.g., 75)
5. Click "Raise" button

**Expected**:
- Slider moves in $10 increments (not $1)
- Quick buttons set correct amounts
- Can type exact amount in input field
- Raise button shows amount: "Raise $XX"

**Status**: [ ] PASS  [ ] FAIL
**Error Details**:
```
(paste any errors here)
```

---

### UAT-5: All-In Button
**Steps**:
1. On your turn, click "All-In" button
2. Verify it bets your entire stack

**Expected**: All chips go to pot, you're marked as all-in
**Status**: [ ] PASS  [ ] FAIL
**Error Details**:
```
(paste any errors here)
```

---

### UAT-6: AI Actions Visible (Show AI Thinking)
**Steps**:
1. Click "Show AI Thinking" button in header
2. Observe AI players' turns
3. Look for reasoning text under each AI player

**Expected**: See AI decision reasoning (e.g., "High SPR - need premium hand")
**Status**: [ ] PASS  [ ] FAIL
**Error Details**:
```
(paste any errors here)
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

**Status**: [ ] PASS  [ ] FAIL
**Error Details**:
```
(paste any errors here)
```

---

### UAT-8: Multiple Hands (Chip Conservation)
**Steps**:
1. Note starting chip totals (should be $4,000 across all players)
2. Play 5+ hands
3. After each hand, verify total chips = $4,000

**How to check**: Add up all player stacks + pot (if mid-hand)

**Expected**: Total chips always = $4,000 (no chip creation/loss)
**Status**: [ ] PASS  [ ] FAIL
**Error Details**:
```
(paste any errors here)
```

---

### UAT-9: BB Option (Pre-flop Only)
**Steps**:
1. When you're the Big Blind, wait for all players to call
2. **Verify you get a chance to act** (raise or check)
3. This should only happen pre-flop

**Expected**: BB gets option to raise even when everyone just called
**Status**: [ ] PASS  [ ] FAIL
**Error Details**:
```
(paste any errors here)
```

---

### UAT-10: Console Error Check
**Steps**:
1. Open browser DevTools (F12 or Cmd+Option+I)
2. Go to Console tab
3. Play 3-5 hands
4. Check for any red errors

**Expected**: No errors, especially no "Infinity" JSON errors
**Status**: [ ] PASS  [ ] FAIL
**Error Details**:
```
(paste any console errors here)
```

---

### UAT-11: Hand Analysis
**Steps**:
1. Complete at least one hand
2. Click "Analyze Hand" button in header
3. Review the analysis modal

**Expected**: Shows analysis of last hand with recommendations
**Status**: [ ] PASS  [ ] FAIL
**Error Details**:
```
(paste any errors here)
```

---

### UAT-12: Quit Game
**Steps**:
1. During a game, click "Quit" button
2. Verify return to lobby/start screen

**Expected**: Game ends, returns to new game screen
**Status**: [ ] PASS  [ ] FAIL
**Error Details**:
```
(paste any errors here)
```

---

## Summary

| Test | Status | Notes |
|------|--------|-------|
| UAT-1: Game Creation | | |
| UAT-2: Call Action | | |
| UAT-3: Fold Action | | |
| UAT-4: Raise Slider UX | | |
| UAT-5: All-In Button | | |
| UAT-6: AI Thinking | | |
| UAT-7: Hand Completion | | |
| UAT-8: Chip Conservation | | |
| UAT-9: BB Option | | |
| UAT-10: Console Errors | | |
| UAT-11: Hand Analysis | | |
| UAT-12: Quit Game | | |

**Overall Result**: [ ] ALL PASS  [ ] HAS FAILURES

**Additional Notes**:
```
(any other observations, suggestions, or issues)
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
