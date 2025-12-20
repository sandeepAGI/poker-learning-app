#!/bin/bash
#
# Run Phase 4 LLM E2E Tests
#
# Usage:
#   ./run_llm_tests.sh              # Run free tests only (no API calls)
#   ./run_llm_tests.sh --with-api   # Run all tests including API calls ($0.11 cost)
#

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Phase 4 LLM Analysis E2E Tests${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if backend and frontend are running
echo "Checking if servers are running..."

if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend not running on http://localhost:8000${NC}"
    echo "Start backend: cd backend && python main.py"
    exit 1
fi

if ! curl -s http://localhost:3000/ > /dev/null 2>&1; then
    echo -e "${RED}❌ Frontend not running on http://localhost:3000${NC}"
    echo "Start frontend: cd frontend && npm run dev"
    exit 1
fi

echo -e "${GREEN}✅ Both servers running${NC}"
echo ""

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ] && [ ! -f "../../backend/.env" ]; then
    echo -e "${YELLOW}⚠️  ANTHROPIC_API_KEY not found${NC}"
    echo "LLM tests will be skipped (only free UI tests will run)"
    echo ""
fi

# Determine which tests to run
if [ "$1" == "--with-api" ]; then
    echo -e "${YELLOW}Running ALL tests (including LLM API calls)${NC}"
    echo -e "${YELLOW}⚠️  This will cost ~$0.11 in API fees${NC}"
    echo ""
    export SKIP_LLM_TESTS=0
else
    echo -e "${GREEN}Running FREE tests only (no API calls)${NC}"
    echo "To run all tests: $0 --with-api"
    echo ""
    export SKIP_LLM_TESTS=1
fi

# Run tests
cd ../..  # Go to repo root

echo "Running E2E tests for LLM analysis..."
echo ""

PYTHONPATH=. python -m pytest tests/e2e/test_llm_analysis.py -v -s

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Test Results Summary${NC}"
echo -e "${GREEN}========================================${NC}"

# Show cost summary
if [ "$SKIP_LLM_TESTS" == "0" ]; then
    echo ""
    echo -e "${YELLOW}💰 API Costs:${NC}"
    echo "  Estimated: ~$0.11"
    echo "  Check actual: http://localhost:8000/admin/analysis-metrics"
    echo ""
fi

echo -e "${GREEN}✅ All tests completed!${NC}"
