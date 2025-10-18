# Poker Learning App - Refactoring Plan

## Project Status
This project has become too complex with over-engineering in the API and frontend layers. The core poker engine, AI strategies, and game logic are solid and should be preserved. We need to simplify the architecture while maintaining the excellent poker gameplay.

## Key Issues Identified
1. **Backend findings** (see BE-FINDINGS.md): Critical bugs in turn order, hand resolution after fold, raise validation, and side pot handling
2. **Over-engineered infrastructure**: Complex state management, chip ledgers, correlation tracking, WebSocket real-time updates
3. **Frontend complexity**: Multiple state management patterns, excessive abstractions, diagnostic tools in production code
4. **Documentation sprawl**: Multiple overlapping documentation files

## Refactoring Strategy
**Preserve the solid poker engine, simplify everything else.** Extract core game logic, build a simple API wrapper, create a clean frontend.

---

# STEP-BY-STEP REFACTORING PLAN

## PHASE 0: Documentation & Cleanup (Current Phase)
**Goal**: Clean up documentation and establish clear project structure.

### Step 0.1: Review and Consolidate Documentation
- [x] Review BE-FINDINGS.md (critical backend issues identified)
- [x] Review REQUIREMENTS.md (clear requirements established)
- [x] Audit all .md files in project
- [x] Create single source of truth documentation structure
- [x] Archive obsolete documentation

**Testing Checkpoint 0.1**:
- [x] All documentation files reviewed and categorized
- [x] Obsolete files moved to `archive/` directory
- [x] CLAUDE.md contains complete refactoring plan
- [x] README.md updated with simplified structure

### Step 0.2: Archive Existing Implementation
- [x] Create `archive/backend-original/` directory
- [x] Move current backend API implementation to archive
- [x] Create `archive/frontend-original/` directory
- [x] Move current frontend implementation to archive
- [x] Document what was archived and why

**Testing Checkpoint 0.2**:
- [x] All original code safely archived with timestamps
- [x] Archive directory has README explaining what's inside
- [x] Git commit created: "Phase 0 complete: Documentation cleanup and code archival"
- [x] Working directory ready for new implementation

### Phase 0 Completion: Git Commit & Push
**Required before proceeding to Phase 1**:
```bash
git add .
git commit -m "Phase 0 complete: Documentation cleanup and code archival

- Updated CLAUDE.md with comprehensive refactoring plan
- Reviewed and categorized all documentation
- Archived complex implementation (backend + frontend)
- Archived obsolete documentation
- Created temporary README
- Repository ready for fresh implementation

Archived: backend/, frontend/, README.md, README_SIMPLE.md"

git push origin main
```

---

## PHASE 1: Extract and Fix Core Backend Logic
**Goal**: Extract working poker engine, fix critical bugs, remove complexity.

### Step 1.1: Extract Core Game Engine Files
Extract these files from archive/current implementation:
- [ ] `backend/game/poker_game.py` → Review and simplify
- [ ] `backend/game/deck_manager.py` → Keep as-is
- [ ] `backend/game/hand_manager.py` → Keep as-is
- [ ] `backend/models/player.py` → Simplify (remove complex tracking)
- [ ] `backend/ai/strategies/` → Keep all 4 strategies, remove decorators

**Testing Checkpoint 1.1**:
```bash
# Create unit tests for extracted components
cd backend
python -m pytest tests/test_deck_manager.py -v
python -m pytest tests/test_hand_manager.py -v
```
- [ ] All extracted files have basic unit tests
- [ ] Tests pass without dependencies on removed infrastructure
- [ ] Code review confirms no ChipLedger/StateManager dependencies

### Step 1.2: Fix Critical Backend Bugs
Address issues from BE-FINDINGS.md:

**1.2.1: Implement Proper Turn Order**
- [ ] Add `current_player_index` to PokerGame state
- [ ] Add `next_to_act()` method to determine whose turn
- [ ] Reject out-of-turn actions in API layer
- [ ] Update `_process_ai_actions()` to respect turn order

