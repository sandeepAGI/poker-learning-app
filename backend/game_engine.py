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

    def bet(self, amount: int):
        """Places a bet, reducing stack size."""
        if amount > self.stack:
            raise ValueError("Insufficient chips to bet this amount.")
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

    def showdown(self):
        """Determines the winner at showdown."""
        evaluator = Evaluator()
        winners = []
        best_score = float("inf")

        print("\n🔹 Showdown: Evaluating Hands...")
        for player in self.players:
            if player.is_active:
                hole_cards = [Card.new(card.replace("10", "T")) for card in player.hole_cards]
                board = [Card.new(card.replace("10", "T")) for card in self.community_cards]
                hand_score = evaluator.evaluate(board, hole_cards)
                
                if hand_score < best_score:
                    best_score = hand_score
                    winners = [player]
                elif hand_score == best_score:
                    winners.append(player)

        # Distribute pot among winners
        if len(winners) > 0:
            split_pot = self.pot // len(winners)
            for winner in winners:
                winner.stack += split_pot
                print(f"🏆 {winner.player_id} wins {split_pot} chips!")

        print(f"💰 Total pot at showdown: {self.pot} chips")  # Debugging statement
        self.pot = 0
        self.community_cards = []

def run_game_test():
    """Runs a short poker simulation with AI and player decisions (max 10 hands)."""
    
    players = [
        Player("User"),  # Human player (for testing)
        AIPlayer("AI-1", personality="Conservative"),
        AIPlayer("AI-2", personality="Risk Taker"),
        AIPlayer("AI-3", personality="Probability-Based"),
        AIPlayer("AI-4", personality="Bluffer"),
    ]

    game = PokerGame(players)

    base_deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]  # Full deck

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

        game_state = {"community_cards": game.community_cards, "current_bet": game.current_bet}
        max_bet = game.current_bet
        
        for player in game.players:
            if isinstance(player, AIPlayer) and player.is_active:
                decision = player.make_decision(game_state, game.deck)
                if decision == "call":
                    bet_amount = max_bet - player.current_bet
                elif decision == "raise":
                    bet_amount = max_bet * 2
                    max_bet = bet_amount
                else:
                    bet_amount = 0
                
                if bet_amount > 0:
                    try:
                        player.bet(bet_amount)
                        game.pot += bet_amount  # ✅ Add bet to pot
                        player.current_bet += bet_amount
                    except ValueError:
                        player.is_active = False
                print(f"{player.player_id} decides to {decision}. Bet: {bet_amount}")
        
        game.current_bet = max_bet
        
        game.community_cards = [game.deck.pop(), game.deck.pop(), game.deck.pop()]
        print(f"\n🔹 Flop: {game.community_cards}")
        
        game.community_cards.append(game.deck.pop())
        print(f"\n🔹 Turn: {game.community_cards}")
        
        game.community_cards.append(game.deck.pop())
        print(f"\n🔹 River: {game.community_cards}")
        
        game.showdown()

    winner = next(p for p in game.players if p.is_active)
    print(f"\n🏆 {winner.player_id} wins the game with {winner.stack} chips! 🏆")

run_game_test()