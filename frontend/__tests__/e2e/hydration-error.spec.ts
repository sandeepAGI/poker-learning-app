import { test, expect } from '@playwright/test';

test.describe('Hydration Error Detection', () => {
  test('no hydration errors when navigating to /game/new', async ({ page }) => {
    const consoleErrors: string[] = [];

    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Navigate to game/new
    await page.goto('http://localhost:3001/game/new');
    await page.waitForLoadState('networkidle');

    // Check for hydration errors
    const hydrationErrors = consoleErrors.filter(err =>
      err.includes('Hydration') ||
      err.includes('server rendered HTML') ||
      err.includes('did not match')
    );

    expect(hydrationErrors).toHaveLength(0);
  });
});