**Testing Checkpoint 1.2.1**:
```python
# Test: backend/tests/test_turn_order.py
def test_turn_order_enforced():
    game = PokerGame(num_players=4)
    # Verify only current player can act
    # Verify turn advances correctly after each action
    # Verify AI players act in order
```
- [ ] Turn order test passes
- [ ] Out-of-turn actions are rejected
- [ ] Turn advances correctly through all players

**1.2.2: Fix Hand Resolution After Fold**
- [ ] Add `betting_complete()` method to check if betting round is done
- [ ] Ensure hand continues when human folds
- [ ] Trigger AI actions even when human is inactive
- [ ] Properly advance to showdown or award pot

**Testing Checkpoint 1.2.2**:
```python
# Test: backend/tests/test_fold_resolution.py
def test_hand_continues_after_human_fold():
    game = PokerGame(num_players=4)
    # Human folds pre-flop
    # Verify AI players continue betting
    # Verify hand resolves to showdown or winner
    # Verify pot is awarded correctly
```
- [ ] Test passes with human folding in all positions
- [ ] Hand completes and pot is awarded
- [ ] Game advances to next hand

**1.2.3: Fix Raise Validation and Accounting**
- [ ] Add minimum raise validation (at least current bet + big blind)
- [ ] Track per-player contributions separately from total pot
- [ ] Fix double-counting in raise accounting
- [ ] Prevent negative bets and stack manipulation

**Testing Checkpoint 1.2.3**:
```python
# Test: backend/tests/test_betting_validation.py
def test_raise_validation():
    game = PokerGame(num_players=4)
    # Test minimum raise enforcement
    # Test raise accounting (no double-counting)
    # Test invalid raise amounts rejected
    # Test chip conservation maintained
```
- [ ] Invalid raises are rejected
- [ ] Chip accounting is correct
- [ ] No chip creation/destruction possible

**1.2.4: Implement Side Pot Handling**
- [ ] Track per-player contributions per betting round
- [ ] Calculate side pots when players go all-in
- [ ] Distribute winnings correctly with side pots
- [ ] Handle edge cases (multiple all-ins, ties)

**Testing Checkpoint 1.2.4**:
```python
# Test: backend/tests/test_side_pots.py
def test_side_pot_distribution():
    game = PokerGame(num_players=4)
    # Simulate multiple all-ins at different amounts
    # Verify correct side pot calculation
    # Verify correct winner determination per pot
    # Verify all chips accounted for
```
- [ ] Side pots calculated correctly
- [ ] Winners receive correct amounts
- [ ] Chip conservation maintained

### Step 1.3: Create Comprehensive Backend Test Suite
- [ ] Create `tests/test_complete_game.py` - Full game simulation
- [ ] Create `tests/test_ai_strategies.py` - Verify all 4 AI personalities
- [ ] Create `tests/test_chip_integrity.py` - Chip conservation tests
- [ ] Create `tests/test_edge_cases.py` - All-in, ties, splits

**Testing Checkpoint 1.3**:
```bash
# Run complete test suite
python -m pytest tests/ -v --cov=game --cov=ai --cov-report=term-missing

# Minimum requirements:
# - 80%+ code coverage on core game logic
# - All tests pass
# - No test warnings or errors
```
- [ ] Test coverage ≥ 80% on core files
- [ ] All tests pass consistently
- [ ] Edge cases covered

**PHASE 1 GATE: Cannot proceed to Phase 2 until all Phase 1 tests pass**

### Phase 1 Completion: Git Commit & Push
**Required before proceeding to Phase 2**:
```bash
git add .
git commit -m "Phase 1 complete: Core backend logic extracted and bug fixes implemented

- Extracted and simplified core game engine files
- Fixed critical bugs: turn order, fold resolution, raise validation, side pots
- Comprehensive test suite with 80%+ coverage
- All tests passing consistently

Tests: [X/X passing]
Coverage: [X%]"

git push origin main
```

---

## PHASE 2: Build Simple API Layer
**Goal**: Create minimal FastAPI wrapper around fixed game engine.

