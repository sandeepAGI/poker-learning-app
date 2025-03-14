#!/bin/bash

# Stop any existing API server
echo "Stopping existing API server..."
pkill -f "python api.py" || true

# Wait a moment for port to be released
sleep 2

# Change to backend directory
cd "$(dirname "$0")"/../..

# Activate virtual environment
source venv/bin/activate

# Start the API server in the background
echo "Starting API server..."
python api.py &
API_PID=$!

# Wait for server to start
echo "Waiting for API server to initialize..."
sleep 5

# Run the comprehensive test
echo "Running comprehensive test..."
cd tests/test_suite
python comprehensive_e2e_test.py

# Capture test status
TEST_STATUS=$?

# Shutdown API server when done
echo "Stopping API server..."
kill $API_PID

# Return the test status
exit $TEST_STATUS