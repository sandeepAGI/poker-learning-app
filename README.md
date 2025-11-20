# Poker Learning App

A full-stack poker application for learning poker strategy through AI opponents with transparent decision-making and **real-time turn-by-turn gameplay via WebSockets**.

**Status**: ✅ Phases 0-3 Complete | 🚧 UX Enhancement In Progress

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

An educational poker app where you play Texas Hold'em against AI opponents that explain their decisions. Now with **real-time WebSocket support** to show each AI action as it happens!

Perfect for learning:
- Poker strategy and decision-making
- SPR (Stack-to-Pot Ratio) concepts
- Pot odds and Expected Value (EV)
- Different playing styles (Conservative, Aggressive, Mathematical)

## Features

### ✅ Implemented
- **AI Opponents**: 3 distinct personalities with transparent reasoning
- **Random AI Names**: 24 creative names (AI-ce, Deep Blue, The Algorithm, etc.)
- **WebSocket Backend**: Real-time AI turn streaming (frontend integration in progress)
- **Hand Analysis**: Rule-based insights after each hand
- **Game Over Screen**: Shows stats when eliminated
- **SPR-Aware AI**: Stack-to-pot ratio decision making
- **Quit Anytime**: Return to lobby with one click
- **Full Game Flow**: Pre-flop → Flop → Turn → River → Showdown
- **Chip Conservation**: Perfect accounting, no bugs

### 🚧 In Progress (UX Enhancement)
- **WebSocket Frontend**: Real-time UI updates
- **Turn-by-Turn Visibility**: See each AI decision as it happens (no more black box!)
- **Visual Animations**: Card dealing, chip movements, turn indicators
- **Learning Tools**: Hand strength indicator, contextual tips, hand history

See [STATUS.md](STATUS.md) for detailed progress and [UX-ROADMAP.md](UX-ROADMAP.md) for complete plan.

## Tech Stack

**Backend**: Python, FastAPI, WebSockets, Treys poker library
**Frontend**: Next.js 15, TypeScript, Tailwind CSS, Framer Motion, Zustand

## Documentation

- **[STATUS.md](STATUS.md)** - Current project status & progress
- **[UX-ROADMAP.md](UX-ROADMAP.md)** - UX enhancement roadmap
- **[SETUP.md](SETUP.md)** - Complete setup & operations guide
- **[CLAUDE.md](CLAUDE.md)** - Master project plan & history

## Project Phases

### Phase 1: Core Backend ✅
- Fixed 7 critical bugs in poker engine
- Comprehensive test suite (80%+ coverage)
- Turn order, fold resolution, side pots, chip conservation

### Phase 1.5: AI Enhancement ✅
- Added SPR (Stack-to-Pot Ratio) to all AI personalities
- Enhanced decision-making with pot-relative logic
- 7/7 SPR tests passing, 5-game AI tournament verified

### Phase 2: API Layer ✅
- FastAPI wrapper with REST endpoints
- WebSocket endpoint for real-time updates
- Hand analysis endpoint
- CORS middleware for Next.js

### Phase 3: Frontend ✅
- Next.js with TypeScript & Tailwind
- Framer Motion animations
- Zustand state management
- Responsive poker table UI
- Game Over, Analysis, and Winner modals

### Phase 4: UX Enhancement 🚧 (In Progress)
- **Backend WebSocket infrastructure** ✅ (Phase 1.1-1.2 complete)
- Frontend WebSocket client (Phase 1.3-1.6)
- Visual animations (Phase 2)
- Learning features (Phase 3)
- Settings & polish (Phase 4-5)

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

```bash
cd backend

# Run all tests
python tests/run_all_tests.py

# Run specific suites
python tests/test_ai_spr_decisions.py  # AI SPR tests
python tests/test_api_integration.py    # API tests (requires backend running)
```

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

**Questions?** Check [STATUS.md](STATUS.md), [SETUP.md](SETUP.md), or [UX-ROADMAP.md](UX-ROADMAP.md) for detailed documentation.

**Live**: http://localhost:3000 (when running locally)
