import random
import uuid
from typing import List, Optional
from dataclasses import dataclass

from game.hand_evaluator import HandEvaluator


@dataclass
class AIDecision:
    """AI decision with reasoning for transparency."""
    action: str
    amount: int
    reasoning: str
    hand_strength: float
    pot_odds: float
    confidence: float
    spr: float = 0.0  # Stack-to-Pot Ratio for pot-relative decision making
    decision_id: str = ""  # FIX Issue #3: Unique ID for deduplication (generated on creation)


class AIStrategy:
    """AI strategies with decision reasoning for learning."""

    @staticmethod
    def make_decision_with_reasoning(personality: str, hole_cards: List[str], community_cards: List[str],
                                   current_bet: int, pot_size: int, player_stack: int, player_bet: int = 0,
                                   big_blind: int = 10, last_raise_amount: Optional[int] = None) -> AIDecision:
        """
        Make AI decision with full reasoning for transparency.
        Fixed: Uses last_raise_amount for correct minimum raise calculation per Texas Hold'em rules
        """

        # Calculate minimum raise increment (Texas Hold'em rule)
        min_raise_increment = last_raise_amount if last_raise_amount is not None else big_blind

        # Hand strength calculation
        evaluator = HandEvaluator()
        hand_score, hand_rank = evaluator.evaluate_hand(hole_cards, community_cards)

        # Use consolidated hand strength calculation
        hand_strength = HandEvaluator.score_to_strength(hand_score)

        # Pot odds calculation
        call_amount = current_bet - player_bet
        pot_odds = call_amount / (pot_size + call_amount) if (pot_size + call_amount) > 0 else 0

        # SPR (Stack-to-Pot Ratio) calculation - key poker metric for pot-relative decisions
        # Use 999.0 instead of infinity for JSON compatibility
        spr = player_stack / pot_size if pot_size > 0 else 999.0

        if personality == "Conservative":
            # SPR-aware Conservative: Tighter with deep stacks, more committed with shallow stacks
            if spr < 3 and hand_strength >= 0.45:  # Low SPR - pot-committed with two pair+
                action = "raise" if random.random() > 0.3 else "call"
                # FIX: Don't use max with player_stack, just calculate min raise and cap it
                amount = (current_bet + min_raise_increment) if action == "raise" else call_amount
                amount = min(amount, player_stack)
                reasoning = f"Low SPR ({spr:.1f}) - pot committed with {hand_rank} ({hand_strength:.1%})"
                confidence = 0.85
            elif spr > 10 and hand_strength < 0.65:  # High SPR - need premium hands
                action = "fold"
                amount = 0
                reasoning = f"High SPR ({spr:.1f}) - need premium hand, folding {hand_rank} ({hand_strength:.1%})"
                confidence = 0.8
            elif hand_strength >= 0.75:  # Flush or better
                action = "raise" if random.random() > 0.3 else "call"
                amount = max(current_bet + min_raise_increment, current_bet * 2) if action == "raise" else call_amount
                amount = min(amount, player_stack)
                reasoning = f"Premium hand ({hand_rank}, {hand_strength:.1%}). Conservative value betting."
                confidence = 0.9
            elif hand_strength >= 0.45:  # Two pair or better
                action = "call"
                amount = call_amount
                reasoning = f"Solid hand ({hand_rank}, {hand_strength:.1%}). Conservative call."
                confidence = 0.7
            elif hand_strength >= 0.25 and call_amount <= player_stack // 20:
                action = "call"
                amount = call_amount
                reasoning = f"Marginal hand ({hand_rank}, {hand_strength:.1%}). Small bet, worth a call."
                confidence = 0.5
            else:
                action = "fold"
                amount = 0
                reasoning = f"Weak hand ({hand_rank}, {hand_strength:.1%}). Conservative fold."
                confidence = 0.9

        elif personality == "Aggressive":
            # SPR-aware Aggressive: Push/fold with low SPR, bluff more with high SPR
            if spr < 3 and hand_strength >= 0.25:  # Low SPR - any pair, push/fold
                action = "raise"
                amount = player_stack  # All-in or near all-in
                reasoning = f"Low SPR ({spr:.1f}) - aggressive push with {hand_rank} ({hand_strength:.1%})"
                confidence = 0.75
            elif spr > 7 and hand_strength < 0.25:  # High SPR - more bluffs
                bluff_chance = 0.4 if call_amount <= player_stack // 20 else 0.2
                if random.random() < bluff_chance:
                    action = "raise"
                    amount = max(current_bet + min_raise_increment, current_bet * 2)
                    amount = min(amount, player_stack)
                    reasoning = f"High SPR ({spr:.1f}) - applying pressure with weak {hand_rank}. Bluff play."
                    confidence = 0.4
                else:
                    action = "fold"
                    amount = 0
                    reasoning = f"High SPR ({spr:.1f}) - weak hand ({hand_rank}), conserving chips for better spots."
                    confidence = 0.7
            elif hand_strength >= 0.55:  # Three of a kind or better
                action = "raise" if random.random() > 0.2 else "call"
                amount = max(current_bet + min_raise_increment, current_bet * 3) if action == "raise" else call_amount
                amount = min(amount, player_stack)
                reasoning = f"Strong hand ({hand_rank}, {hand_strength:.1%}). Aggressive value betting."
                confidence = 0.8
            elif hand_strength >= 0.25:  # Any pair
                if random.random() > 0.4:
                    action = "raise" if random.random() > 0.6 else "call"
                    amount = max(current_bet + min_raise_increment, current_bet * 2) if action == "raise" else call_amount
                    amount = min(amount, player_stack)
                    reasoning = f"Playable hand ({hand_rank}, {hand_strength:.1%}). Aggressive play to build pot."
                    confidence = 0.6
                else:
                    action = "fold"
                    amount = 0
                    reasoning = f"Marginal hand ({hand_rank}). Aggressive fold to control pot size."
                    confidence = 0.5
            else:  # High card
                if random.random() > 0.7 and call_amount <= player_stack // 40:
                    action = "raise"
                    amount = max(current_bet + min_raise_increment, current_bet * 2)
                    amount = min(amount, player_stack)
                    reasoning = f"Weak hand ({hand_rank}) but bluffing for fold equity. Aggressive move."
                    confidence = 0.3
                else:
                    action = "fold"
                    amount = 0
                    reasoning = f"Too weak to continue ({hand_rank}, {hand_strength:.1%}). Smart aggression."
                    confidence = 0.8

        elif personality == "Mathematical":
            # SPR + pot odds combined for optimal EV decisions
            implied_odds_factor = min(spr * pot_odds, 1.0) if spr < 999.0 else pot_odds

            if spr < 3 and hand_strength >= 0.25:  # Low SPR - committed with any pair
                action = "call" if call_amount < player_stack else "raise"
                amount = call_amount if action == "call" else player_stack
                reasoning = f"Low SPR ({spr:.1f}) - pot committed with {hand_rank}. Positive EV."
                confidence = 0.85
            elif hand_strength >= 0.65:  # Straight or better
                action = "raise"
                amount = max(current_bet + min_raise_increment, current_bet * 2)
                amount = min(amount, player_stack)
                reasoning = f"Strong hand ({hand_rank}, {hand_strength:.1%}). Mathematical value betting."
                confidence = 0.9
            elif hand_strength >= 0.45:  # Two pair or better
                action = "call"
                amount = call_amount
                reasoning = f"Solid hand ({hand_rank}, {hand_strength:.1%}). Positive expectation call."
                confidence = 0.8
            elif hand_strength >= 0.25 and (pot_odds <= 0.33 or spr < 5):
                action = "call"
                amount = call_amount
                reasoning = f"Marginal hand ({hand_rank}, {hand_strength:.1%}). Pot odds {pot_odds:.1%}, SPR {spr:.1f} - positive EV."
                confidence = 0.6
            elif hand_strength >= 0.25:
                action = "fold"
                amount = 0
                reasoning = f"Pair ({hand_rank}). Pot odds {pot_odds:.1%}, SPR {spr:.1f} - negative EV fold."
                confidence = 0.8
            else:
                action = "fold"
                amount = 0
                reasoning = f"Weak hand ({hand_rank}, {hand_strength:.1%}). Clear mathematical fold."
                confidence = 0.95

        elif personality == "Loose-Passive":
            # Calling station - calls too much, rarely raises or bluffs
            if hand_strength >= 0.20:  # Any pair or better
                if spr < 3:  # Low SPR - call to see showdown
                    action = "call"
                    amount = call_amount
                    reasoning = f"Low SPR ({spr:.1f}) - calling with {hand_rank}. Loose-passive play."
                    confidence = 0.6
                elif current_bet > player_stack // 3:  # Too expensive
                    action = "fold"
                    amount = 0
                    reasoning = f"Too expensive ({hand_rank}). Even calling stations fold sometimes."
                    confidence = 0.7
                else:  # Default: call almost everything
                    action = "call"
                    amount = call_amount
                    reasoning = f"Calling with {hand_rank} ({hand_strength:.1%}). Loose-passive style."
                    confidence = 0.5
            else:  # Even calling stations fold high card sometimes
                if call_amount <= player_stack // 40:  # Very small bet
                    action = "call"
                    amount = call_amount
                    reasoning = f"Small bet, worth a call with {hand_rank}. Loose play."
                    confidence = 0.4
                else:
                    action = "fold"
                    amount = 0
                    reasoning = f"Weak hand ({hand_rank}). Fold."
                    confidence = 0.8

        elif personality == "Tight-Aggressive":
            # TAG - premium hands only, but aggressive when playing
            if hand_strength >= 0.75:  # Flush or better - premium
                action = "raise"
                amount = max(current_bet + min_raise_increment, pot_size)
                amount = min(amount, player_stack)
                reasoning = f"Premium hand ({hand_rank}, {hand_strength:.1%}). TAG value betting."
                confidence = 0.95
            elif hand_strength >= 0.55:  # Three of a kind - solid
                if spr < 5:  # Low SPR - go all-in
                    action = "raise"
                    amount = player_stack
                    reasoning = f"Low SPR ({spr:.1f}), strong hand ({hand_rank}). TAG push."
                    confidence = 0.9
                else:  # Raise for value
                    action = "raise"
                    amount = max(current_bet + min_raise_increment, current_bet * 2)
                    amount = min(amount, player_stack)
                    reasoning = f"Strong hand ({hand_rank}). TAG value raise."
                    confidence = 0.85
            elif hand_strength >= 0.35:  # Marginal hands - fold
                action = "fold"
                amount = 0
                reasoning = f"Below TAG threshold ({hand_rank}, {hand_strength:.1%}). Fold."
                confidence = 0.8
            else:  # Weak hands - always fold
                action = "fold"
                amount = 0
                reasoning = f"Weak hand ({hand_rank}). TAG disciplined fold."
                confidence = 0.95

        elif personality == "Maniac":
            # Hyper-aggressive - raises almost always
            if hand_strength >= 0.45:  # Two pair or better
                action = "raise"
                amount = max(current_bet + min_raise_increment, pot_size * 2)
                amount = min(amount, player_stack)
                reasoning = f"Strong hand ({hand_rank}). Maniac value aggression!"
                confidence = 0.7
            elif random.random() < 0.70:  # 70% bluff frequency
                action = "raise"
                amount = max(current_bet + min_raise_increment, pot_size)
                amount = min(amount, player_stack)
                reasoning = f"Bluffing with {hand_rank}. Maniac pressure play!"
                confidence = 0.3
            else:  # Occasionally calls to vary play
                if call_amount < player_stack // 2:
                    action = "call"
                    amount = call_amount
                    reasoning = f"Calling with {hand_rank} to vary play. Maniac style."
                    confidence = 0.4
                else:  # Too expensive even for maniac
                    action = "fold"
                    amount = 0
                    reasoning = f"Too expensive. Even maniacs fold sometimes."
                    confidence = 0.6

        else:
            # Default Conservative
            action = "call" if hand_strength > 0.4 else "fold"
            amount = call_amount if action == "call" else 0
            reasoning = f"Default strategy: {action} with {hand_strength:.1%} hand strength."
            confidence = 0.5

        return AIDecision(
            action=action,
            amount=amount,
            reasoning=reasoning,
            hand_strength=hand_strength,
            pot_odds=pot_odds,
            confidence=confidence,
            spr=spr,
            decision_id=str(uuid.uuid4())  # FIX Issue #3: Unique ID for reliable deduplication
        )
