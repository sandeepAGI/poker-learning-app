"""
LLM Hand Analyzer Service

Provides AI-powered poker hand analysis using Claude API (Haiku 4.5 + Sonnet 4.5).
Based on PHASE4_PROMPTING_STRATEGY.md and PHASE4_IMPLEMENTATION_PLAN.md

Cost per analysis:
- Quick (Haiku 4.5): ~$0.016
- Deep Dive (Sonnet 4.5): ~$0.029
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional
from datetime import datetime

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # Will be handled gracefully

from game.poker_engine import CompletedHand, BettingRound, ActionRecord
from llm_prompts import (
    get_system_prompt,
    format_user_prompt,
    ANALYSIS_JSON_SCHEMA,
    get_session_system_prompt,
    format_session_user_prompt,
    SESSION_JSON_SCHEMA
)

logger = logging.getLogger(__name__)


class LLMHandAnalyzer:
    """
    Generate personalized poker hand analysis using Claude AI.

    Supports two analysis depths:
    - Quick: Haiku 4.5 (2s, $0.016) - Good for 90% of hands
    - Deep Dive: Sonnet 4.5 (4s, $0.029) - Expert-level analysis
    """

    def __init__(self):
        """Initialize LLM client with API key."""
        if Anthropic is None:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Get your API key at: https://console.anthropic.com/"
            )

        self.client = Anthropic(api_key=api_key)
        # Use latest Claude 4.5 models (avoiding Feb 2026 deprecations)
        self.haiku_model = "claude-haiku-4-5"  # Latest Haiku 4.5
        self.sonnet_model = "claude-sonnet-4-5-20250929"  # Latest Sonnet 4.5

        # Load model names from environment (with defaults)
        self.haiku_model = os.getenv("LLM_MODEL_QUICK", self.haiku_model)
        self.sonnet_model = os.getenv("LLM_MODEL_DEEP", self.sonnet_model)

        logger.info(f"LLMHandAnalyzer initialized with models: {self.haiku_model} (quick), {self.sonnet_model} (deep)")

    def analyze_hand(
        self,
        completed_hand: CompletedHand,
        hand_history: List[CompletedHand],
        analysis_count: int,
        depth: str = "quick",
        skill_level: str = "beginner"
    ) -> Dict:
        """
        Generate comprehensive hand analysis with LLM.

        Args:
            completed_hand: The hand to analyze
            hand_history: All previous hands in session (for context)
            analysis_count: Number of analyses done so far (for context limiting)
            depth: "quick" (Haiku) or "deep" (Sonnet)
            skill_level: "beginner", "intermediate", or "advanced"

        Returns:
            {
                "summary": str,
                "round_by_round": List[Dict],
                "player_analysis": Dict,
                "ai_opponent_insights": List[Dict],
                "concepts_to_study": List[Dict],
                "tips_for_improvement": List[Dict],
                "discussion_questions": List[str],
                "overall_assessment": str,
                "encouragement": str
            }
        """
        logger.info(f"Analyzing hand #{completed_hand.hand_number} with depth={depth}, skill={skill_level}")

        # 1. Build comprehensive context
        context = self._build_context(completed_hand, hand_history, analysis_count)

        # 2. Create prompts
        system_prompt = get_system_prompt(depth, skill_level)
        user_prompt = format_user_prompt(context, depth, skill_level)

        # 3. Call LLM
        analysis = self._call_llm(system_prompt, user_prompt, depth)

        logger.info(f"Analysis complete for hand #{completed_hand.hand_number}")
        return analysis

    def analyze_session(
        self,
        hand_history: List[CompletedHand],
        starting_stack: int,
        ending_stack: int,
        depth: str = "quick",
        skill_level: str = "beginner",
        hand_count: Optional[int] = None
    ) -> Dict:
        """
        Generate comprehensive session analysis across multiple hands.
        Phase 4.5: Session Analysis

        Args:
            hand_history: All completed hands in the session
            starting_stack: Starting bankroll
            ending_stack: Ending bankroll
            depth: "quick" (Haiku) or "deep" (Sonnet)
            skill_level: "beginner", "intermediate", or "advanced"
            hand_count: Optional limit on number of hands to analyze (default: all)

        Returns:
            {
                "session_summary": str,
                "hands_analyzed": int,
                "overall_stats": Dict,
                "top_3_strengths": List[Dict],
                "top_3_leaks": List[Dict],
                "win_rate_breakdown": Dict,
                "opponent_insights": List[Dict],
                "recommended_adjustments": List[Dict],
                "concepts_to_study": List[Dict],
                "study_plan": List[Dict],
                "progress_tracking": Dict,
                "overall_assessment": str,
                "encouragement": str
            }
        """
        # Limit hands if specified
        hands_to_analyze = hand_history[-hand_count:] if hand_count else hand_history

        logger.info(f"Analyzing session with {len(hands_to_analyze)} hands, depth={depth}, skill={skill_level}")

        # 1. Build session context
        context = self._build_session_context(
            hands_to_analyze,
            starting_stack,
            ending_stack
        )

        # 2. Create prompts
        system_prompt = get_session_system_prompt(depth, skill_level)
        user_prompt = format_session_user_prompt(context, depth, skill_level)

        # 3. Call LLM
        analysis = self._call_llm(system_prompt, user_prompt, depth, schema=SESSION_JSON_SCHEMA)

        logger.info(f"Session analysis complete for {len(hands_to_analyze)} hands")
        return analysis

    def _build_context(
        self,
        hand: CompletedHand,
        history: List[CompletedHand],
        analysis_count: int
    ) -> Dict:
        """
        Build comprehensive context from hand and history.

        Intelligently limits history based on analysis count:
        - First 5 analyses: Full session (up to 50 hands)
        - Analysis 6-20: Last 30 hands
        - Analysis 21+: Last 20 hands (cost control)
        """
        # Determine history limit
        history_limit = self._get_history_limit(analysis_count)
        limited_history = history[-history_limit:] if history else []

        # Calculate player statistics
        player_stats = self._calculate_player_stats(limited_history)

        # Format betting rounds
        formatted_rounds = self._format_betting_rounds(hand.betting_rounds)

        # Format showdown data
        formatted_showdown = self._format_showdown(hand.showdown_hands, hand.hand_rankings)

        # Format AI opponents info
        formatted_ai = self._format_ai_opponents(hand)

        # Format hand history summary
        history_summary = self._format_hand_history_summary(limited_history)

        # Find human player
        human_player = self._find_human_player(hand)

        # Determine result
        result = self._determine_result(hand, human_player)

        return {
            "hand_number": hand.hand_number,
            "timestamp": hand.timestamp or datetime.utcnow().isoformat(),
            "session_id": hand.session_id or "unknown",
            "total_hands": len(history) + 1,

            # Player stats
            "hands_played": player_stats["hands_played"],
            "win_rate": player_stats["win_rate"],
            "vpip": player_stats["vpip"],
            "pfr": player_stats["pfr"],
            "biggest_win": player_stats["biggest_win"],
            "biggest_loss": player_stats["biggest_loss"],
            "detected_skill": "beginner",  # TODO: Implement skill detection
            "confidence": 50,  # TODO: Implement confidence scoring

            # Current hand
            "human_name": human_player["name"],
            "stack_start": human_player["stack_start"],
            "stack_end": hand.human_final_stack,
            "hole_cards": " ".join(hand.human_cards),
            "final_action": hand.human_action,
            "result_description": result,

            # Hand details
            "formatted_betting_rounds": formatted_rounds,
            "community_cards": " ".join(hand.community_cards) if hand.community_cards else "None",
            "formatted_showdown_data": formatted_showdown,
            "formatted_ai_opponents": formatted_ai,

            # History
            "history_count": len(limited_history),
            "formatted_hand_history_summary": history_summary
        }

    def _get_history_limit(self, analysis_count: int) -> int:
        """
        Determine how many hands to include in context for cost control.

        Token budget:
        - First 5 analyses: ~9,500 tokens (50 hands × 150 tokens/hand)
        - Analysis 6-20: ~5,500 tokens (30 hands)
        - Analysis 21+: ~4,000 tokens (20 hands)
        """
        if analysis_count <= 5:
            return 50
        elif analysis_count <= 20:
            return 30
        else:
            return 20

    def _calculate_player_stats(self, history: List[CompletedHand]) -> Dict:
        """Calculate player statistics from hand history."""
        if not history:
            return {
                "hands_played": 0,
                "win_rate": 0.0,
                "vpip": 0.0,
                "pfr": 0.0,
                "biggest_win": 0,
                "biggest_loss": 0
            }

        # Count wins
        wins = sum(1 for h in history if h.winner_ids and "human" in h.winner_ids)
        win_rate = round((wins / len(history)) * 100, 1)

        # Calculate VPIP (Voluntarily Put money In Pot)
        # Did they call/raise pre-flop (not just blind)
        vpip_hands = 0
        for h in history:
            if h.human_action in ["call", "raise", "all-in"]:
                vpip_hands += 1
        vpip = round((vpip_hands / len(history)) * 100, 1)

        # Calculate PFR (Pre-Flop Raise)
        pfr_hands = 0
        for h in history:
            # Check if they raised pre-flop
            if h.betting_rounds:
                pre_flop = h.betting_rounds[0]
                for action in pre_flop.actions:
                    if action.player_id == "human" and action.action == "raise":
                        pfr_hands += 1
                        break
        pfr = round((pfr_hands / len(history)) * 100, 1)

        # Find biggest win/loss (stack changes)
        stack_changes = []
        for h in history:
            # Estimate stack change from events or pot size
            if h.winner_ids and "human" in h.winner_ids:
                # Won hand - estimate profit
                change = h.pot_size // len(h.winner_ids)
            else:
                # Lost hand - estimate loss from human action
                change = -(h.pot_size // 4)  # Rough estimate
            stack_changes.append(change)

        biggest_win = max(stack_changes) if stack_changes else 0
        biggest_loss = abs(min(stack_changes)) if stack_changes else 0

        return {
            "hands_played": len(history),
            "win_rate": win_rate,
            "vpip": vpip,
            "pfr": pfr,
            "biggest_win": biggest_win,
            "biggest_loss": biggest_loss
        }

    def _format_betting_rounds(self, rounds: List[BettingRound]) -> str:
        """Format betting rounds for LLM readability."""
        if not rounds:
            return "No betting rounds recorded"

        formatted = []
        for round_obj in rounds:
            round_str = f"\n{round_obj.round_name.upper()} (Pot: ${round_obj.pot_at_start} → ${round_obj.pot_at_end})"
            if round_obj.community_cards:
                round_str += f"\n  Community Cards: {' '.join(round_obj.community_cards)}"

            for action in round_obj.actions:
                action_str = f"  - {action.player_name}: {action.action}"
                if action.amount > 0:
                    action_str += f" ${action.amount}"
                if action.reasoning:
                    action_str += f" ({action.reasoning})"
                round_str += f"\n{action_str}"

            formatted.append(round_str)

        return "\n".join(formatted)

    def _format_showdown(self, showdown_hands: Dict[str, List[str]], hand_rankings: Dict[str, str]) -> str:
        """Format showdown data for LLM."""
        if not showdown_hands:
            return "No showdown (hand ended before river)"

        formatted = []
        for player_id, cards in showdown_hands.items():
            rank = hand_rankings.get(player_id, "Unknown")
            formatted.append(f"  - {player_id}: {' '.join(cards)} ({rank})")

        return "\n".join(formatted) if formatted else "No showdown data"

    def _format_ai_opponents(self, hand: CompletedHand) -> str:
        """Format AI opponents information."""
        if not hand.ai_decisions:
            return "No AI opponents"

        formatted = []
        for player_id, decision in hand.ai_decisions.items():
            player_name = player_id  # Use player_id as name for now

            # Format AI info - personality not in AIDecision, so omit for now
            formatted.append(
                f"  - {player_name}\n"
                f"    Final action: {decision.action}\n"
                f"    Reasoning: {decision.reasoning}\n"
                f"    Hand strength: {decision.hand_strength:.1%}\n"
                f"    Confidence: {decision.confidence:.1%}"
            )

        return "\n".join(formatted)

    def _format_hand_history_summary(self, history: List[CompletedHand]) -> str:
        """Format hand history summary for LLM."""
        if not history:
            return "No previous hands"

        # Summarize last 5 hands
        recent = history[-5:] if len(history) > 5 else history
        formatted = []

        for h in recent:
            result = "Won" if h.winner_ids and "human" in h.winner_ids else "Lost"
            formatted.append(
                f"  Hand #{h.hand_number}: {result}, "
                f"Action: {h.human_action}, "
                f"Cards: {' '.join(h.human_cards)}"
            )

        return "\n".join(formatted)

    def _find_human_player(self, hand: CompletedHand) -> Dict:
        """Find human player information from hand."""
        # Estimate starting stack (work backwards from final stack and pot involvement)
        estimated_start = hand.human_final_stack + (hand.pot_size // 4)  # Rough estimate

        return {
            "name": "You",  # Default name
            "stack_start": estimated_start,
            "stack_end": hand.human_final_stack
        }

    def _build_session_context(
        self,
        hands: List[CompletedHand],
        starting_stack: int,
        ending_stack: int
    ) -> Dict:
        """
        Build comprehensive session context from multiple hands.

        Args:
            hands: List of completed hands to analyze
            starting_stack: Starting bankroll
            ending_stack: Ending bankroll

        Returns:
            Dictionary with session context for prompt formatting
        """
        if not hands:
            return {}

        # Calculate aggregate statistics
        hands_won = sum(1 for h in hands if h.winner_ids and "human" in h.winner_ids)
        hands_lost = len(hands) - hands_won
        win_rate = (hands_won / len(hands) * 100) if hands else 0

        # Calculate VPIP (voluntarily put money in pot) - hands where human didn't fold pre-flop
        vpip_count = 0
        pfr_count = 0  # Pre-flop raise
        for hand in hands:
            if hand.betting_rounds and hand.betting_rounds[0].actions:
                human_actions = [a for a in hand.betting_rounds[0].actions if a.player_id == "human"]
                if human_actions:
                    last_action = human_actions[-1]
                    if last_action.action in ["call", "raise", "all_in"]:
                        vpip_count += 1
                        if last_action.action == "raise":
                            pfr_count += 1

        vpip = (vpip_count / len(hands) * 100) if hands else 0
        pfr = (pfr_count / len(hands) * 100) if hands else 0

        # Find biggest wins/losses
        net_changes = []
        for hand in hands:
            if hand.winner_ids and "human" in hand.winner_ids:
                # Won hand - estimate profit
                net_changes.append(hand.pot_size // len(hand.winner_ids))
            else:
                # Lost hand - estimate loss from pot size
                net_changes.append(-(hand.pot_size // 4))  # Rough estimate

        biggest_win = max(net_changes) if net_changes else 0
        biggest_loss = min(net_changes) if net_changes else 0

        # Aggregate stats text
        aggregate_stats = f"""
