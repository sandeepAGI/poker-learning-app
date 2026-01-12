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

## Test Infrastructure Changes

### Before Committing Test Changes

1. **Run affected tests locally** (100% pass rate required)
2. **Check platform assumptions** (macOS vs Linux rendering differences)
3. **Validate configuration** (jest.config.ts, pytest.ini work locally)
4. **Update test count** in docs/TEST-SUITE-REFERENCE.md

### CI Workflow Changes

1. **Test in personal fork first** (or use `workflow_dispatch` for testing)
2. **Use Infrastructure Change Checklist** (`.github/INFRASTRUCTURE_CHANGE_CHECKLIST.md`)
3. **Monitor first run after merge** (don't walk away from CI)
4. **Have rollback plan ready** (know commit hash to revert)

### Visual/Snapshot Tests

- **Generate baselines in CI environment (Linux)**, never locally (macOS)
- Use `generate-visual-baselines.yml` workflow for updates
- Chromium renders differently across platforms (fonts, anti-aliasing)
- Document baseline generation in test comments

### Coverage Thresholds

- **Set to current baseline**, not aspirational targets
- Increase gradually (+5% per sprint max)
- **Always test locally before enforcing** in CI
- Never add thresholds without tests that meet them

### Velocity Guidelines

- **Maximum 5-7 commits per day** during infrastructure work
- **Pause every 5 commits** to validate (run full test suite)
- **Don't merge large changes on Fridays** (need monitoring time)
- One logical change per commit

### Code Review for Tests

Test code gets same rigor as production code:

**Check for:**

- Correct player indices (use `enumerate()`, not manual search)
- Meaningful assertions (not just "no crash")
- Proper test isolation (no global state dependencies)

**Red flags:**

- Intermittent failures (race condition or flaky test)
- Always-passing assertions (`assert x is not None` from iteration)
- Tests requiring specific order to pass

## Gotchas

- Hand eval edge cases: see `test_hand_evaluator_validation.py`
- AI opponent strategies are rule-based classes in poker_engine.py; only coaching uses Anthropic API
- Docs go in `docs/` only—see @docs/INDEX.md
