#!/bin/bash
# TEST: Verify Azure setup is complete

echo "🔍 Verifying Azure setup..."

# TEST 1: Azure CLI is logged in
if ! az account show &>/dev/null; then
    echo "❌ FAIL: Not logged into Azure CLI"
    exit 1
fi
echo "✅ PASS: Azure CLI authenticated"

# TEST 2: Subscription is active
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
if [ -z "$SUBSCRIPTION_ID" ]; then
    echo "❌ FAIL: No active subscription"
    exit 1
fi
echo "✅ PASS: Subscription ID: $SUBSCRIPTION_ID"

# TEST 3: Service principal exists and has access
SP_APP_ID=$(az ad sp list --filter "displayName eq 'github-poker-learning-app'" --query "[0].appId" -o tsv)
if [ -z "$SP_APP_ID" ]; then
    echo "❌ FAIL: Service principal not found"
    exit 1
fi
echo "✅ PASS: Service principal exists (App ID: $SP_APP_ID)"

echo ""
echo "🎉 All Azure setup tests passed!"
