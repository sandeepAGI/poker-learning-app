# Migration from Puppeteer to Playwright

This document explains the changes made when converting the E2E tests from Puppeteer to Playwright.

## Why Playwright?

### Advantages

1. **Already Installed**: Playwright was already in `package.json` before the migration
2. **Auto-Waiting**: No more `waitForTimeout()` - Playwright waits intelligently
3. **Better Selectors**: Supports text, CSS, XPath, and more out of the box
4. **Built-in Retry Logic**: Configurable retries on CI
5. **Better Debugging**: UI mode, trace viewer, inspector
6. **Parallel Execution**: Run tests in parallel when ready
7. **Better CI Integration**: GitHub Actions reporter, artifact upload
8. **Video/Screenshots**: Built-in, no extra packages needed

### Comparison

| Feature | Puppeteer | Playwright |
|---------|-----------|------------|
| Text selectors | ❌ Manual workarounds | ✅ `text=Login` |
| Auto-waiting | ❌ Must use `waitForTimeout()` | ✅ Built-in |
| Retry logic | ❌ Manual | ✅ Configurable |
| Multiple browsers | ❌ Chrome only | ✅ Chrome, Firefox, Safari |
| UI mode | ❌ No | ✅ Interactive UI |
| Trace viewer | ❌ No | ✅ Timeline + DOM snapshots |

## Key Migration Changes

### 1. Test Structure

**Before (Puppeteer/Mocha)**:
```javascript
const puppeteer = require('puppeteer');
const { expect } = require('chai');

describe('Suite 1: Connectivity', function() {
  let browser, page;

  before(async () => {
    browser = await puppeteer.launch();
    page = await browser.newPage();
  });

  after(async () => {
    await browser.close();
  });

  it('Test 1.1: Page loads', async () => {
    await page.goto('http://localhost:3000');
    // ...
  });
});
```

**After (Playwright)**:
```typescript
import { test, expect } from '@playwright/test';

test.describe('Suite 1: Connectivity', () => {
  test('1.1: Page loads', async ({ page }) => {
    await page.goto('/');
    // ...
  });
});
```

**Benefits**:
- No manual browser/page creation
- `page` fixture provided automatically
- Base URL from config
- TypeScript support

### 2. Selectors

**Before (Puppeteer)**:
```javascript
// Text selectors don't work
await page.click('button:has-text("Login")'); // ❌ Error

// Must use workarounds
await page.evaluate(() => {
  const buttons = Array.from(document.querySelectorAll('button'));
  const loginBtn = buttons.find(b => b.textContent.includes('Login'));
  loginBtn.click();
});
```

**After (Playwright)**:
```typescript
// Text selectors work natively
await page.click('button:has-text("Login")'); // ✅ Works

// Or use locator API
await page.locator('button', { hasText: 'Login' }).click();
```

### 3. Waiting

**Before (Puppeteer)**:
```javascript
// Arbitrary timeouts everywhere
await page.waitForTimeout(2000); // ❌ Flaky

// Manual element waiting
await page.waitForSelector('button', { timeout: 5000 });
```

**After (Playwright)**:
```typescript
// Auto-waiting (no timeout needed in most cases)
await page.click('button'); // Waits for element automatically

// Semantic waiting
await page.waitForLoadState('networkidle');
await page.waitForURL('/');

// Still can use explicit waits when needed
await expect(page.locator('button')).toBeVisible();
```

### 4. Assertions

**Before (Puppeteer/Chai)**:
```javascript
const { expect } = require('chai');

const title = await page.title();
expect(title).to.equal('Poker Learning App');

const isVisible = await page.$('button') !== null;
expect(isVisible).to.be.true;
```

**After (Playwright)**:
```typescript
import { expect } from '@playwright/test';

await expect(page).toHaveTitle('Poker Learning App');

await expect(page.locator('button')).toBeVisible();
```

**Benefits**:
- Auto-retry assertions
- Better error messages
- More readable

### 5. Configuration

**Before (Puppeteer/Mocha)**:
```javascript
// config.js
module.exports = {
  FRONTEND_URL: process.env.FRONTEND_URL || 'http://localhost:3000',
  HEADLESS: process.env.HEADLESS !== 'false',
};

// package.json
"test:e2e": "mocha tests/e2e/**/*.test.js --timeout 60000"
```

**After (Playwright)**:
```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './e2e',
  timeout: 60000,
  use: {
    baseURL: process.env.FRONTEND_URL || 'http://localhost:3000',
  },
  // ...
});

// package.json
"test:e2e": "playwright test"
```

### 6. Screenshots

**Before (Puppeteer)**:
```javascript
await page.screenshot({ path: 'screenshots/test.png' });
```

