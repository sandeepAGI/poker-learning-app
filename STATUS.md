# Poker Learning App - Current Status

**Last Updated**: December 8, 2025
**Version**: 3.3 (All-In & Analysis Bug Fixes)
**Branch**: `main`

---

## Current State

All UAT bugs fixed. Ready for UAT Round 2.

### Test Results (December 8, 2025)

| Test Suite | Result |
|------------|--------|
| Critical Backend Tests | 32 passed, 1 skipped |
| All-In Scenario Tests | 10 passed |
| Game Start Tests | 8 passed |
| Analysis Tests | 3 passed |
| Property-Based (1,000 scenarios) | 178,060 checks, 0 violations |

### Recent Fixes (December 8, 2025 - UAT Round 1)

| Bug | Issue | Fix |
|-----|-------|-----|
| Bug #9 | Game starts with completed hand (1-2 players) | Use `process_ai=False` in `create_game()` |
| Bug #10 | Game hangs after all-in elimination | Added `isWaitingAllIn` state, fixed `isEliminated` logic |
| All-In UI | "Game Over" shown immediately when going all-in | Fixed `isEliminated = stack === 0 && (!all_in \|\| isShowdown)` |
| UAT-11 | Analysis shows player indices (0,1,2) not names | Fixed array iteration in AnalysisModal |

### Previous Fixes (December 8, 2025 - WebSocket)

| Bug | Issue | Fix |
|-----|-------|-----|
| Bug #7 | Human fold doesn't trigger showdown | Added immediate showdown trigger |
| Bug #8 | Infinite loop when all players all-in | Added early return at SHOWDOWN |
| Betting Round | Incorrect with all-in players | Distinguished folded vs all-in |
| All-In Flag | Not cleared when winning pots | Added clearing in 8 locations |

---

## Architecture

### Backend (Python/FastAPI)
- `game/poker_engine.py` - Core game logic (~1650 lines)
- `main.py` - REST + WebSocket API
- `websocket_manager.py` - Real-time AI turn streaming

### Frontend (Next.js/TypeScript)
- `components/PokerTable.tsx` - Main game UI
- `components/AnalysisModal.tsx` - Hand analysis with AI names
- `lib/store.ts` - Zustand state management
- `lib/websocket.ts` - WebSocket client

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/games` | POST | Create new game |
| `/games/{id}` | GET | Get game state |
| `/games/{id}/actions` | POST | Submit action |
| `/games/{id}/next` | POST | Start next hand |
| `/games/{id}/analysis` | GET | Hand analysis |
| `/ws/{game_id}` | WS | Real-time updates |

---

## Quick Start

```bash
# Backend
cd backend && pip install -r requirements.txt
python main.py  # http://localhost:8000

# Frontend
cd frontend && npm install
npm run dev  # http://localhost:3000
```

---

## Running Tests

```bash
# Critical tests
cd backend && python -m pytest tests/test_turn_order.py tests/test_fold_resolution.py tests/test_bug_fixes.py tests/test_all_in_scenarios.py -v

# Property-based (1K scenarios)
PYTHONPATH=backend python tests/legacy/test_property_based.py

# All backend tests
python -m pytest backend/tests/ -v
```
