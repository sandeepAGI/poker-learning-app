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
        """Assigns hole cards to the player."""
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
        return AIDecisionMaker.make_decision(self.personality, self.hole_cards, game_state, deck, pot_size, spr)

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
#        print("\n--- DEBUG: distribute_pot() START ---")
#        print(f"Total Pot Before Distribution: {self.pot}")
#        print("Player Stacks Before Distribution:")
        for player in self.players:
            print(f"  {player.player_id}: {player.stack} chips, Active: {player.is_active}")

        # ✅ Ensure deck is available before evaluation
        if not deck:
            deck.extend([rank + suit for rank in "23456789TJQKA" for suit in "shdc"])
            random.shuffle(deck)
#            print("🔄 Deck was empty! Resetting and shuffling deck.")

        # ✅ Case where only one player remains (everyone else folded)
        active_players = [player for player in self.players if player.is_active]

        if len(active_players) == 1:
            winner = active_players[0]
            print(f"🏆 {winner.player_id} wins {self.pot} chips by default (all others folded).")
            winner.stack += self.pot
            self.pot = 0
#            print("--- DEBUG: distribute_pot() END ---\n")
            return

        # ✅ Use AI's Monte Carlo hand evaluator
        ai_helper = BaseAI()
        best_score = None
        winner = None

        for player in active_players:
            if player.hole_cards:
                print(f"🃏 Evaluating hand for {player.player_id}: {player.hole_cards}")
                print(f"🂡 Community Cards Before Evaluation: {self.community_cards}")
                print(f"🃏 Deck Size Before Evaluation: {len(deck)}")

                # ✅ Call AI-based hand evaluation with deck explicitly passed
                hand_score = ai_helper.evaluate_hand(
                    hole_cards=player.hole_cards,
                    community_cards=self.community_cards,  
                    deck=deck  # ✅ Now the deck is passed correctly
                )
            
                print(f"🃏 {player.player_id} - Hand Score: {hand_score}")  

                if best_score is None or hand_score < best_score:  
                    best_score = hand_score
                    winner = player

        # ✅ Make sure a winner is chosen
        if winner is None:
            print("❌ ERROR: No winner was determined. Pot remains unassigned!")
            return  

        print(f"🏆 {winner.player_id} wins {self.pot} chips with the best hand!")
        winner.stack += self.pot  
        self.pot = 0  

        print("Player Stacks After Distribution:")
        for player in self.players:
            print(f"  {player.player_id}: {player.stack} chips, Active: {player.is_active}")

        print(f"Total Pot After Distribution: {self.pot}")
        print("--- DEBUG: distribute_pot() END ---\n")

        # ✅ Eliminate players with <5 chips after pot distribution
        for player in self.players:
            player.eliminate()

    def run_game_test(self):
        """Simulates a 10-hand poker game for testing."""
        base_deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]
    
        self.players = [
            AIPlayer("AI-1", personality="Conservative"),
            AIPlayer("AI-2", personality="Risk Taker"),
            AIPlayer("AI-3", personality="Probability-Based"),
            AIPlayer("AI-4", personality="Bluffer"),
        ]

        for hand in range(1, 6):  # Limit to 5 hands for debugging
            self.deck = base_deck[:]
            random.shuffle(self.deck)

            self.community_cards = []
            self.pot = 0
            self.hand_count = hand  # ✅ Ensure hand_count is updated BEFORE post_blinds()
        
            print(f"\n=== 🃏 Hand {self.hand_count} ===")

            self.post_blinds()  # ✅ Call post_blinds() after updating hand_count

            # ✅ Print dealer, SB, and BB for verification
            dealer_position = self.dealer_index
            sb_position = (self.dealer_index + 1) % len(self.players)
            bb_position = (sb_position + 1) % len(self.players)
            print(f"🔄 Hand {self.hand_count} - Dealer: {dealer_position}, SB: {sb_position}, BB: {bb_position}")

            # ✅ Deal Hole Cards to AI Players
            for player in self.players:
                player.receive_cards([self.deck.pop(), self.deck.pop()])

            # ✅ Pre-Flop Betting Round
            print("\n🔹 Pre-Flop Betting Round:")
            self.betting_round()

            # ✅ Deal Flop and Start Betting
            self.community_cards = [self.deck.pop(), self.deck.pop(), self.deck.pop()]
            print(f"\n🂡 Flop: {self.community_cards}")
            print("\n🔹 Flop Betting Round:")
            self.betting_round()

            # ✅ Deal Turn and Start Betting
            self.community_cards.append(self.deck.pop())
            print(f"\n🂡 Turn: {self.community_cards}")
            print("\n🔹 Turn Betting Round:")
            self.betting_round()

            # ✅ Deal River and Start Betting
            self.community_cards.append(self.deck.pop())
            print(f"\n🂡 River: {self.community_cards}")
            print("\n🔹 River Betting Round:")
            self.betting_round()

            # ✅ Reveal AI Hole Cards at End of Hand
            print("\n🔹 Revealing Hole Cards:")
            for player in self.players:
                print(f"{player.player_id} Hole Cards: {player.hole_cards}")

            # ✅ Distribute Pot & Reset for Next Hand
            self.distribute_pot(self.deck)



#Initialize and run test
game = PokerGame([
#    Player("User"),
    AIPlayer("AI-1", personality="Conservative"),
    AIPlayer("AI-2", personality="Risk Taker"),
    AIPlayer("AI-3", personality="Probability-Based"),
    AIPlayer("AI-4", personality="Bluffer"),
])
#game.run_game_test()
