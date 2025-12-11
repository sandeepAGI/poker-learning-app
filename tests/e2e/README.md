# Phase 5: E2E Browser Testing

## Overview

End-to-end tests that validate the **complete stack** using real browser automation via Playwright MCP tools.

**Test Coverage**: Frontend (Next.js) → WebSocket → Backend (FastAPI) → PokerEngine

## Test Categories

### 1. Critical User Flows (6 tests)
- `test_e2e_create_game_and_play_one_hand` - Basic game creation and gameplay
- `test_e2e_all_in_button_works` - UAT-5 regression (all-in hang)
- `test_e2e_play_3_hands_then_quit` - Multi-hand gameplay
- `test_e2e_raise_slider_interaction` - Slider UX
- `test_e2e_hand_analysis_modal` - UAT-11 regression (analysis display)
- `test_e2e_chip_conservation_visual` - UI/backend state sync

### 2. Visual Regression (2 tests)
- `test_visual_poker_table_initial_state` - Initial table screenshot
- `test_visual_showdown_screen` - Showdown screenshot

### 3. Error States (3 tests)
- `test_backend_unavailable_shows_error` - Backend down handling
- `test_websocket_disconnect_recovery` - Connection loss
- `test_invalid_game_id_404_handling` - Invalid routes

### 4. Performance (2 tests)
- `test_game_creation_load_time` - <2s load time
- `test_ai_turn_response_time` - <3s AI response

**Total**: 15 E2E tests

## Prerequisites

### 1. Start Backend Server
```bash
cd /path/to/poker-learning-app
python backend/main.py
# Server runs on http://localhost:8000
```

### 2. Start Frontend Server
```bash
cd /path/to/poker-learning-app/frontend
npm run dev
# Server runs on http://localhost:3000
```

### 3. Verify Servers Running
```bash
# Test backend
curl http://localhost:8000/

# Test frontend (open in browser)
open http://localhost:3000
```

## Running E2E Tests

```bash
# Run all E2E tests
pytest tests/e2e/test_critical_flows.py -v

# Run specific test
pytest tests/e2e/test_critical_flows.py::TestCriticalUserFlows::test_e2e_create_game_and_play_one_hand -v

# Run with detailed output
pytest tests/e2e/test_critical_flows.py -v -s
```

## Implementation Status

**Phase 5 Status**: Framework Complete, Tests Pending Implementation

**Created**:
- ✅ E2E test file structure
- ✅ 15 test placeholders with detailed specs
- ✅ Test categories defined
- ✅ Implementation notes

**Pending**:
- ⏸️ Implement tests using Playwright MCP tools
- ⏸️ Run tests with servers active
- ⏸️ Capture baseline screenshots for visual regression
- ⏸️ Performance benchmarking setup

## Implementation Guide

### Using Playwright MCP Tools

The tests use Playwright MCP tools available through Claude Code:

```python
# Navigate to page
await mcp__playwright__playwright_navigate(
    url="http://localhost:3000",
    browserType="chromium",
    headless=False
)

# Click button
await mcp__playwright__playwright_click(
    selector="button:has-text('New Game')"
)

# Fill input
await mcp__playwright__playwright_fill(
    selector="input[name='player-name']",
    value="TestPlayer"
)

# Take screenshot
await mcp__playwright__playwright_screenshot(
    name="poker-table-initial",
    savePng=True,
    fullPage=False
)

# Get visible text
text = await mcp__playwright__playwright_get_visible_text()
assert "Your turn" in text

# Get HTML
html = await mcp__playwright__playwright_get_visible_html(
    removeScripts=True,
    minify=False
)

# Close browser
await mcp__playwright__playwright_close()
```

### Example Test Implementation

```python
@pytest.mark.asyncio
async def test_e2e_create_game_and_play_one_hand(self):
    """Real implementation example"""

    # Navigate
    await mcp__playwright__playwright_navigate(
        url="http://localhost:3000",
        headless=False,
        width=1920,
        height=1080
    )

    # Click New Game
    await mcp__playwright__playwright_click(
        selector="button:has-text('New Game')"
    )

    # Wait for table to load
    await asyncio.sleep(2)

    # Verify poker table visible
    text = await mcp__playwright__playwright_get_visible_text()
    assert "Pot:" in text or "Your turn" in text

    # Take screenshot
    await mcp__playwright__playwright_screenshot(
        name="poker-table-loaded",
        savePng=True,
        downloadsDir="/tmp/e2e-screenshots"
    )

    # Click Call button
    await mcp__playwright__playwright_click(
        selector="button:has-text('Call')"
    )

    # Wait for hand to complete
    await asyncio.sleep(10)

    # Verify showdown reached
    text = await mcp__playwright__playwright_get_visible_text()
    assert "Winner" in text or "Next Hand" in text

    # Close browser
    await mcp__playwright__playwright_close()
```

## Why E2E Tests Matter

**Unit/Integration tests validate**: Individual functions, WebSocket messages, backend logic

**E2E tests validate**: Complete user experience through real browser

### Bugs E2E Tests Catch

1. **UI/Backend Mismatch**: UI displays wrong chip amounts
2. **Timing Issues**: Animations block interactions
3. **WebSocket Disconnects**: Connection drops not handled
4. **Browser Compatibility**: Works in Chrome, breaks in Firefox
5. **Visual Regressions**: Button moved, text truncated
6. **Performance**: Loads slowly, feels unresponsive

### Phase 5 Goal

**Zero UAT failures** - All user-facing bugs caught by E2E tests before human testing.

## Next Steps

1. Start both servers (backend + frontend)
2. Implement test functions using Playwright MCP tools
3. Run tests and validate they pass
4. Capture baseline screenshots for visual regression
5. Add to CI/CD pipeline (Phase 6)

## Test Results (When Implemented)

```bash
# Expected output:
================= 15 passed in 180.00s ===================

# Breakdown:
- Critical flows: 6/6 passing
- Visual regression: 2/2 passing
- Error states: 3/3 passing
- Performance: 2/2 passing (avg times within limits)
```

---

**Phase 5 Framework**: ✅ COMPLETE
**Phase 5 Implementation**: ⏸️ Pending (requires servers running)
