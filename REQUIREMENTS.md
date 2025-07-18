# Poker Learning App - Requirements (Preserve Core Backend)

## Project Philosophy
**Preserve the solid poker engine, simplify the API complexity.** Your backend game logic, AI strategies, and hand evaluation are excellent - we'll extract and keep those while building a simple API and frontend.

## Core Goal
Learn poker strategy by playing Texas Hold'em against AI opponents with different playing styles.

## Backend Features to PRESERVE

### 1. Core Game Engine (Keep & Extract)
- **PokerGame class**: Your solid Texas Hold'em implementation
- **DeckManager**: Clean deck handling with proper shuffling  
- **HandManager**: Hand evaluation and winner determination
- **Game States**: PRE_FLOP, FLOP, TURN, RIVER, SHOWDOWN flow
- **Betting Logic**: Your working betting rounds and pot management
- **Hand Evaluation**: Integration with Treys library + Monte Carlo simulations

### 2. AI Strategy System (Keep & Simplify)
- **Conservative Strategy**: Tight play, strong hands only
- **Probability-Based Strategy**: Mathematical decisions with SPR calculations  
- **Bluffer Strategy**: Aggressive play with bluffing
- **Risk-Taker Strategy**: Loose aggressive style
- **Hand Evaluation Logic**: Your working Monte Carlo simulations for pre-flop

### 3. Player Management (Keep Core Logic)
- **Player Classes**: Human vs AI player abstractions
- **Chip Management**: Betting, stack management, all-in logic
- **Player States**: Active, folded, all-in handling

### 4. Learning Features (Keep & Simplify)
- **AI Decision Tracking**: Record what AI players decided and why
- **Hand Analysis**: Basic hand strength evaluation
- **Action History**: Track decisions within current hand

## Backend Simplifications (Remove Complexity)

### Remove These Complex Systems
- **ChipLedger**: Replace with simple chip validation
- **StateManager**: Remove atomic transactions, use direct state updates
- **Performance decorators**: Remove caching and profiling
- **Complex logging**: Use simple print statements
- **JWT Authentication**: Replace with simple session management
- **Correlation IDs**: Remove request tracking
- **WebSocket real-time**: Use simple polling instead
- **Complex validation schemas**: Use basic input validation

### Keep This Simple API Structure
```python
# Single FastAPI file with essential endpoints:
POST /games                    # Create new game  
GET /games/{game_id}          # Get game state
POST /games/{game_id}/actions # Submit player action
POST /games/{game_id}/next    # Advance to next hand
```

## Frontend Requirements (Simple & New)

### Basic React Application
- **Simple State**: useState for game state (no complex state management)
- **Direct API Calls**: Fetch/axios without abstraction layers
- **Basic Components**: 
  - PokerTable (show players, cards, pot)
  - GameControls (fold/check/call/bet buttons)
  - GameLobby (create new game)
- **Minimal Styling**: Clean, functional interface

## Technical Implementation Plan

### Phase 1: Extract Core Backend Logic
1. **Extract from archive**:
   - `game/poker_game.py` (simplified - remove StateManager/ChipLedger)
   - `game/deck_manager.py` (keep as-is)
   - `game/hand_manager.py` (keep as-is) 
   - `ai/strategies/` (all 4 strategies, remove performance decorators)
   - `models/player.py` (keep core logic)

2. **Create simple FastAPI wrapper**:
   - Single `main.py` file with 4 endpoints
   - JSON file storage for game state
   - Basic error handling

### Phase 2: Build Simple Frontend
1. **Create React App** with basic components
2. **Simple state management** using useState
3. **Direct API integration** without complex abstractions

### Dependencies to Keep
```python
# Backend
fastapi
uvicorn  
treys           # Hand evaluation (you're already using this well)
random          # For deck shuffling and AI decisions

# Frontend  
react
axios           # Simple API calls
```

## Features to Preserve from Your Implementation

### Game Logic (Definitely Keep)
- ✅ **Complete poker rules**: Your implementation is solid
- ✅ **Betting mechanics**: Working small/big blind, raise/call/fold
- ✅ **Hand progression**: PRE_FLOP → FLOP → TURN → RIVER → SHOWDOWN
- ✅ **Winner determination**: Proper showdown logic
- ✅ **Multi-hand gameplay**: Game continues smoothly between hands

### AI Intelligence (Definitely Keep)  
- ✅ **Strategy differentiation**: Your 4 AI types have distinct personalities
- ✅ **Poker math**: SPR calculations, hand strength evaluation
- ✅ **Monte Carlo simulations**: For incomplete hand evaluation
- ✅ **Reasonable decisions**: AIs make logical poker decisions

### Code Organization (Keep Structure)
- ✅ **Separation of concerns**: Game logic separate from AI logic
- ✅ **Clean classes**: Well-designed Player, PokerGame, DeckManager
- ✅ **Testable code**: Your core logic is well-structured

## Success Criteria

### Functional (Same High Bar)
1. **Complete poker gameplay**: Deal → bet → showdown → next hand
2. **Smart AI opponents**: Each AI plays according to its strategy
3. **Learning value**: Player can see AI decisions and reasoning
4. **Multi-hand sessions**: Play continues smoothly

### Technical (Simplified)
1. **Total backend**: ~500-800 lines (vs your current ~2000+ in core files)
2. **Simple API**: 4 endpoints, JSON file storage
3. **Basic frontend**: ~400-500 lines total
4. **Quick setup**: Run locally in under 5 minutes

## What This Approach Preserves
- 🎯 **Your excellent poker game engine**
- 🎯 **Your working AI strategies** 
- 🎯 **Your solid hand evaluation math**
- 🎯 **Your clean code organization**

## What This Approach Simplifies  
- 🔧 **API complexity** (4 endpoints vs 13+)
- 🔧 **Infrastructure overhead** (no complex middleware)
- 🔧 **Frontend state management** (useState vs complex patterns)
- 🔧 **Error handling** (basic vs enterprise-level)

This approach respects the solid work you've already done while eliminating the complexity that made the system hard to debug and maintain.