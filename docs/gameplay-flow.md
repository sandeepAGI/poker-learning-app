# Gameplay Flow

## Overview

```
 ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
 │ 1. Create │────>│ 2. WS    │────>│ 3. Human │────>│ 4. AI    │
 │    Game   │     │  Connect │     │  Action  │     │  Turns   │
 └──────────┘     └──────────┘     └──────────┘     └────┬─────┘
                       ^                                  │
                       │           ┌──────────┐     ┌─────v────┐
                       │           │ 6. Show- │<────│ 5. State │
                       │           │    down   │     │  Advance │
                       │           └────┬──────┘     └──────────┘
                       │                │
                  ┌────┴───┐    ┌───────v──────┐
                  │ 8.Next │    │ 7. LLM Coach │
                  │  Hand  │    │  (Claude API)│
                  └────────┘    └──────────────┘
```

---

## 1. Game Creation

```
  Frontend                                Backend
  ────────                                ───────
  User enters name + AI count
       │
       ├──> POST /games (JWT auth)  ───>  create_game()          main.py:254
       │                                    │
       │                                    ├── PokerGame(name, aiCount)
       │                                    │                    poker_engine.py:601
       │                                    ├── start_new_hand()
       │                                    │     ├── Reset deck
       │                                    │     ├── Deal 2 hole cards each
       │                                    │     ├── Post SB / BB
       │                                    │     └── Set first player (left of BB)
       │                                    │
       │                                    ├── Save to DB (Game table)
       │                                    └── Store in memory: games[game_id]
       │
       <── { game_id: "uuid" }
```

## 2. WebSocket Connection

```
  Frontend                                Backend
  ────────                                ───────
  connectWebSocket(gameId)
       │
       ├──> WS /ws/{game_id}?token=jwt    websocket_endpoint()  main.py:1176
       │                                    │
       │                                    ├── Verify JWT + game ownership
       │                                    ├── manager.connect(game_id, ws)
       │                                    ├── broadcast_state()
       │                                    │
       │    state_update  <────────────────┘
       │                                    │
       │                                    ├── First player is AI?
       │                                    │     YES ──> process_ai_turns_with_events()
       │                                    │     NO  ──> wait for human action
       │                                    │
       <── Zustand store updates ──────────┘
           PokerTable.tsx renders
```

## 3. Human Player Action

```
  User clicks [Fold] / [Call] / [Raise]
       │
       v
  store.submitAction(action, amount)
       │
       ├──> ws.send({ type: "action",       main.py:1248
       │              action, amount,          │
       │              show_ai_thinking,        ├── thread_safe_manager.execute_action()
       │              step_mode })             │     │
       │                                       │     ├── Acquire asyncio.Lock (per game)
       │                                       │     │
       │                                       │     ├── game.submit_human_action()
       │                                       │     │         │        poker_engine.py:1275
       │                                       │     │         v
       │                                       │     │   apply_action()  <── SINGLE SOURCE OF TRUTH
       │                                       │     │         │             poker_engine.py:1132
       │                                       │     │         │
       │                                       │     │    ┌────┴────────────────────────┐
       │                                       │     │    │  FOLD                       │
       │                                       │     │    │    player.is_active = false  │
       │                                       │     │    │    if <=1 active: showdown   │
       │                                       │     │    ├────────────────────────────  │
       │                                       │     │    │  CALL                       │
       │                                       │     │    │    bet = current - my_bet    │
       │                                       │     │    │    pot += bet_amount         │
       │                                       │     │    ├─────────────────────────────│
       │                                       │     │    │  RAISE                      │
       │                                       │     │    │    validate >= min raise     │
       │                                       │     │    │    update current_bet        │
       │                                       │     │    │    reset others' has_acted   │
       │                                       │     │    └─────────────────────────────┘
       │                                       │     │
       │                                       │     ├── broadcast_state()
       │    state_update  <────────────────────┘     │
       │                                             └── spawn: process_ai_turns_with_events()
       v                                                        (background task)
  UI updates
```

## 4. AI Turn Processing Loop

