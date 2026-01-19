# E2E Tests with Playwright

Comprehensive end-to-end testing for the Poker Learning App using Playwright.

## Overview

This test suite validates the complete application flow from user registration through gameplay to game history, ensuring frontend-backend connectivity, authentication, and game mechanics work correctly in production.

### Test Coverage

| Suite | Tests | Focus | Duration |
|-------|-------|-------|----------|
| 1. Connectivity | 5 | API calls, CORS, WebSocket | ~2 min |
| 2. Authentication | 6 | Registration, login, logout, validation | ~3 min |
| 3. Game Lifecycle | 7 | Game creation, actions, AI turns, history | ~5 min |
| 4. Error Handling | 5 | Validation, duplicates, invalid inputs | ~2 min |
| 5. Performance | 6 | Load times, console errors, resources | ~3 min |

**Total**: 29 tests, ~15 minutes

## Quick Start

### Prerequisites

```bash
# Playwright is already installed in root package.json
# Ensure both frontend and backend are running:

# Terminal 1: Backend
cd backend && python main.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Run All Tests

```bash
# From project root
npm run test:e2e
```

### Run Specific Suite

```bash
# Connectivity only
npx playwright test 01-connectivity

# Authentication only
npx playwright test 02-authentication

# Game lifecycle only
npx playwright test 03-game-lifecycle
```

### Run with UI Mode (Recommended for Development)

```bash
npm run test:e2e:ui
```

This opens the Playwright Test UI where you can:
- Watch tests run in real-time
- Inspect each step
- View screenshots and videos
- Debug failures

### Run in Headed Mode (See Browser)

```bash
npm run test:e2e:headed
```

### Debug Specific Test

```bash
npm run test:e2e:debug -- --grep "User registration flow"
```

## Configuration

### Environment Variables

```bash
# Test against deployed environments
FRONTEND_URL=https://your-app.azurewebsites.net npm run test:e2e
BACKEND_URL=https://your-api.azurewebsites.net npm run test:e2e

# Both together
FRONTEND_URL=https://poker-frontend.azurecontainerapps.io \
BACKEND_URL=https://poker-api-demo.azurewebsites.net \
npm run test:e2e
```

### Test Configuration

Edit `playwright.config.ts` to customize:
- Timeout values
- Retry logic (currently 2 retries on CI)
- Screenshot/video settings
- Browser types (currently Chromium only)
- Parallel execution (currently sequential)

## Test Suites

### Suite 1: Connectivity (01-connectivity.spec.ts)

Validates basic infrastructure:
- Frontend loads with HTTP 200
- CORS headers present on API calls
- Backend health endpoint reachable
- POST requests work from browser
- WebSocket connections establish

**When to run**: After deployment, infrastructure changes

### Suite 2: Authentication (02-authentication.spec.ts)

Tests user authentication flows:
- User registration creates account
- User login with existing credentials
- User logout clears session
- Invalid credentials rejected
- Password validation (mismatch, too short)

**When to run**: After auth changes, user model updates

### Suite 3: Game Lifecycle (03-game-lifecycle.spec.ts)

Tests core game functionality:
- Navigate to game creation
- Create new game with AI players
- Take actions (check, fold, call, raise)
- AI players act and game progresses
- Quit game
- Game appears in history

**When to run**: After game logic changes, UI updates

### Suite 4: Error Handling (04-error-handling.spec.ts)

Validates error states:
- Empty form submission shows validation
- Duplicate username rejected
- Invalid game ID handled
- Password mismatches caught
- Short passwords rejected

**When to run**: After validation logic changes

### Suite 5: Performance (05-performance.spec.ts)

Checks performance metrics:
- Page load times < 5s (local) or < 10s (CI/Azure)
- No console errors on load
- No failed network requests
- Backend health check < 2s
- All resources load successfully

**When to run**: After deployment, before user testing

## Helpers

The `helpers.ts` file provides reusable functions:

```typescript
import { registerUser, loginUser, createGame, takeAction, quitGame } from './helpers';

