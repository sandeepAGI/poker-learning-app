# Documentation Index (updated 2026-01-19)

## Active Documentation

| File | Purpose | Last Updated |
| --- | --- | --- |
| `README.md` | Product overview & quick start | see git log |
| `STATUS.md` | Rolling project status & next actions | see git log |
| `CLAUDE.md` | Working agreement, checklists | see git log |
| `docs/SETUP.md` | Detailed local setup & operations guide | 2024-11-18 |
| `docs/MVP-DAY2-TDD-PLAN.md` | **Day 2 Azure deployment plan** (TDD approach, 6 phases, 125 tests, $32/month, 6-8 hours) | 2026-01-17 |
| `docs/MVP-DAY2-STATUS-2026-01-19.md` | **Day 2 deployment status** (Phase 4 E2E testing in progress) | 2026-01-19 |
| `docs/E2E-FIX-COMPLETION-REPORT-2026-01-18.md` | **E2E test fix completion** (90% pass rate achieved, critical bug resolution) | 2026-01-18 |
| `docs/CI-TEST-RATIONALIZATION-2026-01-19.md` | **CI test workflow analysis & deletion rationale** (removed all CI tests, rely on pre-commit hooks only) | 2026-01-19 |
| `docs/CICD-QUICK-REFERENCE.md` | Quick reference for common CI/CD commands | 2026-01-12 |
| `docs/TESTING.md` | Central hub for test documentation with links to all test-related guides | 2026-01-12 |
| `docs/TEST-CODE-REVIEW-GUIDE.md` | Standards for reviewing test code quality (poker-specific patterns) | 2026-01-12 |
| `docs/TEST-SUITE-REFERENCE.md` | Complete reference for all test suites (backend, frontend, E2E, CI/CD) | 2026-01-12 |
| `docs/DEFER-ISSUES.md` | **Deferred technical debt tracking** (2 of 3 issues RESOLVED, 1 low-priority remains) | 2026-01-17 |
| `docs/DEFER-ISSUES-STATUS-2026-01-17.md` | **Verification report** - Detailed code review of all deferred issues vs actual codebase | 2026-01-17 |
| `docs/ux-review-findings-0103.md` | **UX improvement backlog** with Phase 1-4 quick wins (25% implemented, active work planned) | 2025-01-03 |
| `docs/SPLIT-PANEL-LAYOUT-COMPLETE.md` | **Split-panel layout completion** (70/30 desktop split, responsive mobile, AI thinking panel integration) | 2026-01-19 |
| `docs/POKER-TABLE-ELLIPTICAL-LAYOUT-PLAN.md` | **Split-panel layout plan** (replaced centered-oval with two-column design, learning-app focused) | 2026-01-19 |

## Archived Documentation

See `archive/` directory for completed work:

### Recent Archives (2026-01-19)
- `archive/mvp-day1/` - **MVP Day 1 completion** (backend + frontend implementation, Jan 2026)
  - MVP-DAY1-TDD-PLAN-REVISED.md - Complete Day 1 execution plan
  - MVP-BACKEND-COMPLETION-SUMMARY.md - Backend completion (101 tests)
  - MVP-FRONTEND-COMPLETION-SUMMARY.md - Frontend completion (23 tests)
  - NAVIGATION-FIXES-COMPLETION-SUMMARY.md - Navigation bug fixes
- `archive/e2e-testing/` - **E2E debugging & verification** (Jan 2026)
  - E2E-DEBUGGING-REPORT-2026-01-18.md - Blank page bug investigation
  - E2E-TEST-RESULTS-2026-01-18.md - Initial test results (21/29 passing)
  - E2E-TEST-RESULTS-PHASE-3.md - Interim results after Phase 2 fixes
  - E2E-TESTING-PLAN-PUPPETEER.md - Original test plan (migrated to Playwright)
  - MVP-DEPLOYMENT-VERIFIED-2026-01-19.md - Deployment verification report
- `archive/deployment-planning/` - **Azure deployment planning & setup** (Jan 2026)
  - AZURE-DEPLOYMENT-PLAN.md - Comprehensive Azure architecture (full plan)
  - MVP-DEPLOYMENT-CHECKLIST.md - Step-by-step deployment guide
  - MVP-DEPLOYMENT-SUMMARY.md - MVP deployment overview (CI/CD)
  - MVP-VS-FULL-COMPARISON.md - MVP vs full deployment comparison
  - GITHUB-ACTIONS-SETUP.md - CI/CD setup instructions
  - CICD-FLOW-DIAGRAM.md - Visual CI/CD workflow diagrams
- `archive/frontend-testing/` - **Frontend testing plans** (Jan 2026)
  - frontend-testing-enhancement-plan.md - Comprehensive testing plan (Phase 0 complete, others deferred)
- `archive/historical/` - **Project history & user guides** (2024-2025)
  - HISTORY.md - Development timeline through Dec 2025
  - UX_GUIDE.md - Phase 4.5 user guide (Session Analysis, coaching features)

### Earlier Archives
- `archive/2026-planning/` - Completed planning documents (test optimization plan)
- `archive/2025Q4/` - Code reviews from Dec 2024 (all issues resolved)
- `archive/execution-logs/` - TDD execution logs (navigation fixes, E2E testing reports)
- `archive/fix-logs/` - Completed Phase 4.5 fixes (FIX-01 through FIX-12 except FIX-04/05) and E2E flaky test fixes
- `archive/issue-reports/` - Resolved issue investigations (navigation issues Jan 2026)
- `archive/recommendations/` - Implemented recommendations (navigation fixes Jan 2026)
- `archive/deferred/` - **Deferred technical debt** (CI failures, viewport scaling, test optimization - see DEFER-ISSUES.md)
- `archive/docs/` - Historical analysis and archived specifications

_All other Markdown files should live under `archive/` unless explicitly added to this table._

## How to add documentation
1. Update an existing file above when possible.
2. If a new topic is needed, create `docs/<topic>.md`, add it to the table with a short description and date, and link it from `README.md` or `STATUS.md`.
3. For historical/deprecated content, move the file into `archive/` and log it in git history instead of keeping it here.
4. **Quarterly review**: Move completed work to appropriate archive folders (see `docs/DOCS-ARCHIVE-RECOMMENDATIONS-2026-01-19.md` for latest archive plan).
