import { test, expect } from '@playwright/test';
import { config } from './config';

/**
 * Suite 5: Performance
 *
 * Tests that verify the application performs within acceptable limits:
 * - Page loads within reasonable time
 * - No console errors on page load
 * - Resources load efficiently
 */

test.describe('Suite 5: Performance', () => {
  test('5.1: Page loads within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    const response = await page.goto('/', {
      waitUntil: 'networkidle',
      timeout: config.PAGE_LOAD_TIMEOUT
    });

    const loadTime = Date.now() - startTime;

    console.log(`Page load time: ${loadTime}ms`);

    await page.screenshot({ path: 'e2e/screenshots/05-page-load-time.png' });

    // Expect page to load within 10 seconds (accounting for Azure cold starts)
    // For local development, this should be under 3 seconds
    const threshold = process.env.CI ? 10000 : 5000;
    expect(loadTime).toBeLessThan(threshold);

    // Verify successful response
    expect(response?.status()).toBe(200);
  });

  test('5.2: No console errors on page load', async ({ page }) => {
    const consoleErrors: string[] = [];
    const consoleWarnings: string[] = [];

    // Capture console messages
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      } else if (msg.type() === 'warning') {
        consoleWarnings.push(msg.text());
      }
    });

    // Navigate to home page
    await page.goto('/', { waitUntil: 'networkidle' });

    // Wait for page to fully render
    await page.waitForTimeout(2000);

    await page.screenshot({ path: 'e2e/screenshots/05-console-check.png' });

    console.log('Console errors:', consoleErrors);
    console.log('Console warnings:', consoleWarnings);

    // Should have no console errors
    // Note: Some warnings might be acceptable (e.g., React dev warnings)
    expect(consoleErrors.length).toBe(0);
  });

  test('5.3: No failed network requests', async ({ page }) => {
    const failedRequests: string[] = [];

    // Capture failed requests
    page.on('requestfailed', (request) => {
      failedRequests.push(`${request.method()} ${request.url()} - ${request.failure()?.errorText}`);
    });

    // Navigate and interact
    await page.goto('/', { waitUntil: 'networkidle' });

    await page.waitForTimeout(2000);

    console.log('Failed requests:', failedRequests);

    // Should have no failed requests
    expect(failedRequests.length).toBe(0);
  });

  test('5.4: Login page loads quickly', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/login', {
      waitUntil: 'networkidle',
      timeout: config.PAGE_LOAD_TIMEOUT
    });

    const loadTime = Date.now() - startTime;

    console.log(`Login page load time: ${loadTime}ms`);

    await page.screenshot({ path: 'e2e/screenshots/05-login-load-time.png' });

    // Login page should load very quickly (no complex components)
    const threshold = process.env.CI ? 8000 : 4000;
    expect(loadTime).toBeLessThan(threshold);

    // Verify page is interactive
    await expect(page.locator('input#username')).toBeVisible();
    await expect(page.locator('input#password')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('5.5: Backend health check responds quickly', async ({ page }) => {
    await page.goto('/');

    const startTime = Date.now();

    const healthStatus = await page.evaluate(async (backendUrl) => {
      const start = Date.now();
      try {
        const response = await fetch(`${backendUrl}/health`);
        const data = await response.json();
        const duration = Date.now() - start;

        return {
          status: data.status,
          duration,
          ok: response.ok
        };
      } catch (error: any) {
        return {
          error: error.message,
          duration: Date.now() - start
        };
      }
    }, config.BACKEND_URL);

    const duration = Date.now() - startTime;

    console.log('Health check response:', healthStatus);
    console.log('Total time:', duration, 'ms');

    // Health check should respond within 2 seconds
    expect(healthStatus.duration).toBeLessThan(2000);

    // Should be healthy
    expect(healthStatus).toHaveProperty('status', 'healthy');
    expect(healthStatus.ok).toBe(true);
  });

  test('5.6: Images and assets load successfully', async ({ page }) => {
    const resourceErrors: string[] = [];

    // Track resource loading failures
    page.on('response', (response) => {
      if (!response.ok() && response.request().resourceType() === 'image') {
        resourceErrors.push(`${response.url()} - ${response.status()}`);
      }
    });

    await page.goto('/', { waitUntil: 'networkidle' });

    // Navigate to game creation to check card images
    const newGameLink = page.locator('a:has-text("Start New Game")');
    if (await newGameLink.isVisible().catch(() => false)) {
      await newGameLink.click();
      await page.waitForTimeout(2000);
    }

    console.log('Resource errors:', resourceErrors);

    await page.screenshot({ path: 'e2e/screenshots/05-resource-check.png' });

    // Should have no image loading failures
    expect(resourceErrors.length).toBe(0);
  });
});
