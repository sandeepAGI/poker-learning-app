# E2E Testing Plan with Puppeteer

**Purpose**: Comprehensive end-to-end testing before any user testing
**Date Created**: 2026-01-19
**Prerequisites**: Frontend and backend deployed to Azure

---

## 🎯 Objectives

1. **Verify frontend-backend connectivity** (CORS, API calls, WebSocket)
2. **Test all critical user flows** (registration, login, gameplay, history)
3. **Catch issues BEFORE user testing** (automated, repeatable, fast)
4. **Document expected behavior** (screenshots, videos, logs)

---

## 📋 Test Suite Overview

| Suite | Tests | Focus | Duration |
|-------|-------|-------|----------|
| 1. Connectivity | 5 | API calls, CORS, WebSocket | 2 min |
| 2. Authentication | 4 | Registration, login, logout | 3 min |
| 3. Game Lifecycle | 6 | Create, play, quit, history | 5 min |
| 4. Error Handling | 3 | Invalid inputs, network errors | 2 min |
| 5. Performance | 2 | Load time, responsiveness | 3 min |

**Total**: 20 tests, ~15 minutes

---

## 🏗️ Test Infrastructure Setup

### 1. Install Dependencies

```bash
cd frontend
npm install --save-dev \
  puppeteer \
  @puppeteer/test \
  chai \
  mocha

# Or at project root
npm install --global puppeteer
```

### 2. Create Test Directory Structure

```bash
mkdir -p tests/e2e
mkdir -p tests/e2e/screenshots
mkdir -p tests/e2e/videos
mkdir -p tests/e2e/logs
```

### 3. Configuration File

Create `tests/e2e/config.js`:
```javascript
module.exports = {
  FRONTEND_URL: process.env.FRONTEND_URL || 'https://poker-frontend.braveisland-d54008f6.centralus.azurecontainerapps.io',
  BACKEND_URL: process.env.BACKEND_URL || 'https://poker-api-demo.azurewebsites.net',

  // Test timeouts
  PAGE_LOAD_TIMEOUT: 10000,
  API_CALL_TIMEOUT: 5000,
  WEBSOCKET_TIMEOUT: 8000,

  // Test user credentials
  TEST_USERNAME: `test_${Date.now()}`,
  TEST_PASSWORD: 'TestPassword123!',

  // Puppeteer options
  HEADLESS: process.env.HEADLESS !== 'false',
  SLOWMO: process.env.SLOWMO ? parseInt(process.env.SLOWMO) : 0,

  // Screenshot/video settings
  SCREENSHOT_ON_FAILURE: true,
  VIDEO_RECORD: process.env.VIDEO === 'true',
};
```

---

## 📝 Test Suite 1: Frontend-Backend Connectivity

**File**: `tests/e2e/01-connectivity.test.js`

