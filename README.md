# This game development is part of a training exercise to see if I could build a FS game without any prior experience only using LLMs.

1) Set Up took longer than I thought it would.  The challenge was in installing tailwinds.  Instead of asking AI to fix it (it kept coming with variations of the same step) - have it ask for diagnostics, to understand where the error is coming from and then fix it.
2) API for BackEnd set to port 8080
3) Docker and Git Complete
4) Updated most of the backend.  Added Monte Carlo simulations where less than 5 cards are being sent for evaluation to trey.
5) Updated logic for pot updates, increase in blinds and how bets are being made.
6) ERRORS GOT INTRODUCED IN CODE
#Always save to github once all testing on current passes before you add new functionality.  it sometimes overwrites prior code and difficult to restore.
6) Side pot logic needs to be fixed and then we need to test if the AI players are being too aggressive.

❌ Missing / Outstanding Features:
1️⃣ Blind Level Progression
Blinds should increase by 5 chips every two hands.
Needs to be added in game_engine.py.
2️⃣ Statistics & Post-Hand Analysis (statistics_tracker.py - Missing)
Tracking AI playing frequency (% of hands played).
Tracking betting behaviors (average bet sizes).
Tracking win/loss records.
Stack size trends over multiple hands.
Pot size progression through betting rounds.
🚨 Action Required: Implement statistics_tracker.py to log these stats.

3️⃣ Backend API for Frontend Integration (api.py - Missing)
Required API Endpoints (Not implemented yet):
/new_game → Starts a new game session.
/get_state → Retrieves the current game state.
/post_move → Accepts user moves (e.g., bet, fold, call).
/get_statistics → Provides cumulative game statistics.
