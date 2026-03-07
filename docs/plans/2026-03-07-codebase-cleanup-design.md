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

### Phase 2: Increase Test Coverage on poker_engine.py

Add targeted boundary tests for:
- AIStrategy decision logic (per personality)
- HandEvaluator edge cases
- DeckManager deal/reset

Goal: safe extraction in Phase 3, not 100% coverage.

### Phase 3: Extract Modules from poker_engine.py (2002 lines)

- `backend/game/ai_strategy.py` — AIStrategy class + personality logic
- `backend/game/hand_evaluator.py` — HandEvaluator class
- `backend/game/deck_manager.py` — DeckManager class
- `poker_engine.py` keeps PokerGame, imports from new modules

### Phase 4: Extract Routes from main.py (1505 lines)

- `backend/routes/auth.py` — auth endpoints
- `backend/routes/game.py` — game CRUD + action endpoints
- `backend/routes/analysis.py` — LLM analysis endpoints
- `main.py` becomes app setup, middleware, WebSocket only

### Phase 5: Verify Everything

- Full backend test suite
- Frontend build + Jest tests
- E2E Playwright suite
- Pre-commit hooks pass

### Phase 6: Doc Consolidation (lowest priority)

- Audit 17 active docs, archive stale ones
- Flatten redundant archive subdirs
- Update docs/INDEX.md

## Key Decisions

- **poker_engine.py**: extract self-contained classes only (AIStrategy, HandEvaluator, DeckManager). Do NOT decompose PokerGame itself — test coverage too low.
- **main.py**: standard FastAPI router extraction pattern.
- **Test-first for Phase 3**: add boundary tests before extracting.
