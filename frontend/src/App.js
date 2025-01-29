import React from 'react';
import PokerTable from './components/PokerTable';
import Player from './components/Player';
import GameControls from './components/GameControls';

function App() {
  return (
    <div className="bg-gray-900 text-white min-h-screen">
      <PokerTable />
      <div className="mt-4">
        <Player name="John Doe" chips={1500} />
        <Player name="Jane Doe" chips={2000} />
      </div>
      <div className="mt-4">
        <GameControls />
      </div>
    </div>
  );
}

export default App;
