# Poker Learning App Backend Documentation

This document provides a comprehensive overview of the Poker Learning App backend system, focusing on the information needed for API development and frontend integration.

## Table of Contents

1. [System Overview](#system-overview)
2. [API Endpoints](#api-endpoints)
3. [Core Components](#core-components)
4. [Data Structures](#data-structures)
5. [Game Flow](#game-flow)
6. [AI System](#ai-system)
7. [Learning & Statistics System](#learning--statistics-system)
8. [Error Handling](#error-handling)
9. [Known Limitations & Considerations](#known-limitations--considerations)
10. [Appendix: Recent Updates](#appendix-recent-updates)

## System Overview

The Poker Learning App backend is a comprehensive Texas Hold'em poker game system with AI players and learning capabilities. The system allows human players to play against various AI personalities, tracks game statistics, analyzes player decisions, and provides learning feedback.

### Technology Stack

- **Language**: Python
- **Framework**: FastAPI
- **Key Libraries**: Treys (poker hand evaluation), Pydantic (data validation)
- **Authentication**: JWT token-based authentication
- **Architecture**: Modular component-based design with REST API interface
- **Deployment**: Docker containerization support

## API Endpoints

The API uses standard REST conventions and JWT authentication. All endpoints except for player creation require authentication via a JWT token provided in the X-API-Key header.

### Games Module

#### Create Game
- **Endpoint**: `POST /api/v1/games`
- **Auth**: Required
- **Request Body**:
  ```json
  {
    "player_id": "string",
    "ai_count": 4,
    "ai_personalities": ["Conservative", "Risk Taker", "Probability-Based", "Bluffer"]
  }
  ```
- **Response**: [GameCreateResponse](#gamecreateresponse) - Basic game state with player information

#### Get Game State
- **Endpoint**: `GET /api/v1/games/{game_id}`
- **Auth**: Required
- **Query Parameters**:
  - `show_all_cards` (boolean, default: false) - Whether to show all players' cards
- **Response**: [GameState](#gamestate) - Current game state with player information, community cards, and pot size

#### Player Action
- **Endpoint**: `POST /api/v1/games/{game_id}/actions`
- **Auth**: Required
- **Request Body**:
  ```json
  {
    "player_id": "string",
    "action_type": "fold|call|raise",
    "amount": 20  // Only required for "raise" action
  }
  ```
- **Response**: [ActionResponse](#actionresponse) - Updated game state after action

#### Next Hand
- **Endpoint**: `POST /api/v1/games/{game_id}/next-hand`
- **Auth**: Required
- **Request Body**:
  ```json
  {
    "player_id": "string"
  }
  ```
- **Response**: [NextHandResponse](#nexthandresponse) - Updated game state for new hand

#### End Game
- **Endpoint**: `DELETE /api/v1/games/{game_id}`
- **Auth**: Required
- **Response**: [GameSummary](#gamesummary) - Summary of game duration, final chip counts, and winner

#### Get Showdown Results
- **Endpoint**: `GET /api/v1/games/{game_id}/showdown`
- **Auth**: Required
- **Response**: [ShowdownResponse](#showdownresponse) - Detailed information about player hands and winners

#### Get Player Cards
- **Endpoint**: `GET /api/v1/games/{game_id}/players/{target_player_id}/cards`
- **Auth**: Required
- **Response**: [PlayerCardsResponse](#playercardsresponse) - Information about a player's hole cards

### Players Module

#### Create Player
- **Endpoint**: `POST /api/v1/players`
- **Auth**: Not required
- **Request Body**:
  ```json
  {
    "username": "string",
    "settings": {
      "avatar": "string",
      "theme": "string",
      "sound_enabled": true
    }
  }
  ```
- **Response**: [PlayerResponse](#playerresponse) with authentication token

#### Get Player
- **Endpoint**: `GET /api/v1/players/{player_id}`
- **Auth**: Required (self-only)
- **Response**: [PlayerResponse](#playerresponse) - Player information

#### Get Player Statistics
- **Endpoint**: `GET /api/v1/players/{player_id}/statistics`
- **Auth**: Required (self-only)
- **Query Parameters**:
  - `timeframe` (string, optional) - Time period filter
  - `metric_type` (string, optional) - Type of metrics to return
- **Response**: [PlayerStatistics](#playerstatistics) - Detailed player statistics

### Learning Module

#### Get Learning Feedback
- **Endpoint**: `GET /api/v1/players/{player_id}/feedback`
- **Auth**: Required (self-only)
- **Query Parameters**:
  - `num_decisions` (integer, default: 1) - Number of decisions to include
- **Response**: [FeedbackResponse](#feedbackresponse) - Learning feedback for player decisions

#### Get Strategy Profile
- **Endpoint**: `GET /api/v1/players/{player_id}/strategy-profile`
- **Auth**: Required (self-only)
- **Response**: [StrategyProfile](#strategyprofile) - Analysis of player's strategic tendencies

#### Get Decision Details
- **Endpoint**: `GET /api/v1/players/{player_id}/decisions/{decision_id}`
- **Auth**: Required (self-only)
- **Response**: [DecisionDetails](#decisiondetails) - Detailed analysis of a specific decision

## Core Components

### Game Engine (PokerGame)

The game engine (`game/poker_game.py`) is the central component that coordinates the entire poker game.

```python
class PokerGame:
    # Core attributes
    players: List[Player]           # All players in the game
    deck: List[str]                 # Current deck of cards  
    community_cards: List[str]      # Shared community cards
    pot: int                        # Current pot size
    current_bet: int                # Current bet amount
    small_blind: int                # Small blind amount
    big_blind: int                  # Big blind amount
    dealer_index: int               # Current dealer position
    current_state: GameState        # Current game state
    hand_count: int                 # Number of hands played
    
    # Key methods
    def reset_deck() -> None
    def deal_hole_cards() -> None
    def deal_community_cards() -> None
    def post_blinds() -> None
    def betting_round() -> None
    def advance_game_state() -> None
    def play_hand() -> None
    def distribute_pot(deck=None) -> None
```

### Game Service

The game service (`services/game_service.py`) provides a high-level interface for interacting with game instances.

```python
class GameService:
    # Key methods
    def create_game(player_id: str, ai_count: int, ai_personalities: List[str]) -> Dict[str, Any]
    def get_game_state(game_id: str, player_id: str, show_all_cards: bool = False) -> Dict[str, Any]
    def process_action(game_id: str, player_id: str, action_type: str, amount: Optional[int] = None) -> Dict[str, Any]
    def next_hand(game_id: str, player_id: str) -> Dict[str, Any]
    def end_game(game_id: str, player_id: str) -> Dict[str, Any]
    def get_showdown_results(game_id: str, player_id: str) -> Dict[str, Any]
    def get_player_cards(game_id: str, player_id: str, target_player_id: str) -> Dict[str, Any]
```

### Player Service

Manages player data and statistics.

```python
class PlayerService:
    # Key methods
    def create_player(username: str, settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]
    def get_player(player_id: str) -> Dict[str, Any]
    def get_player_statistics(player_id: str, timeframe: Optional[str] = None, metric_type: Optional[str] = None) -> Dict[str, Any]
```

### Learning Service

Provides learning-related functionality.

```python
class LearningService:
    # Key methods
    def get_learning_feedback(player_id: str, num_decisions: int = 1) -> Dict[str, Any]
    def get_strategy_profile(player_id: str) -> Dict[str, Any]
    def get_decision_details(player_id: str, decision_id: str) -> Dict[str, Any]
```

### Supporting Components

1. **DeckManager**: Manages card dealing and deck state
2. **HandManager**: Evaluates hands and distributes pots
3. **PokerRound**: Manages betting rounds
4. **PotManager**: Calculates pot distributions
5. **StatisticsManager**: Tracks game statistics
6. **AIDecisionMaker**: Coordinates AI decisions

## Data Structures

### API Response Models

#### GameCreateResponse
```json
{
  "game_id": "string",
  "players": [PlayerInfo],
  "dealer_position": 0,
  "small_blind": 5,
  "big_blind": 10,
  "pot": 0,
  "current_bet": 0,
  "current_state": "pre_flop"
}
```

#### GameState
```json
{
  "game_id": "string",
  "current_state": "pre_flop|flop|turn|river|showdown",
  "community_cards": ["Ah", "Kd", "Qs"],
  "community_cards_formatted": "[rendered HTML]",
  "pot": 30,
  "pot_formatted": "$30",
  "current_bet": 10,
  "current_bet_formatted": "$10",
  "players": [PlayerInfo],
  "dealer_position": 0,
  "current_player": "player_id",
  "available_actions": ["fold", "call", "raise"],
  "min_raise": 20,
  "min_raise_formatted": "$20",
  "hand_number": 1,
  "winner_info": [WinnerInfo],
  "showdown_data": {...}
}
```

#### PlayerInfo
```json
{
  "player_id": "string",
  "player_type": "human|ai",
  "personality": "Conservative|Risk Taker|Probability-Based|Bluffer",
  "position": 0,
  "stack": 1000,
  "stack_formatted": "$1000",
  "current_bet": 10,
  "current_bet_formatted": "$10",
  "is_active": true,
  "is_all_in": false,
  "hole_cards": ["Ah", "Kd"],
  "hole_cards_formatted": "[rendered HTML]",
  "visible_to_client": true
}
```

#### ActionResponse
```json
{
  "action_result": "success",
  "updated_game_state": GameState,
  "next_player": "player_id",
  "pot_update": 30,
  "is_showdown": false
}
```

#### NextHandResponse
```json
{
  "hand_number": 2,
  "updated_game_state": GameState
}
```

#### ShowdownResponse
```json
{
  "player_hands": {
    "player1": {
      "hole_cards": ["Ah", "Kd"],
      "hand_rank": "Flush",
      "hand_score": 342,
      "best_hand": ["Ah", "Kh", "Qh", "Jh", "9h"]
    }
  },
  "winners": [
    {
      "player_id": "player1",
      "amount": 100,
      "hand_rank": "Flush",
      "hand_name": "Flush",
      "hand": ["Ah", "Kh", "Qh", "Jh", "9h"],
      "final_stack": 1100
    }
  ],
  "community_cards": ["2h", "Jh", "Qh", "8s", "9h"],
  "total_pot": 100
}
```

#### PlayerCardsResponse
```json
{
  "player_id": "string",
  "hole_cards": ["Ah", "Kd"],
  "is_active": true,
  "visible_to_client": true
}
```

#### PlayerResponse
```json
{
  "player_id": "string",
  "username": "string",
  "created_at": "2023-01-01T00:00:00Z",
  "settings": {
    "avatar": "string",
    "theme": "string",
    "sound_enabled": true
  },
  "access_token": "jwt_token"  // Only included in create response
}
```

#### PlayerStatistics
```json
{
  "player_id": "string",
  "games_played": 10,
  "hands_played": 150,
  "wins": 60,
  "losses": 90,
  "win_rate": 0.4,
  "avg_stack": 1200,
  "largest_pot_won": 500,
  "correct_decisions": 0.7,
  "strategy_distribution": {
    "Conservative": 0.4,
    "Risk Taker": 0.3,
    "Probability-Based": 0.2,
    "Bluffer": 0.1
  },
  "cards_won_with": [
    {
      "hand_type": "Flush",
      "count": 12,
      "win_rate": 0.8
    }
  ]
}
```

#### FeedbackResponse
```json
{
  "player_id": "string",
  "feedback_items": [
    {
      "decision_id": "string",
      "decision": "call",
      "situation": "You called with J♥ 10♥ on a K♥ 9♥ 2♦ board.",
      "analysis": "This was a good call as you had strong draw potential.",
      "recommendation": "Consider raising with this hand strength in the future."
    }
  ],
  "performance_metrics": {
    "correct_decisions": 0.7,
    "improvement_trend": 0.05
  }
}
```

#### StrategyProfile
```json
{
  "player_id": "string",
  "dominant_strategy": "Risk Taker",
  "strategy_distribution": {
    "Conservative": 0.4,
    "Risk Taker": 0.3,
    "Probability-Based": 0.2,
    "Bluffer": 0.1
  },
  "decision_quality": {
    "accuracy": 0.7,
    "ev_ratio": 0.65
  },
  "recommendations": [
    {
      "area": "Pre-flop decisions",
      "suggestion": "Play tighter with weak hands out of position.",
      "expected_improvement": "Increase win rate by ~3%"
    }
  ]
}
```

### Internal Data Structures

#### GameState Enum
```python
class GameState(Enum):
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
```

#### Card Representation
Cards are represented as strings in the format `"rank+suit"`:
- Ranks: 2-9, T (10), J, Q, K, A
- Suits: s (spades), h (hearts), d (diamonds), c (clubs)
- Examples: "Ah" (Ace of hearts), "Ts" (Ten of spades)

## Game Flow

### 1. Game Initialization

1. Client creates a player profile (if new user)
2. Client requests game creation with desired number of AI opponents
3. Server creates a new PokerGame instance with the specified players
4. Server returns initial game state

### 2. Pre-Flop

1. Small and big blinds are posted
2. Hole cards are dealt to all players
3. Client retrieves the current game state
4. Human player decides to fold, call, or raise
5. AI players respond with their actions
6. Betting continues until all active players have called or folded

### 3. Flop, Turn, and River

For each betting round:
1. Community cards are dealt
2. Client retrieves updated game state
3. Active players bet in turn
4. Betting continues until all active players have called or folded

### 4. Showdown

1. If more than one player is active, hand evaluation occurs
2. Pot is distributed to winner(s)
3. Client can retrieve detailed showdown results
4. Client can request to start the next hand

### 5. Learning and Analysis

At any point:
1. Client can request learning feedback
2. Client can view player strategy profile
3. Client can analyze specific decisions

## AI System

### AI Personalities

The system includes four distinct AI personalities:

1. **Conservative**:
   - Plays tight with strong starting hands
   - Rarely bluffs
   - Folds marginal hands
   - Focuses on value betting

2. **Risk Taker**:
   - Plays aggressive with a wide range of hands
   - Frequently bluffs
   - Makes speculative calls with drawing hands
   - Puts pressure on opponents with raises

3. **Probability-Based**:
   - Makes decisions based on pot odds and expected value
   - Balanced approach between tight and loose play
   - Adjusts strategy based on stack-to-pot ratio
   - Consistent betting patterns

4. **Bluffer**:
   - Unpredictable betting patterns
   - Frequently bluffs with weak hands
   - Calls with a wide range of hands
   - Makes surprising moves to confuse opponents

### AI Decision Making

AI decisions follow these steps:
1. Evaluate hand strength
2. Calculate pot odds
3. Consider stack-to-pot ratio
4. Make a decision based on personality profile
5. Return decision (fold, call, raise)

## Learning & Statistics System

### Player Learning Feedback

The system provides personalized learning feedback by:
1. Comparing player decisions to AI strategies
2. Calculating the expected value of decisions
3. Identifying patterns in decision making
4. Generating specific improvement recommendations

### Strategy Profiling

Player strategy profiles include:
1. Distribution of play styles
2. Dominant strategy identification
3. Decision quality metrics
4. Personalized recommendations

### Decision Analysis

Each decision is analyzed for:
1. Mathematical correctness (expected value)
2. Strategic alignment
3. Contextual appropriateness
4. Potential alternative plays

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request (invalid parameters)
- 401: Unauthorized (missing token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found (resource doesn't exist)
- 500: Internal Server Error

Common error responses:
```json
{
  "detail": "Error message describing the issue"
}
```

## Known Limitations & Considerations

1. **Deck Exhaustion**: When large numbers of hands are played, the deck may occasionally need to be reset.

2. **AI Decision Time**: AI decisions are made synchronously, which can cause slight delays when multiple AI players are active.

3. **Card Visibility**: The API now returns all cards with a "visible_to_client" flag, allowing the frontend to control card visibility.

4. **Stack Management**: Player stacks are carefully tracked with validation to ensure consistency between rounds.

5. **Folded Players**: Players who fold in one hand are automatically reactivated for the next hand if they have sufficient chips.

6. **Minimum Raise**: Follows standard Texas Hold'em rules (current bet + big blind).

7. **Blind Progression**: Blinds increase according to the configured schedule, not on every hand.

## Appendix: Recent Updates

The following sections document recent updates to the backend system.

### Card Handling Improvements (03/13/25)

1. **Enhanced Card Dealing**:
   - Cards are explicitly cleared between hands
   - All active players receive fresh cards at the start of each hand
   - Missing cards are proactively dealt when detected

2. **API Visibility Control**:
   - The API now returns all cards with a "visible_to_client" flag
   - Frontend can control card visibility based on this flag
   - Improved consistency in card representation

### Betting and Blinds Fixes (03/14/25)

1. **Corrected Blind Values**:
   - Game now starts with the correct small blind (5) and big blind (10)
   - Blinds increase according to the configured schedule

2. **Standard Raising Rules**:
   - Minimum raise now follows standard Texas Hold'em rules
   - Minimum raise is current bet plus the big blind
   - Both human and AI players use consistent raising logic

3. **Missing Functionality**:
   - Added missing best hand determination for showdowns
   - Fixed pot distribution to correctly handle split pots

### Winner Information and Stack Updates (03/15/25)

1. **Winner Response Enhancements**:
   - Winner information now includes hand name, rank, and best five-card hand
   - Final stack values are included in winner information
   - API consistently returns winner data at both showdown and game state endpoints

2. **Stack Consistency**:
   - Improved stack tracking across betting rounds
   - Added verification to ensure stacks are correctly updated
   - Fixed potential double-counting issues

### Player Status and Betting Improvements (03/17/25)

1. **Player Reactivation**:
   - Fixed issue where folded players would remain inactive in subsequent hands
   - Players with sufficient chips are automatically reactivated for new hands

2. **Folding Behavior**:
   - Improved handling of player folding actions
   - Game advances to showdown when only one player remains active
   - Added checks to prevent folded players from acting

3. **Pot Distribution Reliability**:
   - Enhanced pot calculation and distribution logic
   - Added verification of total chips conservation
   - Improved handling of edge cases like all-in scenarios

These updates significantly improve the reliability and correctness of the poker game system, especially regarding card handling, pot management, and player status tracking.