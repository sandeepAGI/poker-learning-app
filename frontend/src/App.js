import React, { useState, useEffect } from 'react';
import { GameProvider } from './store/gameStore';
import PokerGameContainer from './components/PokerGameContainer';
import AuthModal from './components/AuthModal';
import DebugPanel from './components/DebugPanel';
import DebugDiagnostic from './components/DebugDiagnostic';
import ErrorBoundary from './components/ErrorBoundary';
import { auth } from './services/apiClient';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showDebug, setShowDebug] = useState(false);

  useEffect(() => {
    // Check for existing authentication but allow fresh start option
    const hasToken = auth.isAuthenticated();
    const shouldAskForName = localStorage.getItem('ask_for_name_on_startup') === 'true';
    
    // If user wants fresh start or no token exists, show auth modal
    if (shouldAskForName || !hasToken) {
      setIsAuthenticated(false);
      localStorage.removeItem('ask_for_name_on_startup');
    } else {
      setIsAuthenticated(hasToken);
    }

    // Listen for authentication events
    const handleAuthRequired = () => {
      setIsAuthenticated(false);
    };

    window.addEventListener('auth:required', handleAuthRequired);

    // Cleanup
    return () => {
      window.removeEventListener('auth:required', handleAuthRequired);
    };
  }, []);

  const handleLogin = (token, playerData) => {
    auth.setToken(token);
    setIsAuthenticated(true);
    // Store player data for later use
    localStorage.setItem('player_data', JSON.stringify(playerData));
  };

  const handleLogout = () => {
    auth.clearToken();
    localStorage.removeItem('player_data');
    localStorage.removeItem('game_data'); // Clear any cached game data
    setIsAuthenticated(false);
  };

  const toggleDebug = () => {
    setShowDebug(!showDebug);
  };

  return (
    <ErrorBoundary>
      <div className="bg-gray-900 text-white min-h-screen relative">
        {/* Main application content */}
        {isAuthenticated ? (
          <GameProvider>
            {/* Debug toggle button */}
            {process.env.NODE_ENV === 'development' && (
              <button
                onClick={toggleDebug}
                className="fixed top-4 right-4 z-50 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
              >
                Debug
              </button>
            )}

            {/* Debug panel */}
            {showDebug && <DebugPanel />}
            
            {/* Bug diagnostic tool */}
            <DebugDiagnostic />

            <PokerGameContainer onLogout={handleLogout} />
          </GameProvider>
        ) : (
          <AuthModal onLogin={handleLogin} />
        )}
      </div>
    </ErrorBoundary>
  );
}

export default App;
