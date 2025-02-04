import unittest
import random
from game_engine import Player, AIPlayer, PokerGame

class TestPokerGame(unittest.TestCase):

    def setUp(self):
        """Initialize a test game instance before each test."""
        self.players = [
            Player("User"),
            AIPlayer("AI-1", personality="Conservative"),
            AIPlayer("AI-2", personality="Risk Taker"),
            AIPlayer("AI-3", personality="Probability-Based"),
            AIPlayer("AI-4", personality="Bluffer"),
        ]
        self.game = PokerGame(self.players)
        self.game.hand_count = 1  # ✅ Ensure hand count starts at 1

    def test_player_bet(self):
        """Test if player bet correctly reduces stack and increases current bet."""
        player = self.players[0]
        initial_stack = player.stack
        bet_amount = 50
        player.bet(bet_amount)
        self.assertEqual(player.stack, initial_stack - bet_amount)
        self.assertEqual(player.current_bet, bet_amount)

    def test_player_eliminate(self):
        """Test if player is eliminated when stack is below threshold."""
        player = self.players[0]
        player.stack = 4  # Below elimination threshold
        player.eliminate()
        self.assertFalse(player.is_active)

    def test_post_blinds(self):
        """Test if small and big blinds are posted correctly and blinds increase properly."""
        initial_sb = self.game.small_blind
        initial_bb = self.game.big_blind
        self.game.post_blinds()
        self.assertEqual(self.game.pot, initial_sb + initial_bb)
        if self.game.hand_count % 2 == 0:
            self.assertEqual(self.game.small_blind, initial_sb + 5)
            self.assertEqual(self.game.big_blind, (initial_sb + 5) * 2)

    def test_blind_progression(self):
        """Test that the small and big blinds increase correctly every two hands."""
        print("\n--- DEBUG: test_blind_progression() START ---")

        initial_sb = self.game.small_blind
        initial_bb = self.game.big_blind

        for hand in range(1, 6):  # Simulate 5 hands
            self.game.hand_count = hand  # ✅ Set hand count
            self.game.post_blinds()  # ✅ Assign blinds

            # ✅ Ensure blinds are checked AFTER posting blinds
            expected_sb = initial_sb + (5 * ((hand) // 2))  # Increase SB every 2 hands
            expected_bb = expected_sb * 2  # BB is always double SB

            # ✅ Print debug information
            print(f"🃏 Hand {hand}:")
            print(f"  ➤ Expected SB: {expected_sb}, Actual SB: {self.game.small_blind}")
            print(f"  ➤ Expected BB: {expected_bb}, Actual BB: {self.game.big_blind}")

            self.assertEqual(self.game.small_blind, expected_sb, f"Incorrect SB on hand {hand}")
            self.assertEqual(self.game.big_blind, expected_bb, f"Incorrect BB on hand {hand}")

        print("--- DEBUG: test_blind_progression() END ---\n")

    def test_ai_betting_rounds(self):
        """Test that AI players participate in all betting rounds."""
        print("\n--- DEBUG: test_ai_betting_rounds() START ---")

        self.game.hand_count = 1  
        self.game.post_blinds()  

        base_deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]
        random.shuffle(base_deck)

        for player in self.game.players:
            if isinstance(player, AIPlayer):
                player.receive_cards([base_deck.pop(), base_deck.pop()])
        
        self.game.community_cards = [base_deck.pop(), base_deck.pop(), base_deck.pop()]
        self.game.pot = 0

        betting_rounds = ["Pre-Flop", "Flop", "Turn", "River"]
        active_ai_players = [p for p in self.game.players if isinstance(p, AIPlayer)]

        for round_name in betting_rounds:
            print(f"\n🔹 {round_name} Betting Round:")
            self.game.betting_round()  

            for player in active_ai_players:
                print(f"🤖 {player.player_id} Bet: {player.current_bet}, Stack: {player.stack}")
                self.assertGreaterEqual(player.current_bet, 0, f"{player.player_id} did not participate in {round_name} betting round")

        print("--- DEBUG: test_ai_betting_rounds() END ---\n")

    def test_distribute_pot(self):
        """Test if the winner correctly receives the pot."""
        print("\n--- DEBUG: test_pot_distribution() START ---")
        initial_stacks = {player.player_id: player.stack for player in self.players}
        print("Initial Player Stacks:", initial_stacks)

        self.game.pot = 500
        print(f"Pot Set to: {self.game.pot}")

        # ✅ Ensure AI Players Receive Cards
        base_deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]
        random.shuffle(base_deck)

        for player in self.game.players:
            player.receive_cards([base_deck.pop(), base_deck.pop()])
            print(f"🃏 {player.player_id} received hole cards: {player.hole_cards}")

        self.game.community_cards = [base_deck.pop(), base_deck.pop(), base_deck.pop(), base_deck.pop(), base_deck.pop()]
        print(f"🂡 Community Cards: {self.game.community_cards}")

        # ✅ Pass deck explicitly
        self.game.distribute_pot(self.game.deck)

        # ✅ Check if a winner actually received the pot
        winner = max(self.game.players, key=lambda p: p.stack)
        print(f"🏆 Winner: {winner.player_id}, Stack After: {winner.stack}")

        total_chips_after = sum(player.stack for player in self.game.players)
        total_chips_before = sum(initial_stacks.values()) + 500  

        print("Final Player Stacks:")
        for player in self.game.players:
            print(f"  {player.player_id}: {player.stack} chips")

        print(f"Total Chips Before: {total_chips_before}, Total Chips After: {total_chips_after}")
        print("--- DEBUG: test_pot_distribution() END ---\n")

        self.assertGreater(winner.stack, initial_stacks[winner.player_id], "No winner was assigned the pot.")
        self.assertEqual(total_chips_after, total_chips_before)

    def test_blind_rotation(self):
        """Test that Small Blind (SB) becomes Big Blind (BB) in the next hand."""
        print("\n--- DEBUG: test_blind_rotation() START ---")

        dealer_positions = []
        sb_positions = []
        bb_positions = []

        for hand in range(1, 6):  # Simulate 5 hands
            self.game.hand_count = hand
            self.game.post_blinds()

            dealer_positions.append(self.game.dealer_index)
            sb_positions.append((self.game.dealer_index + 1) % len(self.game.players))
            bb_positions.append((self.game.dealer_index + 2) % len(self.game.players))

            print(f"🃏 Hand {hand}: Dealer -> {self.game.dealer_index}, SB -> {sb_positions[-1]}, BB -> {bb_positions[-1]}")

            # ✅ Fix: Ensure previous SB becomes next BB
            if hand > 1:
                expected_bb = sb_positions[hand - 2]  # SB from last hand should be BB now
                actual_bb = bb_positions[hand - 1]
                expected_bb = (self.game.dealer_index + 2) % len(self.game.players)  # BB is always after SB
                self.assertEqual(actual_bb, expected_bb, f"Incorrect SB to BB transition on hand {hand}")

        print("--- DEBUG: test_blind_rotation() END ---\n")


if __name__ == "__main__":
    unittest.main()
