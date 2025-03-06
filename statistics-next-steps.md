# Learning Statistics Implementation Plan

## Overview

This document outlines the implementation plan for the Learning Statistics component of our poker game. The primary goal is to provide novice players with helpful guidance by comparing their decisions to what different AI strategies would have done in the same situation. This will help players understand different poker playing styles and improve their decision-making.

## Core Concept

The Learning Statistics system will:
1. Evaluate human player decisions
2. Classify these decisions according to AI strategy types
3. Identify which strategy would have been optimal
4. Provide simple, actionable feedback
5. Track improvement over time

## Implementation Tasks

### 1. Create LearningStatistics Class

```python
class LearningStatistics:
    """
    Tracks a player's decision quality and learning progress over time.
    """
    
    # Constants for storage management
    MAX_DETAILED_DECISIONS = 100  # Only store last 100 detailed decisions
    
    def __init__(self, player_id: str):
        self.player_id = player_id
        self.total_decisions = 0
        self.decisions_by_strategy = {
            "Conservative": 0,
            "Risk Taker": 0,
            "Probability-Based": 0,
            "Bluffer": 0
        }
        self.optimal_decisions = 0
        self.decision_history = []  # Limited list of recent decisions with context
        self.current_session_id = None
        self.improvement_by_spr = {
            "low": [],    # SPR < 3
            "medium": [], # 3 <= SPR <= 6
            "high": []    # SPR > 6
        }
    
    def add_decision(self, decision_data):
        """Add a new decision, managing the history size."""
        self.total_decisions += 1
        
        # Update strategy alignment counter
        matching_strategy = decision_data.get("matching_strategy")
        if matching_strategy in self.decisions_by_strategy:
            self.decisions_by_strategy[matching_strategy] += 1
            
        # Check if decision was optimal
        if decision_data.get("was_optimal", False):
            self.optimal_decisions += 1
            
        # Add to history, maintaining size limit
        self.decision_history.append(decision_data)
        if len(self.decision_history) > self.MAX_DETAILED_DECISIONS:
            self.decision_history.pop(0)  # Remove oldest entry
```

Add methods to update and retrieve learning statistics, plus serialization support for storage.

### 2. Update StatisticsManager with Storage Lifecycle Management

Add methods to:
- Create/retrieve LearningStatistics
- Store decision comparisons with session context
- Calculate improvement metrics
- Link with existing PlayerStatistics
- Manage storage lifecycle

```python
class StatisticsManager:
    # Add to existing class
    
    MAX_SESSIONS = 5  # Only keep detailed data for last 5 sessions
    
    def get_learning_statistics(self, player_id: str) -> LearningStatistics:
        """Retrieves learning statistics for a player, creating if needed."""
        # Implementation
    
    def record_decision(self, player_id: str, decision_data: Dict[str, Any]):
        """Records a player's decision with context and classification."""
        learning_stats = self.get_learning_statistics(player_id)
        decision_data["timestamp"] = time.time()
        decision_data["session_id"] = self.current_session_id
        learning_stats.add_decision(decision_data)
        self.save_learning_statistics(player_id)
    
    def start_session(self, session_id: str):
        """Starts a new session for tracking purposes."""
        self.current_session_id = session_id
    
    def end_session(self, session_id: str):
        """
        Ends a session, aggregating data and cleaning up.
        This is where we'd implement pruning of old session data.
        """
        # Aggregate session data into player statistics
        # Prune detailed data beyond retention policy
        self.prune_old_sessions()
    
    def prune_old_sessions(self):
        """
        Removes detailed decision data for sessions beyond our retention policy.
        Keeps aggregate statistics for all sessions.
        """
        # Implementation to remove detailed data for old sessions
        # while preserving the aggregate statistics
```

### 3. Game Engine Integration Points

#### 3.1 Add Decision Classification Method

```python
def classify_decision(self, player_id: str, decision: str, hole_cards: List[str], 
                     game_state: Dict, deck: List[str], pot_size: int, spr: float):
    """
    Classifies a player's decision according to AI strategy types.
    Returns the matching strategy and whether it was optimal.
    """
    # Implement decision classification logic
    # Compare with what each AI type would do
    # Return classification results
```

#### 3.2 Add Hooks in Player Decision Points

Modify the following methods in game_engine.py:
- `betting_round()`: After a human player makes a decision
- `play_hand()`: At the end of each hand

#### 3.3 Create Optimal Strategy Finder

