"""
Phase 2: Boundary tests for safe Phase 3 extraction.

Tests public API contracts of DeckManager, HandEvaluator, and AIStrategy
so they can be extracted to separate modules without breaking behavior.
"""
import pytest
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import DeckManager, HandEvaluator, AIStrategy, Player


# ============================================================
# DeckManager boundary tests
# ============================================================

class TestDeckManagerReset:
    """Verify reset() contract: 52 unique cards, shuffled."""

    def test_reset_produces_52_cards(self):
        dm = DeckManager()
        assert len(dm.deck) == 52

    def test_reset_all_cards_unique(self):
        dm = DeckManager()
        assert len(set(dm.deck)) == 52

    def test_reset_covers_all_ranks_and_suits(self):
        dm = DeckManager()
        ranks = set()
        suits = set()
        for card in dm.deck:
            ranks.add(card[0])
            suits.add(card[1])
        assert ranks == set("23456789TJQKA")
        assert suits == set("shdc")

    def test_reset_shuffles_deck(self):
        """Two resets should produce different orderings (with high probability)."""
        dm1 = DeckManager()
        order1 = list(dm1.deck)
        dm1.reset()
        order2 = list(dm1.deck)
        # Astronomically unlikely to be identical after shuffle
        assert order1 != order2

    def test_reset_restores_full_deck_after_dealing(self):
        dm = DeckManager()
        dm.deal_cards(10)
        assert len(dm.deck) == 42
        dm.reset()
        assert len(dm.deck) == 52


class TestDeckManagerDealCards:
    """Verify deal_cards() contract: returns correct count, mutates deck."""

    def test_deal_returns_requested_count(self):
        dm = DeckManager()
        cards = dm.deal_cards(5)
        assert len(cards) == 5

    def test_deal_removes_cards_from_deck(self):
        dm = DeckManager()
        cards = dm.deal_cards(3)
        assert len(dm.deck) == 49
        for card in cards:
            assert card not in dm.deck

    def test_deal_returns_top_of_deck(self):
        dm = DeckManager()
        top_five = dm.deck[:5]
        dealt = dm.deal_cards(5)
        assert dealt == top_five

    def test_deal_sequential_calls_no_overlap(self):
        dm = DeckManager()
        first = dm.deal_cards(5)
        second = dm.deal_cards(5)
        assert set(first).isdisjoint(set(second))

    def test_deal_zero_cards(self):
        dm = DeckManager()
        cards = dm.deal_cards(0)
        assert cards == []
        assert len(dm.deck) == 52

    def test_deal_all_52_cards(self):
        dm = DeckManager()
        cards = dm.deal_cards(52)
        assert len(cards) == 52
        assert len(dm.deck) == 0

    def test_deal_too_many_raises_valueerror(self):
        dm = DeckManager()
        with pytest.raises(ValueError, match="Not enough cards"):
            dm.deal_cards(53)

    def test_deal_too_many_after_partial_deal(self):
        dm = DeckManager()
        dm.deal_cards(50)
        with pytest.raises(ValueError, match="Not enough cards"):
            dm.deal_cards(5)


# ============================================================
# HandEvaluator boundary tests (Monte Carlo + side pots)
# ============================================================

class TestHandEvaluatorMonteCarlo:
    """Verify evaluate_hand() Monte Carlo path for incomplete boards."""

    def test_preflop_no_community_cards(self):
        """Pre-flop evaluation (0 community cards) should return valid score."""
        ev = HandEvaluator()
        score, rank = ev.evaluate_hand(["As", "Kh"], [])
        assert isinstance(score, (int, float))
        assert isinstance(rank, str)
        strength = ev.score_to_strength(int(score))
        assert 0.0 <= strength <= 1.0

    def test_flop_three_community_cards(self):
        """Flop evaluation (3 community cards) uses Monte Carlo."""
        ev = HandEvaluator()
        score, rank = ev.evaluate_hand(["As", "Kh"], ["Qd", "Jc", "2s"])
        assert isinstance(score, (int, float))
        strength = ev.score_to_strength(int(score))
        assert 0.0 <= strength <= 1.0

    def test_turn_four_community_cards(self):
        """Turn evaluation (4 community cards) uses Monte Carlo."""
        ev = HandEvaluator()
        score, rank = ev.evaluate_hand(["As", "Kh"], ["Qd", "Jc", "2s", "7h"])
        assert isinstance(score, (int, float))
        strength = ev.score_to_strength(int(score))
        assert 0.0 <= strength <= 1.0

    def test_river_five_community_cards_exact(self):
        """River evaluation (5 community cards) is exact, not Monte Carlo."""
        ev = HandEvaluator()
        score, rank = ev.evaluate_hand(["As", "Kh"], ["Qd", "Jc", "Ts", "7h", "2c"])
        # Broadway straight - should be exact
        assert rank == "Straight"
        assert ev.score_to_strength(score) == 0.65

    def test_monte_carlo_strong_hand_scores_well(self):
        """Pocket aces pre-flop should score better than 7-2 offsuit on average."""
        ev = HandEvaluator()
        random.seed(42)
        score_aa, _ = ev.evaluate_hand(["As", "Ah"], [])
        random.seed(42)
        score_72, _ = ev.evaluate_hand(["7s", "2h"], [])
        # Lower score = better hand in treys
        assert score_aa < score_72


