# Poker Learning App API Implementation

This document provides an overview of the implemented APIs for the Poker Learning App as of March 10, 2025. The implementation follows a RESTful design with JSON as the standard data format and includes proper HTTP status codes and error handling.

## Table of Contents

1. [API Architecture](#api-architecture)
2. [Game Management Endpoints](#game-management-endpoints)
3. [Player Management Endpoints](#player-management-endpoints)
4. [Learning Endpoints](#learning-endpoints)
5. [WebSocket Implementation](#websocket-implementation)
6. [Error Handling](#error-handling)
7. [Authentication](#authentication)
8. [Rate Limiting](#rate-limiting)
9. [Documentation](#documentation)
10. [Appendix: Requirements Checklist](#appendix-requirements-checklist)

## API Architecture

The API is built using FastAPI and follows these architectural principles:

- RESTful API design with clear resource paths
- JSON as the standard data format
- Proper HTTP status codes and error handling
- JWT-based authentication
- Request validation using Pydantic models
- Rate limiting middleware
- WebSocket support for real-time updates

The base URL for all REST endpoints is `/api/v1` with versioning built-in for future compatibility.

## Game Management Endpoints

### Create Game

**Endpoint:** `POST /api/v1/games`

**Description:** Creates a new game session

**Authentication:** Required (JWT token in `X-API-Key` header)

**Request Body:**
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

**Implementation Notes:**
- Creates a new `PokerGame` instance
- Stores the game in the session manager
- Initializes players with the requested AI personalities
- Returns a unique game ID for subsequent requests

### Get Game State

**Endpoint:** `GET /api/v1/games/{game_id}`

**Description:** Fetches current game state

**Authentication:** Required (JWT token in `X-API-Key` header)

**Response:**
```json
{
  "game_id": "string",
  "current_state": "pre_flop|flop|turn|river|showdown",
  "community_cards": ["Ah", "Kd", "..."],
  "community_cards_formatted": [{"rank": "A", "suit": "h", ...}, ...],
  "pot": "integer",
  "pot_formatted": "$100",
  "current_bet": "integer",
  "current_bet_formatted": "$10",
  "players": [
    {
      "player_id": "string",
      "player_type": "human|ai",
      "stack": "integer",
      "stack_formatted": "$500",
      "current_bet": "integer",
      "current_bet_formatted": "$10",
      "is_active": "boolean",
      "is_all_in": "boolean",
      "hole_cards": ["Jh", "Js"],  // Only visible for current player
      "hole_cards_formatted": [{"rank": "J", "suit": "h", ...}, ...],
      "position": "integer"
    }
  ],
  "dealer_position": "integer",
  "current_player": "string",
  "available_actions": ["fold", "call", "raise"],
  "min_raise": "integer",
  "min_raise_formatted": "$20",
  "hand_number": "integer"
}
```

**Implementation Notes:**
- Retrieves the game from session manager
- Filters sensitive data (other players' hole cards)
- Calculates available actions for current player
- Includes formatted values for currency and cards

### Player Action

**Endpoint:** `POST /api/v1/games/{game_id}/actions`

**Description:** Processes player decisions (fold, call, raise)

**Authentication:** Required (JWT token in `X-API-Key` header)

**Request Body:**
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

**Implementation Notes:**
- Validates action legality
- Updates game state
- Triggers AI decisions if needed
- Handles progression to next game state if round completes
- Broadcasts game updates via WebSocket

### Next Hand

**Endpoint:** `POST /api/v1/games/{game_id}/next-hand`

**Description:** Advances to the next hand after a hand is complete

**Authentication:** Required (JWT token in `X-API-Key` header)

**Request Body:**
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

**Implementation Notes:**
- Resets player states
- Deals new cards
- Posts blinds
- Starts new hand
- Broadcasts new hand event via WebSocket

### End Game

**Endpoint:** `DELETE /api/v1/games/{game_id}`

**Description:** Ends a game session

**Authentication:** Required (JWT token in `X-API-Key` header)

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

**Implementation Notes:**
- Cleans up resources
- Saves statistics
- Generates game summary
- Broadcasts game end event via WebSocket

## Player Management Endpoints

### Create Player

**Endpoint:** `POST /api/v1/players`

**Description:** Creates a new player profile

**Authentication:** Not required (this is the only endpoint that doesn't require authentication)

**Request Body:**
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
  },
  "access_token": "string" // JWT token for authentication
}
```

**Implementation Notes:**
- Creates player record with UUID
- Initializes statistics
- Generates a JWT token for authentication

### Get Player

**Endpoint:** `GET /api/v1/players/{player_id}`

**Description:** Fetches player information

**Authentication:** Required (JWT token in `X-API-Key` header)

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

**Implementation Notes:**
- Retrieves and formats player data
- Includes basic statistics summary
- Security check to ensure players can only access their own info

### Get Player Statistics

**Endpoint:** `GET /api/v1/players/{player_id}/statistics`

**Description:** Fetches detailed player statistics

**Authentication:** Required (JWT token in `X-API-Key` header)

**Query Parameters:**
- `timeframe` (optional): Filter by timeframe
- `metric_type` (optional): Filter by metric type

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

**Implementation Notes:**
- Retrieves detailed statistics
- Applies filtering based on query parameters
- Security check to ensure players can only access their own statistics

## Learning Endpoints

### Get Learning Feedback

**Endpoint:** `GET /api/v1/players/{player_id}/feedback`

**Description:** Fetches learning feedback for a player

**Authentication:** Required (JWT token in `X-API-Key` header)

**Query Parameters:**
- `num_decisions` (optional, default: 1): Number of decisions to include in feedback

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

**Implementation Notes:**
- Retrieves feedback from `LearningTracker`
- Formats for readability
- Includes relevant context for each feedback item
- Security check to ensure players can only access their own feedback

### Get Strategy Profile

**Endpoint:** `GET /api/v1/players/{player_id}/strategy-profile`

**Description:** Fetches player's strategic profile

**Authentication:** Required (JWT token in `X-API-Key` header)

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

**Implementation Notes:**
- Retrieves strategy profile data
- Formats recommendations for frontend display
- Includes visualization-ready data
- Security check to ensure players can only access their own profile

### Get Decision Details

**Endpoint:** `GET /api/v1/players/{player_id}/decisions/{decision_id}`

**Description:** Fetches detailed analysis of a specific decision

**Authentication:** Required (JWT token in `X-API-Key` header)

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

**Implementation Notes:**
- Retrieves specific decision record
- Adds contextual information
- Includes detailed analysis explanation
- Security check to ensure players can only access their own decision details

## WebSocket Implementation

The API includes WebSocket support for real-time updates to game state.

**Endpoint:** `WebSocket /api/ws/games/{game_id}`

**Query Parameters:**
- `player_id`: Required for authentication and to identify the connecting player

**Events:**
- `player_connected`: When a new player connects
- `player_disconnected`: When a player disconnects
- `player_action`: When a player takes an action
- `new_hand`: When a new hand begins
- `game_end`: When the game ends

**Message Format:**
```json
{
  "event_type": "string",
  "timestamp": "timestamp",
  "data": {
    /* Event-specific data */
  }
}
```

**Implementation Notes:**
- Uses a `ConnectionManager` class to handle WebSocket connections
- Authenticates players before accepting connections
- Broadcasts events to all players in a game
- Supports sending personal messages to specific players
- Handles disconnections gracefully

## Error Handling

The API implements a standardized error response format:

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

**Implemented Error Codes:**

| Code | Description | HTTP Status |
|------|-------------|-------------|
| GAME_NOT_FOUND | Game session not found | 404 |
| PLAYER_NOT_FOUND | Player not found | 404 |
| INVALID_ACTION | Action not allowed in current state | 400 |
| NOT_YOUR_TURN | Not the player's turn to act | 403 |
| INSUFFICIENT_FUNDS | Not enough chips for action | 400 |
| INVALID_AMOUNT | Bet amount is invalid | 400 |
| VALIDATION_ERROR | Request data validation failed | 422 |
| SERVER_ERROR | Internal server error | 500 |
| RATE_LIMIT_EXCEEDED | Too many requests | 429 |

**Implementation Notes:**
- Custom exception classes for different error types
- Error handlers registered with FastAPI
- Detailed error messages for debugging
- Rate limit error includes retry information

## Authentication

The API uses JWT-based authentication:

- Tokens are issued when a player is created
- All endpoints except player creation require authentication
- Tokens are passed in the `X-API-Key` header
- Tokens include an expiry time (default 30 days for better UX)
- Security checks ensure players can only access their own data

**Implementation Notes:**
- JWT encoding/decoding with the `jwt` library
- Token creation with expiry
- Dependency injection for authentication
- Claims validation

## Rate Limiting

The API implements rate limiting to prevent abuse:

- Default limit of 60 requests per minute per client
- Configurable via environment variable (`RATE_LIMIT`)
- Identifies clients by IP address
- Returns 429 status code with retry information when limit exceeded

**Implementation Notes:**
- Custom middleware implementation
- Per-client tracking with reset interval
- Configurable limits

## Documentation

The API includes built-in documentation:

- Swagger UI at `/api/docs`
- ReDoc at `/api/redoc`
- Comprehensive schema definitions using Pydantic models
- Endpoint descriptions and parameter details

## Appendix: Requirements Checklist

### 1. Architecture

- [x] RESTful API design with clear resource paths
- [x] JSON as the standard data format
- [x] Proper HTTP status codes and error handling
- [x] Authentication/authorization mechanism
- [x] Request validation and sanitization

### 2. Game Management Endpoints

- [x] Create Game (`POST /api/v1/games`)
- [x] Get Game State (`GET /api/v1/games/{game_id}`)
- [x] Player Action (`POST /api/v1/games/{game_id}/actions`)
- [x] Next Hand (`POST /api/v1/games/{game_id}/next-hand`)
- [x] End Game (`DELETE /api/v1/games/{game_id}`)

### 3. Player Management Endpoints

- [x] Create Player (`POST /api/v1/players`)
- [x] Get Player (`GET /api/v1/players/{player_id}`)
- [x] Get Player Statistics (`GET /api/v1/players/{player_id}/statistics`)

### 4. Learning Endpoints

- [x] Get Learning Feedback (`GET /api/v1/players/{player_id}/feedback`)
- [x] Get Strategy Profile (`GET /api/v1/players/{player_id}/strategy-profile`)
- [x] Get Decision Details (`GET /api/v1/players/{player_id}/decisions/{decision_id}`)

### 5. Session Management

- [x] Mapping between game_id and PokerGame instances
- [x] Handle inactive sessions (timeout after period of inactivity)
- [x] Authentication to ensure players can only access their own information
- [x] Support reconnection to active games

### 6. Data Transformations

- [x] Filter hole cards: Only show current player's cards
- [x] Format card data for frontend rendering (suit/rank separation)
- [x] Convert internal state enums to frontend-friendly strings
- [x] Format currency/chip values consistently
- [x] Structure decision histories in a way that's easy to display
- [x] Normalize timestamps to ISO format

### 7. Error Handling

- [x] Standardized error response format
- [x] Appropriate error codes and HTTP status codes
- [x] Custom exception classes
- [x] Error handlers for different types of exceptions

### 8. Websocket Implementation

- [x] WebSocket endpoint (`/api/ws/games/{game_id}`)
- [x] Event broadcasting
- [x] Connection management
- [x] Authentication for WebSocket connections
- [x] Standardized message format

### 9. Documentation

- [x] OpenAPI/Swagger documentation
- [x] Examples for request/response formats
- [x] Authentication instructions
- [x] Error code references

### 10. Versioning

- [x] API versioning (e.g., `/api/v1/games`)