```python
def find_optimal_strategy(self, hole_cards: List[str], game_state: Dict, 
                         deck: List[str], pot_size: int, spr: float) -> str:
    """
    Determines which AI strategy would be optimal in the current situation.
    This could be the strategy that maximizes EV or best handles the specific 
    game context.
    """
    # Test each strategy
    # Return the strategy with the best outcome
```

### 4. Feedback Generation (2 days)

Create a system to generate actionable feedback for players:

```python
def generate_feedback(self, player_decision: str, optimal_decision: str, 
                     matching_strategy: str, optimal_strategy: str,
                     context: Dict) -> Dict[str, str]:
    """
    Generates personalized feedback based on a player's decision.
    """
    # Create explanation of the player's approach
    # Compare with optimal approach
    # Provide specific advice
    # Return formatted feedback
```

### 5. Statistics Analyzer Updates (2 days)

Enhance StatisticsAnalyzer to:
- Track strategy preferences over time
- Identify recurring decision patterns
- Calculate improvement rates
- Generate learning recommendations

```python
def analyze_learning_progress(self, player_id: str) -> Dict[str, Any]:
    """
    Analyzes a player's learning progress over time.
    """
    # Retrieve learning statistics
    # Calculate improvement metrics
    # Identify patterns and trends
    # Generate recommendations
```

### 6. Testing Framework (3 days)

#### 6.1 Unit Tests for LearningStatistics

Create comprehensive tests for:
- Decision classification
- Strategy comparison
- Feedback generation
- Progress tracking

#### 6.2 Integration Tests

Test the entire flow from:
- Player decision capture
- Classification and comparison
- Feedback generation
- Statistics storage and retrieval

### 7. Documentation (1 day)

- Add detailed docstrings to all new components
- Update existing documentation to reflect new capabilities
- Create examples of how to interpret learning statistics

## Implementation Sequence

1. **Week 1:**
   - Implement LearningStatistics class
   - Update StatisticsManager
   - Create basic classification method

2. **Week 2:**
   - Integrate with game engine
   - Implement feedback generation
   - Update analyzer for learning statistics

3. **Week 3:**
   - Develop testing framework
   - Complete documentation
   - Perform final integration and testing

## Technical Considerations

### Data Structure for Decision History

Store decision contexts with:
- Hand state (hole cards, community cards)
- Game state (pot size, SPR, betting position)
- Player's decision
- Matched strategy
- Optimal strategy
- Outcome (if applicable)
- Session ID (to track and prune by session)
- Timestamp (for chronological analysis)

Example decision data structure:
```python
decision_data = {
    "hand_id": "hand_123",
    "session_id": "session_456",
    "timestamp": 1678234567,
    "hole_cards": ["Ah", "Kh"],
    "community_cards": ["7s", "8d", "Qc"],
    "game_state": "flop",
    "pot_size": 120,
    "spr": 4.5,
    "player_decision": "raise",
    "matching_strategy": "Risk Taker",
    "optimal_strategy": "Probability-Based",
    "was_optimal": False,
    "explanation": "With top pair and a strong kicker, a call would be more appropriate given the medium SPR."
}
```

### Classification Methodology

Use the same thresholds and logic from AI strategies:
- Conservative: Plays only strong hands
- Risk Taker: Raises aggressively
- Probability-Based: Uses hand strength thresholds
- Bluffer: Makes unpredictable bets

### Storage Lifecycle Management

1. **Limited Decision History:**
   - Keep only the MAX_DETAILED_DECISIONS most recent decisions (e.g., 100)
   - Implement as a rolling buffer in the LearningStatistics class
   - Older decisions are discarded when new ones are added

2. **Session-Based Retention:**
   - Track decisions by session_id
   - Keep detailed data for only MAX_SESSIONS most recent sessions (e.g., 5)
   - Automatically prune older session data during application startup

3. **Aggregation Strategy:**
   - After each session, aggregate detailed data into summary statistics
   - Update trend data based on these aggregates
   - Keep aggregate statistics indefinitely, but prune detailed data

4. **Storage Format:**
   - Use JSON for compatibility with existing statistics system
   - Separate files for current session vs. historical aggregates
   - Store in the same game-data directory structure

## Potential Future Enhancements

1. **Personalized Learning Path:**
   - Generate custom learning plans based on identified weaknesses

2. **Hand Replays:**
   - Allow players to review past hands with detailed feedback

3. **Strategy Adaptation:**
   - Suggest adjustments based on opponents' playing styles

4. **Visual Learning Dashboard:**
   - Create visual representations of learning progress

These enhancements would be implemented after the core functionality is complete and validated.