import random
from dataclasses import dataclass, field
from typing import List
import config  # Import configuration file
from treys import Evaluator, Card  # Poker hand evaluator
from ai.ai_manager import AIDecisionMaker  # Import AI decision-making manager

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
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        sb_index = (self.dealer_index + 1) % len(self.players)
        bb_index = (sb_index + 1) % len(self.players)
        sb_player = self.players[sb_index]
        bb_player = self.players[bb_index]
        sb_player.bet(self.small_blind)
        bb_player.bet(self.big_blind)
        self.pot += self.small_blind + self.big_blind
        self.current_bet = self.big_blind
        print(f"{sb_player.player_id} is Small Blind (SB)")
        print(f"{bb_player.player_id} is Big Blind (BB)")
        if self.hand_count % 2 == 0:
            self.small_blind += 5
            self.big_blind = self.small_blind * 2

    def betting_round(self):
        """Enforces betting rules where players must match the highest bet, raise, or fold."""
        max_bet = self.current_bet
        betting_done = False
        while not betting_done:
            betting_done = True
            for player in self.players:
                if isinstance(player, AIPlayer) and player.is_active and player.stack > 0:
                    if player.current_bet < max_bet:
                        # Calculate Effective Stack (minimum between AI and largest opponent stack)
                        effective_stack = min(player.stack, max(p.stack for p in self.players if p != player and p.is_active))
                        spr = effective_stack / self.pot if self.pot > 0 else float("inf")

                        # AI makes a decision considering SPR
                        decision = player.make_decision(
                            {"community_cards": self.community_cards, "current_bet": self.current_bet, "pot_size": self.pot},
                            self.deck,
                            self.pot,
                            spr
                        )

                        if decision == "call":
                            bet_amount = min(max_bet - player.current_bet, player.stack)
                        elif decision == "raise":
                            bet_amount = max(min(max_bet * 2, player.stack), self.big_blind)
                            max_bet = player.current_bet + bet_amount
                            betting_done = False  # Another round needed if a raise occurs
                        else:  # Fold
                            bet_amount = 0
                            player.is_active = False
                        
                        if bet_amount > 0:
                            player.bet(bet_amount)
                            self.pot += bet_amount
                            print(f"{player.player_id} (Stack: {player.stack}, SPR: {spr:.2f}) decides to {decision}. Bet: {bet_amount}")
                        else:
                            print(f"{player.player_id} decides to fold.")
                    
                    if player.stack <= 0:
                        player.is_active = False  # Eliminate players with no money
        self.current_bet = max_bet


    def distribute_pot(self):
        """Determines the winner and distributes the pot accordingly."""
        best_score = None
        winner = None
        for player in self.players:
            if player.is_active:
                hole_cards = [Card.new(card) for card in player.hole_cards]
                board_cards = [Card.new(card) for card in self.community_cards]
                hand_score = self.evaluator.evaluate(board_cards, hole_cards)
                if best_score is None or hand_score < best_score:
                    best_score = hand_score
                    winner = player
        if winner:
            winner.stack += self.pot
            print(f"🏆 {winner.player_id} wins {self.pot} chips with the best hand!")
        self.pot = 0

    def run_game_test(self):
        """Simulates a 10-hand poker game for testing."""
        base_deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]
        while self.hand_count < 10 and sum(p.is_active for p in self.players) > 1:
            self.deck = base_deck[:]
            random.shuffle(self.deck)
            self.community_cards = []
            self.pot = 0
            self.hand_count += 1

            print(f"\n=== 🃏 Hand {self.hand_count} ===")
            self.post_blinds()
        
            # Run betting round and capture AI decisions
            print("\n🔹 Betting Round:")
            self.betting_round()

            # Deal community cards (flop, turn, river)
            self.community_cards = [self.deck.pop(), self.deck.pop(), self.deck.pop()]
            self.community_cards.append(self.deck.pop())
            self.community_cards.append(self.deck.pop())

            # Show community cards
            print(f"\n🂡 Community Cards: {self.community_cards}")

            # Show AI hole cards at the end
            print("\n🔹 Revealing Hole Cards:")
            for player in self.players:
                if isinstance(player, AIPlayer) or player.player_id == "User":
                    print(f"{player.player_id} Hole Cards: {player.hole_cards}")

            # Distribute pot and show results
            self.distribute_pot()

# Initialize and run test
game = PokerGame([
    Player("User"),
    AIPlayer("AI-1", personality="Conservative"),
    AIPlayer("AI-2", personality="Risk Taker"),
    AIPlayer("AI-3", personality="Probability-Based"),
    AIPlayer("AI-4", personality="Bluffer"),
])
game.run_game_test()
