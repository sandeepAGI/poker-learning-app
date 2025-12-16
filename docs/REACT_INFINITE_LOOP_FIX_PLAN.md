# React Infinite Loop Fix - Complete Execution Plan

**Date**: December 16, 2025
**Bug**: React infinite loop in AI decision history tracking
**Approach**: 3-phase complete architectural fix
**Estimated Time**: 8.5 hours
**Testing**: Comprehensive - all tests must pass at each phase

---

## Pre-Execution Checklist

- [x] Root cause analysis complete
- [x] User approved full architectural fix (Option C)
- [ ] Backup current working state
- [ ] Verify all existing tests pass
- [ ] Document baseline behavior

---

## Phase 1: IMMEDIATE FIX (30 min)

**Goal**: Stop the infinite loop immediately in both files

### Tasks

1. **Fix `/frontend/app/page.tsx`** (lines 29-62)
   - Remove `decisionHistory` from useEffect dependency array
   - Change to functional setState using `prev`
   - Update all `decisionHistory` references to `prev`

2. **Fix `/frontend/app/game/[gameId]/page.tsx`** (lines 61-94)
   - Same changes as above
   - Ensure exact same logic

3. **Manual Testing**
   - Start game
   - Play several hands
   - Toggle AI thinking sidebar
   - Verify no console errors
   - Verify decisions appear correctly

4. **Automated Testing**
   - Run all backend tests: `PYTHONPATH=backend python -m pytest backend/tests/ -v`
   - Run frontend build: `cd frontend && npm run build`
   - Run E2E tests: `PYTHONPATH=. python -m pytest tests/e2e/test_critical_flows.py -v`

5. **Commit**
   - Commit message: "Phase 1: Fix React infinite loop in AI decision history"
   - Tag: `fix/react-infinite-loop-phase1`

### Success Criteria
- ✅ No "Maximum update depth exceeded" errors
- ✅ AI decisions display correctly
- ✅ History clears on new hand
- ✅ All existing tests pass

---

## Phase 2: EXTRACT TO CUSTOM HOOK (2-3 hours)

**Goal**: Remove code duplication, create reusable hook

### Tasks

1. **Create custom hook file**
   - Path: `/frontend/lib/hooks/useAIDecisionHistory.ts`
   - Export `useAIDecisionHistory` function
   - Include TypeScript types
   - Add JSDoc comments

2. **Implement hook logic**
   - Move fixed logic from Phase 1
   - Accept `gameState` as parameter
   - Return `decisionHistory`
   - Include proper error handling

3. **Update `/frontend/app/page.tsx`**
   - Import hook
   - Replace useEffect with hook
   - Remove local state
   - Remove duplicate logic

4. **Update `/frontend/app/game/[gameId]/page.tsx`**
   - Same changes as above

5. **Create unit tests**
   - Path: `/frontend/lib/hooks/__tests__/useAIDecisionHistory.test.ts`
   - Test: Deduplication works
   - Test: History clears on pre_flop
   - Test: Multiple decisions handled
   - Test: Edge cases (null gameState, empty decisions)
   - Test: Performance (large history)

6. **Run tests**
   - Unit tests: `cd frontend && npm test`
   - Backend tests: `PYTHONPATH=backend python -m pytest backend/tests/ -v`
   - E2E tests: `PYTHONPATH=. python -m pytest tests/e2e/test_critical_flows.py -v`
   - Frontend build: `cd frontend && npm run build`

7. **Manual Testing**
   - Start game
   - Play 5+ hands
   - Toggle AI sidebar multiple times
   - Verify decisions persist correctly
   - Test browser refresh (Phase 7 feature)

8. **Commit**
   - Commit message: "Phase 2: Extract AI decision history to custom hook"
   - Tag: `refactor/ai-decision-hook-phase2`

### Success Criteria
- ✅ No code duplication
- ✅ Hook unit tests pass (5+ tests)
- ✅ All existing tests pass
- ✅ Frontend builds successfully
- ✅ Manual testing confirms behavior unchanged

---

## Phase 3: MOVE TO ZUSTAND STORE (4 hours)

**Goal**: Proper architectural placement in application state

### Tasks

1. **Update type definitions**
   - Path: `/frontend/lib/types.ts`
   - Export `AIDecisionEntry` interface
   - Ensure proper typing

2. **Update Zustand store**
   - Path: `/frontend/lib/store.ts`
   - Add `decisionHistory: AIDecisionEntry[]` to state
   - Add `addAIDecision(decision: AIDecisionEntry): void` action
   - Add `clearDecisionHistory(): void` action
   - Add `_processAIDecisions(gameState: GameState): void` internal method
   - Call `_processAIDecisions` in `setGameState` and WebSocket updates

3. **Update `/frontend/app/page.tsx`**
   - Remove `useAIDecisionHistory` hook
   - Use `const { decisionHistory } = useGameStore()`
   - Remove all useEffect related to decisions
   - Simplify component

4. **Update `/frontend/app/game/[gameId]/page.tsx`**
   - Same changes as above

5. **Remove custom hook** (no longer needed)
   - Delete `/frontend/lib/hooks/useAIDecisionHistory.ts`
   - Delete `/frontend/lib/hooks/__tests__/useAIDecisionHistory.test.ts`