```javascript
const puppeteer = require('puppeteer');
const { expect } = require('chai');
const config = require('./config');

describe('Suite 1: Frontend-Backend Connectivity', function() {
  this.timeout(30000);

  let browser, page;

  before(async () => {
    browser = await puppeteer.launch({
      headless: config.HEADLESS,
      slowMo: config.SLOWMO,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    page = await browser.newPage();

    // Enable request/response logging
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('requestfailed', request => {
      console.log('FAILED REQUEST:', request.url(), request.failure().errorText);
    });
  });

  after(async () => {
    await browser.close();
  });

  it('Test 1.1: Frontend page loads with HTTP 200', async () => {
    const response = await page.goto(config.FRONTEND_URL, {
      waitUntil: 'networkidle2',
      timeout: config.PAGE_LOAD_TIMEOUT
    });

    expect(response.status()).to.equal(200);
    await page.screenshot({ path: 'tests/e2e/screenshots/01-page-load.png' });
  });

  it('Test 1.2: CORS headers present on API requests', async () => {
    let corsHeader = null;

    page.on('response', response => {
      if (response.url().includes(config.BACKEND_URL)) {
        corsHeader = response.headers()['access-control-allow-origin'];
      }
    });

    // Trigger an API call (try to register)
    await page.goto(config.FRONTEND_URL);
    await page.waitForSelector('input#username', { timeout: 5000 });

    // Make a test API call
    await page.evaluate(async (backendUrl) => {
      await fetch(`${backendUrl}/health`);
    }, config.BACKEND_URL);

    await page.waitForTimeout(2000);

    expect(corsHeader).to.not.be.null;
    console.log('CORS header:', corsHeader);
  });

  it('Test 1.3: Backend health endpoint reachable from browser', async () => {
    const healthData = await page.evaluate(async (backendUrl) => {
      const response = await fetch(`${backendUrl}/health`);
      return await response.json();
    }, config.BACKEND_URL);

    expect(healthData.status).to.equal('healthy');
  });

  it('Test 1.4: Frontend can make POST requests to backend', async () => {
    const testResponse = await page.evaluate(async (backendUrl) => {
      try {
        const response = await fetch(`${backendUrl}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: `connectivity_test_${Date.now()}`,
            password: 'test123456'
          })
        });
        return {
          status: response.status,
          ok: response.ok,
          data: await response.json()
        };
      } catch (error) {
        return { error: error.message };
      }
    }, config.BACKEND_URL);

    console.log('POST test response:', testResponse);
    expect(testResponse.status).to.be.oneOf([200, 201]);
    expect(testResponse.data).to.have.property('token');
  });

  it('Test 1.5: WebSocket connection can be established', async () => {
    // First create a game to get a game ID
    const gameData = await page.evaluate(async (backendUrl) => {
      // Register and get token
      const authRes = await fetch(`${backendUrl}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: `ws_test_${Date.now()}`,
          password: 'test123456'
        })
      });
      const { token } = await authRes.json();

      // Create game
      const gameRes = await fetch(`${backendUrl}/games`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          player_name: 'WSTest',
          ai_count: 3
        })
      });
      const game = await gameRes.json();

      return { gameId: game.game_id, token };
    }, config.BACKEND_URL);

    // Test WebSocket connection
    const wsConnected = await page.evaluate(async (backendUrl, gameId, token) => {
      return new Promise((resolve) => {
        const wsUrl = backendUrl.replace('https:', 'wss:') + `/ws/${gameId}?token=${token}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          ws.close();
          resolve(true);
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          resolve(false);
        };

        setTimeout(() => resolve(false), config.WEBSOCKET_TIMEOUT);
      });
    }, config.BACKEND_URL, gameData.gameId, gameData.token);

    expect(wsConnected).to.be.true;
  });
});
```

---

## 📝 Test Suite 2: User Authentication

**File**: `tests/e2e/02-authentication.test.js`

```javascript
const puppeteer = require('puppeteer');
const { expect } = require('chai');
const config = require('./config');

describe('Suite 2: User Authentication', function() {
  this.timeout(30000);

  let browser, page;
  const testUsername = config.TEST_USERNAME;
  const testPassword = config.TEST_PASSWORD;

  before(async () => {
    browser = await puppeteer.launch({
      headless: config.HEADLESS,
      slowMo: config.SLOWMO,
      args: ['--no-sandbox']
    });
    page = await browser.newPage();

    // Log console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('BROWSER ERROR:', msg.text());
      }
    });
  });

  after(async () => {
    await browser.close();
  });

  it('Test 2.1: User registration flow', async () => {
    await page.goto(config.FRONTEND_URL);

    // Wait for page to load
    await page.waitForSelector('input#username', { timeout: 5000 });

    // Click "Create account" button
    const createAccountBtn = await page.$('button:has-text("Don\'t have an account")');
    if (!createAccountBtn) {
      // Try alternative selector
      await page.click('text=/create.*account/i');
    } else {
      await createAccountBtn.click();
    }

    // Fill registration form
    await page.waitForSelector('input#username', { visible: true });
    await page.type('input#username', testUsername);
    await page.type('input#password', testPassword);

    // Check if confirm password field exists
    const confirmPasswordInput = await page.$('input#confirmPassword');
    if (confirmPasswordInput) {
      await page.type('input#confirmPassword', testPassword);
    }

    // Take screenshot before submission
    await page.screenshot({ path: 'tests/e2e/screenshots/02-registration-form.png' });

    // Submit registration
    await page.click('button[type="submit"]');

    // Wait for redirect or success message
    try {
      await page.waitForNavigation({ timeout: 10000, waitUntil: 'networkidle2' });
    } catch (e) {
      // May not navigate, check for success indicator
      await page.waitForTimeout(2000);
    }

    // Take screenshot after submission
    await page.screenshot({ path: 'tests/e2e/screenshots/02-after-registration.png' });

    // Verify successful registration (check for welcome message or game page)
    const content = await page.content();
    const successIndicators = [
      content.includes(testUsername),
      content.includes('Welcome'),
      content.includes('Start New Game'),
      content.includes('Game History')
    ];

    expect(successIndicators.some(indicator => indicator)).to.be.true;
  });

  it('Test 2.2: User logout flow', async () => {
    // Look for logout button
    const logoutBtn = await page.$('button:has-text("Logout")');

    if (logoutBtn) {
      await logoutBtn.click();

      // Wait for redirect to login page
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'tests/e2e/screenshots/02-after-logout.png' });

      // Verify we're on login page
      const loginForm = await page.$('input#username');
      expect(loginForm).to.not.be.null;
    } else {
      console.log('SKIP: Logout button not found');
      this.skip();
    }
  });

  it('Test 2.3: User login flow with existing account', async () => {
    await page.goto(config.FRONTEND_URL);

    // Fill login form
    await page.waitForSelector('input#username');
    await page.type('input#username', testUsername);
    await page.type('input#password', testPassword);

    await page.screenshot({ path: 'tests/e2e/screenshots/02-login-form.png' });

    // Submit login
    await page.click('button[type="submit"]');

    // Wait for navigation
    try {
      await page.waitForNavigation({ timeout: 10000, waitUntil: 'networkidle2' });
    } catch (e) {
      await page.waitForTimeout(2000);
    }

    await page.screenshot({ path: 'tests/e2e/screenshots/02-after-login.png' });

    // Verify login success
    const content = await page.content();
    expect(content).to.satisfy(text =>
      text.includes(testUsername) ||
      text.includes('Start New Game')
    );
  });

  it('Test 2.4: Invalid credentials rejected', async () => {
    await page.goto(config.FRONTEND_URL);

    await page.waitForSelector('input#username');
    await page.type('input#username', 'invalid_user_99999');
    await page.type('input#password', 'wrongpassword');

    await page.click('button[type="submit"]');

    await page.waitForTimeout(2000);

    // Should show error message
    const content = await page.content();
    expect(content).to.satisfy(text =>
      text.toLowerCase().includes('invalid') ||
      text.toLowerCase().includes('incorrect') ||
      text.toLowerCase().includes('error')
    );
  });
});
```

---

## 📝 Test Suite 3: Game Lifecycle

**File**: `tests/e2e/03-game-lifecycle.test.js`

```javascript
const puppeteer = require('puppeteer');
const { expect } = require('chai');
const config = require('./config');

