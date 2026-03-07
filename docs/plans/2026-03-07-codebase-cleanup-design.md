# Codebase Cleanup & Refactor Design

**Date:** 2026-03-07
**Branch:** refactor/codebase-cleanup
**Strategy:** Single refactor branch, merge once when complete

## Phases

### Phase 1: Safe Deletions (zero risk) -- COMPLETE (2026-03-07)

Commit: `e2b4832d` -- 4,918 lines deleted, 41/41 pre-commit tests pass.

| Target | Reason | Status |
|--------|--------|--------|
| `frontend/frontend/` | Empty nested dirs from bad deploy/copy | Removed (local) |
| `frontend-latest-logs/` | Azure deploy logs (1MB, not source) | Removed (local) |
| `backend/test_api_key.py` | One-off script, not part of test suite | git rm |
| `tests/e2e/` | Duplicate of `./e2e/` | git rm (52 files) |
| `.claude/worktrees/angry-stonebraker/` | Stale worktree | Removed (local) |
| `backend/venv/` | Virtual env committed to git | Already gitignored, not tracked |
| `frontend/.pytest_cache/` | Cache dir | Removed (local) |
| `frontend/.swc/` | SWC compiler cache | Removed (local), added to .gitignore |

### Phase 2: Increase Test Coverage on poker_engine.py -- COMPLETE (2026-03-07)

Commit: `07823424` -- 62 new boundary tests, 28 redundant tests removed, 9 fixed, 1 bug fix.

**New tests** (`test_extraction_boundaries.py`, 62 tests):
- DeckManager: reset (5), deal_cards (8)
- HandEvaluator: Monte Carlo eval (5), side pot edges (6)
- AIStrategy: amount capping (12), default fallback (3), last_raise (2), SPR (4), decision fields (5)
- Engine edge cases: call-as-check, showdown rejection, invalid actions (12)

**Broken test cleanup** (net -19 tests):
- Deleted `test_user_scenarios.py` (12 redundant)
- Deleted 16 redundant WebSocket/REST tests across 3 files
- Fixed auth in 9 unique WebSocket tests (JWT tokens)
- Added shared auth helpers to `conftest.py`
- Added `slow`/`monthly` marker filtering to `pytest.ini`

**Bug fix**: `create_game` now saves completed hands when AI finishes hand during `start_new_hand` (heads-up AI fold edge case).

**Result**: 421 passed, 0 failed (was 377 passed, 1 failed, 43 broken + 5 timeout)

### Phase 3: Extract Modules from poker_engine.py (2002 lines) -- COMPLETE (2026-03-07)

Extracted 466 lines into 3 new modules. `poker_engine.py` reduced to 1536 lines. All 421 tests pass.

- `backend/game/ai_strategy.py` (278 lines) — AIStrategy class + AIDecision dataclass
- `backend/game/hand_evaluator.py` (193 lines) — HandEvaluator class
- `backend/game/deck_manager.py` (23 lines) — DeckManager class
- `backend/game/__init__.py` — package init
- `poker_engine.py` keeps PokerGame + shared dataclasses, imports/re-exports from new modules

### Phase 4: Extract Routes from main.py (1505 lines) -- COMPLETE (2026-03-07)

Extracted 1087 lines into 3 route modules + shared state. `main.py` reduced to 422 lines. All 421 tests pass.

- `backend/routes/auth.py` (77 lines) — auth endpoints (register, login)
- `backend/routes/game.py` (528 lines) — game CRUD + action endpoints + hand history
- `backend/routes/analysis.py` (422 lines) — LLM analysis endpoints + metrics
- `backend/app_state.py` (130 lines) — shared state (games dict, caches, Pydantic models)
- `main.py` becomes app setup, CORS, WebSocket, router includes, test endpoints

### Phase 5: Verify Everything -- COMPLETE (2026-03-07)

- Full backend test suite: 421 passed, 0 failed (matches baseline)
- Frontend build: succeeds
- Frontend Jest tests: 54 passed (8 pre-existing Playwright-in-Jest failures unrelated)
- Property-based infinite loop guard: 6/6 passed

### Phase 6: Doc Consolidation (lowest priority)

- Audit 17 active docs, archive stale ones
- Flatten redundant archive subdirs
- Update docs/INDEX.md

## Key Decisions

- **poker_engine.py**: extract self-contained classes only (AIStrategy, HandEvaluator, DeckManager). Do NOT decompose PokerGame itself — test coverage too low.
- **main.py**: standard FastAPI router extraction pattern.
- **Test-first for Phase 3**: add boundary tests before extracting.
