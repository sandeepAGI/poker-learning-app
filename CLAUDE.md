# Poker Learning App

Human vs AI poker training. Players face opponents with distinct styles (rule-based strategies), get coaching on hands/sessions. Coaching analysis powered by Claude API (Haiku/Sonnet 4.5).

## Stack

**Backend:** FastAPI, WebSockets, treys (hand eval), Anthropic SDK
**Frontend:** Next.js 15 (App Router/Turbopack), React 19, Zustand 5, Tailwind 4, Framer Motion

## Key Files

- `backend/game/poker_engine.py` — core game logic + AI strategy classes
- `backend/main.py` — REST + WebSocket endpoints
- `backend/auth.py` — JWT authentication
- `backend/database.py` — SQLAlchemy DB session
- `backend/models.py` — ORM models (User, Game, Hand, AnalysisCache)
- `backend/llm_analyzer.py` — LLM coaching integration (Anthropic SDK)
- `backend/websocket_manager.py` — WebSocket connection management
- `frontend/components/PokerTable.tsx` — main game UI
- `frontend/components/AISidebar.tsx` — AI coaching sidebar (split-panel right)
- `frontend/lib/store.ts` — Zustand state; `websocket.ts` — real-time client
- `frontend/lib/api.ts` — REST API client
- `backend/alembic/` — DB migrations (run `alembic upgrade head` after schema changes)

## Architecture

See `docs/gameplay-flow.md` for end-to-end gameplay trace (game creation → WebSocket → AI turns → showdown → coaching).

## Commands

```bash
cd backend && python main.py              # API :8000
cd frontend && npm run dev                # UI :3000
PYTHONPATH=backend pytest backend/tests/ -v   # tests (run before commits)
cd frontend && npm run build              # verify build
cd frontend && npm run test               # frontend Jest unit tests
npm run test:e2e                          # Playwright E2E (both servers must be running)
npm run test:e2e:ui                       # E2E with interactive UI
```

## Environment Setup

```bash
alembic -c backend/alembic.ini upgrade head   # initialize DB
```

LLM coaching requires `ANTHROPIC_API_KEY` in `backend/.env` (already configured). Game works without it — coaching is just disabled.

## Workflows

**Before touching `poker_engine.py`:** run `pytest backend/tests/test_property_based_enhanced.py -v` first—guards against infinite loop regression.

**Features:** failing test → implement → quick tests → STATUS.md if significant
**Bugs:** reproduce with test → fix → regression suite

## Pre-Commit Hooks

Critical tests run automatically before each commit (via `hooks/pre-commit`):

- Regression suite: action processing, state advancement, turn order, fold resolution
- Infinite loop guard (only if poker_engine.py modified)

**Installation** (for new contributors):

```bash
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**To bypass** (emergency only):

```bash
git commit --no-verify -m "message"
```

## Test Infrastructure

- Run affected tests locally before committing (100% pass rate required)
- Update test count in docs/TEST-SUITE-REFERENCE.md when adding/removing tests
- All CI workflows removed (2026-01-19) — rely on pre-commit hooks only
- See docs/TESTING.md for detailed test review guidelines

## Gotchas

- Hand eval edge cases: see `test_hand_evaluator_validation.py`
- AI opponent strategies are rule-based classes in poker_engine.py; only coaching uses Anthropic API
- Docs go in `docs/` only—see @docs/INDEX.md
