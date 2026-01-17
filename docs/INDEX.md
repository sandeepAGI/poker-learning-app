# Documentation Index (updated 2026-01-17)

## Active Documentation

| File | Purpose | Last Updated |
| --- | --- | --- |
| `README.md` | Product overview & quick start | see git log |
| `STATUS.md` | Rolling project status & next actions | see git log |
| `CLAUDE.md` | Working agreement, checklists | see git log |
| `docs/HISTORY.md` | Chronological release / milestone notes | 2024-12-17 |
| `docs/SETUP.md` | Detailed local setup & operations guide | 2024-11-18 |
| `docs/AZURE-DEPLOYMENT-PLAN.md` | Full production deployment plan for Azure (Auth0, Redis, 8 tables) | 2026-01-12 |
| `docs/MVP-DEPLOYMENT-SUMMARY.md` | **MVP deployment with CI/CD - Start here for deployment** | 2026-01-12 |
| `docs/MVP-DAY1-TDD-PLAN-REVISED.md` | **Day 1 TDD execution plan (14-16 hours, ready for autonomous execution)** | 2026-01-13 |
| `docs/MVP-BACKEND-COMPLETION-SUMMARY.md` | **Backend MVP completion summary (101 tests passing, production-ready)** | 2026-01-13 |
| `docs/MVP-FRONTEND-COMPLETION-SUMMARY.md` | **Frontend MVP 100% complete** (23 tests passing, auth + history + game UI fully functional) | 2026-01-13 |
| `docs/MVP-DEPLOYMENT-CHECKLIST.md` | Step-by-step MVP deployment guide (2 days, $27/month) | 2026-01-12 |
| `docs/GITHUB-ACTIONS-SETUP.md` | Complete GitHub Actions CI/CD setup guide | 2026-01-12 |
| `docs/CICD-QUICK-REFERENCE.md` | Quick reference for common CI/CD commands | 2026-01-12 |
| `docs/CICD-FLOW-DIAGRAM.md` | Visual diagrams of CI/CD flows (deployment, rollback, monitoring) | 2026-01-12 |
| `docs/MVP-VS-FULL-COMPARISON.md` | Comparison of MVP vs full deployment (shows simplifications) | 2026-01-12 |
| `docs/TESTING.md` | Central hub for test documentation with links to all test-related guides | 2026-01-12 |
| `docs/TEST-CODE-REVIEW-GUIDE.md` | Standards for reviewing test code quality (poker-specific patterns) | 2026-01-12 |
| `docs/TEST-SUITE-REFERENCE.md` | Complete reference for all test suites (backend, frontend, E2E, CI/CD) | 2026-01-12 |
| `docs/UX_GUIDE.md` | User guide for Session Analysis, API setup, and coaching features | 2024-12-21 |
| `docs/DEFER-ISSUES.md` | **Deferred technical debt tracking** (4 of 5 issues RESOLVED, 1 low-priority segfault remains) | 2026-01-17 |
| `docs/DEFER-ISSUES-STATUS-2026-01-17.md` | **Verification report** - Detailed code review of all deferred issues vs actual codebase | 2026-01-17 |
| `docs/frontend-testing-enhancement-plan.md` | Complete frontend testing plan with TDD execution (Phases 0-4; consolidates roadmap) | 2026-01-12 |
| `docs/ux-review-findings-0103.md` | UX improvement backlog with Phase 1-4 quick wins (25% implemented) | 2025-01-03 |

## Archived Documentation

See `archive/` directory for completed work:
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
