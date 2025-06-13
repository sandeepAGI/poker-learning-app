# Frontend Architecture Documentation

## Overview
React-based poker game frontend with centralized state management using React Context and useReducer.

## Core Architecture

### State Management (`src/store/gameStore.js`)
- **Pattern**: React Context + useReducer (Redux-like pattern)
- **Global State**: Game state, player data, UI state
- **Actions**: Async actions for API calls, synchronous actions for state updates

### Component Hierarchy
```
App.js
├── AuthModal.js (when not authenticated)
└── GameProvider (when authenticated)
    └── PokerGameContainer.js
        ├── GameLobby.js (when gameState === LOBBY)
        └── Game Components (when gameState === PLAYING)
            ├── PokerTable.js
            ├── GameControls.js
            ├── PlayerStats.js
            └── Action History
```

## Critical Data Flow

### 1. Authentication Flow
```
User enters name → AuthModal → createPlayer API → setPlayer action → App shows PokerGameContainer
```

### 2. Game Creation Flow
```
GameLobby → createGame API → UPDATE_GAME_STATE → gameState becomes PLAYING → Show poker table
```

### 3. Action Submission Flow (THE PROBLEM AREA)
```
User clicks raise → GameControls → submitAction → gameApi.submitAction → 
mapBackendResponse → UPDATE_GAME_STATE → Should stay PLAYING but going to LOBBY
```

## State Shape

### Game Store State
```javascript
{
  // Game identification
  gameId: string | null,
  gameState: 'lobby' | 'playing' | 'finished',
  roundState: 'pre_flop' | 'flop' | 'turn' | 'river' | 'showdown',
  
  // Player data
  playerId: string | null,
  playerName: string | null,
  isAuthenticated: boolean,
  
  // Game data
  players: Array<Player>,
  communityCards: Array<string>,
  pot: number,
  currentBet: number,
  currentPlayerIndex: number,
  dealerIndex: number,
  
  // UI state
  loading: boolean,
  error: string | null,
  selectedAction: string | null,
  betAmount: number,
  actionHistory: Array<Action>
}
```

### Player Object Structure
```javascript
{
  id: string,           // Could be 'player_id' from backend
  name: string,         // Player display name
  chips: number,        // Current chip count
  current_bet: number,  // Current bet amount
  status: 'active' | 'folded' | 'eliminated',
  hole_cards: Array<string> | null,  // Only visible for human player
  is_active: boolean
}
```

## Action Types and Reducers

### Critical Actions
- `SET_PLAYER`: Sets authentication data
- `UPDATE_GAME_STATE`: **CRITICAL** - Updates entire game state from backend
- `SET_GAME_ID`: Sets current game ID
- `ADD_ACTION_TO_HISTORY`: Adds player action to history

### Critical Reducer Logic
The `UPDATE_GAME_STATE` reducer is where the lobby redirect bug likely occurs:
```javascript
case ACTION_TYPES.UPDATE_GAME_STATE:
  const updatedState = { ...state, ...action.payload };
  
  // CRITICAL: This logic determines if we stay in game or go to lobby
  if (state.gameState === GAME_STATES.PLAYING && 
      action.payload.gameState === GAME_STATES.LOBBY && 
      updatedState.players && updatedState.players.length > 0) {
    updatedState.gameState = GAME_STATES.PLAYING;  // Should prevent lobby redirect
  }
```

## Backend Response Mapping

### Critical Function: `mapBackendResponse()`
This function transforms backend responses into frontend state:
```javascript
const mapBackendResponse = (response) => {
  const hasPlayers = response.players && response.players.length > 0;
  const isGameFinished = response.current_state === 'finished' || response.game_status === 'finished';
  
  // CRITICAL: This determines gameState
  let gameState = GAME_STATES.PLAYING;
  if (!hasPlayers || isGameFinished) {
    gameState = GAME_STATES.LOBBY;  // This might be triggering incorrectly
  }
  
  return { gameState, ...otherData };
}
```

## Component Rendering Logic

### PokerGameContainer Conditional Rendering
```javascript
{state.gameState === GAME_STATES.LOBBY ? (
  <GameLobby onCreateGame={handleCreateGame} />  // CREATE NEW GAME SCREEN
) : (
  // POKER GAME COMPONENTS
)}
```

**This is where the redirect happens!** If `state.gameState` becomes `LOBBY`, user sees create new game screen.

## API Integration

### Game API Methods
- `createPlayer(data)`: Creates player and returns auth token
- `createGame(config)`: Creates new game, returns game state
- `submitAction(gameId, playerId, action)`: **CRITICAL** - Submits player action
- `getGameState(gameId, playerId)`: Gets current game state

### WebSocket Integration
- Real-time updates via WebSocket
- Action broadcasting to other players
- Connection state management

## Identified Problem Areas

### 1. Action Submission Flow
The `submitAction` flow is where the bug occurs:
1. User submits action (raise)
2. `gameApi.submitAction()` succeeds (backend logs confirm this)
3. Response goes through `mapBackendResponse()`
4. Result triggers `UPDATE_GAME_STATE` 
5. **Something causes gameState to become LOBBY**
6. PokerGameContainer shows GameLobby (create new game screen)

### 2. Potential Root Causes
- Backend response format unexpected
- `mapBackendResponse()` logic incorrect
- Reducer logic failing
- State corruption during update
- Race condition with multiple state updates

### 3. Testing Strategy
Need comprehensive tests for:
- `mapBackendResponse()` with various backend responses
- `UPDATE_GAME_STATE` reducer with different scenarios
- `submitAction` flow end-to-end
- Component rendering based on gameState
- Error handling in action submission

## Next Steps

1. **Unit test `mapBackendResponse()`** with real backend response data
2. **Unit test the reducer** with various action payloads  
3. **Integration test the `submitAction` flow**
4. **Mock backend responses** to test edge cases
5. **Test component rendering** based on gameState changes