### Step 2.1: Create Simple API Structure
- [ ] Create `backend/main.py` with 4 core endpoints
- [ ] Implement simple in-memory game storage (dict)
- [ ] Add basic request/response models (Pydantic)
- [ ] Remove all complex middleware, correlation tracking, etc.

**API Endpoints**:
```python
POST   /games                    # Create new game
GET    /games/{game_id}          # Get game state
POST   /games/{game_id}/actions  # Submit player action
POST   /games/{game_id}/next     # Next hand
```

**Testing Checkpoint 2.1**:
```bash
# Start server
uvicorn main:app --reload

# Test endpoints
curl -X POST http://localhost:8000/games -H "Content-Type: application/json" -d '{"ai_count": 3}'
curl http://localhost:8000/games/{game_id}
curl -X POST http://localhost:8000/games/{game_id}/actions -d '{"action": "call"}'
```
- [ ] All endpoints return correct responses
- [ ] Error handling works (400, 404, 500)
- [ ] Game state serializes/deserializes correctly

### Step 2.2: Integration Testing
- [ ] Create `tests/test_api_integration.py`
- [ ] Test complete game flow through API
- [ ] Test error conditions
- [ ] Test concurrent games

**Testing Checkpoint 2.2**:
```python
# Test: tests/test_api_integration.py
def test_complete_game_via_api():
    # Create game
    # Play through pre-flop → flop → turn → river → showdown
    # Verify all actions work correctly
    # Verify game state updates properly
    # Test next hand
```
- [ ] Integration tests pass
- [ ] API correctly wraps game engine
- [ ] No data loss between API calls

**PHASE 2 GATE: Cannot proceed to Phase 3 until API integration tests pass**

### Phase 2 Completion: Git Commit & Push
**Required before proceeding to Phase 3**:
```bash
git add .
git commit -m "Phase 2 complete: Simple API layer implemented

- Created minimal FastAPI with 4 core endpoints
- Integration tests passing
- API correctly wraps game engine
- No data loss between API calls

Tests: [X/X passing]"

git push origin main
```

---

## PHASE 3: Build Simple Frontend
**Goal**: Create clean React UI with minimal complexity.

### Step 3.1: Setup Basic React App
- [ ] Create new React app with create-react-app
- [ ] Setup basic folder structure
- [ ] Add axios for API calls
- [ ] Setup simple CSS/styling

**Testing Checkpoint 3.1**:
```bash
cd frontend
npm install
npm start
# Verify app loads without errors
```
- [ ] React app runs successfully
- [ ] No build warnings
- [ ] Can connect to backend API

### Step 3.2: Create Core Components
- [ ] `GameLobby.js` - Create new game interface
- [ ] `PokerTable.js` - Display table, players, cards, pot
- [ ] `GameControls.js` - Action buttons (fold/check/call/bet)
- [ ] `App.js` - Simple routing and state management

**Component Requirements**:
- Use simple `useState` and `useEffect` (no complex state management)
- Direct API calls with axios (no abstraction layers)
- Clear, readable code
- Basic but functional styling

**Testing Checkpoint 3.2**:
```bash
# Manual testing checklist:
```
- [ ] Can create a new game
- [ ] Poker table displays correctly
- [ ] Player positions shown
- [ ] Community cards display
- [ ] Pot amount visible
- [ ] Action buttons appear for human player

### Step 3.3: Implement Game Flow
- [ ] Connect GameLobby to POST /games
- [ ] Poll GET /games/{id} for state updates
- [ ] Implement action submission
- [ ] Handle game state transitions
- [ ] Implement "Next Hand" button

**Testing Checkpoint 3.3**:
```bash
# Manual end-to-end testing:
```
- [ ] Create game with 3 AI opponents
- [ ] Play complete hand: pre-flop → flop → turn → river → showdown
- [ ] AI players act automatically
- [ ] Can fold/check/call/raise appropriately
- [ ] Pot awarded correctly
- [ ] Can start next hand
- [ ] Play 5+ consecutive hands without errors

