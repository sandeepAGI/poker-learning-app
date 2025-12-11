# Poker Learning App

A full-stack poker application for learning poker strategy through AI opponents with transparent decision-making and **real-time turn-by-turn gameplay via WebSockets**.

**Status**: ✅ Phases 1-7 Complete (Testing + WebSocket) | ✅ UX Improvements Complete | 🎯 Production-Ready

## Quick Start

```bash
# 1. Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 2. Start backend (Terminal 1)
cd backend && python main.py

# 3. Start frontend (Terminal 2)
cd frontend && npm run dev

# 4. Play! → http://localhost:3000
```

## What is This?

An educational poker app where you play Texas Hold'em against AI opponents that explain their decisions. Now with **real-time WebSocket support**, **comprehensive test coverage**, and **production-ready reliability**!

Perfect for learning:
- Poker strategy and decision-making
- SPR (Stack-to-Pot Ratio) concepts
- Pot odds and Expected Value (EV)
- Different playing styles (Conservative, Aggressive, Mathematical)

**Testing Maturity**: 67 automated tests across 7 phases validate the complete stack from unit tests to E2E browser automation with WebSocket reconnection and browser refresh recovery.

## Features

### ✅ Core Game (Phases 1-3)
- **AI Opponents**: 3 distinct personalities with transparent reasoning
- **Random AI Names**: 24 creative names (AI-ce, Deep Blue, The Algorithm, etc.)
- **WebSocket Support**: Real-time AI turn streaming
- **Hand Analysis**: Rule-based insights after each hand
- **Game Over Screen**: Shows stats when eliminated
- **SPR-Aware AI**: Stack-to-pot ratio decision making
- **Quit Anytime**: Return to lobby with one click
- **Full Game Flow**: Pre-flop → Flop → Turn → River → Showdown
- **Chip Conservation**: Perfect accounting, no bugs

### ✅ Testing Framework (Phases 1-7)
- **67 Automated Tests**: Backend unit/integration + E2E browser tests
- **Negative Testing**: 12 error handling tests (invalid actions, edge cases)
- **Property-Based Testing**: 1,250+ scenarios validated
- **Scenario Testing**: 12 comprehensive user journey tests
- **E2E Browser Testing**: 21 Playwright tests covering full stack + refresh recovery
- **WebSocket Reconnection**: 10 tests validating production-ready reliability
- **Browser Refresh Recovery**: 8 tests for localStorage + URL-based reconnection
- **UAT Regression Tests**: Prevents known issues from reoccurring
- **100% Test Pass Rate**: All phases validated