class TestDetermineWinnersEdgeCases:
    """Verify determine_winners_with_side_pots() edge cases."""

    def _make_player(self, pid, cards, active=True, all_in=False, invested=100):
        p = Player(pid, pid)
        p.hole_cards = cards
        p.is_active = active
        p.all_in = all_in
        p.total_invested = invested
        return p

    def test_single_eligible_winner(self):
        """One active player gets the whole pot."""
        ev = HandEvaluator()
        winner = self._make_player("p1", ["As", "Kh"], active=True, invested=100)
        folded = self._make_player("p2", [], active=False, invested=50)
        community = ["Qd", "Jc", "Ts", "7h", "2c"]
        pots = ev.determine_winners_with_side_pots([winner, folded], community)
        assert len(pots) == 1
        assert pots[0]['winners'] == ["p1"]
        assert pots[0]['amount'] == 150

    def test_equal_investment_single_pot(self):
        """All-equal investments should produce a single pot (optimization path)."""
        ev = HandEvaluator()
        p1 = self._make_player("p1", ["As", "Ah"], active=True, invested=100)
        p2 = self._make_player("p2", ["Ks", "Kh"], active=True, invested=100)
        community = ["Qd", "Jc", "2s", "7h", "3c"]
        pots = ev.determine_winners_with_side_pots([p1, p2], community)
        assert len(pots) == 1
        assert pots[0]['amount'] == 200
        assert "p1" in pots[0]['winners']  # Aces beat Kings

    def test_side_pot_different_investments(self):
        """Unequal investments produce main + side pots."""
        ev = HandEvaluator()
        # p1 all-in for 50, p2 invested 100
        p1 = self._make_player("p1", ["As", "Ah"], active=False, all_in=True, invested=50)
        p2 = self._make_player("p2", ["Ks", "Kh"], active=True, invested=100)
        community = ["Qd", "Jc", "2s", "7h", "3c"]
        pots = ev.determine_winners_with_side_pots([p1, p2], community)
        # Main pot: 50+50=100, side pot: 50 (only p2 eligible)
        assert len(pots) == 2
        total = sum(p['amount'] for p in pots)
        assert total == 150

    def test_split_pot_tied_hands(self):
        """Two identical hands split the pot."""
        ev = HandEvaluator()
        # Both have same hand via community cards
        p1 = self._make_player("p1", ["2s", "3h"], active=True, invested=100)
        p2 = self._make_player("p2", ["2h", "3s"], active=True, invested=100)
        # Board plays: AAKKQ - both have same two pair
        community = ["Ad", "Ac", "Kd", "Kc", "Qd"]
        pots = ev.determine_winners_with_side_pots([p1, p2], community)
        assert len(pots) == 1
        assert len(pots[0]['winners']) == 2

    def test_no_eligible_winners_empty_result(self):
        """No eligible winners returns empty list."""
        ev = HandEvaluator()
        folded1 = self._make_player("p1", [], active=False, invested=50)
        folded2 = self._make_player("p2", [], active=False, invested=50)
        community = ["Ad", "Kd", "Qd", "Jd", "Td"]
        pots = ev.determine_winners_with_side_pots([folded1, folded2], community)
        assert pots == []

    def test_folded_player_contributes_to_pot_but_cant_win(self):
        """Folded player's chips go to the pot but they can't win."""
        ev = HandEvaluator()
        active = self._make_player("p1", ["2s", "3h"], active=True, invested=100)
        folded = self._make_player("p2", ["As", "Ah"], active=False, invested=100)
        community = ["Kd", "Qd", "Jd", "9c", "8c"]
        pots = ev.determine_winners_with_side_pots([active, folded], community)
        assert pots[0]['winners'] == ["p1"]
        assert pots[0]['amount'] == 200  # Includes folded player's chips


