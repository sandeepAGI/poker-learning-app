import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for E2E tests
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: './tests/e2e',
  testMatch: '**/*.spec.ts', // Only match .spec.ts files
  fullyParallel: false, // Run tests sequentially for poker game state
  forbidOnly: !!process.env.CI, // Fail if test.only in CI
  retries: process.env.CI ? 2 : 0, // Retry on CI
  workers: 1, // Single worker for game state isolation
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  // Configure projects
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Auto-start servers
  webServer: [
    {
      command: 'cd backend && TEST_MODE=1 python main.py',
      url: 'http://localhost:8000',
      reuseExistingServer: true, // Reuse if already running
      timeout: 30000,
    },
    {
      command: 'cd frontend && npm run build && npm start',
      url: 'http://localhost:3000',
      reuseExistingServer: true,
      timeout: 120000,
    },
  ],
});
