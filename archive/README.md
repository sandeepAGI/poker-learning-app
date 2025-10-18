# Archive Directory

**Date Archived**: 2025-10-18
**Reason**: Refactoring project to simplify architecture

---

## What's in This Archive

### `docs-original/`
Original project documentation before refactoring:

- **README-complex.md**: 896-line README documenting the complex implementation with WebSockets, correlation tracking, debug panels, ChipLedger, StateManager, etc.
- **README_SIMPLE-unverified.md**: Document claiming a "simple" implementation exists. Verification showed claims don't match reality (claimed 650 lines, actually ~7,000 lines).
- **README_SIMPLE_VERIFICATION.md**: Detailed analysis comparing README_SIMPLE claims vs actual codebase.

### `backend-original/`
Complete backend implementation as it existed before refactoring:

**Files**:
- `main.py` (129 lines): FastAPI with 4 endpoints
- `poker_engine.py` (572 lines): Game logic with AI, hand tracking, learning features
- `requirements.txt`: Python dependencies
- `venv/`: Python virtual environment
- `__pycache__/`: Python bytecode cache

**Total**: ~701 lines of Python code

**Known Issues** (from BE-FINDINGS.md):
1. ❌ Turn order not enforced - AI processes all actions at once
2. ❌ Hand cannot resolve after human folds - game stalls
3. ❌ Raise validation allows chip manipulation
4. ❌ Raise accounting has double-counting bug
5. ❌ Side pots not implemented

### `frontend-original/`
Complete frontend implementation as it existed before refactoring:

**Files**:
- `src/App.js` (314 lines): Main React application
- `src/App.css` (~6,000 lines): Extensive styling
- `src/index.js`: Entry point
- `package.json`: Dependencies
- `node_modules/`: 872 npm packages
- `public/`: Static assets

**Total**: ~314 lines JavaScript + ~6,000 lines CSS

---

## Why This Was Archived

### Problems with Original Implementation

1. **Over-Engineering**
   - Complex state management patterns
   - Extensive infrastructure (WebSockets, correlation tracking)
   - Debug tools mixed with production code
   - Premature optimization

2. **Critical Bugs**
   - Core poker logic has 5 major bugs (see BE-FINDINGS.md)
   - Turn order not enforced
   - Raise validation exploitable
   - Side pots not working

3. **Complexity Creep**
   - Started simple, became complex
   - Hard to debug and maintain
   - Difficult for new developers

4. **Documentation Issues**
   - Multiple conflicting documentation files
   - Claims don't match reality
   - Hard to understand actual state

### Refactoring Goals

**Preserve**:
- ✅ Core poker game logic (after bug fixes)
- ✅ AI strategies (Conservative, Mathematical, Bluffer)
- ✅ Hand evaluation with Treys library
- ✅ Learning/tracking features (hand history, AI transparency)

**Simplify**:
- 🔧 Remove ChipLedger, StateManager complexity
- 🔧 Simple API (4 endpoints, no middleware)
- 🔧 Simple frontend (useState, no abstraction layers)
- 🔧 Fix critical bugs from BE-FINDINGS.md
- 🔧 Clear, maintainable code

**Target**:
- Backend: < 800 lines (vs 701 buggy lines)
- Frontend: < 500 lines (vs ~6,300 lines)
- Clean architecture with comprehensive tests

---

## How to Use This Archive

### If You Need to Reference Old Code

```bash
# View old backend
cd archive/backend-original/

# View old frontend
cd archive/frontend-original/

# Read old documentation
cd archive/docs-original/
```

### If You Need to Restore

```bash
# DON'T! This code has critical bugs
# Instead, follow the refactoring plan in CLAUDE.md
# which preserves the good parts and fixes the bugs
```

### If You're Curious About What Changed

1. Read `CLAUDE.md` for refactoring plan
2. Read `BE-FINDINGS.md` for critical bugs
3. Compare archive/ with new implementation
4. See git history for detailed changes

---

## Timeline

- **Before 2025-07-18**: Complex implementation developed
- **2025-07-18**: Last modifications to archived code
- **2025-10-18**: Project reviewed, refactoring plan created
- **2025-10-18**: Code archived, refactoring begins

---

## Key Lessons

1. **Start Simple**: Don't add infrastructure until you need it
2. **Fix Bugs Early**: Core logic bugs compound with complexity
3. **Test Thoroughly**: Critical bugs went unnoticed
4. **Document Accurately**: README_SIMPLE claimed 650 lines, reality was 7,000+
5. **Refactor Proactively**: When complexity exceeds value, simplify

---

## Status of Archived Code

**NOT RECOMMENDED FOR USE**
- Contains critical bugs
- Over-engineered
- Hard to maintain

**USE THE REFACTORED VERSION INSTEAD**
- Follow CLAUDE.md refactoring plan
- Bugs will be fixed in Phase 1
- Simplified in Phases 2-3
- Tested in Phase 4

---

This archive preserves the work done while allowing a fresh start with better architecture.