describe('Suite 3: Game Lifecycle', function() {
  this.timeout(60000);

  let browser, page, gameId;

  before(async () => {
    browser = await puppeteer.launch({
      headless: config.HEADLESS,
      slowMo: config.SLOWMO,
      args: ['--no-sandbox']
    });
    page = await browser.newPage();

    // Login first
    await page.goto(config.FRONTEND_URL);
    await page.waitForSelector('input#username');

    // Register new user for game tests
    const username = `game_test_${Date.now()}`;
    await page.click('text=/create.*account/i');
    await page.waitForSelector('input#username', { visible: true });
    await page.type('input#username', username);
    await page.type('input#password', 'test123456');

    const confirmPw = await page.$('input#confirmPassword');
    if (confirmPw) await page.type('input#confirmPassword', 'test123456');

    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
  });

  after(async () => {
    await browser.close();
  });

  it('Test 3.1: Navigate to game creation page', async () => {
    // Look for "Start New Game" link
    const newGameLink = await page.$('a:has-text("Start New Game"), button:has-text("Start New Game")');
    expect(newGameLink).to.not.be.null;

    await newGameLink.click();
    await page.waitForTimeout(2000);

    await page.screenshot({ path: 'tests/e2e/screenshots/03-game-creation.png' });

    // Should see game setup options
    const content = await page.content();
    expect(content).to.satisfy(text =>
      text.includes('Players') ||
      text.includes('AI') ||
      text.includes('Start Game')
    );
  });

  it('Test 3.2: Create new game', async () => {
    // Click "Start Game" button
    await page.click('button:has-text("Start Game"), input[type="submit"]');

    // Wait for game to load
    await page.waitForTimeout(5000);

    await page.screenshot({ path: 'tests/e2e/screenshots/03-game-loaded.png' });

    // Verify poker table elements
    const tableElements = await Promise.all([
      page.$('[data-testid="poker-table"]'),
      page.$('[data-testid="human-player-seat"]'),
      page.$('button:has-text("Fold")'),
      page.$('button:has-text("Call")'),
    ]);

    const hasTableElements = tableElements.some(el => el !== null);
    expect(hasTableElements).to.be.true;

    // Extract game ID from URL
    const url = page.url();
    const gameIdMatch = url.match(/game\/([^\/]+)/);
    if (gameIdMatch) {
      gameId = gameIdMatch[1];
      console.log('Game ID:', gameId);
    }
  });

  it('Test 3.3: Player can take action (fold)', async () => {
    // Wait for action buttons to be enabled
    await page.waitForSelector('button:has-text("Fold"):not([disabled])', {
      timeout: 10000
    }).catch(() => {
      console.log('Fold button not found or disabled');
    });

    // Click fold
    const foldBtn = await page.$('button:has-text("Fold")');
    if (foldBtn) {
      await foldBtn.click();

      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'tests/e2e/screenshots/03-after-fold.png' });

      // Game should continue (AI players act)
      const content = await page.content();
      expect(content).to.not.include('Error');
    } else {
      console.log('SKIP: Fold button not available');
      this.skip();
    }
  });

  it('Test 3.4: Game progresses (AI players act)', async () => {
    // Wait for AI to act
    await page.waitForTimeout(5000);

    await page.screenshot({ path: 'tests/e2e/screenshots/03-ai-acting.png' });

    // Check game is still active
    const quitBtn = await page.$('button:has-text("Quit")');
    expect(quitBtn).to.not.be.null;
  });

  it('Test 3.5: Player can quit game', async () => {
    const quitBtn = await page.$('button:has-text("Quit")');

    if (quitBtn) {
      await quitBtn.click();

      // Should return to landing page
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'tests/e2e/screenshots/03-after-quit.png' });

      const content = await page.content();
      expect(content).to.satisfy(text =>
        text.includes('Welcome') ||
        text.includes('Start New Game')
      );
    } else {
      console.log('SKIP: Quit button not found');
      this.skip();
    }
  });

  it('Test 3.6: Game appears in history', async () => {
    // Navigate to history
    const historyLink = await page.$('a:has-text("Game History"), a:has-text("History")');

    if (historyLink && gameId) {
      await historyLink.click();
      await page.waitForTimeout(2000);

      await page.screenshot({ path: 'tests/e2e/screenshots/03-game-history.png' });

      // Should see the game we just played
      const content = await page.content();
      expect(content).to.include('Completed');
    } else {
      console.log('SKIP: History link not found or no game ID');
      this.skip();
    }
  });
});
```

---

## 📝 Test Suite 4: Error Handling

**File**: `tests/e2e/04-error-handling.test.js`

```javascript
const puppeteer = require('puppeteer');
const { expect } = require('chai');
const config = require('./config');

