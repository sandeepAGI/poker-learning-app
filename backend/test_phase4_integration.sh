#!/bin/bash
# Phase 4 Integration Test - Tests complete LLM analysis workflow
# Tests the actual LLM call (costs ~$0.016)

set -e  # Exit on error

echo "==================================================================="
echo "Phase 4 Integration Test - LLM Hand Analysis"
echo "==================================================================="
echo ""

# Check backend is running
echo "1. Checking backend is running..."
if ! curl -s http://localhost:8000/admin/analysis-metrics > /dev/null 2>&1; then
    echo "❌ Backend not running on port 8000"
    exit 1
fi
echo "✅ Backend is running"
echo ""

# Create game
echo "2. Creating new game..."
GAME_ID=$(curl -s -X POST http://localhost:8000/games \
    -H "Content-Type: application/json" \
    -d '{"num_ai_players": 3}' | jq -r '.game_id')

if [ -z "$GAME_ID" ] || [ "$GAME_ID" = "null" ]; then
    echo "❌ Failed to create game"
    exit 1
fi
echo "✅ Game created: $GAME_ID"
echo ""

# Play one hand (fold)
echo "3. Playing one hand (folding)..."
STATE=$(curl -s -X POST "http://localhost:8000/games/${GAME_ID}/actions" \
    -H "Content-Type: application/json" \
    -d '{"action": "fold"}' | jq -r '.state')

if [ "$STATE" != "showdown" ]; then
    echo "❌ Hand didn't complete properly (state: $STATE)"
    exit 1
fi
echo "✅ Hand completed (showdown)"
echo ""

# Request Quick Analysis (Haiku 4.5, ~$0.016)
echo "4. Requesting Quick Analysis (Haiku 4.5, cost: ~\$0.016)..."
echo "   This will make a real API call to Anthropic..."
RESPONSE=$(curl -s "http://localhost:8000/games/${GAME_ID}/analysis-llm?depth=quick&use_cache=false")

# Parse response
MODEL=$(echo "$RESPONSE" | jq -r '.model_used')
COST=$(echo "$RESPONSE" | jq -r '.cost')
ERROR=$(echo "$RESPONSE" | jq -r '.error // "None"')
HAS_SUMMARY=$(echo "$RESPONSE" | jq '.analysis.summary != null')
TIP_COUNT=$(echo "$RESPONSE" | jq '.analysis.tips_for_improvement | length')

echo "   Model used: $MODEL"
echo "   Cost: \$$COST"
echo "   Error: $ERROR"
echo ""

# Validate response
if [ "$ERROR" != "None" ] && [ "$ERROR" != "null" ]; then
    echo "❌ LLM analysis failed with error: $ERROR"
    echo ""
    echo "Response keys:"
    echo "$RESPONSE" | jq 'keys'
    echo ""
    echo "Analysis keys (if present):"
    echo "$RESPONSE" | jq '.analysis | keys'
    exit 1
fi

if [ "$MODEL" = "rule-based-fallback" ]; then
    echo "⚠️  LLM analysis fell back to rule-based (quality check failed)"
    echo ""
    echo "This suggests the LLM response didn't match expected schema."
    echo "Showing response structure for debugging:"
    echo ""
    echo "$RESPONSE" | jq '{model, cost, error, analysis_keys: (.analysis | keys)}'
    exit 1
fi

if [ "$HAS_SUMMARY" != "true" ]; then
    echo "❌ Analysis missing 'summary' field"
    exit 1
fi

if [ "$TIP_COUNT" -lt 1 ]; then
    echo "❌ Analysis has no tips ($TIP_COUNT tips)"
    exit 1
fi

echo "✅ Quick Analysis successful!"
echo "   - Model: $MODEL"
echo "   - Cost: \$$COST"
echo "   - Has summary: Yes"
echo "   - Tips count: $TIP_COUNT"
echo ""

# Check metrics updated
echo "5. Verifying metrics were updated..."
METRICS=$(curl -s http://localhost:8000/admin/analysis-metrics)
TOTAL=$(echo "$METRICS" | jq '.total_analyses')
HAIKU=$(echo "$METRICS" | jq '.haiku_analyses')
TOTAL_COST=$(echo "$METRICS" | jq '.total_cost')

echo "   Total analyses: $TOTAL"
echo "   Haiku analyses: $HAIKU"
echo "   Total cost: \$$TOTAL_COST"

if [ "$TOTAL" -lt 1 ]; then
    echo "❌ Metrics not updated (total=$TOTAL)"
    exit 1
fi

echo "✅ Metrics updated correctly"
echo ""

# Test caching
echo "6. Testing caching (should return instantly)..."
START_TIME=$(date +%s)
CACHED_RESPONSE=$(curl -s "http://localhost:8000/games/${GAME_ID}/analysis-llm?depth=quick")
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

CACHED=$(echo "$CACHED_RESPONSE" | jq -r '.cached')

if [ "$CACHED" != "true" ]; then
    echo "❌ Response not cached (cached=$CACHED)"
    exit 1
fi

if [ $DURATION -gt 2 ]; then
    echo "⚠️  Cached response took ${DURATION}s (should be <1s)"
fi

echo "✅ Caching works (cached=true, ${DURATION}s)"
echo ""

# Summary
echo "==================================================================="
echo "✅ All Phase 4 Integration Tests PASSED"
echo "==================================================================="
echo ""
echo "Summary:"
echo "  - Backend API: Working"
echo "  - Game creation: Working"
echo "  - Hand completion: Working"
echo "  - LLM Analysis (Haiku): Working (\$$COST)"
echo "  - Metrics tracking: Working"
echo "  - Caching: Working"
echo ""
echo "Total cost: ~\$$COST"
echo ""
