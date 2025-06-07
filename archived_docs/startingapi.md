# Starting the Poker Learning App API Server

This guide provides detailed instructions for starting the Poker Learning App's backend API server for development and testing purposes.

## Prerequisites

1. Python 3.9+ installed
2. Virtual environment set up (instructions included below)
3. Access to the backend code in the `/backend` directory

## Setting Up the Environment

If you haven't set up the virtual environment yet, follow these steps:

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment (if not already created)
python -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Linux/macOS
# or
.\venv\Scripts\activate   # On Windows
```

## Installing Dependencies

With the virtual environment activated, install the required dependencies:

```bash
pip install -r requirements.txt
```

## Starting the API Server

There are several ways to start the API server:

### Method 1: Basic Start

```bash
# Make sure you're in the backend directory with the activated virtual environment
cd backend  # If not already there
source venv/bin/activate  # If not already activated

# Start the API server with defaults (port 8080)
python api.py
```

### Method 2: With Custom Port

```bash
# Start API on a specific port
python api.py --port 8000
```

### Method 3: Using Uvicorn Directly

```bash
# Start using uvicorn (gives more control)
uvicorn api:app --host 0.0.0.0 --port 8080 --reload
```

The `--reload` flag enables auto-reloading when code changes are detected, which is useful during development.

## Verifying the API Server is Running

Once started, the API server should be available at:

- http://localhost:8080/api/v1/ (or whichever port you specified)
- http://localhost:8080/docs for the automatically generated Swagger UI documentation

You can test this with a simple curl command:

```bash
curl http://localhost:8080/api/v1/health
```

## Running API Tests

The repository includes several test scripts to verify API functionality:

```bash
# Run the basic API test
python tests/test_api.py

# Run specific end-to-end tests
python tests/new_e2e_test.py
```

## Rate Limiting

The API has rate limiting enabled by default. If you're running into "429 Too Many Requests" errors during testing, consider:

1. Adding delays between API calls in your test scripts
2. Temporarily increasing the rate limit in config.py (for development only)

## Shutting Down

To stop the API server:

1. If running in the foreground, press `Ctrl+C`
2. If running in the background, find the process ID and kill it:
   ```bash
   ps aux | grep "python api.py"
   kill <PID>
   ```

## Troubleshooting

- **Port already in use**: If you get an error about the port being in use, choose a different port or kill the process using the current port.
- **Module not found errors**: Ensure you're in the correct directory and have activated the virtual environment.
- **Authentication errors**: The default development setup uses a test token. Check the auth.py file if you're having authentication issues.

## Configuration

The API behavior can be customized through environment variables or by editing `config.py`. Key configuration options include:

- `PORT`: Server port (default: 8080)
- `RATE_LIMIT`: Requests per minute (default: 60)
- `SECRET_KEY`: For JWT token authentication
- `STARTING_CHIPS`: Initial chips for players (default: 1000)
- `SMALL_BLIND` / `BIG_BLIND`: Blind values (defaults: 5/10)