```
  process_ai_turns_with_events()             websocket_manager.py:333
       │
       v
  ┌─── LOOP (max 50 iterations) ─────────────────────────────────────┐
  │                                                                   │
  │    Betting round complete? ──YES──> go to [5. State Advancement]  │
  │         │ NO                                                      │
  │         v                                                         │
  │    Current player is human? ──YES──> BREAK (wait for action)      │
  │         │ NO                                                      │
  │         v                                                         │
  │    Player inactive / all-in / acted? ──YES──> skip, next player   │
  │         │ NO                                                      │
  │         v                                                         │
  │    AIStrategy.make_decision_with_reasoning()  poker_engine.py:347 │
  │         │                                                         │
  │         ├── Evaluate hand strength (treys library)                │
  │         ├── Apply personality (tight/aggressive/loose/etc.)       │
  │         └── Return AIDecision { action, amount, reasoning }       │
  │         │                                                         │
  │         v                                                         │
  │    apply_action(ai_index, decision.action, decision.amount)       │
  │         │                                                         │
  │         ├── If action fails validation --> force fold (safety)     │
  │         │                                                         │
  │         v                                                         │
  │    send_event({ type: "ai_action", ... })  ──> Frontend animates  │
  │    broadcast_state()                       ──> UI updates         │
  │         │                                                         │
  │         v                                                         │
  │    Step mode enabled?                                             │
  │         │ YES: send "awaiting_continue", pause until user clicks  │
  │         │ NO:  asyncio.sleep(0.5) for pacing                      │
  │         │                                                         │
  │         v                                                         │
  │    Advance to next player ──> back to top of loop                 │
  │                                                                   │
  └───────────────────────────────────────────────────────────────────┘
```

## 5. State Advancement

```
  _advance_state_core()                      poker_engine.py:1406
       │
       │    All betting done for current round
       │
       ├── PRE_FLOP ──> deal 3 community cards ──> FLOP
       ├── FLOP     ──> deal 1 community card  ──> TURN
       ├── TURN     ──> deal 1 community card  ──> RIVER
       └── RIVER    ──> _resolve_showdown()    ──> SHOWDOWN
                              │
                              ├── Evaluate all active hands (treys)
                              ├── Determine winner(s)
                              ├── Handle side pots
                              ├── Award pot to winner(s)
                              └── Save hand summary for LLM analysis
       │
       v
  broadcast_state()
       │
       v
  Next player is AI? ──YES──> process_ai_turns_with_events() [recurse]
                      ──NO──> wait for human action
```

## 6. Showdown & Results

```
  state = SHOWDOWN
       │
       v
  Frontend receives state_update with winner_info:
       │
       ├── winner name, amount won
       ├── hand_rank (e.g. "Full House")
       ├── all_showdown_hands (ranked best to worst)
       ├── AI hole cards revealed
       └── folded_players list
       │
       v
  PokerTable.tsx shows winner overlay
       │
       v
  User chooses:
       │
       ├── [Next Hand]     ──> ws.send({ type: "next_hand" })   ──> go to [8]
       ├── [Analyze Hand]  ──> GET /games/{id}/analysis          ──> go to [7]
       └── [Quit]          ──> store.quitGame()                  ──> Home Screen
                                  ├── POST /games/{id}/quit
                                  ├── Disconnect WebSocket
                                  └── Clear Zustand state + localStorage
```

## 7. LLM Coaching (Claude API)

```
  GET /games/{id}/analysis
       │
       v
  llm_analyzer.analyze_hand()                llm_analyzer.py
       │
       ├── Build prompt from hand history
       │     ├── Player actions & bet amounts
       │     ├── Community cards at each street
       │     ├── Hand outcome
       │     └── Player's hole cards
       │
       ├── Call Anthropic API (Haiku / Sonnet 4.5)
       │
       └── Return coaching feedback
              │
              v
       AISidebar.tsx displays analysis
       (split-panel, right side of table)
```

## 8. Next Hand

```
  ws.send({ type: "next_hand" })
       │
       v                                     main.py:1289
  save_completed_hand() to DB
       │
       v
  game.start_new_hand(process_ai=False)
       │
       ├── Rotate dealer position
       ├── Reset all players (clear bets, cards, flags)
       ├── Reset deck, deal new hole cards
       ├── Post new SB / BB
       └── Set first player to act
       │
       v
  broadcast_state()
       │
       v
  First player is AI? ──YES──> process_ai_turns_with_events()
                       ──NO──> wait for human action

  ──────── cycle repeats from [2] ────────
```

---

## Key Design Decisions

```
  Concern                 Solution
  ───────────────────     ──────────────────────────────────────────
  Real-time updates       WebSocket per game, event per AI action
  Concurrency             asyncio.Lock per game (no race conditions)
  AI pacing               0.5s delay between actions (or step-mode)
  Infinite loop safety    Max 50 iterations + same-player detection
  Action validation       Single apply_action() is source of truth
  Hand evaluation         treys library (fast C-based evaluator)
  AI strategies           Rule-based personalities (no LLM needed)
  LLM usage               Post-hand coaching analysis only
  Browser refresh         localStorage gameId + WS reconnect
```