### Step 3.4: Error Handling and Polish
- [ ] Add loading states
- [ ] Add error messages for failed API calls
- [ ] Add basic validation (bet amounts, etc.)
- [ ] Test edge cases (disconnection, invalid actions)

**Testing Checkpoint 3.4**:
- [ ] Error messages display clearly
- [ ] Loading states prevent double-actions
- [ ] Invalid bets are caught before API call
- [ ] Game recovers gracefully from errors

**PHASE 3 GATE: Cannot proceed to Phase 4 until end-to-end gameplay works**

### Phase 3 Completion: Git Commit & Push
**Required before proceeding to Phase 4**:
```bash
git add .
git commit -m "Phase 3 complete: Simple frontend implemented

- React app with minimal complexity
- End-to-end gameplay working
- All manual testing scenarios pass
- 5+ consecutive hands played without errors

Manual testing: Complete"

git push origin main
```

---

## PHASE 4: Final Testing and Documentation
**Goal**: Comprehensive testing and clean documentation.

### Step 4.1: Comprehensive Testing
- [ ] Run full backend test suite
- [ ] Run full API integration tests
- [ ] Manual frontend testing (30+ minute play session)
- [ ] Test all 4 AI personalities
- [ ] Test all edge cases (all-in, folds, ties)

**Testing Checkpoint 4.1**:
```bash
# Backend
cd backend
python -m pytest tests/ -v --cov=game --cov=ai

# Frontend manual testing
cd frontend
npm start
# Play 20+ hands testing various scenarios
```
- [ ] All backend tests pass
- [ ] All integration tests pass
- [ ] 30-minute play session completed without errors
- [ ] All AI personalities behave correctly
- [ ] All edge cases handled properly

### Step 4.2: Performance and Cleanup
- [ ] Remove all debug code
- [ ] Remove unused imports
- [ ] Check for memory leaks (long game session)
- [ ] Verify game performance is acceptable

**Testing Checkpoint 4.2**:
- [ ] No console errors or warnings
- [ ] Code is clean and readable
- [ ] No memory leaks in 100+ hand session
- [ ] Response times < 1 second

### Step 4.3: Final Documentation
- [ ] Update README.md with simple setup instructions
- [ ] Document API endpoints
- [ ] Add code comments for complex logic
- [ ] Create ARCHITECTURE.md explaining design decisions

**Testing Checkpoint 4.3**:
- [ ] New developer can setup and run in < 10 minutes
- [ ] Documentation is accurate and complete
- [ ] Code is well-commented

**PHASE 4 GATE: Final acceptance testing**

### Phase 4 Completion: Git Commit & Push
**Required for project completion**:
```bash
git add .
git commit -m "Phase 4 complete: Poker learning app refactoring finished

- All acceptance criteria met
- Complete test suite passing
- Documentation updated and accurate
- Ready for production use

All phases complete ✅"

git push origin main
git tag -a v2.0-simplified -m "Simplified poker learning app - refactoring complete"
git push origin v2.0-simplified
```

---

## ACCEPTANCE CRITERIA (Must Pass All)

### Functional Requirements
- [ ] Complete Texas Hold'em gameplay works correctly
- [ ] All 4 AI opponents work with distinct strategies
- [ ] Turn order enforced correctly
- [ ] Hand resolution works in all scenarios (fold, showdown, all-in)
- [ ] Raise validation prevents exploitation
- [ ] Side pots handled correctly
- [ ] Chip conservation maintained (no chip creation/destruction)
- [ ] Multiple hands can be played consecutively
- [ ] Game state persists correctly between actions

### Technical Requirements
- [ ] Backend: < 800 lines of core code (excluding tests)
- [ ] Frontend: < 500 lines of code
- [ ] API: 4 endpoints only
- [ ] No complex infrastructure (no WebSockets, correlation tracking, etc.)
- [ ] Test coverage ≥ 80% on backend core logic
- [ ] All tests pass consistently
- [ ] Setup time < 10 minutes for new developer

### Code Quality Requirements
- [ ] Code is readable and well-commented
- [ ] No over-engineering or premature optimization
- [ ] Clean separation of concerns
- [ ] Minimal dependencies
- [ ] No debug code in production

