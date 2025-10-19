# Poker Learning App

A full-stack poker application for learning poker strategy through AI opponents with transparent decision-making.

**Status**: ✅ All 3 Phases Complete - Production Ready

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

An educational poker app where you play Texas Hold'em against AI opponents that explain their decisions in real-time. Perfect for learning:
- Poker strategy and decision-making
- SPR (Stack-to-Pot Ratio) concepts
- Pot odds and Expected Value (EV)
- Different playing styles (Conservative, Aggressive, Mathematical)

## Features

- **AI Opponents**: 3 distinct personalities with transparent reasoning
- **Real-time Learning**: See why AIs fold, call, or raise
- **Beginner Mode**: Toggle between simple and advanced explanations
- **Smooth Animations**: Card dealing, chip movements, turn indicators
- **Full Game Flow**: Pre-flop → Flop → Turn → River → Showdown
- **Chip Conservation**: Perfect accounting, no bugs

## Tech Stack

**Backend**: Python, FastAPI, Treys poker library  
**Frontend**: Next.js 15, TypeScript, Tailwind CSS, Framer Motion, Zustand

## Documentation

- **[SETUP.md](SETUP.md)** - Complete setup & operations guide
- **[PHASE3-UAT.md](PHASE3-UAT.md)** - User acceptance testing instructions
- **[CLAUDE.md](CLAUDE.md)** - Master project plan
- **Backend**: PHASE1-SUMMARY.md, PHASE2-SUMMARY.md
- **Tests**: backend/tests/ directory

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
- FastAPI wrapper with 4 endpoints
- CORS middleware for Next.js
- 9/9 integration tests passing

### Phase 3: Frontend ✅
- Next.js with TypeScript & Tailwind
- Framer Motion animations
- Zustand state management  
- Responsive poker table UI

## Running the App

**Start Backend:**
```bash
cd backend
python main.py
# → http://localhost:8000
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
├── poker_engine.py  → Core game logic
├── main.py          → REST API (4 endpoints)
└── tests/           → Comprehensive test suite

Frontend (Next.js/TypeScript)
├── app/page.tsx        → Main game page
├── components/         → Card, PlayerSeat, PokerTable
└── lib/                → API client, types, state management
```

## AI Personalities

**Conservative**: Plays tight, folds weak hands, SPR-aware tightness  
**Aggressive**: Bluffs often, pushes with low SPR, pressure tactics  
**Mathematical**: Pot odds + EV calculations, optimal decision-making

## API Endpoints

- `GET /` - Health check
- `POST /games` - Create new game
- `GET /games/{id}` - Get game state
- `POST /games/{id}/actions` - Submit player action
- `POST /games/{id}/next` - Start next hand

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

**Questions?** Check SETUP.md, PHASE3-UAT.md, or CLAUDE.md for detailed documentation.

**Live**: http://localhost:3000 (when running locally)
