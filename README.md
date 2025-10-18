# Poker Learning App - Under Refactoring

**Status**: 🚧 Phase 0 Complete - Ready to begin Phase 1
**Last Updated**: 2025-10-18

---

## ⚠️ Important Notice

This project is currently being refactored to **simplify the architecture** while preserving the excellent poker game logic and AI strategies.

**DO NOT USE** the archived implementation - it contains critical bugs (see `BE-FINDINGS.md`).

---

## Current Status

### ✅ Phase 0: Documentation & Cleanup (COMPLETE)
- [x] Created comprehensive refactoring plan (see `CLAUDE.md`)
- [x] Reviewed and categorized all documentation
- [x] Archived complex implementation
- [x] Verified code and documentation accuracy
- [x] Repository ready for fresh implementation

### 🎯 Next: Phase 1 - Extract and Fix Core Backend Logic
**Goals**:
1. Extract core game engine from archive
2. Fix 5 critical bugs identified in `BE-FINDINGS.md`:
   - Turn order enforcement
   - Hand resolution after folds
   - Raise validation
   - Raise accounting
   - Side pot handling
3. Create comprehensive test suite (80%+ coverage)
4. All tests must pass before proceeding to Phase 2

---

## Project Overview

### What We're Building
A **simple, educational poker learning app** where users can:
- Play Texas Hold'em against AI opponents
- Learn poker strategy through transparent AI decision-making
- Track progress and improve skills

### What We're Preserving
From the original implementation:
- ✅ Solid poker game engine (after bug fixes)
- ✅ AI strategies (Conservative, Mathematical, Bluffer, Risk-Taker)
- ✅ Hand evaluation with Treys library + Monte Carlo simulations
- ✅ Learning features (hand history, AI transparency)

### What We're Simplifying
- 🔧 Remove complex infrastructure (ChipLedger, StateManager, correlation tracking, WebSockets)
- 🔧 Simple API: 4 endpoints instead of 13+
- 🔧 Simple frontend: React with useState instead of complex state management
- 🔧 Minimal dependencies
- 🔧 Clean, readable code

---

## Architecture Goals

### Backend
- **Target**: < 800 lines of core code
- **API**: 4 simple endpoints (create game, get state, submit action, next hand)
- **Storage**: Simple in-memory or JSON file
- **Testing**: 80%+ coverage with comprehensive test suite

### Frontend
- **Target**: < 500 lines of code
- **Stack**: React with simple useState/useEffect
- **API Calls**: Direct axios calls, no abstraction layers
- **Styling**: Basic but functional

---

## Critical Issues Being Fixed

From `BE-FINDINGS.md` analysis:

### 🔴 Critical
1. **Turn order not enforced**: AI processes all actions simultaneously instead of sequentially
2. **Hand cannot resolve after human folds**: Game stalls when human player folds
3. **Raise validation allows chip manipulation**: Players can exploit betting validation

### 🟡 Major
4. **Raise accounting incorrect**: Double-counting bug in bet tracking
5. **Showdown payout ignores side pots**: All-in scenarios handled incorrectly

All bugs will be fixed in Phase 1 with comprehensive tests.

---

## Documentation

### 📋 Key Documents

- **`CLAUDE.md`**: Complete refactoring plan with phase-by-phase instructions and testing checkpoints
- **`BE-FINDINGS.md`**: Critical bug analysis from code review
- **`REQUIREMENTS.md`**: Requirements and what to preserve vs simplify
- **`DOCUMENTATION-REVIEW.md`**: Documentation audit results

### 📁 Archive

- **`archive/`**: Original implementation safely preserved
  - `backend-original/`: 701 lines with known bugs
  - `frontend-original/`: ~6,300 lines, over-engineered
  - `docs-original/`: Original documentation
  - See `archive/README.md` for details

---

## Getting Started (After Phase 4)

### Setup (Not Ready Yet)
The application is being rebuilt from scratch. Check back after Phase 2 completion for:
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Frontend
cd frontend
npm install
npm start
```

**Estimated ready**: After Phase 4 completion

---

## Development Roadmap

### Phase 0: Documentation & Cleanup ✅
- Comprehensive planning
- Code archival
- Documentation cleanup

### Phase 1: Extract and Fix Core Backend 🎯 NEXT
- Extract core game engine
- Fix 5 critical bugs
- Comprehensive test suite
- 80%+ code coverage

### Phase 2: Build Simple API Layer
- 4 minimal endpoints
- Simple in-memory storage
- Integration tests

### Phase 3: Build Simple Frontend
- Clean React UI
- Direct API integration
- End-to-end testing

### Phase 4: Final Testing & Documentation
- Comprehensive testing
- Performance validation
- Final documentation
- Ready for use

---

## Testing Requirements

Each phase has **strict testing checkpoints**:

### Phase 1 Gate
- [ ] All extracted files have unit tests
- [ ] All 5 critical bugs fixed and tested
- [ ] Test coverage ≥ 80%
- [ ] All tests pass consistently
- [ ] Cannot proceed to Phase 2 until complete

### Phase 2 Gate
- [ ] API integration tests pass
- [ ] Complete game flow works via API
- [ ] No data loss between calls

### Phase 3 Gate
- [ ] End-to-end gameplay works
- [ ] 5+ consecutive hands playable
- [ ] All manual tests pass

### Phase 4 Gate
- [ ] All acceptance criteria met
- [ ] 30+ minute play session without errors
- [ ] Setup time < 10 minutes

---

## Contributing

**During Refactoring**: Please refer to `CLAUDE.md` for current phase and requirements.

**After Refactoring**: Standard contribution workflow will be established.

---

## Git Workflow

**Mandatory**: Each phase must be committed and pushed before proceeding to next phase.

See `CLAUDE.md` → "Git Commit Requirements" for commit message templates.

---

## Success Criteria

### Functional
- [ ] Complete Texas Hold'em gameplay
- [ ] All 4 AI opponents with distinct strategies
- [ ] Turn order enforced correctly
- [ ] All edge cases handled (folds, all-ins, side pots)
- [ ] No chip creation/destruction bugs

### Technical
- [ ] Backend: < 800 lines
- [ ] Frontend: < 500 lines
- [ ] API: 4 endpoints only
- [ ] Test coverage ≥ 80%
- [ ] Setup time < 10 minutes

### Quality
- [ ] Readable, well-commented code
- [ ] No over-engineering
- [ ] Minimal dependencies
- [ ] Clean separation of concerns

---

## Questions?

- **Refactoring Plan**: See `CLAUDE.md`
- **Bug Details**: See `BE-FINDINGS.md`
- **Original Code**: See `archive/`
- **Current Progress**: Check Phase status above

---

## License

Educational project for learning poker strategy and software development with AI assistance.

---

**Next Step**: Begin Phase 1 - Extract and fix core backend logic per `CLAUDE.md`