---

## HOW TO UPDATE THIS DOCUMENT

### When to Update CLAUDE.md
1. **After completing any phase**: Check off completed items
2. **When discovering new issues**: Add to appropriate phase
3. **When changing approach**: Update plan and document reasoning
4. **After testing reveals problems**: Add new test requirements

### Update Procedure
1. Read current CLAUDE.md
2. Make changes using Edit tool
3. Ensure all checklists remain intact
4. Add notes in "Update History" section below
5. Commit changes with descriptive message

### Git Commit Requirements
**MANDATORY**: At the end of each phase (0, 1, 2, 3, 4), you MUST:
1. Run all applicable tests and verify they pass
2. Update CLAUDE.md with completion status
3. Create a git commit with the template provided in that phase
4. Push to the repository: `git push origin main`
5. **DO NOT** proceed to the next phase until commit is pushed

This ensures:
- Work is safely versioned at each milestone
- Progress can be tracked and rolled back if needed
- Each phase is a stable checkpoint
- Team/reviewer can see incremental progress

### What to Track
- [x] Completed checkpoints (use [x])
- [ ] Pending checkpoints (use [ ])
- Issues discovered during implementation
- Deviations from plan (with justification)
- Testing results and failures

---

## DOCUMENTATION MANAGEMENT POLICY

### Core Principle
**ZERO DOCUMENTATION SPRAWL**: Strictly control documentation growth to prevent the complexity we're trying to eliminate.

### Allowed Documentation Files (MAX 5)

1. **CLAUDE.md** (THIS FILE)
   - **Purpose**: Master refactoring plan and single source of truth
   - **Updates**: Phase completion, findings, discoveries
   - **Keep**: Concise summaries only, detailed analysis in Update History

2. **README.md**
   - **Purpose**: User-facing quick start and status
   - **Updates**: After Phase 4 only (final documentation)
   - **Keep**: < 200 lines, simple setup instructions

3. **BE-FINDINGS.md**
   - **Purpose**: Critical bugs reference
   - **Updates**: NEVER (historical record)
   - **Archive**: After Phase 1 when bugs are fixed

4. **REQUIREMENTS.md**
   - **Purpose**: What to preserve vs simplify
   - **Updates**: NEVER (historical record)
   - **Archive**: After Phase 2 when approach is validated

5. **ARCHITECTURE.md** (Create in Phase 4)
   - **Purpose**: Final design decisions
   - **Updates**: One-time creation in Phase 4
   - **Keep**: < 150 lines, design rationale only

### FORBIDDEN During Development

❌ **DO NOT CREATE**:
- No FINDINGS.md, ANALYSIS.md, REVIEW.md files
- No separate verification reports
- No phase-specific documentation
- No TODO.md, NOTES.md, THOUGHTS.md
- No duplicate documentation with different names

❌ **DO NOT LET GROW**:
- CLAUDE.md must stay < 600 lines (currently ~540)
- If it grows beyond 600 lines, archive old content
- Update History should be concise bullets, not essays

### Where to Put Findings

