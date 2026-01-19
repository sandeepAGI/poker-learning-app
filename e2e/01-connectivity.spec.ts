import { test, expect, Page } from '@playwright/test';
import { config, generateTestUsername, isBackendHealthy } from './config';

/**
 * Suite 1: Frontend-Backend Connectivity
 *
 * Tests that verify the frontend can communicate with the backend:
 * - Page loads successfully
 * - CORS headers are present
 * - API endpoints are reachable
 * - POST requests work
 * - WebSocket connections can be established
 */

test.describe('Suite 1: Frontend-Backend Connectivity', () => {
  test.beforeAll(async () => {
    // Verify backend is healthy before running tests
    const healthy = await isBackendHealthy(config.BACKEND_URL);
    if (!healthy) {
      throw new Error(`Backend at ${config.BACKEND_URL} is not healthy. Run backend server first.`);
    }
  });

  test('1.1: Frontend page loads with HTTP 200', async ({ page }) => {
    // Use 'domcontentloaded' instead of 'networkidle' to avoid timeout on continuous requests
    const response = await page.goto('/', {
      waitUntil: 'domcontentloaded',
      timeout: config.PAGE_LOAD_TIMEOUT
    });

    expect(response?.status()).toBe(200);

    // Verify page has basic content
    await expect(page.locator('input#username')).toBeVisible({ timeout: 5000 });

    // Take screenshot for documentation
    await page.screenshot({ path: 'e2e/screenshots/01-page-load.png' });
  });

  test('1.2: CORS headers present on API requests', async ({ page }) => {
    let corsHeader: string | null = null;

    // Listen for API responses
    page.on('response', (response) => {
      if (response.url().includes(config.BACKEND_URL)) {
        const headers = response.headers();
        corsHeader = headers['access-control-allow-origin'] || null;
      }
    });

    // Navigate to trigger potential API calls
    await page.goto('/');
    await page.waitForSelector('input#username', { timeout: 5000 });

    // Make a test API call from browser context
    await page.evaluate(async (backendUrl) => {
      await fetch(`${backendUrl}/health`);
    }, config.BACKEND_URL);

    // Wait for response to be processed
    await page.waitForTimeout(2000);

    // CORS header should be present
    expect(corsHeader).not.toBeNull();
    console.log('CORS header:', corsHeader);
  });

  test('1.3: Backend health endpoint reachable from browser', async ({ page }) => {
    await page.goto('/');

    const healthData = await page.evaluate(async (backendUrl) => {
      const response = await fetch(`${backendUrl}/health`);
      return await response.json();
    }, config.BACKEND_URL);

    expect(healthData).toHaveProperty('status', 'healthy');
  });

  test('1.4: Frontend can make POST requests to backend', async ({ page }) => {
    await page.goto('/');

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
      } catch (error: any) {
        return { error: error.message };
      }
    }, config.BACKEND_URL);

    console.log('POST test response:', testResponse);

    expect(testResponse).not.toHaveProperty('error');
    expect([200, 201]).toContain(testResponse.status);
    expect(testResponse.data).toHaveProperty('token');
  });

  test('1.5: WebSocket connection can be established', async ({ page }) => {
    await page.goto('/');

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
    const wsConnected = await page.evaluate(async (args) => {
      return new Promise<boolean>((resolve) => {
        const wsUrl = args.backendUrl.replace('https:', 'wss:').replace('http:', 'ws:') +
                      `/ws/${args.gameId}?token=${args.token}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log('WebSocket connected successfully');
          ws.close();
          resolve(true);
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          resolve(false);
        };

        // Timeout after configured duration
        setTimeout(() => {
          console.error('WebSocket connection timeout');
          ws.close();
          resolve(false);
        }, args.timeout);
      });
    }, {
      backendUrl: config.BACKEND_URL,
      gameId: gameData.gameId,
      token: gameData.token,
      timeout: config.WEBSOCKET_TIMEOUT
    });

    expect(wsConnected).toBe(true);
  });
});
