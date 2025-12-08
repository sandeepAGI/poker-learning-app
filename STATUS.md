# Poker Learning App - Current Status

**Last Updated**: December 8, 2025
**Version**: 3.1 (Test Stabilization Complete)
**Branch**: `main`

---

## Current State

All backend tests passing. Ready for UAT.

### Test Results (December 8, 2025)

| Test Suite | Result |
|------------|--------|
| Unit Tests | 48 passed, 9 skipped |
| Property-Based (10,000 scenarios) | 1,757,335 checks, 0 violations |
| API Integration | Skipped (requires running server) |

### Recent Fixes

| Bug | Issue | Fix |
|-----|-------|-----|
| BB Option | Test used invalid raise amount | Use `current_bet + big_blind` as minimum |
| Raise Validation | Tests didn't account for AI processing | Added `process_ai=False` parameter |
| Side Pots | Community cards made a straight | Changed to non-straight board |
| WebSocket Flow | Tests used wrong AI processing mode | Added `process_ai=False` for WebSocket |
| API Integration | Tests fail when server not running | Added skip decorator |

---

## Architecture

### Backend (Python/FastAPI)
- `game/poker_engine.py` - Core game logic (~1600 lines)
- `main.py` - REST + WebSocket API
- `websocket_manager.py` - Real-time AI turn streaming

### Frontend (Next.js/TypeScript)
- `components/PokerTable.tsx` - Main game UI
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
# Unit tests
cd backend && python -m pytest tests/ -v

# Property-based (10K scenarios)
PYTHONPATH=backend python tests/legacy/test_property_based.py

# API integration (requires running server)
python main.py &  # Start server first
python -m pytest tests/test_api_integration.py -v
```
