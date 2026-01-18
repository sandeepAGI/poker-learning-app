#!/bin/bash
# TEST: Verify GitHub secrets are configured
# Note: This test runs IN GitHub Actions, not locally

echo "🔍 Verifying GitHub secrets..."

# TEST 1: AZURE_CREDENTIALS exists
if [ -z "$AZURE_CREDENTIALS" ]; then
    echo "❌ FAIL: AZURE_CREDENTIALS not set"
    exit 1
fi
echo "✅ PASS: AZURE_CREDENTIALS is set"

# TEST 2: ANTHROPIC_API_KEY exists
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ FAIL: ANTHROPIC_API_KEY not set"
    exit 1
fi
echo "✅ PASS: ANTHROPIC_API_KEY is set"

# TEST 3: Parse Azure credentials
if ! echo "$AZURE_CREDENTIALS" | jq -e '.clientId' > /dev/null 2>&1; then
    echo "❌ FAIL: AZURE_CREDENTIALS is not valid JSON"
    exit 1
fi
echo "✅ PASS: AZURE_CREDENTIALS is valid JSON"

echo ""
echo "🎉 All GitHub secrets tests passed!"
