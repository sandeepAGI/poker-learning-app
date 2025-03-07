# Poker Learning App API Requirements

This document outlines the requirements for the API layer that will serve as the interface between the frontend and backend of the Poker Learning App.

## 1. Architecture

- RESTful API design with clear resource paths
- JSON as the standard data format
- Proper HTTP status codes and error handling
- Authentication/authorization mechanism
- Request validation and sanitization

## 2. Game Management Endpoints

### 2.1 Create Game

**Endpoint:** `POST /api/games`

**Description:** Creates a new game session

**Parameters:**
```json
{
  "player_id": "string",
  "ai_count": "integer",
  "ai_personalities": ["Conservative", "Risk Taker", "Probability-Based", "Bluffer"]
}
```

**Response:**
```json
{
  "game_id": "string",
  "players": [
    {
      "player_id": "string",
      "player_type": "human|ai",
      "personality": "string",
      "position": "integer",
      "stack": "integer"
    }
  ],
  "dealer_position": "integer",
  "small_blind": "integer",
  "big_blind": "integer"
}
```

**Responsibilities:**
- Initialize PokerGame instance
- Store in session manager
- Set up initial player positions

### 2.2 Get Game State

**Endpoint:** `GET /api/games/{game_id}`

**Description:** Fetches current game state

**Parameters:**
- `game_id` (path)
- `player_id` (query, for authentication)

**Response:**
```json
{
  "game_id": "string",
  "current_state": "pre_flop|flop|turn|river|showdown",
  "community_cards": ["Ah", "Kd", "..."],
  "pot": "integer",
  "current_bet": "integer",
  "players": [
    {
      "player_id": "string",
      "player_type": "human|ai",
      "stack": "integer",
      "current_bet": "integer",
      "is_active": "boolean",
      "is_all_in": "boolean",
      "hole_cards": ["Jh", "Js"],  // Only visible for current player
      "position": "integer"
    }
  ],
  "dealer_position": "integer",
  "current_player": "string",
  "available_actions": ["fold", "call", "raise"],
  "min_raise": "integer",
  "hand_number": "integer"
}
```

