# Poker Table UX Review (January 2026)

## Current Observations

1. **Table feels undersized and off-center**
   - `frontend/components/PokerTable.tsx` clamps the felt container to `maxWidth: min(100%, 90vh * 1.6)` and `maxHeight: 75vh` (`#L445-L454`). On widescreen monitors the table never expands beyond ~1.6 × viewport height, so the 75/25 split leaves large amounts of unused green space above/below the felt while the control panel still consumes 25% width.
2. **Opponent seats only use the upper arc**
   - `frontend/lib/poker-table-layout.ts` distributes AI seats across a 180° (4-player) or 220° (6-player) arc at the *top* of the ellipse (`#L33-L69`). The lower-left/right quadrants are empty, making the table look sparse while the human hero sits alone at the bottom.
3. **Hero highlight is visually jarring**
   - Player seat highlight uses `bg-yellow-100 border-4 border-yellow-400` in `PlayerSeat.tsx` (`#L23-L34`). Because the hero is active by default, the bottom of the table is dominated by a bright yellow tile that clashes with the otherwise muted palette.
4. **Control panel palette clashes**
   - The right panel stacks saturated orange (pot), neon green (current bet), red/blue/green action buttons, and a dark navy background (`PokerTable.tsx #483-586`). The mix feels more arcade than coaching tool and competes with the felt for attention.
5. **Raise workflow is hidden**
   - Raise slider and confirm button live in a collapsible panel triggered by the green "Raise" button (`PokerTable.tsx #552-611`). Users see no hint of the slider until the panel opens, and when expanded the slider overlaps the button row.
6. **Recurring React 418 console errors**
   - Playwright logs show "Minified React error #418" on `/game/[gameId]` whenever the table renders. This indicates a hydration mismatch or streaming issue that could manifest as subtle UI glitches.

## Recommendations

1. **Responsive felt sizing**
   - Replace the hard-coded `maxWidth/maxHeight` clamp with a CSS `clamp()` that references actual available width (e.g., `width: clamp(600px, calc((100vw - controlPanelWidth) - 2rem), 1100px)` and `height: width / 1.6`). Keep a `max-height: 85vh` fallback for short viewports. This keeps the table centered and fully utilizes the left column on widescreens.
2. **Full-ellipse opponent placement**
   - Extend `calculateOpponentPositions()` to use the lower quadrants (e.g., spread 4-player tables across ~240° and 6-player tables across ~280° or the entire circumference with a gap behind the hero). This makes the felt feel populated and fixes the top-heavy layout seen in the current screenshot.
3. **Subtle hero emphasis**
   - Swap the hero highlight to a ring/glow (`ring-4 ring-amber-300`) and keep the card block on the neutral `bg-gray-100`. Consider renaming the hero label to "You" to avoid long user IDs spilling into the felt.
4. **Unified control-panel palette**
   - Adopt a single accent hue (e.g., teal) for buttons and use lighter shades of the felt green for pot/current-bet badges. Lighten the panel background from `bg-gray-900` to `bg-[#122a1c]` (or similar) to visually connect it to the table instead of feeling like a separate app.
5. **Expose raise controls inline**
   - Always show the slider beneath the action buttons on desktop, with the green button simply confirming the amount. On mobile, convert the "Raise" button into a split-button that shows the current slider amount so users understand the flow without expanding an extra panel.
6. **Investigate React hydration error**
   - The console error points to a mismatch between server-rendered and client-rendered markup on `/game/[gameId]`. Audit the component tree (especially conditional rendering around `gameState`) and resolve the mismatch to prevent hidden UX bugs.

Addressing these items will make the poker table feel larger, more balanced, and visually cohesive, while ensuring core interactions (raise slider) remain discoverable.

## Implementation Plan (Single Source of Truth)

The earlier split-panel release intentionally kept conservative layout clamps and partial arcs so we could ship without overlapping the new control panel. Those guard rails solved the immediate regression but left the UX issues above. This plan replaces the archived phase breakdowns and is the only roadmap going forward.

1. **Responsive felt sizing**
   - Replace the current `maxWidth: min(100%, 90vh * 1.6)` / `maxHeight: 75vh` clamp with CSS `clamp()` logic tied to the left-column width (e.g., `width: clamp(640px, calc(100vw - panelWidth - 4rem), 1200px)` and `height: calc(width / 1.6)` with a fallback `max-height: 85vh`).
   - Keep the felt centered and occupying the full left column on 1280×720, 1440×900, 1920×1080, and 2560×1440 canvases.
2. **Full-ellipse opponent placement**
   - Extend `calculateOpponentPositions()` so 4-player tables span ~240° and 6-player tables span ~280° while reserving a 10% horizontal safety margin near the control panel. Update the Jest layout tests to guard these coordinates.
3. **Palette + hero highlight refresh**
   - Swap the hero’s `bg-yellow-100` fill for a ring/glow (`ring-4 ring-amber-300`) and rename the seat to “You” to avoid long IDs.
   - Harmonize the control-panel palette (single accent hue, lighter background) and expose the raise slider inline beneath the action buttons instead of hiding it behind a toggle.
4. **Raise workflow polish**
   - Ensure slider + confirm button remain visible on desktop; on mobile, convert the “Raise” control into a split-button that always shows the selected amount.
5. **Hydration warning fix**
   - Reproduce the React 418 console error, audit `/game/[gameId]` conditional rendering, and eliminate the mismatch so Playwright logs stay clean.

## Testing Plan

1. **New Playwright coverage (`e2e/06-layout-ux.spec.ts`)**
   - Run twice: once with 3 AI opponents (4-player layout) and once with 5 AI opponents (6-player layout).
   - For each run: ensure `poker-table-container` fills the left column (±5% of available width), assert opponent seats appear in all four quadrants and none sit only in the top arc, verify the control panel stays 22–28% of the viewport width, confirm the raise slider is visible without toggles and that the confirm button reflects the slider value, and fail on any console `error` event (catches React 418).
2. **Update existing suites**
   - `e2e/03-game-lifecycle.spec.ts` should explicitly execute both 4-player and 6-player scenarios so the main user journey stays covered.
3. **Unit tests**
   - Expand `frontend/lib/__tests__/poker-table-layout.test.ts` with cases that validate the new arc spans and safety margins.
4. **Manual/visual QA**
   - Capture screenshots at 1280×720, 1440×900, 1920×1080, and 2560×1440 for UX sign-off once Playwright passes.

Exit criteria: Playwright suites (existing + new) pass with zero console errors, Jest layout tests cover the updated math, and UX review signs off on the refreshed screenshots for both 4- and 6-player tables.
