import random
from dataclasses import dataclass, field
from typing import List
import config  # Import configuration file
from treys import Evaluator, Card  # Poker hand evaluator
from ai.ai_manager import AIDecisionMaker  # Import AI decision-making manager
from ai.base_ai import BaseAI  # Import BaseAI for hand evaluation in distribute_pot()

@dataclass
class Player:
    player_id: str
    stack: int = config.STARTING_CHIPS
    hole_cards: List[str] = field(default_factory=list)
    is_active: bool = True
    current_bet: int = 0
    all_in: bool = False

    def bet(self, amount: int):
        """Places a bet, reducing stack size."""
        if amount > self.stack:
            amount = self.stack
            self.all_in = True
        self.stack -= amount
        self.current_bet += amount
        return amount

    def receive_cards(self, cards: List[str]):
        """Assigns hole cards to the player, but warns if already set."""
        print(f"[DEBUG] {self.player_id} receiving new cards: {cards} (Previous: {self.hole_cards})")

        if self.hole_cards:  # ✅ Warn if cards are already assigned
            print(f"[WARNING] {self.player_id} already had hole cards! This might be a duplicate deal.")
            return

        self.hole_cards = cards

    def eliminate(self):
        """Marks player as eliminated if they have less than 5 chips."""
        if self.stack < 5:
            self.is_active = False

@dataclass
class AIPlayer(Player):
    personality: str = ""

    def make_decision(self, game_state, deck, pot_size, spr):
        """Delegates AI decision-making to ai_manager.py, passing deck for Monte Carlo evaluation."""
        
        print(f"\n[CRITICAL DEBUG] game_engine.py - AIPlayer {self.player_id} making decision")
        print(f"  Deck Size Before Sending to AI Manager: {len(deck)}")  # 🔴 ADD THIS LINE

        decision = AIDecisionMaker.make_decision(self.personality, self.hole_cards, game_state, self.deck, pot_size, spr)

        print(f"  AI Decision: {decision}")  # 🔴 CONFIRM DECISION
        print(f"  Deck Size After AI Decision: {len(self.deck)}")  # 🔴 TRACK IF DECK IS LOST

        return decision

