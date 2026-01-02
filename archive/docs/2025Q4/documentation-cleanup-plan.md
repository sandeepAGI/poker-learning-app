# Documentation Cleanup Plan (2024-12-26)

Objective: consolidate Markdown files so CLAUDE.md reflects the real structure. Work in two phases to preserve context.

## Phase 1 – Map & Approve Structure
1. **Inventory** existing `.md` files (snapshot in repo as of 2024-12-26; see `stat` output above).
2. **Design target structure**:
   - Root: `README.md`, `STATUS.md`, `CLAUDE.md` only.
   - Active docs under `docs/`: `INDEX.md` (new), `HISTORY.md`, `SETUP.md`, `TESTING.md` (rename from `TESTING_STRATEGY_ANALYSIS.md`), `UX_GUIDE.md` (rename from `PHASE4_5_USER_GUIDE.md`), `PHASE4_5_FIXES.md` (rename to `CURRENT_FIX_LOG.md` per latest work), `codex-code-review-1226.md`, `documentation-cleanup-plan.md` (this file; archive once work completes).
   - Legacy docs listed below to move under `archive/docs/2025Q4/`.
3. Confirm scope with repo owner (complete with note about `PHASE4_5_FIXES.md`).

## Phase 2 – Execute
1. **Rename active docs**:
   - `docs/TESTING_STRATEGY_ANALYSIS.md` → `docs/TESTING.md`.
   - `docs/PHASE4_5_USER_GUIDE.md` → `docs/UX_GUIDE.md`.
   - `docs/PHASE4_5_FIXES.md` → `docs/CURRENT_FIX_LOG.md`.
2. **Create `docs/INDEX.md`** summarizing active docs + last updated timestamps.
3. **Move legacy docs** (list below) into `archive/docs/2025Q4/`. Keep directory structure simple.
4. **Backend/test markdowns**: move `backend/PHASE*.md`, `backend/tests/*.md`, `tests/e2e/*.md` into `archive/backend-phases/` or `archive/tests/2025Q4/` after confirming they’re not referenced.
5. **Update references** in `README.md`, `STATUS.md`, `CLAUDE.md`, `docs/INDEX.md` to match new file names.
6. **Update CLAUDE.md** after filesystem matches target: add the new documentation protocol and commit checklist item.
7. **Verification after each batch**:
   - Run `rg --files -g "*.md"` to ensure only approved docs remain outside `archive/`.
   - Check `README.md`, `STATUS.md`, `CLAUDE.md`, `docs/INDEX.md` for stale links.
   - `git status` clean (apart from expected moves) before each commit.

## Legacy Docs to Archive (move to `archive/docs/2025Q4/`)
*(sorted by last-modified timestamp for priority)*
- `docs/BROWSER_REFRESH_TESTING.md` (2024-12-18)
- `docs/NEXT_SESSION_START_HERE.md` (2024-12-18)
- `docs/REACT_INFINITE_LOOP_FIX_PLAN.md` (2024-12-16)
- `docs/PHASE4_5_TEST_RESULTS.md` (2024-12-21)
- `docs/PHASE4_5_FIXES.md` (keep active via rename; do **not** archive yet)
- `docs/PHASE4_EVALUATION_REPORT.md` (2024-12-21)
- `docs/PHASE4_PROMPTING_STRATEGY.md` (2024-12-21)
- `docs/ENHANCEMENT_PLAN_2025-12.md` (2024-12-18)
- `archive/docs/2025Q4/UX_REVIEW_2025-12-11.md` (moved 2024-12-26)
- `docs/TEST_ARCHIVE_PLAN.md` (2024-12-20)
- `docs/PHASE4_5_USER_GUIDE.md` (rename to `UX_GUIDE.md` before moving anything)

Backend/test markdown (last touched >10 days ago) to archive: `backend/PHASE4-TEST-RESULTS.md`, `backend/PHASE4_TEST_RESULTS.md`, `backend/PHASE1/2 summaries`, `backend/tests/PHASE7_SUMMARY.md`, `tests/e2e/PHASE5_SUMMARY.md`, `tests/e2e/README_LLM_TESTS.md`, etc.

## Notes
- `docs/CURRENT_FIX_LOG.md` remains active until work finishes; revisit after fixes complete.
- This plan itself stays in `docs/` until cleanup is done, then move it to archive or delete.

*Next step*: begin Phase 2 with file renames and `INDEX.md` creation.
