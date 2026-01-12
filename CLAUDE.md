# Poker Learning App

Human vs AI poker training. Players face opponents with distinct styles (rule-based strategies), get coaching on hands/sessions. Coaching analysis powered by Claude API (Haiku/Sonnet 4.5).

## Stack

**Backend:** FastAPI, WebSockets, treys (hand eval), Anthropic SDK
**Frontend:** Next.js 15 (App Router/Turbopack), React 19, Zustand 5, Tailwind 4, Framer Motion

## Key Files

- `backend/game/poker_engine.py` — core game logic + AI strategy classes
- `backend/main.py` — REST + WebSocket endpoints
- `frontend/components/PokerTable.tsx` — main game UI
- `frontend/lib/store.ts` — Zustand state; `websocket.ts` — real-time client

## Commands

```bash
cd backend && python main.py              # API :8000
cd frontend && npm run dev                # UI :3000
PYTHONPATH=backend pytest backend/tests/ -v   # tests (run before commits)
cd frontend && npm run build              # verify build
```

## Workflows

**Before touching `poker_engine.py`:** run `pytest backend/tests/test_property_based_enhanced.py -v` first—guards against infinite loop regression.

**Features:** failing test → implement → quick tests → STATUS.md if significant
**Bugs:** reproduce with test → fix → regression suite

## Gotchas

- Hand eval edge cases: see `test_hand_evaluator_validation.py`
- AI opponent strategies are rule-based classes in poker_engine.py; only coaching uses Anthropic API
- Docs go in `docs/` only—see @docs/INDEX.md