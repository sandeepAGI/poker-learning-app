# Comprehensive E2E Test Suite

This directory contains a comprehensive end-to-end test suite for the Poker Learning App backend.

## What This Test Does

The `comprehensive_e2e_test.py` script:

1. Plays 10 complete poker hands with 4 AI players and 1 human player
2. Human player always calls (for testing consistency)
3. Records and analyzes game statistics
4. Provides gameplay tips at the end based on data collected
5. Verifies:
   - Winner determination works correctly
   - Stack updates are properly applied
   - Pot calculations are accurate
   - Folding behavior is handled properly
   - API returns expected data structures

## Key Features Tested

- Multiple hand progression
- Pot distribution to winners
- Stack tracking across hands
- Showdown handling
- Game state transitions
- Card dealing and management
- Player statistics and analytics

## Running the Test

Use the included shell script to run the test suite:

```bash
./run_comprehensive_test.sh
```

This script will:
1. Stop any existing API server
2. Start a fresh API server instance
3. Run the comprehensive test
4. Generate gameplay analysis and tips
5. Shutdown the API server when complete

## Test Output

The test generates several outputs:

1. Console logs showing game progression and player actions
2. A `game_analysis.json` file with complete test data including:
   - Hand results
   - Player actions
   - Showdown data
   - Player statistics
   - Gameplay tips
3. An `e2e_test_suite.log` file with detailed logging

## Rate Limiting Protection

The test implements several measures to avoid 429 Too Many Requests errors:

1. **Strategic Delays**:
   - 10-second delay before each human player action
   - 5-second delay before starting each new hand
   - 3-second delays during initial game setup

2. **Robust API Request Handling**:
   - All API calls use a retry mechanism with exponential backoff
   - Automatically retries requests when rate limits are hit (up to 3 attempts)
   - Provides detailed logging of rate limit encounters

These delays mimic realistic human gameplay speed and ensure the test can run reliably without hitting API rate limits.

## Modifying the Test

You can adjust these parameters to change test behavior:

- `STARTING_STACK`: Change the starting chip amount (default: 1,000,000)
- `hands_played`: Change target number of hands to play (default: 10)
- In `execute_player_turn()`: Modify human player strategy (currently always calls)
- Delay timings in various functions to adjust test speed (longer delays = more reliable but slower tests)

## Retry Mechanism

The test uses a custom `make_api_request` helper function that:

1. Accepts HTTP method, URL, headers, and JSON payload
2. Makes the request and checks for 429 status code
3. If rate limited, waits with exponential backoff and retries
4. Returns response object or None if all retries failed
5. Provides detailed error logging

This ensures tests can recover from temporary rate limiting issues.

## Using This For Frontend Testing

Once this test suite passes consistently, you can be confident that:

1. The backend API is functioning correctly
2. All core game mechanics work as expected
3. Data is properly structured and consistent
4. Rate limiting is properly handled

This provides a solid foundation for developing the frontend, knowing the API will behave predictably.