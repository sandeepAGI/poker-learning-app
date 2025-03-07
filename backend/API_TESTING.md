# Poker Learning App API Testing Guide

This document provides instructions for manually testing the Poker Learning App API endpoints. Follow these steps to verify that all components are working correctly.

## Prerequisites

Before testing, ensure:

1. The backend server is running on port 8080
   ```bash
   cd backend
   ./venv/bin/python api.py
   ```

2. Install required Python packages for testing:
   ```bash
   pip install requests websocket-client
   ```

## Testing Flow

### 1. Basic API Connectivity

1. **Test Root Endpoint**
   ```python
   import requests
   response = requests.get("http://localhost:8080/")
   print(response.status_code)  # Should be 200
   print(response.json())       # Should contain welcome message
   ```

2. **Verify Swagger Documentation is Available**
   - Open http://localhost:8080/api/docs in your browser
   - Confirm that the Swagger UI loads properly

### 2. Player Management

1. **Create Players**
   ```python
   import requests
   import json

   # Create a human player
   human_player = {
       "name": "Human Player",
       "strategy": "probability_based"
   }
   response = requests.post("http://localhost:8080/api/v1/players", json=human_player)
   human_data = response.json()
   human_id = human_data["id"]
   human_token = human_data["auth_token"]
   print(f"Human player created with ID: {human_id}")
   print(f"Auth token: {human_token}")

   # Create AI players with different strategies
   ai_players = [
       {"name": "Conservative AI", "strategy": "conservative"},
       {"name": "Risk Taker AI", "strategy": "risk_taker"},
       {"name": "Bluffer AI", "strategy": "bluffer"}
   ]

   ai_ids = []
   for ai in ai_players:
       response = requests.post("http://localhost:8080/api/v1/players", json=ai)
       player_data = response.json()
       ai_ids.append(player_data["id"])
       print(f"AI player created with ID: {player_data['id']}")
   ```

2. **Get All Players**
   ```python
   response = requests.get("http://localhost:8080/api/v1/players")
   print(json.dumps(response.json(), indent=2))
   ```

3. **Get Specific Player**
   ```python
   # Use a player ID from the previous step
   player_id = human_id
   response = requests.get(f"http://localhost:8080/api/v1/players/{player_id}")
   print(json.dumps(response.json(), indent=2))
   ```

### 3. Game Management

1. **Create a Game**
   ```python
   game_data = {
       "name": "Test Poker Game",
       "max_players": 4,
       "initial_stack": 1000,
       "small_blind": 10,
       "big_blind": 20
   }
   
   headers = {"Authorization": f"Bearer {human_token}"}
   
   response = requests.post("http://localhost:8080/api/v1/games", json=game_data, headers=headers)
   game_info = response.json()
   game_id = game_info["id"]
   print(f"Game created with ID: {game_id}")
   ```

2. **Get All Games**
   ```python
   response = requests.get("http://localhost:8080/api/v1/games")
   print(json.dumps(response.json(), indent=2))
   ```

3. **Get Specific Game**
   ```python
   response = requests.get(f"http://localhost:8080/api/v1/games/{game_id}")
   print(json.dumps(response.json(), indent=2))
   ```

4. **Join Game with AI Players**
   ```python
   for ai_id in ai_ids:
       # Note: In a real implementation, you would use the AI's token
       # This is simplified for testing
       response = requests.post(
           f"http://localhost:8080/api/v1/games/{game_id}/join", 
           headers={"Authorization": f"Bearer {human_token}"}
       )
       print(f"AI player {ai_id} joining game: {response.status_code}")
   ```

5. **Start Game**
   ```python
   response = requests.post(
       f"http://localhost:8080/api/v1/games/{game_id}/start", 
       headers={"Authorization": f"Bearer {human_token}"}
   )
   print(f"Starting game: {response.status_code}")
   print(json.dumps(response.json(), indent=2))
   ```

6. **Get Game State**
   ```python
   response = requests.get(
       f"http://localhost:8080/api/v1/games/{game_id}/state", 
       headers={"Authorization": f"Bearer {human_token}"}
   )
   print(json.dumps(response.json(), indent=2))
   ```

### 4. Gameplay Actions

1. **Player Actions (Check, Call, Fold, Raise, Bet)**
   ```python
   # Check action
   check_data = {"action": "check"}
   response = requests.post(
       f"http://localhost:8080/api/v1/games/{game_id}/action", 
       json=check_data,
       headers={"Authorization": f"Bearer {human_token}"}
   )
   print(f"Check action: {response.status_code}")
   print(json.dumps(response.json(), indent=2))
   
   # Call action
   call_data = {"action": "call"}
   response = requests.post(
       f"http://localhost:8080/api/v1/games/{game_id}/action", 
       json=call_data,
       headers={"Authorization": f"Bearer {human_token}"}
   )
   
   # Raise action
   raise_data = {"action": "raise", "amount": 50}
   response = requests.post(
       f"http://localhost:8080/api/v1/games/{game_id}/action", 
       json=raise_data,
       headers={"Authorization": f"Bearer {human_token}"}
   )
   
   # Fold action
   fold_data = {"action": "fold"}
   response = requests.post(
       f"http://localhost:8080/api/v1/games/{game_id}/action", 
       json=fold_data,
       headers={"Authorization": f"Bearer {human_token}"}
   )
   ```

### 5. Learning Features

1. **Get Learning Progress**
   ```python
   response = requests.get(
       f"http://localhost:8080/api/v1/learning/progress/{human_id}", 
       headers={"Authorization": f"Bearer {human_token}"}
   )
   print(json.dumps(response.json(), indent=2))
   ```

### 6. WebSocket Connection Testing

1. **Test WebSocket Connection for Real-time Updates**
   ```python
   import websocket
   import json
   import threading
   import time
   from datetime import datetime
   
   def on_message(ws, message):
       print(f"Message received: {message}")
   
   def on_error(ws, error):
       print(f"Error: {error}")
   
   def on_close(ws, close_status_code, close_msg):
       print("Connection closed")
   
   def on_open(ws):
       print("Connection opened")
       
       # Send a test message
       test_msg = {
           "type": "ping",
           "timestamp": datetime.now().isoformat()
       }
       ws.send(json.dumps(test_msg))
   
   websocket_url = f"ws://localhost:8080/api/ws/games/{game_id}?player_id={human_id}"
   ws = websocket.WebSocketApp(websocket_url,
                             on_open=on_open,
                             on_message=on_message,
                             on_error=on_error,
                             on_close=on_close)
   
   # Run the WebSocket connection in a separate thread
   wst = threading.Thread(target=ws.run_forever)
   wst.daemon = True
   wst.start()
   
   # Keep the connection open for a few seconds
   time.sleep(10)
   ws.close()
   ```

## Complete End-to-End Test Script

For a comprehensive test of all endpoints, you can use the `test_api.py` script in the backend directory:

```bash
cd backend
python test_api.py
```

Follow the interactive menu to test specific endpoints or run a full end-to-end test.

## Common Issues and Troubleshooting

1. **API Not Responding**
   - Ensure the server is running on port 8080
   - Check if there are any errors in the terminal running the server

2. **Authentication Errors**
   - Ensure you're including the Authorization header with the format `Bearer {token}`
   - Verify that the token is valid and belongs to the correct player

3. **Swagger Documentation Not Loading**
   - Ensure the server is running
   - Try accessing the API directly at http://localhost:8080/api/openapi.json

4. **WebSocket Connection Issues**
   - Make sure the game ID and player ID are valid
   - Verify that the player is part of the game
   - Check for any CORS issues in the browser console