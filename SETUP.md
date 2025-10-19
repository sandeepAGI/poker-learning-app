# Poker Learning App - Setup & Operations Guide

Complete guide for setting up, running, and managing the Poker Learning App.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Starting the Application](#starting-the-application)
4. [Stopping the Application](#stopping-the-application)
5. [Testing](#testing)
6. [Development Workflow](#development-workflow)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

**Prerequisites**: Python 3.8+, Node.js 18+, npm

```bash
# 1. Clone and navigate to project
cd poker-learning-app

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Install frontend dependencies
cd ../frontend
npm install

# 4. Start backend (Terminal 1)
cd ../backend
python main.py

# 5. Start frontend (Terminal 2)
cd ../frontend
npm run dev

# 6. Open browser
# Navigate to http://localhost:3000
```

---

## Installation

### Step 1: Prerequisites

**Check versions:**
```bash
python3 --version  # Should be 3.8+
node --version     # Should be 18+
npm --version      # Should be 8+
```

**Install if needed:**
- **Python**: https://www.python.org/downloads/
- **Node.js**: https://nodejs.org/

### Step 2: Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# If using pip3
pip3 install -r requirements.txt

# Verify installation
python -c "import fastapi; print('FastAPI installed')"
```

**Backend dependencies installed:**
- fastapi
- uvicorn
- pydantic
- treys
- requests (for tests)

### Step 3: Frontend Setup

```bash
cd frontend

# Install Node dependencies
npm install

# Verify installation
npm list next react
```

**Frontend dependencies installed:**
- next (15.5.6)
- react (19.x)
- typescript
- tailwindcss
- framer-motion
- zustand
- axios

### Step 4: Environment Variables

Create `frontend/.env.local`:
```bash
cd frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

**Verify:**
```bash
cat frontend/.env.local
# Should show: NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Starting the Application

### Method 1: Two Terminals (Recommended)

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Expected output:**
```
   ▲ Next.js 15.5.6 (Turbopack)
   - Local:        http://localhost:3000
   - Network:      http://192.168.x.x:3000

 ✓ Starting...
 ✓ Ready in 962ms
```

### Method 2: Background Processes

**Start backend in background:**
```bash
cd backend
nohup python main.py > backend.log 2>&1 &
echo $! > backend.pid
```

**Start frontend in background:**
```bash
cd frontend
nohup npm run dev > frontend.log 2>&1 &
echo $! > frontend.pid
```

**Check logs:**
```bash
tail -f backend/backend.log
tail -f frontend/frontend.log
```

### Verify Application is Running

**Check backend:**
```bash
curl http://localhost:8000/
# Expected: {"status":"ok","service":"Poker Learning App API",...}
```

**Check frontend:**
```bash
curl -I http://localhost:3000
# Expected: HTTP/1.1 200 OK
```

**Open in browser:**
- http://localhost:3000

---

## Stopping the Application

### Method 1: Interactive Terminals

**In each terminal, press:**
```
Ctrl+C
```

### Method 2: Kill by Port

**Stop backend (port 8000):**
```bash
# macOS/Linux
kill -9 $(lsof -ti:8000)

# Or find and kill
lsof -ti:8000  # Get PID
kill -9 <PID>
```

**Stop frontend (port 3000):**
```bash
# macOS/Linux
kill -9 $(lsof -ti:3000)

# Or find and kill
lsof -ti:3000  # Get PID
kill -9 <PID>
```

### Method 3: Kill Background Processes

**Using PID files:**
```bash
# Stop backend
kill $(cat backend/backend.pid)
rm backend/backend.pid

# Stop frontend
kill $(cat frontend/frontend.pid)
rm frontend/frontend.pid
```

### Method 4: Kill All Node/Python

**⚠️ WARNING: This kills ALL node/python processes!**
```bash
pkill -9 node
pkill -9 python
```

### Verify Processes Stopped

```bash
# Check if ports are free
lsof -ti:8000  # Should return nothing
lsof -ti:3000  # Should return nothing

# Or check processes
ps aux | grep "python main.py"
ps aux | grep "npm run dev"
```

---

## Testing

### Backend Tests

**Run all tests:**
```bash
cd backend
python tests/run_all_tests.py
```

**Run specific test suites:**
```bash
# Phase 1 tests
python tests/test_turn_order.py          # Turn order enforcement
python tests/test_fold_resolution.py     # Fold handling

# Phase 1.5 tests
python tests/test_ai_spr_decisions.py    # AI SPR decision making
python tests/test_ai_only_games.py       # AI tournament (5 games)

# Phase 2 tests (requires backend running)
python main.py &                         # Start backend
python tests/test_api_integration.py     # API integration tests
kill %1                                   # Stop backend
```

**Expected results:**
```
Phase 1: All tests passing
Phase 1.5: 7/7 SPR tests passing, 5/5 AI games complete
Phase 2: 9/9 API integration tests passing
```

### Frontend Tests

**Currently:** Manual UAT testing (see PHASE3-UAT.md)

**Future:** Add Jest/React Testing Library tests

---

## Development Workflow

### Making Changes

**Backend changes:**
1. Edit files in `backend/`
2. Backend auto-reloads (FastAPI reload enabled)
3. Test changes: `curl http://localhost:8000/games`

**Frontend changes:**
1. Edit files in `frontend/`
2. Frontend auto-reloads (Next.js hot reload)
3. Browser auto-refreshes at http://localhost:3000

### Adding New Features

**Backend (new endpoint):**
1. Edit `backend/main.py`
2. Add endpoint function
3. Add tests in `backend/tests/`
4. Update API docs

**Frontend (new component):**
1. Create component in `frontend/components/`
2. Import in page/component
3. Test in browser

### Git Workflow

**Check status:**
```bash
git status
```

**Stage changes:**
```bash
git add <files>
# Or stage all
git add -A
```

**Commit:**
```bash
git commit -m "Description of changes"
```

**Push:**
```bash
git push origin main
```

---

## Troubleshooting

### Backend Issues

**Problem: "Address already in use" (port 8000)**
```bash
# Solution: Kill process using port
kill -9 $(lsof -ti:8000)
```

**Problem: "ModuleNotFoundError: No module named 'fastapi'"**
```bash
# Solution: Reinstall dependencies
pip install -r backend/requirements.txt
```

**Problem: "Python version too old"**
```bash
# Solution: Use Python 3.8+
python3 --version
python3 -m pip install -r backend/requirements.txt
python3 main.py
```

### Frontend Issues

**Problem: "Port 3000 already in use"**
```bash
# Solution: Kill process using port
kill -9 $(lsof -ti:3000)
```

**Problem: "Module not found" errors**
```bash
# Solution: Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Problem: "CORS errors" in browser**
```bash
# Solution 1: Verify backend is running
curl http://localhost:8000/

# Solution 2: Check .env.local
cat frontend/.env.local
# Should show: NEXT_PUBLIC_API_URL=http://localhost:8000

# Solution 3: Restart both servers
```

### Game Not Loading

**Check 1: Both servers running?**
```bash
curl http://localhost:8000/  # Backend health check
curl http://localhost:3000/  # Frontend health check
```

**Check 2: Browser console errors?**
- Open browser DevTools (F12)
- Check Console tab for errors
- Check Network tab for failed requests

**Check 3: API connectivity?**
```bash
# Test create game endpoint
curl -X POST http://localhost:8000/games \
  -H "Content-Type: application/json" \
  -d '{"player_name":"Test","ai_count":3}'

# Should return: {"game_id":"<uuid>"}
```

### Performance Issues

**Frontend slow:**
```bash
# Clear Next.js cache
cd frontend
rm -rf .next
npm run dev
```

**Backend slow:**
- Check `backend.log` for errors
- Verify no infinite loops in game logic
- Check CPU usage: `top` or `htop`

---

## Quick Reference

### Ports
- **Backend API**: 8000
- **Frontend**: 3000
- **API Docs**: http://localhost:8000/docs

### Important Files
- `backend/main.py` - FastAPI application
- `backend/game/poker_engine.py` - Core game logic
- `frontend/app/page.tsx` - Main page
- `frontend/lib/store.ts` - State management

### Useful Commands

**Check if running:**
```bash
lsof -ti:8000  # Backend
lsof -ti:3000  # Frontend
```

**View logs (if running in background):**
```bash
tail -f backend/backend.log
tail -f frontend/frontend.log
```

**Restart everything:**
```bash
# Stop all
kill -9 $(lsof -ti:8000)
kill -9 $(lsof -ti:3000)

# Start backend
cd backend && python main.py &

# Start frontend
cd frontend && npm run dev &
```

**Run full test suite:**
```bash
cd backend
python tests/run_all_tests.py
python tests/test_api_integration.py
```

---

## Next Steps

1. Complete UAT testing (see PHASE3-UAT.md)
2. Add beginner-friendly AI reasoning
3. Deploy to production
4. Add more poker variants

---

**Need Help?**
- Check CLAUDE.md for project plan
- Review phase summaries (PHASE1-SUMMARY.md, PHASE2-SUMMARY.md)
- Check UAT documents for testing instructions
