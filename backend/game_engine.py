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
        """Marks player as eliminated if they have 0 chips."""
        if self.stack == 0:
            self.is_active = False

@dataclass
class AIPlayer(Player):
    personality: str = ""

    def make_decision(self, game_state, deck):
        """Delegates AI decision-making to ai_manager.py, passing deck for Monte Carlo evaluation."""
        return AIDecisionMaker.make_decision(self.personality, self.hole_cards, game_state, deck)

@dataclass
class PokerGame:
    players: List[Player]
    deck: List[str] = field(default_factory=list)
    community_cards: List[str] = field(default_factory=list)
    pot: int = 0
    current_bet: int = 0
    small_blind: int = config.SMALL_BLIND
    big_blind: int = config.BIG_BLIND
    dealer_index: int = 0
    hand_count: int = 0

    def post_blinds(self):
        """Assigns small and big blinds at the start of each hand and rotates dealer."""
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        sb_index = (self.dealer_index + 1) % len(self.players)
        bb_index = (self.dealer_index + 2) % len(self.players)
        sb_player = self.players[sb_index]
        bb_player = self.players[bb_index]
        try:
            sb_player.bet(self.small_blind)
            bb_player.bet(self.big_blind)
            self.pot += self.small_blind + self.big_blind
            self.current_bet = self.big_blind
        except ValueError:
            pass
        if self.hand_count % 2 == 0:
            self.small_blind += 5
            self.big_blind = self.small_blind * 2

    def distribute_pot(self, winner):
        """Awards the pot to the winning player."""
        winner.stack += self.pot
        print(f"🏆 {winner.player_id} wins {self.pot} chips!")
        self.pot = 0

def run_game_test():
    players = [
        Player("User"),
        AIPlayer("AI-1", personality="Conservative"),
        AIPlayer("AI-2", personality="Risk Taker"),
        AIPlayer("AI-3", personality="Probability-Based"),
        AIPlayer("AI-4", personality="Bluffer"),
    ]

    game = PokerGame(players)
    base_deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]

    while game.hand_count < 10 and sum(p.is_active for p in game.players) > 1:
        game.deck = base_deck[:]
        random.shuffle(game.deck)
        game.community_cards = []
        game.pot = 0
        game.hand_count += 1

        print(f"\n=== 🃏 Hand {game.hand_count} ===")

        for player in game.players:
            if player.is_active:
                player.receive_cards([game.deck.pop(), game.deck.pop()])

        game.post_blinds()

        game_state = {"community_cards": game.community_cards, "current_bet": game.current_bet}
        max_bet = game.current_bet

        for player in game.players:
            if isinstance(player, AIPlayer) and player.is_active:
                decision = player.make_decision(game_state, game.deck)
                if decision == "call":
                    bet_amount = min(max_bet - player.current_bet, player.stack)
                elif decision == "raise":
                    bet_amount = max(min(max_bet * 2, player.stack), game.big_blind)
                    max_bet = bet_amount
                else:
                    bet_amount = 0
                if bet_amount > 0:
                    try:
                        actual_bet = player.bet(bet_amount)
                        game.pot += actual_bet
                    except ValueError:
                        player.is_active = False
                print(f"{player.player_id} decides to {decision}. Bet: {actual_bet if bet_amount > 0 else 0}")
        game.current_bet = max_bet
        game.community_cards = [game.deck.pop(), game.deck.pop(), game.deck.pop()]
        print(f"\n🔹 Flop: {game.community_cards}")
        game.community_cards.append(game.deck.pop())
        print(f"\n🔹 Turn: {game.community_cards}")
        game.community_cards.append(game.deck.pop())
        print(f"\n🔹 River: {game.community_cards}")
        winner = next(p for p in game.players if p.is_active)
        game.distribute_pot(winner)
        print("\n📊 Player Stacks:")
        for player in game.players:
            print(f"{player.player_id}: {player.stack} chips")
run_game_test()