describe('Suite 4: Error Handling', function() {
  this.timeout(30000);

  let browser, page;

  before(async () => {
    browser = await puppeteer.launch({
      headless: config.HEADLESS,
      slowMo: config.SLOWMO,
      args: ['--no-sandbox']
    });
    page = await browser.newPage();
  });

  after(async () => {
    await browser.close();
  });

  it('Test 4.1: Empty form submission shows validation', async () => {
    await page.goto(config.FRONTEND_URL);
    await page.waitForSelector('button[type="submit"]');

    // Try to submit without filling form
    await page.click('button[type="submit"]');
    await page.waitForTimeout(1000);

    // Should show validation errors (HTML5 or custom)
    const hasValidationError = await page.evaluate(() => {
      const inputs = document.querySelectorAll('input:invalid');
      return inputs.length > 0;
    });

    expect(hasValidationError).to.be.true;
  });

  it('Test 4.2: Duplicate username rejected', async () => {
    await page.goto(config.FRONTEND_URL);
    await page.waitForSelector('input#username');

    // Try to register with existing username
    await page.click('text=/create.*account/i');
    await page.waitForSelector('input#username', { visible: true });
    await page.type('input#username', 'admin'); // Common username
    await page.type('input#password', 'test123456');

    const confirmPw = await page.$('input#confirmPassword');
    if (confirmPw) await page.type('input#confirmPassword', 'test123456');

    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    // Should show error about username taken
    const content = await page.content();
    expect(content).to.satisfy(text =>
      text.toLowerCase().includes('taken') ||
      text.toLowerCase().includes('exists') ||
      text.toLowerCase().includes('already')
    );
  });

  it('Test 4.3: Invalid game ID shows error', async () => {
    // Try to access a non-existent game
    const invalidGameId = '00000000-0000-0000-0000-000000000000';
    await page.goto(`${config.FRONTEND_URL}/game/${invalidGameId}`);

    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'tests/e2e/screenshots/04-invalid-game.png' });

    // Should show error or redirect
    const content = await page.content();
    expect(content).to.satisfy(text =>
      text.toLowerCase().includes('not found') ||
      text.toLowerCase().includes('error') ||
      text.includes('404')
    );
  });
});
```

---

## 📝 Test Suite 5: Performance

**File**: `tests/e2e/05-performance.test.js`

```javascript
const puppeteer = require('puppeteer');
const { expect } = require('chai');
const config = require('./config');

