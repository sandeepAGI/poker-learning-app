# UX Improvement Implementation Log

**Branch:** `refactor/codebase-cleanup`
**Date:** 2026-03-07
**Plan:** `docs/plans/ux-improvement.md`

## Status: Complete

All 5 implementation items from the plan have been implemented and visually verified.

## Changes Made

### 1. Responsive Felt Sizing (PokerTable.tsx)
- Replaced `maxWidth: min(100%, 90vh * 1.6)` / `maxHeight: 75vh` with `width: clamp(360px, calc(100vw - 25vw - 4rem), 1200px)` and `maxHeight: 85vh`
- Table now fills the left column on all tested viewport sizes

### 2. Full-Ellipse Opponent Placement (poker-table-layout.ts)
- 4-player tables now use 240-degree arc (was 180) with start angle 210 to -30
- 6-player tables now use 280-degree arc (was 220) with start angle 230 to -50
- Opponents appear in all four quadrants instead of only the top arc
- Updated DEFAULT_ELLIPSE_CONFIG: centerY 40->45, radiusX 40->42, radiusY 30->38
- Single opponent (heads-up) uses config-based position instead of hardcoded

### 3. Palette + Hero Highlight Refresh
- **Hero highlight:** Replaced `bg-yellow-100 border-4 border-yellow-400` with `ring-4 ring-amber-300 shadow-lg shadow-amber-300/40` on neutral `bg-gray-100`
- **Hero label:** Shows "You" instead of username (required adding `is_human` to backend human_player serialization)
- **Control panel:** Background changed from `bg-gray-900` to `bg-[#122a1c]` (dark green, connects to felt)
- **POT display:** Changed from `bg-[#D97706]` (orange) to `bg-[#0D7377]` (teal)
- **Call button:** Changed from `bg-[#2563EB]` (blue) to `bg-[#0D7377]` (teal, matches POT accent)
- **AI reasoning panel:** Background `bg-gray-800` to `bg-[#0a1f14]`, borders unified to `border-[#1F7A47]/30`
- **Bottom controls:** `bg-gray-700` to `bg-[#1a3d2a]`

### 4. Raise Workflow Polish (PokerTable.tsx)
- Raise slider + quick bet buttons + confirm button always visible on desktop (`md:block`)
- Mobile retains collapsible behavior via toggle button (hidden on desktop with `md:hidden`)
- Removed AnimatePresence wrapper from raise panel (no longer needed for desktop)

### 5. Hydration Warning Fix (game/[gameId]/page.tsx)
- Replaced `useState('')` + `useEffect` params unwrapping with `React.use(params)` (Next.js 15 pattern)
- Removed unused `useState` import
- This eliminates the server/client mismatch that caused React error #418 on the game page

### Backend Fix: is_human Serialization
- Added `"is_human": p.is_human` to player dict in `poker_engine.py` `get_state()` serialization
- Added `"is_human": True` to `human_data` dict in `websocket_manager.py` `serialize_game_state()`
- Required for the "You" label feature to work (frontend checks `player.is_human`)

## Test Results

### Jest Unit Tests (25/25 passing)
- Updated `poker-table-layout.test.ts` with new arc span expectations (240/280 degrees)
- Added quadrant distribution tests for both 4-player and 6-player layouts
- Added safety margin test (x stays within 5-95% range)
- Fixed pre-existing test failures (human position, center position matched to new config)

### Playwright E2E Suite (new: e2e/06-layout-ux.spec.ts)
- 6.1: 4-player layout — table sizing, opponent quadrant placement, raise slider visibility, no React errors
- 6.2: 6-player layout — all four quadrants occupied, opponent count, no React errors
- 6.3: Hero seat shows "You" label
- 6.4: Control panel palette verification

### Backend Tests
- 424 passed, 7 failed (pre-existing LLM integration test issues), 14 errors (pre-existing API integration test issues)
- No new failures from `is_human` serialization change

### Visual QA (Playwright MCP)
- 4-player screenshot: `e2e/screenshots/06-4player-layout.png`
- 6-player screenshot: `e2e/screenshots/06-6player-layout.png`
- Both verified: opponents in all quadrants, "You" label, teal palette, inline raise slider

## Files Modified

| File | Changes |
|------|---------|
| `frontend/components/PokerTable.tsx` | Responsive sizing, palette, inline raise slider |
| `frontend/components/PlayerSeat.tsx` | Ring highlight, "You" label |
| `frontend/lib/poker-table-layout.ts` | Full-ellipse arcs, updated config |
| `frontend/app/game/[gameId]/page.tsx` | Hydration fix (React.use) |
| `frontend/lib/__tests__/poker-table-layout.test.ts` | Updated test expectations |
| `backend/game/poker_engine.py` | Added is_human to player serialization |
| `backend/websocket_manager.py` | Added is_human to human_data |
| `e2e/06-layout-ux.spec.ts` | New Playwright test suite |
