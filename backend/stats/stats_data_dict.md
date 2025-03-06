# Poker Statistics System: Data Dictionary, Function Reference, and Dependencies

## Table of Contents

1. [Data Dictionary](#data-dictionary)
2. [Function Reference](#function-reference)
3. [Dependency Map](#dependency-map)
4. [File Structure](#file-structure)
5. [External Dependencies](#external-dependencies)

---

## Data Dictionary

### Core Data Structures

#### Decision Data
| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| decision | string | Player's decision | "fold", "call", "raise" |
| matching_strategy | string | Strategy that best matches player's decision | "Conservative" |
| optimal_strategy | string | Optimal strategy for the situation | "Risk Taker" |
| was_optimal | boolean | Whether player's decision was optimal | true |
| strategy_decisions | dict | Decisions from each strategy | {"Conservative": "fold", "Risk Taker": "raise"} |
| expected_value | float | Expected value of optimal decision | 1.2 |
| spr | float | Stack-to-pot ratio | 4.5 |
| game_state | string | Current game stage | "pre_flop", "flop", "turn", "river" |
| hole_cards | list | Player's private cards | ["Ah", "Kh"] |
| community_cards | list | Shared community cards | ["7s", "8d", "Qc"] |
| pot_size | float | Current pot size | 120.0 |
| current_bet | float | Current bet to call | 30.0 |
| timestamp | float | Time when decision was recorded | 1678234567.0 |
| session_id | string | Session identifier | "session_456" |

#### Learning Statistics
| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| player_id | string | Unique player identifier | "player_123" |
| total_decisions | int | Total number of decisions analyzed | 125 |
| correct_decisions | int | Number of optimal decisions | 75 |
| decisions_by_strategy | dict | Count of decisions by strategy | {"Conservative": 45, "Risk Taker": 30} |
| optimal_strategies | dict | Count of optimal strategies | {"Conservative": 35, "Risk Taker": 40} |
| decision_history | list | Recent decision data (limited) | [decision_data_1, decision_data_2, ...] |
| current_session_id | string | Current active session | "session_456" |
| positive_ev_decisions | int | Decisions with positive expected value | 80 |
| negative_ev_decisions | int | Decisions with negative expected value | 45 |
| improvement_by_spr | dict | Improvement tracking by SPR range | {"low": [], "medium": [], "high": []} |

#### Player Statistics
| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| player_id | string | Unique player identifier | "player_123" |
| hands_played | int | Total hands played | 250 |
| hands_won | int | Hands won | 75 |
| total_winnings | float | Total amount won | 1200.0 |
| total_losses | float | Total amount lost | 800.0 |
| vpip | float | Voluntarily Put Money In Pot percentage | 25.5 |
| pfr | float | Pre-Flop Raise percentage | 18.2 |
| aggression_factor | float | Aggression factor | 2.5 |
| showdown_count | int | Number of showdowns | 60 |
| showdown_wins | int | Showdowns won | 30 |
| position_hands | dict | Hands played by position | {"early": 80, "middle": 85, "late": 85} |
| position_wins | dict | Hands won by position | {"early": 20, "middle": 25, "late": 30} |

#### Session Statistics
| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| session_id | string | Unique session identifier | "session_456" |
| start_time | float | Session start timestamp | 1678234000.0 |
| end_time | float | Session end timestamp | 1678240000.0 |
| hands_played | int | Hands played in session | 45 |
| players | list | Players in session | ["player_123", "player_456"] |
| starting_chips | int | Initial chip count | 1000 |
| final_chip_counts | dict | Final chips by player | {"player_123": 1200, "player_456": 800} |
| elimination_order | list | Order of player eliminations | ["player_789", "player_456"] |

#### Strategy Profile
| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| strategy_distribution | dict | Distribution of matched strategies | {"Conservative": 35.0, "Risk Taker": 25.0} |
| dominant_strategy | string | Most frequent strategy match | "Conservative" |
| recommended_strategy | string | Strategy that would be optimal | "Probability-Based" |
| decision_accuracy | float | Percentage of optimal decisions | 65.2 |
| ev_ratio | float | Percentage of +EV decisions | 70.3 |
| total_decisions | int | Total decisions analyzed | 125 |
| improvement_areas | list | Areas needing improvement | [{"type": "game_state", "area": "turn"}] |
| learning_recommendations | list | Personalized recommendations | [{"focus": "turn_play", "title": "Improve Turn Decision Making"}] |
| decision_trend | dict | Trend in decision quality | {"trend": "improving", "description": "..."}|

#### Improvement Area
| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| type | string | Type of improvement area | "game_state", "spr_range", "strategy_alignment" |
| area | string | Specific area for improvement | "turn", "high", "strategy_shift" |
| description | string | Detailed description | "Your decisions on the turn are less optimal..." |

#### Learning Recommendation
| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| focus | string | Focus area for improvement | "turn_play", "medium_spr_play", "fundamentals" |
| title | string | Recommendation title | "Improve Turn Decision Making" |
| description | string | Detailed advice | "Focus on re-evaluating hand strength..." |

#### Decision Trend
| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| trend | string | Overall trend direction | "improving", "declining", "stable" |
| description | string | Trend description | "Your decision making is showing clear improvement!" |
| improvement_rate | float | Rate of improvement | 12.5 |
| first_half_accuracy | float | Accuracy in first half of decisions | 50.3 |
| second_half_accuracy | float | Accuracy in second half of decisions | 62.8 |
| recent_trend | string | Very recent trend (optional) | "recent_improvement" |
| recent_description | string | Description of recent trend | "Your most recent decisions show significant improvement!" |

---

## Function Reference

### StatisticsManager (backend/stats/statistics_manager.py)

| Function | Parameters | Returns | Description | Dependencies |
|----------|------------|---------|-------------|--------------|
| get_statistics_manager() | None | StatisticsManager | Returns singleton instance of statistics manager | None |
| \_\_init__() | None | None | Initializes manager and ensures data directories exist | os (for directory creation) |
| start_session() | session_id (optional) | str | Starts a new game session, returns session ID | uuid (if no session ID provided) |
| end_session() | session_id | None | Ends a session and finalizes statistics | SessionStatistics |
| get_player_statistics() | player_id | PlayerStatistics | Gets statistics for a player | PlayerStatistics |
| get_session_statistics() | session_id | SessionStatistics | Gets statistics for a session | SessionStatistics |
| get_learning_statistics() | player_id | LearningStatistics | Gets learning statistics for a player | LearningStatistics |
| record_decision() | player_id, decision_data | None | Records a player's decision with context | LearningStatistics |
| _load_player_statistics() | player_id | None | Loads player statistics from disk | json, PlayerStatistics |
| _save_player_statistics() | player_id | None | Saves player statistics to disk | json |
| _load_session_statistics() | session_id | None | Loads session statistics from disk | json, SessionStatistics |
| _save_session_statistics() | session_id | None | Saves session statistics to disk | json |
| _load_learning_statistics() | player_id | None | Loads learning statistics from disk | json, LearningStatistics |
| _save_learning_statistics() | player_id | None | Saves learning statistics to disk | json |
| _prune_old_sessions() | None | None | Removes detailed data for sessions beyond retention policy | os (for file operations) |

### AIDecisionAnalyzer (backend/stats/ai_decision_analyzer.py)

| Function | Parameters | Returns | Description | Dependencies |
|----------|------------|---------|-------------|--------------|
| get_decision_analyzer() | None | AIDecisionAnalyzer | Returns singleton instance of analyzer | None |
| \_\_init__() | None | None | Initializes the AI decision analyzer | get_statistics_manager() |
| analyze_decision() | player_id, player_decision, hole_cards, game_state, deck, pot_size, spr | dict | Analyzes a player's poker decision | AIDecisionMaker |
| _find_matching_strategy() | player_decision, strategy_decisions | str | Finds which strategy most closely matches player's decision | None |
| _find_optimal_strategy() | strategy_decisions, hole_cards, game_state, pot_size, spr | (str, float) | Determines the optimal strategy for the game context | None |
| generate_feedback() | decision_data | str | Generates detailed, educational feedback | FeedbackGenerator (if available) |
| get_player_strategy_profile() | player_id | dict | Gets a player's strategy profile with recommendations | LearningStatistics, PatternAnalyzer, RecommendationEngine, TrendAnalyzer |

### LearningStatistics (backend/stats/learning_statistics.py)

| Function | Parameters | Returns | Description | Dependencies |
|----------|------------|---------|-------------|--------------|
| \_\_init__() | player_id | None | Initialize learning statistics for a player | None |
| add_decision() | decision_data | None | Add a new decision, managing the history size | None |
| decision_accuracy (property) | None | float | Returns the percentage of correct decisions | None |
| dominant_strategy (property) | None | str | Returns the strategy that best matches player's decisions | None |
| recommended_strategy (property) | None | str | Returns the strategy that would have been optimal most often | None |
| get_recent_decisions() | num_decisions=10 | list | Get the most recent decisions with full context | None |
| get_strategy_distribution() | None | dict | Calculate the percentage distribution of decisions by strategy | None |
| to_dict() | None | dict | Convert object to dictionary for serialization | None |
| from_dict() | data | LearningStatistics | Create a LearningStatistics object from dictionary data | None |

### FeedbackGenerator (backend/stats/analyzer/feedback_generator.py)

| Function | Parameters | Returns | Description | Dependencies |
|----------|------------|---------|-------------|--------------|
| generate_feedback() | decision_data | str | Generates detailed, educational feedback for a player | HandAnalyzer |
| get_game_stage_tip() | game_state, decision, was_optimal | str | Provides stage-specific poker tips | None |
| get_improvement_tip() | matching_strategy, optimal_strategy, was_optimal, decision | str | Provides forward-looking advice for player improvement | None |

### HandAnalyzer (backend/stats/analyzer/hand_analyzer.py)

| Function | Parameters | Returns | Description | Dependencies |
|----------|------------|---------|-------------|--------------|
| analyze_hand_strength() | hole_cards, community_cards, game_state | str | Analyzes the strength of the player's hand | None |
| get_strategy_reasoning() | strategy, decision, game_state, spr, hole_cards, community_cards | str | Provides reasoning for a strategy's decision | None |
| get_spr_based_tip() | spr, game_state | str | Provides educational tips based on stack-to-pot ratio | None |

### PatternAnalyzer (backend/stats/analyzer/pattern_analyzer.py)

| Function | Parameters | Returns | Description | Dependencies |
|----------|------------|---------|-------------|--------------|
| analyze_game_state_patterns() | decisions | dict | Analyzes player decisions across different game states | None |
| analyze_spr_patterns() | decisions | dict | Analyzes player decisions across different SPR ranges | None |
| identify_improvement_areas() | recent_decisions, dominant_strategy, recommended_strategy, accuracy, spr_patterns, game_state_patterns | list | Identifies specific areas for improvement | None |

### RecommendationEngine (backend/stats/analyzer/recommendation_engine.py)

| Function | Parameters | Returns | Description | Dependencies |
|----------|------------|---------|-------------|--------------|
| generate_learning_recommendations() | dominant_strategy, recommended_strategy, improvement_areas, total_decisions | list | Generates personalized learning recommendations | None |

### TrendAnalyzer (backend/stats/analyzer/trend_analyzer.py)

| Function | Parameters | Returns | Description | Dependencies |
|----------|------------|---------|-------------|--------------|
| analyze_decision_quality_trend() | recent_decisions | dict | Analyzes the trend in decision quality over time | None |

### AIDecisionMaker (backend/ai/ai_manager.py)

| Function | Parameters | Returns | Description | Dependencies |
|----------|------------|---------|-------------|--------------|
| make_decision() | personality, hole_cards, game_state, deck, pot_size, spr | str | Makes a poker decision based on personality and game state | ConservativeStrategy, RiskTakerStrategy, ProbabilityBasedStrategy, BlufferStrategy |

---

## Dependency Map

### Component Dependencies

```
+----------------------+     +----------------------+     +----------------------+
| Game Engine          |---->| AIDecisionAnalyzer   |---->| AIDecisionMaker      |
+----------------------+     +----------------------+     +----------------------+
                             |                      |     | - ConservativeStrategy
                             |                      |     | - RiskTakerStrategy
                             |                      |     | - ProbabilityBasedStrategy
                             |                      |     | - BlufferStrategy
                             v                      |     +----------------------+
                      +------+-------+          +---+--------------------+
                      | StatisticsManager |     | HandEvaluator           |
                      +------+-------+          +------------------------+
                             |
           +----------------++-----------------+-------------+
           |                |                  |             |
+----------+-----+ +--------+------+ +---------+---+ +-------+-------+
| PlayerStatistics| |SessionStatistics| |LearningStatistics| |Analyzer Modules|
+----------------+ +---------------+ +-------------+ +---------------+
                                                      |
                     +--------------------+-----------+-----------+------------+
                     |                    |                       |            |
          +----------+-------+ +----------+--------+ +-----------+----+ +-----+------------+
          | FeedbackGenerator | | PatternAnalyzer    | | TrendAnalyzer  | | RecommendationEngine |
          +------------------+ +-------------------+ +----------------+ +------------------+
```

### Initialization Order

For proper system functioning, components should be initialized in this order:

1. HandEvaluator (required by AI strategies)
2. AI Strategy implementations
3. AIDecisionMaker
4. StatisticsManager
5. LearningStatistics instances (created by StatisticsManager as needed)
6. AIDecisionAnalyzer
7. Analyzer modules (if available):
   - FeedbackGenerator
   - HandAnalyzer
   - PatternAnalyzer
   - RecommendationEngine
   - TrendAnalyzer

---

## File Structure

```
backend/
├── ai/
│   ├── __init__.py
│   ├── ai_manager.py             # AIDecisionMaker implementation
│   ├── ai_protocol.py            # Protocol for AI strategies
│   ├── base_ai.py                # Base AI implementation
│   ├── hand_evaluator.py         # Poker hand evaluation
│   └── strategies/
│       ├── __init__.py
│       ├── bluffer.py            # Bluffer strategy implementation
│       ├── conservative.py       # Conservative strategy implementation
│       ├── probability_based.py  # Probability-Based strategy implementation
│       └── risk_taker.py         # Risk Taker strategy implementation
├── stats/
│   ├── __init__.py
│   ├── ai_decision_analyzer.py   # Decision analysis implementation
│   ├── learning_statistics.py    # Learning progress tracking
│   ├── statistics_manager.py     # Statistics management
│   └── analyzer/
│       ├── __init__.py
│       ├── feedback_generator.py # Feedback generation
│       ├── hand_analyzer.py      # Hand analysis
│       ├── pattern_analyzer.py   # Pattern recognition
│       ├── recommendation_engine.py # Recommendation generation
│       └── trend_analyzer.py     # Trend analysis
└── utils/
    └── logger.py                 # Logging utilities
```

---

## External Dependencies

### Core Python Libraries

| Library | Purpose | Usage |
|---------|---------|-------|
| typing | Type annotations | Used throughout for type definitions |
| json | Data serialization | Used for storing/loading statistics |
| time | Timestamp management | Used for recording decision times |
| uuid | Unique ID generation | Used for session ID creation |
| os | File operations | Used for file and directory management |
| sys | Path management | Used for import path configuration |
| copy | Object copying | Used for deep copying objects |
| enum | Enumeration support | Used for defining poker positions |
| random | Random number generation | Used in Monte Carlo simulations |

### Third-Party Libraries

| Library | Purpose | Version | Usage |
|---------|---------|---------|-------|
| treys | Poker hand evaluation | N/A | Used for evaluating hand strength |

### Storage Requirements

The system uses a directory structure for data persistence:

```
game_data/
├── players/              # Player statistics
│   ├── player_123.json
│   └── ...
├── sessions/             # Session statistics
│   ├── session_456.json
│   └── ...
└── learning/             # Learning statistics
    ├── player_123.json
    └── ...
```

### Constants and Configuration Values

| Constant | Value | Location | Description |
|----------|-------|----------|-------------|
| MAX_DETAILED_DECISIONS | 100 | LearningStatistics | Maximum number of detailed decisions to store |
| MAX_SESSIONS | 5 | StatisticsManager | Maximum number of sessions to keep detailed data for |
| DATA_DIR | "game_data" | StatisticsManager | Base directory for storing statistics |