@dataclass
class PokerGame:
    players: List[Player]
    deck: List[str] = field(default_factory=list)
    community_cards: List[str] = field(default_factory=list)
    pot: int = 0
    current_bet: int = 0
    small_blind: int = config.SMALL_BLIND
    big_blind: int = config.BIG_BLIND
    dealer_index: int = -1  # Dealer starts at -1 so first hand SB/BB starts correctly
    hand_count: int = 0
    evaluator: Evaluator = field(default_factory=Evaluator)

    def reset_deck(self):
        """Ensures a new shuffled deck at the start of each hand."""
        self.deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]
        random.shuffle(self.deck)    
        print(f"[DEBUG] Resetting deck: New deck size = {len(self.deck)}")

    def deal_hole_cards(self):
        """Deals 2 hole cards to each active player at the start of a new hand."""
        if self.hand_count == self.last_hand_dealt:
            print(f"[DEBUG] Hole cards already dealt for hand {self.hand_count}, skipping.")
            return

        print(f"[DEBUG] Dealing hole cards for new hand {self.hand_count}... Initial Deck Size: {len(self.deck)}")

        assigned_players = []  # Track players who received cards

        for player in self.players:
            if player.is_active:
                if player.hole_cards:
                    print(f"[WARNING] {player.player_id} already has hole cards! Skipping dealing.")
                    continue  

                hole_cards = self.deck[:2]  # ✅ Get 2 unique cards for this player
                player.receive_cards(hole_cards)
                print(f"[DEBUG] Assigning to {player.player_id}: {hole_cards}")

                self.deck = self.deck[2:]  # ✅ Remove assigned cards from deck IMMEDIATELY
                assigned_players.append(player)

        print(f"[DEBUG] Deck Size After Dealing Hole Cards: {len(self.deck)}")
        self.last_hand_dealt = self.hand_count  # ✅ Marks that hole cards were assigned


    def post_blinds(self):
        """Assigns small and big blinds at the start of each hand, ensuring SB becomes BB next hand."""

        print(f"\n--- DEBUG: post_blinds() START ---")
        print(f"🃏 Hand {self.hand_count} - Dealer Before Rotation: {self.dealer_index}")

        # Rotate dealer position correctly
        self.dealer_index = (self.dealer_index + 1) % len(self.players)

        sb_index = (self.dealer_index + 1) % len(self.players)  # SB is after the dealer

    
        # Instead of guessing, we find who was SB in the previous round
        if self.hand_count > 1:
            previous_sb = (self.dealer_index) % len(self.players)  # Previous dealer was the last SB
            bb_index = previous_sb  # Set BB to be the previous SB
        else:
            bb_index = (sb_index + 1) % len(self.players)  # Standard for first hand

        print(f"➡️ New Dealer: {self.dealer_index}")
        print(f"➡️ Expected SB: {sb_index}, Expected BB: {bb_index}")

        sb_player = self.players[sb_index]
        bb_player = self.players[bb_index]

        print(f"✔️ {sb_player.player_id} is Small Blind (SB)")
        print(f"✔️ {bb_player.player_id} is Big Blind (BB)")

        sb_player.bet(self.small_blind)
        bb_player.bet(self.big_blind)

        self.pot += self.small_blind + self.big_blind
        self.current_bet = self.big_blind  

        print(f"🎯 Small Blind: {self.small_blind}, Big Blind: {self.big_blind}")

        # Increase blinds every 2 hands
        if self.hand_count % 2 == 0:  
            self.small_blind += 5
            self.big_blind = self.small_blind * 2
            print(f"⬆️ Blinds Increased! New SB: {self.small_blind}, New BB: {self.big_blind}")

        # ✅ Call `deal_hole_cards()` ONLY if we are starting a NEW hand
        if self.hand_count > self.last_hand_dealt:
            print(f"[DEBUG] New hand detected: {self.hand_count}, dealing hole cards.")
            self.deal_hole_cards()
            self.last_hand_dealt = self.hand_count  # ✅ Update last hand dealt
        else:
            print(f"[DEBUG] No new hand detected. Skipping hole card deal.")

        print("--- DEBUG: post_blinds() END ---\n")
        
    def betting_round(self):
        """Handles betting rounds where players must match the highest bet, raise, or fold."""
        self.current_bet = 0  # ✅ Reset current bet for each betting round
        max_bet = 0
        betting_done = False

        while not betting_done:
            betting_done = True  # Assume no more betting will occur, reset if a raise happens
        
            for player in self.players:
                if isinstance(player, AIPlayer) and player.is_active and player.stack > 0:
                    if player.current_bet < max_bet:
                        # ✅ Calculate Stack-to-Pot Ratio (SPR)
                        effective_stack = min(player.stack, max(p.stack for p in self.players if p != player and p.is_active))
                        spr = effective_stack / self.pot if self.pot > 0 else float("inf")

                        print(f"[DEBUG] game_engine.py - Passing Deck of Size {len(self.deck)} to AI Manager")

                        # ✅ AI Decision
                        decision = player.make_decision(
                            {"community_cards": self.community_cards, "current_bet": self.current_bet, "pot_size": self.pot},
                            self.deck,
                            self.pot,
                            spr
                        )

                        # ✅ Process AI's Decision
                        if decision == "call":
                            bet_amount = min(max_bet - player.current_bet, player.stack)
                        elif decision == "raise":
                            bet_amount = max(min(max_bet * 2, player.stack), self.big_blind)
                            max_bet = player.current_bet + bet_amount
                            betting_done = False
                        else:
                            bet_amount = 0
                            player.is_active = False
                    
                        if bet_amount > 0:
                            player.bet(bet_amount)
                            self.pot += bet_amount
                            print(f"{player.player_id} (Stack: {player.stack}, SPR: {spr:.2f}) decides to {decision}. Bet: {bet_amount}")
                        else:
                            print(f"{player.player_id} decides to fold.")

            self.current_bet = max_bet

    def distribute_pot(self, deck):
        """Determines the winner and distributes the pot accordingly."""
        for player in self.players:
            print(f"  {player.player_id}: {player.stack} chips, Active: {player.is_active}")

        # ✅ Case where only one player remains (everyone else folded)
        active_players = [player for player in self.players if player.is_active]

        if len(active_players) == 1:
            winner = active_players[0]
            print(f"🏆 {winner.player_id} wins {self.pot} chips by default (all others folded).")
            winner.stack += self.pot
            self.pot = 0
#            print("--- DEBUG: distribute_pot() END ---\n")
            return

        # Use AI's Monte Carlo hand evaluator
        ai_helper = BaseAI()
        best_score = None
        winner = None
        best_hand_rank = None  # Track best hand rank for display

        for player in active_players:
            if player.hole_cards:
                print(f"🃏 Evaluating hand for {player.player_id}: {player.hole_cards}")
                assert len(self.deck) > 0, "[ERROR] game_engine.py - Deck is empty before AI decision!"

                # ✅ Call AI-based hand evaluation
                hand_score, hand_rank = ai_helper.evaluate_hand(
                    hole_cards=player.hole_cards,
                    community_cards=self.community_cards,
                    deck=self.deck
                )
    
                print(f"🃏 {player.player_id} - Hand Score: {hand_score} ({hand_rank})")  # Show rank with score  

                # ✅ Determine the winning hand based on score
                if best_score is None or hand_score < best_score:  
                    best_score = hand_score
                    best_hand_rank = hand_rank  # Track winning hand rank
                    winner = player

        # ✅ Display the winner's hand rank
        if winner:
            print(f"🏆 {winner.player_id} wins {self.pot} chips with a {best_hand_rank}!")
            winner.stack += self.pot  
            self.pot = 0  
            self.hand_count += 1  # ✅ New hand starts
            self.reset_deck()  # ✅ Fresh deck for the next hand

        print("Player Stacks After Distribution:")
        for player in self.players:
            print(f"  {player.player_id}: {player.stack} chips, Active: {player.is_active}")

        print(f"Total Pot After Distribution: {self.pot}")
        print("--- DEBUG: distribute_pot() END ---\n")

        # ✅ Eliminate players with <5 chips after pot distribution
        for player in self.players:
            player.eliminate()
