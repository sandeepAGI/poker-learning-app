# Poker Learning App - Current Status

**Last Updated**: December 8, 2025
**Version**: 3.4 (Refactoring Phase)
**Branch**: `main`

---

## Current State

UAT Round 2 complete. Code audit identified 9 divergence issues. Entering refactoring phase.

### UAT Round 2 Results (December 8, 2025)

| Test | Status | Notes |
|------|--------|-------|
| UAT-1: Game Creation | FAIL | AI folds too fast with 1-2 players (design issue) |
| UAT-2: Call Action | PASS | |
| UAT-3: Fold Action | PASS | |
| UAT-4: Raise Slider UX | PASS | |
| UAT-5: All-In Flow | FAIL | Game hangs when multiple players go all-in |
| UAT-6: AI Thinking | PASS | But not very useful - AI moves too quickly |
| UAT-7: Hand Completion | PASS | |
| UAT-8: Chip Conservation | PASS | |
| UAT-9: BB Option | PASS | |
| UAT-10: Console Errors | PASS | |
| UAT-11: Hand Analysis | FAIL | Intermittent - sometimes doesn't show |
| UAT-12: Quit Game | PASS | |
| UAT-13: Heads-Up All-In | PASS | |

### Code Audit Findings

Found 9 code divergence issues between REST and WebSocket paths:

| Priority | Issue | Impact |
|----------|-------|--------|
| CRITICAL | Raise bet calculation differs | Pot grows incorrectly via WebSocket |
| CRITICAL | All-in fast-forward missing in WS | UAT-5 hang bug |
| HIGH | `last_raiser_index` not set in WS | BB option broken |
| HIGH | Fold doesn't set `has_acted` in WS | Potential infinite loop |
| HIGH | Hand strength has 4 copies (2 incomplete) | Wrong analysis |

Full details in [docs/REFACTOR-PLAN.md](docs/REFACTOR-PLAN.md).

---

## Next Steps: Refactoring Plan

See [docs/REFACTOR-PLAN.md](docs/REFACTOR-PLAN.md) for complete plan.

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Consolidate action processing (`apply_action()`) | Pending |
| 2 | Consolidate state advancement (`_advance_state_core()`) | Pending |
| 3 | Consolidate hand strength calculation | Pending |
| 4 | Implement Step Mode (UAT-1 fix) | Pending |
| 5 | Enhanced test suite | Pending |

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
