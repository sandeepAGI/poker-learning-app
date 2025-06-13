import React from 'react';
import { useGame } from '../store/gameStore';

const DebugDiagnostic = () => {
  const { state, actions } = useGame();

  const runDiagnosticTest = () => {
    console.log('=== LOBBY REDIRECT BUG DIAGNOSTIC ===');
    
    // Test 1: Current game state
    console.log('1. Current Game State:', {
      gameState: state.gameState,
      gameId: state.gameId,
      playerId: state.playerId,
      playerName: state.playerName,
      playersCount: state.players.length,
      loading: state.loading,
      error: state.error
    });
    
    // Test 2: Players data
    console.log('2. Players Data:', state.players);
    
    // Test 3: Test mapBackendResponse with mock data
    const mockSuccessfulActionResponse = {
      players: [
        { player_id: state.playerId, name: state.playerName, chips: 950, current_bet: 50, status: 'active' },
        { player_id: 'ai_1', name: 'AI Player', chips: 950, current_bet: 50, status: 'active' }
      ],
      pot: 100,
      current_bet: 50,
      current_state: 'pre_flop',
      current_player: 'ai_1',
      community_cards: [],
      hand_number: 1
    };
    
    console.log('3. Mock Response to Test:', mockSuccessfulActionResponse);
    
    // Test the mapping logic
    const hasPlayers = mockSuccessfulActionResponse.players && mockSuccessfulActionResponse.players.length > 0;
    const isGameFinished = mockSuccessfulActionResponse.current_state === 'finished' || mockSuccessfulActionResponse.game_status === 'finished';
    
    console.log('4. Mapping Logic Test:', {
      hasPlayers,
      isGameFinished,
      shouldBePlayingState: hasPlayers && !isGameFinished,
      current_state: mockSuccessfulActionResponse.current_state,
      game_status: mockSuccessfulActionResponse.game_status
    });
    
    // Test 4: Submit a test action and monitor state changes
    if (state.gameId && state.playerId && state.gameState === 'playing') {
      console.log('5. Testing Action Submission Flow...');
      
      // Add a state change listener
      const originalSubmitAction = actions.submitAction;
      
      console.log('Before action submission:', {
        gameState: state.gameState,
        players: state.players.length
      });
      
      // This would need to be monitored in real-time
      console.log('Ready to submit test action. Check Network tab and console during next action.');
    } else {
      console.log('5. Cannot test action submission - game not active');
    }
    
    // Test 5: Check localStorage
    console.log('6. LocalStorage Data:', {
      player_data: localStorage.getItem('player_data'),
      auth_token: localStorage.getItem('auth_token'),
      ask_for_name_on_startup: localStorage.getItem('ask_for_name_on_startup')
    });
  };

  const simulateBugScenario = async () => {
    if (!state.gameId || !state.playerId) {
      console.error('Cannot simulate - game not initialized');
      return;
    }

    console.log('=== SIMULATING LOBBY REDIRECT BUG ===');
    
    try {
      // Mock the exact scenario that causes the bug
      const mockBackendResponse = {
        players: [
          { player_id: state.playerId, name: state.playerName, chips: 950, status: 'active' },
          { player_id: 'ai_1', name: 'AI1', chips: 1050, status: 'active' }
        ],
        pot: 100,
        current_state: 'pre_flop'
      };
      
      console.log('Simulating backend response:', mockBackendResponse);
      
      // Manually trigger the state update to see what happens
      console.log('State before update:', state.gameState);
      
      // This would trigger the mapBackendResponse and UPDATE_GAME_STATE logic
      // We can't directly call it here, but we can analyze what should happen
      
      const hasPlayers = mockBackendResponse.players && mockBackendResponse.players.length > 0;
      const isGameFinished = mockBackendResponse.current_state === 'finished';
      
      console.log('Analysis:', {
        hasPlayers,
        isGameFinished,
        expectedGameState: hasPlayers && !isGameFinished ? 'playing' : 'lobby'
      });
      
    } catch (error) {
      console.error('Simulation error:', error);
    }
  };

  const checkActionFlow = () => {
    console.log('=== ACTION FLOW MONITOR ===');
    
    // Monitor the action submission function
    const originalSubmitAction = actions.submitAction;
    
    // Override with monitoring version
    actions.submitAction = async (action, amount) => {
      console.log('ACTION SUBMITTED:', { action, amount });
      console.log('State before action:', {
        gameState: state.gameState,
        playersCount: state.players.length
      });
      
      try {
        const result = await originalSubmitAction(action, amount);
        console.log('ACTION RESULT:', result);
        
        // Check state after a delay
        setTimeout(() => {
          console.log('State after action:', {
            gameState: state.gameState,
            playersCount: state.players.length
          });
          
          if (state.gameState === 'lobby') {
            console.error('🚨 BUG DETECTED: Game went to lobby after action!');
          }
        }, 100);
        
        return result;
      } catch (error) {
        console.error('Action failed:', error);
        throw error;
      }
    };
    
    console.log('Action flow monitoring enabled. Submit an action to test.');
  };

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 bg-gray-800 border border-gray-600 rounded-lg p-4 text-white text-xs max-w-sm z-50">
      <h3 className="font-bold mb-2 text-red-400">🐛 Bug Diagnostic Tool</h3>
      
      <div className="space-y-2">
        <button
          onClick={runDiagnosticTest}
          className="block w-full bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-xs"
        >
          Run Diagnostic Test
        </button>
        
        <button
          onClick={simulateBugScenario}
          className="block w-full bg-yellow-600 hover:bg-yellow-700 px-3 py-1 rounded text-xs"
        >
          Simulate Bug Scenario
        </button>
        
        <button
          onClick={checkActionFlow}
          className="block w-full bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-xs"
        >
          Monitor Action Flow
        </button>
        
        <div className="text-xs text-gray-400 mt-2">
          Check browser console for results
        </div>
      </div>
    </div>
  );
};

export default DebugDiagnostic;