**Responsibilities:**
- Retrieve game from session manager
- Filter sensitive data (other players' hole cards)
- Calculate available actions for current player

### 2.3 Player Action

**Endpoint:** `POST /api/games/{game_id}/actions`

**Description:** Processes player decisions (fold, call, raise)

**Parameters:**
```json
{
  "player_id": "string",
  "action_type": "fold|call|raise",
  "amount": "integer"  // Required for raise
}
```

**Response:**
```json
{
  "action_result": "success|error",
  "updated_game_state": { /* Same format as GET game state */ },
  "next_player": "string",
  "pot_update": "integer"
}
```

**Responsibilities:**
- Validate action legality
- Update game state
- Trigger AI decisions if needed
- Handle progression to next game state if round completes

### 2.4 Next Hand

**Endpoint:** `POST /api/games/{game_id}/next-hand`

**Description:** Advances to the next hand after a hand is complete

**Parameters:**
```json
{
  "player_id": "string"
}
```

**Response:**
```json
{
  "hand_number": "integer",
  "updated_game_state": { /* Same format as GET game state */ }
}
```

**Responsibilities:**
- Reset game state
- Deal new cards
- Post blinds
- Start new hand

### 2.5 End Game

**Endpoint:** `DELETE /api/games/{game_id}`

**Description:** Ends a game session

**Parameters:**
- `game_id` (path)
- `player_id` (query, for authentication)

**Response:**
```json
{
  "game_summary": {
    "duration": "integer",
    "hands_played": "integer",
    "final_chips": {
      "player_id": "integer"
    },
    "winner": "string"
  }
}
```

**Responsibilities:**
- Clean up resources
- Save statistics
- Generate game summary

## 3. Player Management Endpoints

### 3.1 Create Player

**Endpoint:** `POST /api/players`

**Description:** Creates a new player profile

**Parameters:**
```json
{
  "username": "string",
  "settings": {
    /* Optional player settings */
  }
}
```

**Response:**
```json
{
  "player_id": "string",
  "username": "string",
  "created_at": "timestamp",
  "statistics": {
    "hands_played": "integer",
    "hands_won": "integer",
    "win_rate": "float"
  }
}
```

**Responsibilities:**
- Create player record
- Initialize statistics

### 3.2 Get Player

**Endpoint:** `GET /api/players/{player_id}`

**Description:** Fetches player information

**Parameters:**
- `player_id` (path)

**Response:**
```json
{
  "player_id": "string",
  "username": "string",
  "created_at": "timestamp",
  "statistics": {
    "hands_played": "integer",
    "hands_won": "integer",
    "win_rate": "float",
    "total_winnings": "integer",
    "total_losses": "integer"
  }
}
```

**Responsibilities:**
- Retrieve and format player data
- Include basic statistics summary

### 3.3 Get Player Statistics

**Endpoint:** `GET /api/players/{player_id}/statistics`

**Description:** Fetches detailed player statistics

**Parameters:**
- `player_id` (path)
- `timeframe` (query, optional)
- `metric_type` (query, optional)

**Response:**
```json
{
  "player_id": "string",
  "basic_stats": {
    "hands_played": "integer",
    "hands_won": "integer",
    "win_rate": "float",
    "showdown_success": "float"
  },
  "position_stats": {
    "early": { "win_rate": "float", "hands_played": "integer" },
    "middle": { "win_rate": "float", "hands_played": "integer" },
    "late": { "win_rate": "float", "hands_played": "integer" },
    "blinds": { "win_rate": "float", "hands_played": "integer" }
  },
  "strategy_metrics": {
    "vpip": "float",
    "pfr": "float",
    "aggression_factor": "float"
  }
}
```

**Responsibilities:**
- Retrieve detailed statistics from StatisticsManager
- Format and categorize for frontend display
- Apply any filtering based on query parameters

## 4. Learning Endpoints

### 4.1 Get Learning Feedback

**Endpoint:** `GET /api/players/{player_id}/feedback`

**Description:** Fetches learning feedback for a player

**Parameters:**
- `player_id` (path)
- `num_decisions` (query, optional, default: 1)

**Response:**
```json
{
  "feedback": [
    {
      "decision_id": "string",
      "game_context": {
        "game_state": "pre_flop|flop|turn|river",
        "hole_cards": ["Ah", "Kd"],
        "community_cards": ["Jh", "Js", "7d"],
        "pot_size": "integer",
        "spr": "float"
      },
      "decision": "fold|call|raise",
      "feedback_text": "string",
      "optimal_decision": "fold|call|raise",
      "improvement_areas": ["string"],
      "timestamp": "timestamp"
    }
  ]
}
```

**Responsibilities:**
- Retrieve feedback from LearningTracker
- Format for readability
- Include relevant context for each feedback item

### 4.2 Get Strategy Profile

**Endpoint:** `GET /api/players/{player_id}/strategy-profile`

**Description:** Fetches player's strategic profile

**Parameters:**
- `player_id` (path)

**Response:**
```json
{
  "dominant_strategy": "Conservative|Risk Taker|Probability-Based|Bluffer",
  "strategy_distribution": {
    "Conservative": "float",
    "Risk Taker": "float",
    "Probability-Based": "float",
    "Bluffer": "float"
  },
  "recommended_strategy": "string",
  "decision_accuracy": "float",
  "total_decisions": "integer",
  "improvement_areas": [
    {
      "area": "pre_flop|position|aggression|etc",
      "description": "string"
    }
  ],
  "learning_recommendations": [
    {
      "focus": "string",
      "title": "string",
      "description": "string"
    }
  ],
  "decision_trend": {
    "trend": "improving|declining|stable",
    "description": "string"
  }
}
```

**Responsibilities:**
- Retrieve strategy profile data
- Format recommendations for frontend display
- Include visualization-ready data

### 4.3 Get Decision Details

**Endpoint:** `GET /api/players/{player_id}/decisions/{decision_id}`

**Description:** Fetches detailed analysis of a specific decision

**Parameters:**
- `player_id` (path)
- `decision_id` (path)

**Response:**
```json
{
  "decision_id": "string",
  "timestamp": "timestamp",
  "game_context": {
    "game_state": "pre_flop|flop|turn|river",
    "hole_cards": ["Ah", "Kd"],
    "community_cards": ["Jh", "Js", "7d"],
    "pot_size": "integer",
    "current_bet": "integer",
    "spr": "float"
  },
  "player_decision": "fold|call|raise",
  "matching_strategy": "string",
  "optimal_strategy": "string",
  "was_optimal": "boolean",
  "strategy_decisions": {
    "Conservative": "fold|call|raise",
    "Risk Taker": "fold|call|raise",
    "Probability-Based": "fold|call|raise",
    "Bluffer": "fold|call|raise"
  },
  "expected_value": "float",
  "detailed_analysis": "string"
}
```

**Responsibilities:**
- Retrieve specific decision record
- Add contextual information
- Include detailed analysis explanation

## 5. Session Management

- API needs to maintain mapping between game_id and actual PokerGame instances
- Handle inactive sessions (timeout after period of inactivity)
- Implement authentication to ensure players can only access their own information
- Support reconnection to active games

**Specific Requirements:**
- Sessions should expire after 30 minutes of inactivity
- Authentication should use JWT tokens or similar
- Game state should be persisted to allow reconnection
- Rate limiting to prevent abuse

## 6. Data Transformations

The API layer is responsible for transforming internal data structures to frontend-friendly formats:

- Filter hole cards: Only show current player's cards
- Format card data for frontend rendering (suit/rank separation)
- Convert internal state enums to frontend-friendly strings
- Format currency/chip values consistently
- Structure decision histories in a way that's easy to display
- Normalize timestamps to ISO format

## 7. Error Handling

### 7.1 Error Response Format

```json
{
  "error": true,
  "code": "ERROR_CODE",
  "message": "Human-readable message",
  "details": {
    /* Optional additional context */
  }
}
```

### 7.2 Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| GAME_NOT_FOUND | Game session not found | 404 |
| PLAYER_NOT_FOUND | Player not found | 404 |
| INVALID_ACTION | Action not allowed in current state | 400 |
| NOT_YOUR_TURN | Not the player's turn to act | 403 |
| INSUFFICIENT_FUNDS | Not enough chips for action | 400 |
| INVALID_AMOUNT | Bet amount is invalid | 400 |
| AUTHENTICATION_REQUIRED | Authentication needed | 401 |
| AUTHORIZATION_FAILED | Not authorized for this resource | 403 |
| SERVER_ERROR | Internal server error | 500 |

## 8. Websocket Considerations

For real-time updates, consider implementing websocket connections:

**Events to broadcast:**
- Game state changes
- Player actions
- AI decisions
- Hand results

**Websocket endpoint:** `/api/ws/games/{game_id}`

**Subscription authentication:** Require same authentication as REST API

**Message format:**
```json
{
  "event_type": "game_update|player_action|hand_complete",
  "timestamp": "timestamp",
  "data": {
    /* Event-specific data */
  }
}
```

## 9. Documentation Requirements

- OpenAPI/Swagger documentation for all endpoints
- Clear examples for request/response formats
- Authentication instructions
- Error code references
- Sequence diagrams for common flows
- Rate limiting information

## 10. Versioning

- API should be versioned (e.g., `/api/v1/games`)
- Support for at least one previous version when changes are made
- Deprecation notices for outdated endpoints