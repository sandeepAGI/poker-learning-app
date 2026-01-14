import { useGameStore } from '../store';

describe('Zustand Store - WebSocket Management', () => {
  it('disconnectWebSocket does not block execution', async () => {
    const store = useGameStore.getState();

    // Mock WebSocket client with slow disconnect
    const mockDisconnect = jest.fn(() => {
      return new Promise(resolve => setTimeout(resolve, 1000)); // Slow disconnect
    });

    // @ts-ignore - Setting mock for testing
    store.wsClient = { disconnect: mockDisconnect } as any;

    const startTime = Date.now();
    store.disconnectWebSocket();
    const endTime = Date.now();

    // Should not wait for disconnect
    expect(endTime - startTime).toBeLessThan(100);

    // State should be updated immediately
    const currentState = useGameStore.getState();
    expect(currentState.wsClient).toBeNull();
  });
});
