# Phase 3 - User Acceptance Testing (UAT)

Manual verification to confirm the Next.js frontend works correctly with the FastAPI backend.

## Prerequisites

**Start both servers:**

Terminal 1:
```bash
cd backend
python main.py
```

Terminal 2:
```bash
cd frontend
npm run dev
```

**Verify servers:**
- Backend: http://localhost:8000 → `{"status":"ok",...}`
- Frontend: http://localhost:3000 → Welcome screen

---

## Quick Smoke Test (5 minutes)

1. Open http://localhost:3000
2. Enter name, select 3 AI opponents
3. Click "Start Game"
4. Play one complete hand (call to showdown)
5. Click "Next Hand"
6. Try fold, call, and raise actions

✅ All 6 steps work = Basic functionality confirmed

---

## Complete UAT Tests

### UAT-1: Welcome Screen & Game Creation ✓
- [ ] Welcome screen displays correctly
- [ ] Player name input works
- [ ] AI opponent selection works
- [ ] "Start Game" creates game successfully
- [ ] No console errors

### UAT-2: Poker Table Layout ✓
- [ ] 3 AI players displayed (top row)
- [ ] Community cards area (center)
- [ ] Pot display visible
- [ ] Human player (bottom)
- [ ] All UI elements render correctly

### UAT-3: Game State & Turn Indicator ✓
- [ ] Game state displayed (PRE_FLOP, FLOP, TURN, RIVER, SHOWDOWN)
- [ ] Current player has yellow border
- [ ] Turn indicator animates between players

### UAT-4: Action Buttons & Human Turn ✓
- [ ] Fold button works
- [ ] Call button works (shows correct amount)
- [ ] Raise button works (validates minimum)
- [ ] Actions update game state correctly

### UAT-5: AI Decision Reasoning ✓
- [ ] AI reasoning appears after actions
- [ ] Shows action, amount, reasoning
- [ ] Shows SPR, pot odds, hand strength
- [ ] Beginner/Expert mode toggle works

### UAT-6: Community Cards & Game Progression ✓
- [ ] Flop: 3 cards appear
- [ ] Turn: 4th card appears
- [ ] River: 5th card appears
- [ ] Showdown: All AI cards revealed

### UAT-7: Showdown & Next Hand ✓
- [ ] Showdown reveals all cards
- [ ] "Next Hand" button appears
- [ ] New hand deals fresh cards
- [ ] Stacks update correctly

### UAT-8: Chip Conservation ✓
- [ ] Total chips always = $4000
- [ ] Blinds deducted correctly
- [ ] Pot calculation accurate
- [ ] Winners receive pot

### UAT-9: Animations & Visual Feedback ✓
- [ ] Cards animate smoothly
- [ ] Turn indicator pulses
- [ ] Pot badge animates
- [ ] No janky animations

### UAT-10: Error Handling ✓
- [ ] Invalid raises rejected
- [ ] Errors display in red banner
- [ ] Clear error messages
- [ ] App doesn't crash

---

## Sign-Off

Phase 3 Status: ✅ APPROVED / ❌ NEEDS WORK

Tested by: _______________
Date: _______________

Ready for Production: YES / NO

---

See full UAT details in project documentation.
