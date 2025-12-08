# Poker Learning App - Current Status

**Last Updated**: December 8, 2025
**Version**: 3.2 (WebSocket Bug Fixes Complete)
**Branch**: `main`

---

## Current State

All critical WebSocket game flow bugs fixed. Ready for UAT.

### Test Results (December 8, 2025)

| Test Suite | Result |
|------------|--------|
| Backend Unit Tests | 64 passed, 9 skipped |
| Property-Based (1,000 scenarios) | 176,450 checks, 0 violations |
| Bug-Specific Tests | 8/8 pass |
| API Integration | Skipped (requires running server) |

### Recent Fixes (December 8, 2025)

| Bug | Issue | Fix |
|-----|-------|-----|
| Bug #7 | Human fold doesn't trigger showdown with `process_ai=False` | Added immediate showdown trigger in `submit_human_action()` |
| Bug #8 | Infinite loop when all players all-in at SHOWDOWN | Added early return in `_advance_state_for_websocket()` |
| Betting Round | `_betting_round_complete()` incorrect with all-in players | Distinguished "others folded" vs "others all-in" scenarios |
| All-In Flag | `all_in` not cleared when players win pots | Added clearing in all 8 pot award locations |

---

## Architecture

### Backend (Python/FastAPI)
- `game/poker_engine.py` - Core game logic (~1650 lines)
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

# Property-based (1K scenarios)
PYTHONPATH=backend python tests/legacy/test_property_based.py

# Bug-specific tests
python -m pytest tests/test_fold_and_allin_bugs.py -v

# API integration (requires running server)
python main.py &  # Start server first
python -m pytest tests/test_api_integration.py -v
```
