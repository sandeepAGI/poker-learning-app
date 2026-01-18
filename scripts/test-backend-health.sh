#!/bin/bash
# TEST: Comprehensive backend health checks

BACKEND_URL="${1:-https://poker-api-demo.azurewebsites.net}"

echo "🔍 Testing backend at $BACKEND_URL"
echo ""

# TEST 1: Health endpoint responds
echo "Test 1: Health endpoint..."
HEALTH=$(curl -s "$BACKEND_URL/health" -m 10)
if echo "$HEALTH" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    echo "✅ PASS: Health endpoint healthy"
    echo "   Response: $HEALTH"
else
    echo "❌ FAIL: Health endpoint unhealthy or unreachable"
    echo "   Response: $HEALTH"
    exit 1
fi

echo ""
echo "🎉 Backend health check passed!"
echo "Backend URL: $BACKEND_URL"