- Win rate: {win_rate:.1f}% ({hands_won}/{len(hands)} hands won)
- VPIP: {vpip:.1f}% ({vpip_count}/{len(hands)} hands played)
- PFR: {pfr:.1f}% ({pfr_count}/{len(hands)} hands raised pre-flop)
- Biggest win: ${biggest_win}
- Biggest loss: ${biggest_loss}
- Net profit: ${ending_stack - starting_stack}
"""

        # Hands summary (compact)
        hands_summary_lines = []
        for hand in hands[:20]:  # Limit to last 20 hands for context
            result = "Won" if hand.winner_ids and "human" in hand.winner_ids else "Lost"
            cards_str = " ".join(hand.human_cards) if hand.human_cards else "N/A"
            hands_summary_lines.append(
                f"Hand #{hand.hand_number}: {cards_str} - {result}"
            )

        hands_summary = "\n".join(hands_summary_lines)

        # AI opponents summary - use betting_rounds to get player names
        ai_opponents = {}
        for hand in hands:
            # Get AI players from betting rounds
            for betting_round in hand.betting_rounds:
                for action in betting_round.actions:
                    if action.player_id != "human":
                        if action.player_name not in ai_opponents:
                            ai_opponents[action.player_name] = {
                                "hands": 0,
                                "personality": "Unknown"
                            }
                        # Count unique hands per player
                        # (we'll increment later to avoid double-counting)

            # Count this hand for all AI players who participated
            for betting_round in hand.betting_rounds:
                players_in_hand = set(a.player_name for a in betting_round.actions if a.player_id != "human")
                for player_name in players_in_hand:
                    if player_name in ai_opponents:
                        ai_opponents[player_name]["hands"] += 1
                break  # Only count once per hand

        ai_opponents_summary = "\n".join(
            f"- {name}: {data['hands']} hands played"
            for name, data in ai_opponents.items()
        )

        # Session timestamps
        session_start = hands[0].timestamp if hands else "N/A"
        session_end = hands[-1].timestamp if hands else "N/A"

        return {
            "hand_count": len(hands),
            "session_start": session_start,
            "session_end": session_end,
            "human_name": "You",
            "starting_stack": starting_stack,
            "ending_stack": ending_stack,
            "net_change": ending_stack - starting_stack,
            "net_change_pct": ((ending_stack - starting_stack) / starting_stack * 100) if starting_stack > 0 else 0,
            "aggregate_stats": aggregate_stats,
            "hands_summary": hands_summary,
            "ai_opponents_summary": ai_opponents_summary
        }

    def _determine_result(self, hand: CompletedHand, human_player: Dict) -> str:
        """Determine hand result description."""
        if hand.winner_ids and "human" in hand.winner_ids:
            return f"Won ${hand.pot_size // len(hand.winner_ids)}"
        else:
            loss = human_player["stack_start"] - hand.human_final_stack
            return f"Lost ${loss}"

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        depth: str,
        schema: str = None
    ) -> Dict:
        """
        Call Anthropic API with error handling and quality validation.

        Args:
            system_prompt: System role prompt
            user_prompt: User prompt with hand context
            depth: "quick" or "deep"
            schema: Optional JSON schema (defaults to ANALYSIS_JSON_SCHEMA for hand analysis)

        Returns:
            Parsed and validated analysis dictionary

        Raises:
            Exception: If LLM call fails (caller should handle fallback)
        """
        model = self.sonnet_model if depth == "deep" else self.haiku_model
        # Quick Analysis: 5000 tokens for complete JSON
        # Deep Dive: 8000 tokens for comprehensive analysis
        max_tokens = 8000 if depth == "deep" else 5000

        logger.info(f"Calling {model} with {len(user_prompt)} chars input, max_tokens={max_tokens}")

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            # Extract response text
            content = response.content[0].text

            print(f"[LLM] Response length: {len(content)} chars (depth={depth}, max_tokens={max_tokens})")
            print(f"[LLM] Last 100 chars: ...{content[-100:]}")
            if len(content) < 100:
                print(f"[LLM] WARNING: Response too short! Content: {content}")

            # Parse JSON response
            analysis = self._parse_response(content)

            # Validate quality (only for hand analysis, not session analysis)
            # Session analysis has different fields and is validated separately
            is_session_analysis = schema is not None and "session_summary" in str(schema)
            if not is_session_analysis:
                if not self._validate_analysis(analysis):
                    logger.warning("Analysis failed quality validation")
                    raise ValueError("Analysis quality check failed")

            return analysis

        except Exception as e:
            logger.error(f"LLM analysis failed: {type(e).__name__}: {e}")
            raise  # Let caller handle fallback

    def _parse_response(self, response_text: str) -> Dict:
        """
        Parse LLM JSON response with error handling.

        Handles:
        - Direct JSON
        - JSON in markdown code blocks
        - Common JSON formatting issues
        """
        try:
            # Try direct JSON parse
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.debug("Direct JSON parse failed, trying cleanup...")

            # Try extracting from markdown code blocks
            match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass

            # Try cleanup common issues
            cleaned = response_text.strip()
            cleaned = re.sub(r',\s*}', '}', cleaned)  # Remove trailing commas in objects
            cleaned = re.sub(r',\s*]', ']', cleaned)  # Remove trailing commas in arrays
            cleaned = re.sub(r'}\s*{', '},{', cleaned)  # Fix missing commas between objects

            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse failed even after cleanup: {e}")
                logger.error(f"Response preview: {response_text[:500]}...")
                raise ValueError(f"Failed to parse LLM response as JSON: {e}")

    def _validate_analysis(self, analysis: Dict) -> bool:
        """
        Validate analysis meets quality standards.

        Required fields:
        - summary (>20 chars)
        - player_analysis
        - tips_for_improvement (at least 1 tip with actionable_step)

        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        required = ["summary", "player_analysis", "tips_for_improvement"]
        if not all(field in analysis for field in required):
            logger.warning(f"Missing required fields. Has: {list(analysis.keys())}")
            return False

        # Check summary length
        if len(analysis["summary"]) < 20:
            logger.warning(f"Summary too short: {len(analysis['summary'])} chars")
            return False

        # Check at least one tip
        tips = analysis.get("tips_for_improvement", [])
        if len(tips) < 1:
            logger.warning("No tips provided")
            return False

        # Check tips have actionable steps
        for tip in tips:
            if "actionable_step" not in tip:
                logger.warning(f"Tip missing actionable_step: {tip}")
                return False

        return True