# ============================================================
# AIStrategy boundary tests
# ============================================================

class TestAIStrategyAmountCapping:
    """Verify raise amounts never exceed player_stack."""

    @pytest.mark.parametrize("personality", [
        "Conservative", "Aggressive", "Mathematical",
        "Loose-Passive", "Tight-Aggressive", "Maniac"
    ])
    def test_amount_never_exceeds_stack(self, personality):
        """No personality should return amount > player_stack."""
        random.seed(42)
        for _ in range(20):
            decision = AIStrategy.make_decision_with_reasoning(
                personality=personality,
                hole_cards=["As", "Ah"],
                community_cards=["Ad", "Kh", "Ks"],
                current_bet=500,
                pot_size=1000,
                player_stack=200,
                player_bet=0,
                big_blind=10
            )
            if decision.action == "raise":
                assert decision.amount <= 200, \
                    f"{personality} amount {decision.amount} exceeds stack 200"

    @pytest.mark.parametrize("personality", [
        "Conservative", "Aggressive", "Mathematical",
        "Loose-Passive", "Tight-Aggressive", "Maniac"
    ])
    def test_fold_amount_is_zero(self, personality):
        """Fold should always have amount=0."""
        for _ in range(20):
            decision = AIStrategy.make_decision_with_reasoning(
                personality=personality,
                hole_cards=["2s", "7h"],
                community_cards=["Kd", "Qc", "Js"],
                current_bet=500,
                pot_size=1000,
                player_stack=200,
                player_bet=0,
                big_blind=10
            )
            if decision.action == "fold":
                assert decision.amount == 0, \
                    f"{personality} fold has non-zero amount {decision.amount}"


class TestAIStrategyDefaultFallback:
    """Verify unknown personality falls back to default behavior."""

    def test_unknown_personality_returns_valid_decision(self):
        decision = AIStrategy.make_decision_with_reasoning(
            personality="UnknownType",
            hole_cards=["As", "Kh"],
            community_cards=["Qd", "Jc", "2s"],
            current_bet=20,
            pot_size=50,
            player_stack=1000,
            player_bet=0,
            big_blind=10
        )
        assert decision.action in ["fold", "call", "raise"]
        assert len(decision.reasoning) > 0
        assert "Default" in decision.reasoning

    def test_default_calls_with_strong_hand(self):
        decision = AIStrategy.make_decision_with_reasoning(
            personality="UnknownType",
            hole_cards=["As", "Ah"],
            community_cards=["Ad", "Kh", "Ks"],
            current_bet=20,
            pot_size=50,
            player_stack=1000,
            player_bet=0,
            big_blind=10
        )
        assert decision.action == "call"

    def test_default_folds_with_weak_hand(self):
        decision = AIStrategy.make_decision_with_reasoning(
            personality="UnknownType",
            hole_cards=["2s", "7h"],
            community_cards=["Kd", "Qc", "Js", "9h", "8c"],
            current_bet=20,
            pot_size=50,
            player_stack=1000,
            player_bet=0,
            big_blind=10
        )
        assert decision.action == "fold"


class TestAIStrategyLastRaiseAmount:
    """Verify last_raise_amount affects minimum raise sizing."""

    def test_min_raise_uses_last_raise_when_provided(self):
        """With last_raise_amount=40, min raise should be current_bet + 40."""
        random.seed(1)
        results = []
        for _ in range(50):
            decision = AIStrategy.make_decision_with_reasoning(
                personality="Aggressive",
                hole_cards=["As", "Ah"],
                community_cards=["Ad", "Kh", "2s"],
                current_bet=60,
                pot_size=200,
                player_stack=1000,
                player_bet=0,
                big_blind=10,
                last_raise_amount=40
            )
            if decision.action == "raise":
                results.append(decision.amount)

        # All raises should be at least current_bet + last_raise_amount = 100
        assert len(results) > 0, "Should have at least one raise"
        for amount in results:
            assert amount >= 100, \
                f"Raise {amount} < min raise 100 (current_bet=60 + last_raise=40)"

    def test_min_raise_defaults_to_big_blind(self):
        """Without last_raise_amount, min raise increment = big_blind."""
        random.seed(1)
        results = []
        for _ in range(50):
            decision = AIStrategy.make_decision_with_reasoning(
                personality="Aggressive",
                hole_cards=["As", "Ah"],
                community_cards=["Ad", "Kh", "2s"],
                current_bet=20,
                pot_size=50,
                player_stack=1000,
                player_bet=0,
                big_blind=10,
                last_raise_amount=None
            )
            if decision.action == "raise":
                results.append(decision.amount)

        assert len(results) > 0
        for amount in results:
            assert amount >= 30, \
                f"Raise {amount} < min raise 30 (current_bet=20 + bb=10)"