**After (Playwright)**:
```typescript
// Manual
await page.screenshot({ path: 'e2e/screenshots/test.png' });

// Auto on failure (configured in playwright.config.ts)
screenshot: 'only-on-failure'
```

### 7. Browser Console Logs

**Before (Puppeteer)**:
```javascript
page.on('console', msg => console.log('PAGE LOG:', msg.text()));
```

**After (Playwright)**:
```typescript
page.on('console', msg => console.log('BROWSER:', msg.text()));
// Same API, but better integration with test reports
```

### 8. Navigation

**Before (Puppeteer)**:
```javascript
await page.goto('http://localhost:3000/login', {
  waitUntil: 'networkidle2'
});
```

**After (Playwright)**:
```typescript
await page.goto('/login', {
  waitUntil: 'networkidle'
});
// Uses baseURL from config
```

## Test Count Changes

| Suite | Puppeteer Plan | Playwright Implementation |
|-------|---------------|---------------------------|
| 1. Connectivity | 5 tests | 5 tests |
| 2. Authentication | 4 tests | 6 tests (added validation tests) |
| 3. Game Lifecycle | 6 tests | 7 tests (better granularity) |
| 4. Error Handling | 3 tests | 5 tests (added password validation) |
| 5. Performance | 2 tests | 6 tests (expanded coverage) |
| **Total** | **20 tests** | **29 tests** |

## File Structure

**Before**:
```
tests/e2e/
├── config.js
├── 01-connectivity.test.js
├── 02-authentication.test.js
├── 03-game-lifecycle.test.js
├── 04-error-handling.test.js
├── 05-performance.test.js
└── screenshots/
```

**After**:
```
e2e/
├── config.ts              # TypeScript config
├── helpers.ts             # NEW: Reusable test helpers
├── 01-connectivity.spec.ts
├── 02-authentication.spec.ts
├── 03-game-lifecycle.spec.ts
├── 04-error-handling.spec.ts
├── 05-performance.spec.ts
├── screenshots/
└── README.md              # NEW: Comprehensive docs

playwright.config.ts       # NEW: Playwright config at root
package.json               # Updated with Playwright scripts
```

## Running Tests

**Before (Puppeteer/Mocha)**:
```bash
# Run all
npx mocha tests/e2e/**/*.test.js --timeout 60000

# Run specific
npx mocha tests/e2e/01-connectivity.test.js

# Headed mode
HEADLESS=false npx mocha tests/e2e/**/*.test.js
```

**After (Playwright)**:
```bash
# Run all
npm run test:e2e

# Run specific
npx playwright test 01-connectivity

# UI mode (better than headed)
npm run test:e2e:ui

# Debug mode
npm run test:e2e:debug
```

## Helper Functions

**New Addition**: The `helpers.ts` file provides reusable functions to reduce duplication:

```typescript
// Before: Inline in every test
await page.goto('/');
await page.click('button:has-text("Don\'t have an account")');
await page.fill('input#username', username);
await page.fill('input#password', password);
await page.fill('input#confirmPassword', password);
await page.click('button[type="submit"]');
await page.waitForURL('/');

// After: One line
const { username, password } = await registerUser(page);
```

Available helpers:
- `registerUser(page, username?, password?)`
- `loginUser(page, username, password)`
- `logoutUser(page)`
- `createGame(page, playerName?, aiCount?)`
- `takeAction(page, 'fold' | 'check' | 'call' | 'raise', amount?)`
- `waitForAITurn(page, maxWait?)`
- `quitGame(page)`

## CI/CD Integration

**Before**: Not documented

**After**: Full GitHub Actions example in `e2e/README.md` with:
- Artifact upload on failure
- Environment variable support
- GitHub Actions reporter

## Recommendations

1. **Delete old Puppeteer tests** in `tests/e2e/*.py` after verifying Playwright tests work
2. **Add `data-testid` attributes** to critical UI elements (next step)
3. **Run against deployed environment** before user testing
4. **Add to CI/CD** to prevent regressions

## Migration Checklist

- [x] Install Playwright (`@playwright/test` - already installed)
- [x] Create `playwright.config.ts`
- [x] Convert Suite 1: Connectivity
- [x] Convert Suite 2: Authentication
- [x] Convert Suite 3: Game Lifecycle
- [x] Convert Suite 4: Error Handling
- [x] Convert Suite 5: Performance
- [x] Add helper functions
- [x] Create comprehensive README
- [x] Update npm scripts
- [ ] Add `data-testid` to frontend components
- [ ] Run tests against deployed app
- [ ] Add to CI/CD pipeline
- [ ] Delete old Puppeteer test files

## Questions?

See `e2e/README.md` for:
- Running tests
- Debugging
- Common issues
- Best practices
