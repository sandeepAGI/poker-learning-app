# Poker Learning App - Development Guide

**Current Status**: See [STATUS.md](STATUS.md)
**Development History**: See [docs/HISTORY.md](docs/HISTORY.md)

---

## Quick Start

```bash
# Backend
cd backend && pip install -r requirements.txt
python main.py  # Runs on http://localhost:8000

# Frontend (separate terminal)
cd frontend && npm install
npm run dev  # Runs on http://localhost:3000
```

---

## Before Committing Checklist

1. **Run backend tests**:
   ```bash
   cd backend && python -m pytest tests/ -v
   ```

2. **Run property-based test** (thorough validation):
   ```bash
   cd /path/to/repo && python tests/legacy/test_property_based.py
   ```

3. **Check frontend builds**:
   ```bash
   cd frontend && npm run build
   ```

4. **Update STATUS.md** if significant changes were made

5. **Commit with descriptive message**:
   ```bash
   git add .
   git commit -m "Brief description of changes"
   git push origin main
   ```

---

## Project Structure

```
poker-learning-app/
├── backend/
│   ├── game/poker_engine.py  # Core game logic (~1600 lines)
│   ├── main.py               # FastAPI server + WebSocket
│   ├── websocket_manager.py  # WebSocket handling
│   └── tests/                # Backend unit tests
├── frontend/
│   ├── app/                  # Next.js pages
│   ├── components/           # React components
│   └── lib/                  # Store, API, WebSocket client
├── tests/
│   └── legacy/               # Integration/exploratory tests
├── docs/
│   └── HISTORY.md            # Development history
├── archive/
│   └── docs/                 # Archived documentation
├── README.md                 # User-facing quick start
├── STATUS.md                 # Current project status
└── CLAUDE.md                 # This file
```

---

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `backend/game/poker_engine.py` | Core poker logic, AI strategies | ~1600 |
| `backend/main.py` | REST API + WebSocket endpoints | ~450 |
| `frontend/components/PokerTable.tsx` | Main game UI | ~400 |
| `frontend/lib/store.ts` | Zustand state management | ~200 |
| `frontend/lib/websocket.ts` | WebSocket client | ~360 |

---

## API Endpoints

### REST
- `POST /games` - Create new game
- `GET /games/{id}` - Get game state
- `POST /games/{id}/actions` - Submit player action
- `POST /games/{id}/next` - Start next hand
- `GET /games/{id}/analysis` - Get hand analysis

### WebSocket
- `WS /ws/{game_id}` - Real-time game updates

---

## Documentation Policy

**Maximum 5 .md files in root**:
1. `README.md` - User quick start
2. `STATUS.md` - Current status
3. `CLAUDE.md` - This guide (max 200 lines)

**Additional docs in `/docs/`**:
- `HISTORY.md` - Development history
- `SETUP.md` - Detailed setup (if needed)

**Rules**:
- No separate phase documentation
- No TODO.md, NOTES.md, FINDINGS.md
- Update history goes in docs/HISTORY.md
- Keep CLAUDE.md under 200 lines

---

## Testing Strategy

### Must Pass Before Commit (Quick - 2 min)
```bash
# Phase 1-3 tests (23 tests in ~48s)
PYTHONPATH=backend python -m pytest backend/tests/test_negative_actions.py \
  backend/tests/test_hand_evaluator_validation.py \
  backend/tests/test_property_based_enhanced.py -v

# Frontend build check
cd frontend && npm run build
```

### Full Test Suite (Before Major Changes - 25 min)
```bash
# All Phase 1-5 tests (49 tests)
# Backend tests (36 tests - ~20 min)
PYTHONPATH=backend python -m pytest backend/tests/test_negative_actions.py \
  backend/tests/test_hand_evaluator_validation.py \
  backend/tests/test_property_based_enhanced.py \
  backend/tests/test_user_scenarios.py -v

# E2E tests (13 tests - ~2.5 min, requires servers running)
python backend/main.py &
cd frontend && npm run dev &
PYTHONPATH=. python -m pytest tests/e2e/test_critical_flows.py -v
```

### Test Coverage
- **Phase 1**: Infinite loop regression (1 test)
- **Phase 2**: Negative testing (12 tests)
- **Phase 3**: Fuzzing + validation (11 tests)
- **Phase 4**: Scenario testing (12 tests)
- **Phase 5**: E2E browser testing (13 tests)
- **Total**: 49 tests, 100% passing

---

## Common Tasks

### Add a new feature
1. Update poker_engine.py if backend change needed
2. Update frontend components
3. Add tests in backend/tests/
4. Run full test suite
5. Update STATUS.md

### Fix a bug
1. Write a failing test first
2. Fix the bug
3. Verify test passes
4. Run regression tests
5. Commit with descriptive message

### Debug an issue
1. Check backend logs: `python main.py` output
2. Check browser console for frontend errors
3. Run property-based test to find edge cases
4. Add QC assertions if needed (poker_engine.py)