class TestAIStrategySPRMissingPersonalities:
    """SPR-aware tests for Loose-Passive, Tight-Aggressive, Maniac."""

    def test_loose_passive_low_spr_calls(self):
        """Loose-Passive should call with low SPR and a pair."""
        decision = AIStrategy.make_decision_with_reasoning(
            personality="Loose-Passive",
            hole_cards=["9h", "9d"],
            community_cards=["2c", "5h", "8s"],
            current_bet=50,
            pot_size=400,
            player_stack=200,
            player_bet=0,
            big_blind=10
        )
        assert decision.spr < 1.0
        assert decision.action == "call"

    def test_tight_aggressive_low_spr_pushes(self):
        """TAG with strong hand and low SPR should raise (push)."""
        decision = AIStrategy.make_decision_with_reasoning(
            personality="Tight-Aggressive",
            hole_cards=["As", "Ah"],
            community_cards=["Ad", "Kh", "2s"],
            current_bet=50,
            pot_size=400,
            player_stack=200,
            player_bet=0,
            big_blind=10
        )
        assert decision.spr < 1.0
        assert decision.action == "raise"

    def test_tight_aggressive_folds_marginal_hands(self):
        """TAG should fold hands below its threshold."""
        decision = AIStrategy.make_decision_with_reasoning(
            personality="Tight-Aggressive",
            hole_cards=["9h", "8h"],
            community_cards=["Kd", "7c", "2s"],
            current_bet=20,
            pot_size=50,
            player_stack=1000,
            player_bet=0,
            big_blind=10
        )
        assert decision.action == "fold"

    def test_maniac_raises_with_low_spr(self):
        """Maniac should raise aggressively even with marginal hands."""
        raise_count = 0
        for _ in range(30):
            decision = AIStrategy.make_decision_with_reasoning(
                personality="Maniac",
                hole_cards=["Ts", "9s"],
                community_cards=["2c", "5h", "8s"],
                current_bet=50,
                pot_size=200,
                player_stack=300,
                player_bet=0,
                big_blind=10
            )
            if decision.action == "raise":
                raise_count += 1
        # Maniac should raise majority of the time
        assert raise_count >= 15, f"Maniac only raised {raise_count}/30 times"


class TestAIStrategyDecisionFields:
    """Verify all AIDecision fields are populated correctly."""

    def test_decision_has_unique_id(self):
        d1 = AIStrategy.make_decision_with_reasoning(
            "Conservative", ["As", "Kh"], ["Qd", "Jc", "2s"],
            20, 50, 1000, 0, 10
        )
        d2 = AIStrategy.make_decision_with_reasoning(
            "Conservative", ["As", "Kh"], ["Qd", "Jc", "2s"],
            20, 50, 1000, 0, 10
        )
        assert d1.decision_id != ""
        assert d2.decision_id != ""
        assert d1.decision_id != d2.decision_id

    def test_spr_calculation(self):
        decision = AIStrategy.make_decision_with_reasoning(
            "Conservative", ["As", "Kh"], ["Qd", "Jc", "2s"],
            20, 100, 500, 0, 10
        )
        assert decision.spr == 5.0  # 500 / 100

    def test_spr_with_zero_pot(self):
        decision = AIStrategy.make_decision_with_reasoning(
            "Conservative", ["As", "Kh"], ["Qd", "Jc", "2s"],
            0, 0, 500, 0, 10
        )
        assert decision.spr == 999.0  # Sentinel for infinity

    def test_pot_odds_calculation(self):
        decision = AIStrategy.make_decision_with_reasoning(
            "Conservative", ["As", "Kh"], ["Qd", "Jc", "2s"],
            20, 80, 500, 0, 10
        )
        # call_amount = 20-0 = 20, pot_odds = 20/(80+20) = 0.20
        assert abs(decision.pot_odds - 0.20) < 0.01

    def test_pot_odds_with_existing_bet(self):
        decision = AIStrategy.make_decision_with_reasoning(
            "Conservative", ["As", "Kh"], ["Qd", "Jc", "2s"],
            50, 100, 500, 30, 10
        )
        # call_amount = 50-30 = 20, pot_odds = 20/(100+20) = 0.167
        assert abs(decision.pot_odds - 0.167) < 0.01


