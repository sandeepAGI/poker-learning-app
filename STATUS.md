# Poker Learning App - Current Status

**Last Updated**: December 9, 2025 (Evening)
**Version**: 4.2 (Testing Overhaul - Critical Bug Found)
**Branch**: `main`

---

## Current State

🚨 **CRITICAL BUG FOUND** - Testing strategy under review
- All 7 integration tests + 72 regression tests passing ✅
- **BUT**: User found infinite loop bug in <1 minute of testing ⚠️
- **Root cause**: Tests never validated error handling paths
- **Issue**: WebSocket AI processing doesn't check `apply_action()` success
- **Status**: Bug NOT yet fixed - analyzing root cause first

**Lesson Learned**: "All tests passing" ≠ "No bugs exist"

**Next Steps**: Execute comprehensive testing improvement plan
- See `docs/TESTING_IMPROVEMENT_PLAN.md` for 6-phase plan
- See `docs/TESTING_FAILURES_ANALYSIS.md` for root cause analysis
- See `docs/TESTING_PLAN_COMPARISON.md` for what previous plans missed

✅ **Phase 4 Refactoring COMPLETE** - Core consolidation done
- Core code consolidated into single sources of truth
- 59 unit tests + 350+ edge case tests + 600 stress tests all passing
- Engine-level logic is solid
- **Gap**: Integration layer (WebSocket/API) insufficiently tested

**Old testing docs archived** to `archive/docs/testing-history-2025-12/`

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

### Code Audit Findings (Archived)

Phase 4 refactoring addressed 9 code divergence issues:
- ✅ Consolidated action processing into `apply_action()`
- ✅ Consolidated state advancement into `_advance_state_core()`
- ✅ Consolidated hand strength calculation into `score_to_strength()`

**However**: Refactoring tests bypassed WebSocket layer, missing integration bugs.

Full details in `archive/docs/testing-history-2025-12/REFACTOR-PLAN.md`

---

## Phase 4 Refactoring: COMPLETE ✅ (But Testing Was Incomplete)

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Consolidate action processing (`apply_action()`) | ✅ DONE (20 tests) |
| 2 | Consolidate state advancement (`_advance_state_core()`) | ✅ DONE (15 tests) |
| 3 | Consolidate hand strength (`score_to_strength()`) | ✅ DONE (24 tests) |
| 4 | Comprehensive test suite | ⏸️ PARTIAL (engine-level only) |

**Test Coverage** (Engine-Level):
- Unit tests: 59/59 passing ✅
- Edge cases: 350+ scenarios ✅
- Stress tests: 600 complete games ✅
- Heads-up: 100 dedicated games ✅
- Multi-player: 100 4-player games ✅

**Missing Coverage** (Integration-Level):
- ❌ Negative testing (error handling paths)
- ❌ E2E testing (frontend → backend)
- ❌ Scenario testing (user journeys)
- ❌ Failure recovery testing

Details in `archive/docs/testing-history-2025-12/PHASE4_COMPLETE_SUMMARY.md`

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
# Quick smoke test (1 min)
PYTHONPATH=backend python -m pytest tests/test_stress_ai_games.py::TestStressAIGames::test_run_10_quick_games -v

# Phase 4 unit tests (instant)
PYTHONPATH=backend python -m pytest tests/test_action_processing.py tests/test_hand_strength.py tests/test_state_advancement.py tests/test_heads_up.py -v

# Edge case scenarios (instant)
PYTHONPATH=backend python -m pytest tests/test_edge_case_scenarios.py -v

# Comprehensive (50 min)
cd backend && python -m pytest tests/test_stress_ai_games.py::TestStressAIGames::test_run_500_ai_games_varied_players -v

# Multi-player intensive (19 min)
cd backend && python -m pytest tests/test_stress_ai_games.py::TestStressAIGames::test_run_multi_player_intensive -v
```