**During Development (Phases 0-3)**:
- ✅ **Critical discoveries**: Add to CLAUDE.md "Update History" as concise bullets
- ✅ **Bug findings**: Reference BE-FINDINGS.md (don't duplicate)
- ✅ **Code issues**: Add inline comments in code, not separate docs
- ✅ **Test failures**: In test output and git commit messages

**Example - GOOD**:
```
### 2025-10-18: Phase 0 Backend Review
- Reviewed REQUIREMENTS.md against actual code (poker_engine.py: 572 lines)
- Found: ChipLedger, StateManager, JWT don't exist (no removal needed)
- Found: Only 3 AI personalities (not 4), no Risk-Taker
- Found: File structure is single-file, not multi-directory
- Conclusion: Backend already simplified, focus Phase 1 on fixing 5 bugs
```

**Example - BAD**:
```
Created 250-line REQUIREMENTS-VS-REALITY.md with detailed analysis...
(This creates documentation sprawl)
```

### Documentation Review Checkpoints

**At End of Each Phase**:
- [ ] Count .md files in root (must be ≤ 5)
- [ ] Check CLAUDE.md line count (must be < 600)
- [ ] Archive historical docs to archive/docs-original/
- [ ] Remove any temporary analysis files

### Archive Strategy

**When to Archive**:
- BE-FINDINGS.md → Archive after Phase 1 (bugs fixed)
- REQUIREMENTS.md → Archive after Phase 2 (approach validated)
- DOCUMENTATION-REVIEW.md → Archive now (Phase 0 complete)

**How to Archive**:
```bash
mv OLD-DOC.md archive/docs-original/
# Add note to CLAUDE.md Update History
```

### Violation Response

**If documentation sprawls** (> 5 .md files or CLAUDE.md > 600 lines):
1. STOP work immediately
2. Consolidate into existing docs
3. Archive what's no longer needed
4. Delete redundant files
5. Update this policy if needed

### Success Metrics

**Phase 0**: ✅ 5 .md files (CLAUDE.md, README.md, BE-FINDINGS.md, REQUIREMENTS.md, DOCUMENTATION-REVIEW.md)
**Phase 1-3**: ≤ 5 .md files
**Phase 4**: ≤ 5 .md files (add ARCHITECTURE.md, archive BE-FINDINGS.md + REQUIREMENTS.md)
**Final**: Exactly 3 .md files (CLAUDE.md, README.md, ARCHITECTURE.md)

---

## UPDATE HISTORY

### 2025-10-18: Initial Refactoring Plan Created
- Created comprehensive phase-by-phase plan
- Added strict testing checkpoints at each step
- Established acceptance criteria
- Documented update procedures
- Added mandatory git commit/push requirements at end of each phase
- Ensures work is versioned at every milestone

### 2025-10-18: Phase 0 Completed
- Reviewed all documentation files (5 .md files audited)
- Created verification report for README_SIMPLE.md (claims vs reality)
- Archived original implementation:
  - `archive/backend-original/`: 701 lines Python (with known bugs)
  - `archive/frontend-original/`: ~6,300 lines (over-engineered)
  - `archive/docs-original/`: All obsolete documentation
- Created archive/README.md explaining what was archived and why
- Created new temporary README.md for refactoring period
- Updated CLAUDE.md with git commit requirements for each phase
- **Added Documentation Management Policy** to prevent sprawl (max 5 .md files)
- Repository ready for Phase 1

### 2025-10-18: Phase 0 Backend Review (REQUIREMENTS.md vs Reality)
**Reviewed**: REQUIREMENTS.md claims against actual backend code (poker_engine.py: 572 lines, main.py: 129 lines)

**Key Findings**:
- ✅ **Already simplified**: 701 lines total (within 500-800 target), NOT "2000+" as claimed
- ❌ **File structure wrong**: Claims game/, ai/strategies/, models/ directories don't exist - everything in one file
- ❌ **Removal claims false**: ChipLedger, StateManager, JWT, WebSockets, correlation tracking NOT present (already removed/never added)
- ✅ **Good features verified**: DeckManager clean, Treys+MonteCarlo excellent, AI decision tracking exceptional
- ⚠️ **3 AI personalities** (not 4): Conservative, Aggressive, Mathematical - no "Risk-Taker"
- ❌ **"Solid/excellent" contradicted**: 5 critical bugs from BE-FINDINGS.md prove it's buggy but fixable
- ✅ **Learning features**: HandEvent tracking, AI reasoning, action history all well-implemented
- ❌ **Missing features**: SPR calculations (claimed), side pots (required), proper turn order

**Critical Insight**: Backend has **good structure** but **critical bugs**. Not "excellent" - it's **buggy but well-organized**.

**Phase 1 Implication**: Focus on **fixing 5 bugs** (BE-FINDINGS.md), NOT removing complexity that doesn't exist.

**Documentation Strategy**: Use REQUIREMENTS.md for philosophy (what to value), NOT as facts (what exists).