### ✅ UX/UI Improvements (December 2025)
- **Professional Card Design**: 96×134px cards with corner-only layout
- **Circular Table Layout**: Absolute positioning for professional poker aesthetics
- **Dedicated Community Cards**: Isolated component with stage labels (FLOP/TURN/RIVER)
- **Simplified Action Controls**: 3 primary buttons + expandable raise panel
- **AI Thinking Sidebar**: 320px collapsible sidebar with decision stream
- **Professional Color Palette**: Poker table felt (#0D5F2F) with accent colors
- **Responsive Design**: Mobile-friendly breakpoints + touch targets (44px minimum)
- **Enhanced Animations**: Framer Motion throughout (card dealing, pot updates, sidebar)
- **Completed**: All 4 phases in 8.5 hours (ahead of 10-14h estimate)

### 🎯 Next Phase (Phase 8+)
- **Concurrency Testing**: Thread safety and race condition validation
- **Production Deployment**: Cloud hosting and monitoring
- **Advanced Features**: Hand history, replays, learning tools

See [STATUS.md](STATUS.md) for detailed progress.

## Tech Stack

**Backend**: Python, FastAPI, WebSockets, Treys poker library
**Frontend**: Next.js 15, TypeScript, Tailwind CSS, Framer Motion, Zustand

## Documentation

- **[STATUS.md](STATUS.md)** - Current project status & progress
- **[docs/UX_REVIEW_2025-12-11.md](docs/UX_REVIEW_2025-12-11.md)** - Complete UX improvements documentation
- **[SETUP.md](SETUP.md)** - Complete setup & operations guide
- **[CLAUDE.md](CLAUDE.md)** - Master project plan & history

## Testing Improvement Plan (Phases 1-7)

### Phase 1: Bug Fix + Regression ✅
- Fixed infinite loop bug (AI action failure handling)
- 1 regression test ensures bug never returns

### Phase 2: Negative Testing ✅
- 12 error handling tests (invalid actions, edge cases)
- Error path coverage: 0% → 40%

### Phase 3: Fuzzing + Validation ✅
- 11 tests: hand evaluator validation, property-based testing
- 1,250+ scenarios validated, MD5 regression checksums

### Phase 4: Scenario Testing ✅
- 12 comprehensive user journey tests
- Multi-hand gameplay, complex betting sequences, edge cases
- 40+ poker hands played in test scenarios

### Phase 5: E2E Browser Testing ✅
- 13 Playwright tests covering full stack
- Visual regression, performance benchmarks, UAT regression tests
- Complete user flow validation through real browser

### Phase 6: CI/CD Infrastructure ✅
- Pre-commit hooks for fast regression tests (<1s)
- GitHub Actions workflows (full suite + quick tests)
- Coverage tracking with pytest-cov
- Automated testing on every commit

### Phase 7: WebSocket Reconnection + Browser Refresh ✅
- 10 WebSocket reconnection tests (production-ready)
- 8 browser refresh recovery tests (localStorage + URL routing)
- Exponential backoff validation
- Invalid game ID handling

### Phase 8: Concurrency & Race Conditions 🎯 (Next)
- Thread safety validation
- Race condition testing
- Concurrent action handling

## Running the App

**Start Backend:**
```bash
cd backend
python main.py
# → http://localhost:8000
# → WebSocket: ws://localhost:8000/ws/{game_id}
```

**Start Frontend:**
```bash
cd frontend
npm run dev
# → http://localhost:3000
```

**Stop Servers:**
```bash
# Press Ctrl+C in each terminal
# Or kill by port:
kill -9 $(lsof -ti:8000)  # Backend
kill -9 $(lsof -ti:3000)  # Frontend
```

## Testing

**Test Suite**: 67 tests across 7 phases (100% passing)

```bash
# Backend Tests (46 tests)
PYTHONPATH=backend python -m pytest backend/tests/test_negative_actions.py \
  backend/tests/test_hand_evaluator_validation.py \
  backend/tests/test_property_based_enhanced.py \
  backend/tests/test_user_scenarios.py \
  backend/tests/test_websocket_reliability.py -v

# E2E Browser Tests (21 tests - requires servers running)
# Terminal 1: python backend/main.py
# Terminal 2: cd frontend && npm run dev
# Terminal 3:
PYTHONPATH=. python -m pytest tests/e2e/test_critical_flows.py \
  tests/e2e/test_browser_refresh.py -v

# Quick regression tests (41 tests)
PYTHONPATH=backend python -m pytest backend/tests/test_action_processing.py \
  backend/tests/test_turn_order.py backend/tests/test_fold_resolution.py -v
```

See [STATUS.md](STATUS.md) for complete testing documentation.

## Architecture

```
Backend (Python/FastAPI)
├── game/
│   └── poker_engine.py     → Core game logic (764 lines)
├── main.py                 → REST + WebSocket API (437 lines)
├── websocket_manager.py    → WebSocket infrastructure (233 lines)
└── tests/                  → Comprehensive test suite (18 files)

Frontend (Next.js/TypeScript)
├── app/page.tsx            → Main game page
├── components/             → PokerTable, PlayerSeat, Card, Modals
└── lib/                    → API client, WebSocket (upcoming), state management
```

## AI Personalities

**Conservative**: Plays tight, folds weak hands, SPR-aware tightness
**Aggressive**: Bluffs often, pushes with low SPR, pressure tactics
**Mathematical**: Pot odds + EV calculations, optimal decision-making

## API Endpoints

### REST API
- `GET /` - Health check
- `POST /games` - Create new game
- `GET /games/{id}` - Get game state (query: `show_ai_thinking`)
- `POST /games/{id}/actions` - Submit player action
- `POST /games/{id}/next` - Start next hand
- `GET /games/{id}/analysis` - Get hand analysis

### WebSocket
- `WS /ws/{game_id}` - Real-time game updates

**Full API docs**: http://localhost:8000/docs (when running)

## Troubleshooting

**Port already in use:**
```bash
kill -9 $(lsof -ti:8000)  # Backend
kill -9 $(lsof -ti:3000)  # Frontend
```

**Module not found:**
```bash
cd backend && pip install -r requirements.txt
cd frontend && npm install
```

**CORS errors**: Verify backend is running and check frontend/.env.local

**WebSocket connection issues**: Ensure backend is running and check browser console

See [SETUP.md](SETUP.md) for detailed troubleshooting.

## Contributing

1. Fork the repository
2. Create feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit pull request

## License

Educational purposes.

---

**Questions?** Check [STATUS.md](STATUS.md) for detailed testing documentation.

**Live**: http://localhost:3000 (when running locally)

**Testing Documentation**:
- [STATUS.md](STATUS.md) - Complete testing progress and results
- [tests/e2e/README.md](tests/e2e/README.md) - E2E testing guide
- [tests/e2e/PHASE5_SUMMARY.md](tests/e2e/PHASE5_SUMMARY.md) - Phase 5 implementation details