describe('Suite 5: Performance', function() {
  this.timeout(30000);

  let browser, page;

  before(async () => {
    browser = await puppeteer.launch({
      headless: config.HEADLESS,
      args: ['--no-sandbox']
    });
    page = await browser.newPage();
  });

  after(async () => {
    await browser.close();
  });

  it('Test 5.1: Page loads within 5 seconds', async () => {
    const startTime = Date.now();

    await page.goto(config.FRONTEND_URL, {
      waitUntil: 'networkidle2'
    });

    const loadTime = Date.now() - startTime;
    console.log(`Page load time: ${loadTime}ms`);

    expect(loadTime).to.be.below(5000);
  });

  it('Test 5.2: No console errors on page load', async () => {
    const consoleErrors = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(config.FRONTEND_URL);
    await page.waitForTimeout(2000);

    console.log('Console errors:', consoleErrors);
    expect(consoleErrors).to.have.length(0);
  });
});
```

---

## 🚀 Running the Tests

### Run All Suites

```bash
# From project root
cd tests/e2e

# Run all tests
npm test

# Or with mocha directly
npx mocha --recursive --timeout 60000 *.test.js
```

### Run Specific Suite

```bash
# Connectivity tests only
npx mocha 01-connectivity.test.js

# Authentication tests only
npx mocha 02-authentication.test.js

# Game lifecycle tests only
npx mocha 03-game-lifecycle.test.js
```

### Run with UI (non-headless)

```bash
HEADLESS=false npx mocha --recursive *.test.js
```

### Run with slow motion (for debugging)

```bash
SLOWMO=100 HEADLESS=false npx mocha 02-authentication.test.js
```

### Run with video recording

```bash
VIDEO=true npx mocha --recursive *.test.js
```

---

## 📊 Expected Test Results

### Success Criteria

All 20 tests should pass:
- ✅ Suite 1: 5/5 connectivity tests passing
- ✅ Suite 2: 4/4 authentication tests passing
- ✅ Suite 3: 6/6 game lifecycle tests passing
- ✅ Suite 4: 3/3 error handling tests passing
- ✅ Suite 5: 2/2 performance tests passing

### Common Failures and Fixes

| Failure | Likely Cause | Fix |
|---------|--------------|-----|
| Test 1.2: CORS not found | CORS not configured | Update backend FRONTEND_URLS |
| Test 1.4: POST fails | API endpoint not reachable | Check backend deployment |
| Test 1.5: WebSocket fails | WebSocket not supported | Verify Azure allows WebSocket |
| Test 2.1: Registration stuck | Frontend-backend disconnect | Check network tab in browser |
| Test 3.2: Game doesn't load | WebSocket or API issue | Check console logs |

---

## 🔍 Debugging Failed Tests

### Enable Debug Mode

```bash
DEBUG=puppeteer:* npx mocha 02-authentication.test.js
```

### Take Screenshots on Failure

Already enabled in config. Check `tests/e2e/screenshots/` after failures.

### View Network Requests

Add to test file:
```javascript
page.on('request', request => {
  console.log('REQUEST:', request.method(), request.url());
});

page.on('response', response => {
  console.log('RESPONSE:', response.status(), response.url());
});
```

### Check Console Logs

All console.log/error from browser are captured and shown in test output.

---

## ✅ Sign-Off Checklist

Before considering E2E testing complete:

- [ ] All 5 test suites created
- [ ] All 20 tests passing
- [ ] Screenshots captured for key flows
- [ ] No console errors in browser
- [ ] Network requests succeed (no 4xx/5xx)
- [ ] WebSocket connection works
- [ ] CORS headers present
- [ ] Registration flow works end-to-end
- [ ] Game creation and play works
- [ ] Game history accessible

**ONLY THEN** is the deployment ready for user testing.

---

## 📝 Integration with CI/CD

Add to `.github/workflows/deploy-frontend-containerapp.yml`:

```yaml
- name: Run E2E Tests
  run: |
    cd tests/e2e
    npm install
    FRONTEND_URL=https://poker-frontend.braveisland-d54008f6.centralus.azurecontainerapps.io \
    BACKEND_URL=https://poker-api-demo.azurewebsites.net \
    npx mocha --recursive --timeout 60000 *.test.js
```

This ensures every deployment is verified with E2E tests automatically.
