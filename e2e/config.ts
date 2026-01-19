/**
 * E2E Test Configuration
 * Environment-specific URLs and test settings
 */

export const config = {
  // Environment URLs
  FRONTEND_URL: process.env.FRONTEND_URL || 'http://localhost:3000',
  BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8000',

  // Test timeouts
  PAGE_LOAD_TIMEOUT: 30000,
  API_CALL_TIMEOUT: 10000,
  WEBSOCKET_TIMEOUT: 15000,

  // Test user credentials (dynamic to avoid conflicts)
  TEST_USERNAME: `test_${Date.now()}`,
  TEST_PASSWORD: 'TestPassword123!',

  // Test data
  AI_PLAYER_COUNT: 3,
  MIN_GAME_HANDS: 2, // Minimum hands to play in test games
};

/**
 * Generate a unique test username to avoid conflicts
 */
export function generateTestUsername(prefix: string = 'test'): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substring(7)}`;
}

/**
 * Check if backend is healthy
 */
export async function isBackendHealthy(backendUrl: string): Promise<boolean> {
  try {
    const response = await fetch(`${backendUrl}/health`);
    const data = await response.json();
    return data.status === 'healthy';
  } catch {
    return false;
  }
}