6. **Create store tests**
   - Path: `/frontend/lib/__tests__/store.test.ts`
   - Test: `addAIDecision` adds to history
   - Test: `clearDecisionHistory` clears
   - Test: `_processAIDecisions` deduplicates
   - Test: `_processAIDecisions` clears on pre_flop
   - Test: `setGameState` triggers processing
   - Test: WebSocket updates trigger processing

7. **Update E2E tests** (if needed)
   - Ensure AI sidebar tests still pass
   - Add test for decision history persistence

8. **Run all tests**
   - Store unit tests: `cd frontend && npm test`
   - Backend tests: `PYTHONPATH=backend python -m pytest backend/tests/ -v`
   - E2E tests: `PYTHONPATH=. python -m pytest tests/e2e/test_critical_flows.py -v`
   - Frontend build: `cd frontend && npm run build`

9. **Manual Testing - Complete Flow**
   - Start game
   - Play 10+ hands
   - Toggle AI sidebar
   - Browser refresh (verify decisions persist via Phase 7 localStorage)
   - Open game in new tab via URL
   - Verify WebSocket updates work
   - Play until elimination
   - Start new game
   - Verify history resets

10. **Performance Testing**
    - Monitor browser DevTools Performance tab
    - Play 20 hands
    - Verify no memory leaks
    - Verify no excessive re-renders

11. **Commit**
    - Commit message: "Phase 3: Move AI decision history to Zustand store"
    - Tag: `refactor/ai-decisions-store-phase3`

### Success Criteria
- ✅ No component-level useEffect for decisions
- ✅ Single source of truth in store
- ✅ Store unit tests pass (6+ tests)
- ✅ All existing tests pass
- ✅ E2E tests pass
- ✅ Frontend builds successfully
- ✅ Manual testing confirms all features work
- ✅ No performance regressions

---

## Post-Completion Tasks

1. **Documentation Updates**
   - Update STATUS.md with Bug Fix 5
   - Update this document with actual times
   - Update CLAUDE.md if architecture changed significantly

2. **Final Testing Round**
   - Run full test suite: `PYTHONPATH=backend python -m pytest backend/tests/ -v`
   - Run E2E suite: `PYTHONPATH=. python -m pytest tests/e2e/ -v`
   - Run frontend tests: `cd frontend && npm test`
   - Build frontend: `cd frontend && npm run build`
   - Manual smoke test: Play 5 complete hands

3. **Git Cleanup**
   - Create summary commit with all 3 phases
   - Push to GitHub
   - Verify GitHub Actions CI passes

4. **Create Prevention Plan**
   - Document learnings
   - Add linting rules
   - Update code review checklist

---

## Testing Strategy

### Unit Tests
- Hook tests (Phase 2): 5-7 tests
- Store tests (Phase 3): 6-8 tests
- **Total new tests**: 11-15 tests

### Integration Tests
- All existing backend tests must pass
- All existing E2E tests must pass

### Manual Tests
- Game creation
- Multiple hands (10+)
- AI sidebar toggle
- Browser refresh
- URL navigation
- WebSocket reconnection
- Game elimination
- New game start

### Performance Tests
- No memory leaks
- No excessive re-renders
- Smooth animations maintained

---

## Rollback Plan

If any phase fails:

1. **Identify failing phase**
2. **Revert to previous tag**:
   - Phase 1 fails: `git reset --hard HEAD~1`
   - Phase 2 fails: `git reset --hard fix/react-infinite-loop-phase1`
   - Phase 3 fails: `git reset --hard refactor/ai-decision-hook-phase2`
3. **Document failure reason**
4. **Re-plan approach**

---

## Time Tracking

| Phase | Estimated | Actual | Notes |
|-------|-----------|--------|-------|
| Pre-execution | 15 min | TBD | Setup, baseline |
| Phase 1 | 30 min | TBD | Immediate fix |
| Phase 2 | 2-3 hours | TBD | Custom hook |
| Phase 3 | 4 hours | TBD | Store refactor |
| Post-completion | 30 min | TBD | Docs, final tests |
| **Total** | **~8.5 hours** | **TBD** | |

---

## Completion Checklist

- [ ] Phase 1 complete and tested
- [ ] Phase 2 complete and tested
- [ ] Phase 3 complete and tested
- [ ] All unit tests pass
- [ ] All backend tests pass
- [ ] All E2E tests pass
- [ ] Frontend builds successfully
- [ ] Manual testing complete
- [ ] Performance validated
- [ ] Documentation updated
- [ ] Commits pushed to GitHub
- [ ] GitHub Actions CI passes
- [ ] User notified of completion

---

## Success Definition

**This fix is complete when**:
1. ✅ No React infinite loop errors occur
2. ✅ AI decision history works correctly
3. ✅ No code duplication exists
4. ✅ Decision history is in Zustand store (proper architecture)
5. ✅ All tests pass (unit + integration + E2E)
6. ✅ Frontend builds without errors
7. ✅ Manual testing confirms all features work
8. ✅ Performance is maintained or improved
9. ✅ Documentation is complete
10. ✅ GitHub Actions CI is green