# ============================================================
# Engine edge-case gap tests (from redundancy audit)
# ============================================================

from game.poker_engine import PokerGame, GameState


class TestEngineEdgeCaseGaps:
    """Cover three gaps identified in the redundancy audit,
    exercising PokerGame.apply_action() directly."""

    # --- Gap 1: Call-as-check (call when current_bet == player_bet) ---

    def test_call_when_already_matched_acts_as_check(self):
        """Calling when current_bet == player_bet should succeed with 0 chips moved."""
        game = PokerGame("TestHuman", ai_count=1)
        game.start_new_hand(process_ai=False)

        # Advance to flop so current_bet resets to 0
        game.current_state = GameState.FLOP
        game.current_bet = 0
        human_index = next(i for i, p in enumerate(game.players) if p.is_human)
        game.players[human_index].current_bet = 0
        game.players[human_index].has_acted = False
        game.current_player_index = human_index

        pot_before = game.pot
        result = game.apply_action(human_index, "call")

        assert result["success"] is True
        assert result["bet_amount"] == 0
        assert game.pot == pot_before  # no chips moved

    # --- Gap 2: Post-showdown action rejection ---

    def test_action_rejected_at_showdown(self):
        """apply_action() should still technically succeed at the engine level,
        but submit_human_action() should reject it because it's not the player's turn.
        At SHOWDOWN, current_player_index is None so submit_human_action returns False."""
        game = PokerGame("TestHuman", ai_count=1)
        game.start_new_hand(process_ai=False)

        # Force game into SHOWDOWN
        game.current_state = GameState.SHOWDOWN
        game.current_player_index = None

        # submit_human_action checks turn order and rejects
        result = game.submit_human_action("call", process_ai=False)
        assert result is False

    def test_apply_action_at_showdown_still_processes(self):
        """apply_action() itself doesn't check game state — it processes the action.
        The higher-level submit_human_action guards state.
        Verify apply_action doesn't crash when called at SHOWDOWN."""
        game = PokerGame("TestHuman", ai_count=1)
        game.start_new_hand(process_ai=False)

        game.current_state = GameState.SHOWDOWN

        # apply_action at engine level processes without state guard
        human_index = next(i for i, p in enumerate(game.players) if p.is_human)
        result = game.apply_action(human_index, "fold")
        # It processes (success=True) because apply_action has no state check
        assert result["success"] is True

    # --- Gap 3: Invalid action type strings ---

    @pytest.mark.parametrize("bad_action", [
        "check",   # not a valid action string
        "bet",     # not a valid action string
        "CALL",    # wrong case
        "",        # empty string
        "allin",   # not a valid action string
    ])
    def test_invalid_action_strings_rejected(self, bad_action):
        """apply_action() must reject action strings outside {fold, call, raise}."""
        game = PokerGame("TestHuman", ai_count=1)
        game.start_new_hand(process_ai=False)

        human_index = next(i for i, p in enumerate(game.players) if p.is_human)
        game.current_player_index = human_index

        result = game.apply_action(human_index, bad_action)
        assert result["success"] is False
        assert "Invalid action" in result["error"]

    @pytest.mark.parametrize("bad_action", ["check", "bet", "CALL", ""])
    def test_submit_human_action_rejects_invalid_strings(self, bad_action):
        """submit_human_action() also rejects invalid action strings."""
        game = PokerGame("TestHuman", ai_count=1)
        game.start_new_hand(process_ai=False)

        human_index = next(i for i, p in enumerate(game.players) if p.is_human)
        game.current_player_index = human_index

        result = game.submit_human_action(bad_action, process_ai=False)
        assert result is False
