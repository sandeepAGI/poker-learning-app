#My thoughts on work so far

This game development is part of a training exercise to see if I could build a FS game without any prior experience only using LLMs.

##Lessons learnt
1) Set Up took longer than I thought it would.  The challenge was in installing tailwinds.  Instead of asking AI to fix it (it kept coming with variations of the same step) - have it ask for diagnostics, to understand where the error is coming from and then fix it.
2) API for BackEnd set to port 8080
3) Docker and Git Complete
4) Updated most of the backend.  Added Monte Carlo simulations where less than 5 cards are being sent for evaluation to trey.
5) Updated logic for pot updates, increase in blinds and how bets are being made.
6) ALl unit tests passed.
7) Testing next AI decisions to make sure they are as expected.
8) How is call or fold handeled when SPR =0 ... the decision maker says call but we need to make sure that the logic in game_engine will force a fold if someone else raises.
9) Fixed errors in game_engine in how hands are dealt with to all players.  there were missing logic.
10) Need thorough testing of a game sequence
11) Effective stack and SPR calculation (by each player, before each round), was correct but variable to AIDecision maker was not in same order, mixing up calculations.  Fixed and also cleaned code to make sure the arguments being passes were correct using kwargs
12) Learning Module Tested; now to finalize API tests
13) Always save to github once all testing on current passes before you add new functionality.  it sometimes overwrites prior code and difficult to restore.
14) Claude code is a game changer!!