// In your test
const { username, password } = await registerUser(page);
await createGame(page, username, 3); // 3 AI players
await takeAction(page, 'fold');
await quitGame(page);
```

## Screenshots

All tests capture screenshots at key moments:
- Saved to `e2e/screenshots/`
- Named by suite and action (e.g., `02-after-login.png`)
- Automatically captured on failure
- Useful for debugging and documentation

## Videos

Playwright automatically records video on failure:
- Saved to `test-results/`
- Only kept when test fails (saves disk space)
- View in HTML report

## Reports

### HTML Report (Default)

```bash
npm run test:e2e

# Open report
npx playwright show-report e2e-report
```

The HTML report includes:
- Test results with status
- Screenshots and videos
- Execution timeline
- Error messages and stack traces

### CI/GitHub Actions Report

When running in CI with `CI=true`:
- Uses GitHub Actions reporter
- Shows inline annotations in PR
- Uploads artifacts for failed tests

## Common Issues

### Tests Fail Locally But Pass in CI

**Cause**: Different screen sizes, fonts, or timing
**Fix**: Run in headed mode to see what's happening:
```bash
npm run test:e2e:headed
```

### WebSocket Connection Fails

**Cause**: Backend not running or wrong URL
**Fix**: Check `config.ts` and verify backend is up:
```bash
curl http://localhost:8000/health
```

### "Selector not found" Errors

**Cause**: UI elements changed or test too fast
**Fix**:
1. Check if element exists in current UI
2. Add `await page.waitForSelector()` if needed
3. Use `data-testid` attributes for stability

### Race Conditions / Flaky Tests

**Cause**: Tests don't wait for async operations
**Fix**: Use Playwright's auto-waiting or explicit waits:
```typescript
// Bad
await page.click('button');
await page.waitForTimeout(1000); // Arbitrary wait

// Good
await page.click('button');
await page.waitForSelector('[data-testid="success-message"]');
```

## Best Practices

### 1. Use Semantic Selectors

```typescript
// Good: Semantic, stable
await page.locator('button[type="submit"]')
await page.locator('a[href="/game/new"]')
await page.locator('[data-testid="fold-button"]')

// Bad: Fragile, breaks easily
await page.locator('.css-ab123cd')
await page.locator('div > div > button:nth-child(3)')
```

### 2. Avoid Arbitrary Timeouts

```typescript
// Bad
await page.waitForTimeout(2000);

// Good
await page.waitForSelector('button:not([disabled])');
await page.waitForLoadState('networkidle');
```

### 3. Clean Up Test Data

Each test creates unique users with timestamps to avoid conflicts.
No manual cleanup needed for MVP, but consider adding cleanup for production.

### 4. Test Against Deployed Environments

Before user testing, always run E2E against deployed URLs:
```bash
FRONTEND_URL=https://your-production-app.com npm run test:e2e
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on:
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run E2E tests
        env:
          FRONTEND_URL: ${{ secrets.FRONTEND_URL }}
          BACKEND_URL: ${{ secrets.BACKEND_URL }}
        run: npm run test:e2e

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: e2e-report/
```

## Debugging

### Debug Mode

```bash
# Opens inspector, pauses at each step
npm run test:e2e:debug

# Debug specific test
npm run test:e2e:debug -- --grep "User registration"
```

### Console Logs

All browser console logs are captured:
```typescript
// In test file
page.on('console', msg => console.log('BROWSER:', msg.text()));
```

### Network Requests

Track all network activity:
```typescript
page.on('request', req => console.log('→', req.method(), req.url()));
page.on('response', res => console.log('←', res.status(), res.url()));
```

### Traces

View full trace of test execution:
```bash
# After test runs
npx playwright show-trace test-results/path-to-trace.zip
```

## Next Steps

1. **Add data-testid attributes** to critical UI elements for more stable selectors
2. **Run against staging** before each deployment
3. **Add to CI/CD pipeline** to block broken deployments
4. **Expand coverage** for advanced features (AI analysis, session review)

## Resources

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Debugging Guide](https://playwright.dev/docs/debug)
