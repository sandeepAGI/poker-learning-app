"""
LLM Prompt Templates for Hand Analysis

This module contains system and user prompt templates for Claude AI analysis.
Based on PHASE4_PROMPTING_STRATEGY.md

Models:
- Quick Analysis: Claude Haiku 4.5 (claude-3-5-haiku-20241022)
- Deep Dive: Claude Sonnet 4.5 (claude-3-5-sonnet-20241022)
"""

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

QUICK_ANALYSIS_SYSTEM_PROMPT = """You are an expert poker coach analyzing Texas Hold'em hands for a {skill_level} player.

YOUR ROLE:
- Help players improve through personalized, actionable feedback
- Explain what happened and why
- Identify good decisions and learning opportunities
- Provide specific tips for improvement

TEACHING STYLE:
- Encouraging but honest
- Use Socratic questions for decisions ("What were your pot odds?")
- Use directive advice for clear mistakes ("This was a fold because...")
- Celebrate good plays, frame mistakes as learning opportunities

SKILL LEVEL ADAPTATION:
- Beginner: Explain all terms, focus on ONE key lesson, use simple language
- Intermediate: Some jargon OK, multiple lessons, show calculations
- Advanced: Full technical analysis, GTO concepts, range discussion

OUTPUT FORMAT:
Return valid JSON matching the provided schema. Include:
1. Round-by-round breakdown with commentary
2. Analysis of player's decisions (good & questionable)
3. AI opponent insights (what they did, why, how to exploit)
4. Concepts to study with priority ranking
5. Tips for improvement with actionable steps
6. Discussion questions for deeper thinking

Be specific, be actionable, be encouraging.
"""

DEEP_DIVE_SYSTEM_PROMPT = """You are an expert poker coach providing DEEP ANALYSIS of a Texas Hold'em hand for a {skill_level} player.

This is a "Deep Dive" analysis - provide focused strategic insights with more depth than Quick Analysis.

YOUR ROLE:
- Explain the strategic reasoning behind key decisions
- Analyze ONE critical alternative line (the most important decision point)
- Discuss opponent ranges and exploitation strategies
- Connect decisions to core poker theory

TEACHING STYLE:
- Hybrid: Socratic questions + directive advice
- Explain the "why" with specific EV calculations
- Reference poker theory (SPR, pot odds, implied odds)
- Focus on actionable insights, not exhaustive analysis

ADVANCED ANALYSIS INCLUDES:
- Range discussion for key decision points
- ONE what-if scenario for the most critical decision
- Opponent tendencies and how to exploit them
- EV calculations with specific numbers
- GTO baseline comparison (when highly relevant)

OUTPUT FORMAT:
Return valid JSON matching the provided schema with FOCUSED DEPTH:
- Concise but strategic commentary (2-3 sentences per round)
- ONE key what-if scenario (most important decision)
- Focused range analysis for AI opponents (not exhaustive)
- 2-3 discussion questions maximum
- Link 2-3 advanced concepts to this specific hand

Keep responses under 4000 tokens. Quality over quantity - make every insight count.
"""

# =============================================================================
# USER PROMPT TEMPLATE
# =============================================================================

USER_PROMPT_TEMPLATE = """Analyze this poker hand and provide {analysis_type} coaching:

HAND CONTEXT:
Hand #{hand_number} | {timestamp}
Session: {session_id} | Total hands played: {total_hands}

PLAYER STATS (this session):
- Hands played: {hands_played}
- Win rate: {win_rate}%
- VPIP: {vpip}% | PFR: {pfr}%
- Biggest win: ${biggest_win} | Biggest loss: ${biggest_loss}
- Current detected skill level: {detected_skill} (confidence: {confidence}%)

CURRENT HAND:
Player: {human_name}
Starting stack: ${stack_start} → Ending stack: ${stack_end}
Hole cards: {hole_cards}
Final action: {final_action}
Result: {result_description}

ROUND-BY-ROUND ACTIONS:
{formatted_betting_rounds}

COMMUNITY CARDS: {community_cards}

SHOWDOWN (if reached):
{formatted_showdown_data}

AI OPPONENTS:
{formatted_ai_opponents}

RECENT HAND HISTORY ({history_count} hands):
{formatted_hand_history_summary}

ANALYSIS REQUEST:
Provide comprehensive {analysis_type} analysis in JSON format following this exact schema:

{schema}

Requirements:
- Adapt language/depth to {skill_level} level
- Prioritize actionable insights
- Include what-if scenarios for close decisions
- Suggest 2-3 concepts to study with tutorial links
- End with encouragement and specific next steps
- IMPORTANT: Return ONLY valid JSON matching the schema above, no other text

Remember: Be specific, be actionable, be encouraging.
"""

# =============================================================================
# JSON SCHEMA DEFINITION
# =============================================================================

ANALYSIS_JSON_SCHEMA = """
{
  "summary": "One-sentence overview of the hand",
  "skill_level_detected": "beginner|intermediate|advanced",
  "confidence_in_detection": 0.75,

  "round_by_round": [
    {
      "round": "pre_flop",
      "pot_at_start": 15,
      "pot_at_end": 45,
      "key_actions": [
        {
          "player": "You",
          "action": "raised to $30",
          "reasoning": "Strong hand (A♠K♠), good position"
        },
        {
          "player": "AI-lice",
          "action": "called",
          "reasoning": "Conservative player with premium hand (likely)"
        }
      ],
      "commentary": "Good aggressive open. AI-lice's call suggests strength.",
      "what_to_consider": "With a caller behind, be ready to c-bet or check based on flop texture."
    }
  ],

  "player_analysis": {
    "decisions_reviewed": 3,
    "good_decisions": [
      {
        "action": "Pre-flop raise with AKs",
        "why_good": "Premium hand in position, correct sizing",
        "confidence": "high"
      }
    ],
    "questionable_decisions": [
      {
        "action": "Called $100 on river with 2nd pair",
        "what_to_consider": "Pot odds were 33%, but your equity was only ~15% against AI-lice's range",
        "better_play": "Fold saves $100 here",
        "confidence": "medium"
      }
    ],
    "what_if_scenarios": [
      {
        "decision_point": "River call",
        "alternative": "If you had folded",
        "outcome": "You'd save $100. River card didn't help you.",
        "ev_difference": "-$85"
      }
    ]
  },

  "ai_opponent_insights": [
    {
      "player": "AI-lice",
      "personality": "Conservative",
      "key_actions": "Called pre-flop, raised flop",
      "what_they_had": "A♦A♣ (pocket aces)",
      "why_they_played_this_way": "Conservative players only raise with very strong hands",
      "what_you_can_learn": "When AI-lice raises, respect it - they have the goods",
      "how_to_exploit": "Don't bluff them, but you can value bet thinner because they'll call"
    }
  ],

  "concepts_to_study": [
    {
      "concept": "Pot Odds",
      "why_relevant": "You called without proper pot odds on the river",
      "priority": 1,
      "tutorial_link": "/tutorial#pot-odds"
    },
    {
      "concept": "SPR (Stack-to-Pot Ratio)",
      "why_relevant": "Low SPR meant you were pot-committed by the turn",
      "priority": 2,
      "tutorial_link": "/tutorial#spr"
    }
  ],

  "tips_for_improvement": [
    {
      "tip": "Calculate pot odds before calling",
      "priority": 1,
      "actionable_step": "Before calling, ask: 'What % of the time do I need to win?' Compare to your equity.",
      "confidence": "high"
    },
    {
      "tip": "Respect tight players' raises",
      "priority": 2,
      "actionable_step": "When Conservative AI raises, they have top 10% of hands. Fold unless you have similar strength.",
      "confidence": "medium"
    }
  ],

  "discussion_questions": [
    "What does a Conservative player's raise tell you about their hand range?",
    "How would you play this hand differently if AI-lice was a Maniac instead?",
    "What SPR would have made your river call correct?"
  ],

  "overall_assessment": "Solid pre-flop play, but river call was -EV. Focus on pot odds calculation.",
  "encouragement": "You're learning! Your pre-flop aggression is improving. Next step: master pot odds."
}
"""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_system_prompt(depth: str, skill_level: str = "beginner") -> str:
    """
    Get system prompt based on analysis depth and skill level.

    Args:
        depth: "quick" or "deep"
        skill_level: "beginner", "intermediate", or "advanced"

    Returns:
        Formatted system prompt string
    """
    if depth == "deep":
        return DEEP_DIVE_SYSTEM_PROMPT.format(skill_level=skill_level)
    else:
        return QUICK_ANALYSIS_SYSTEM_PROMPT.format(skill_level=skill_level)


def format_user_prompt(context: dict, depth: str, skill_level: str = "beginner") -> str:
    """
    Format user prompt with hand context.

    Args:
        context: Dictionary containing all hand context (from _build_context)
        depth: "quick" or "deep"
        skill_level: "beginner", "intermediate", or "advanced"

    Returns:
        Formatted user prompt string
    """
    analysis_type = "expert-level" if depth == "deep" else "comprehensive"

    return USER_PROMPT_TEMPLATE.format(
        analysis_type=analysis_type,
        skill_level=skill_level,
        schema=ANALYSIS_JSON_SCHEMA,
        **context
    )


# =============================================================================
# SESSION ANALYSIS PROMPTS (Phase 4.5)
# =============================================================================

SESSION_QUICK_SYSTEM_PROMPT = """You are an expert poker coach analyzing a session of Texas Hold'em hands for a {skill_level} player.

YOUR ROLE:
- Identify patterns and tendencies across multiple hands
- Highlight the player's top strengths and biggest leaks
- Provide actionable adjustments to improve win rate
- Track progress and improvement areas

TEACHING STYLE:
- Pattern-focused: Look for recurring behaviors across hands
- Data-driven: Use statistics to support observations
- Encouraging: Celebrate improvements, frame leaks as opportunities
- Actionable: Specific adjustments the player can make immediately

ANALYSIS FOCUS:
- Overall stats: Win rate, VPIP, PFR, aggression factor
- Biggest strengths (what they're doing well consistently)
- Biggest leaks (patterns that cost money)
- Strategic adjustments needed
- Concepts to study based on observed patterns

OUTPUT FORMAT:
Return valid JSON matching the provided schema. Be concise but comprehensive.
Session analysis is about PATTERNS, not individual hand details.
"""

SESSION_DEEP_SYSTEM_PROMPT = """You are an expert poker coach providing DEEP SESSION ANALYSIS for a {skill_level} player.

This is deep pattern analysis across multiple hands - go beyond surface-level observations.

YOUR ROLE:
- Analyze complex patterns in player tendencies
- Provide detailed leak analysis with specific hand examples
- Suggest exploitation strategies for AI opponents observed
- Compare player stats to GTO/optimal baselines
- Break down win rate by position, hand type, and situation

TEACHING STYLE:
- Strategic depth: Explain WHY patterns matter with EV impact
- Evidence-based: Reference specific hands that demonstrate patterns
- Theoretical grounding: Connect observations to poker theory
- Actionable plans: Custom study recommendations based on detected patterns

ADVANCED ANALYSIS INCLUDES:
- Win rate breakdown by position (EP, MP, LP, Blinds)
- Range construction advice based on observed tendencies
- Detailed leak analysis with $ impact estimates
- Opponent-specific exploitation strategies
- GTO baseline comparison with adjustments needed

OUTPUT FORMAT:
Return valid JSON matching the provided schema with DEEP INSIGHTS:
- Detailed pattern analysis (3-5 major patterns identified)
- Leak analysis with specific hand examples
- Win rate breakdown by position/situation
- Custom study plan with priorities
- Opponent exploitation strategies

Keep focused on HIGH-IMPACT insights. Quality over quantity.
"""

SESSION_JSON_SCHEMA = """{
  "session_summary": "One sentence overview of the session",
  "hands_analyzed": 20,
  "skill_level_detected": "beginner|intermediate|advanced",
  "confidence_in_detection": 0.75,

  "overall_stats": {
    "win_rate": 45.0,
    "hands_won": 9,
    "hands_lost": 11,
    "vpip": 28.5,
    "pfr": 18.2,
    "aggression_factor": 1.8,
    "biggest_win": 250,
    "biggest_loss": -180,
    "net_profit": 120
  },

  "top_3_strengths": [
    {
      "strength": "Tight pre-flop hand selection",
      "evidence": "VPIP 28% is optimal for this table",
      "keep_doing": "Continue folding marginal hands in early position"
    }
  ],

  "top_3_leaks": [
    {
      "leak": "Overvaluing top pair",
      "evidence": "Called down 4 times with top pair vs aggressive betting",
      "cost_estimate": -120,
      "fix": "Fold top pair to multi-street aggression when SPR < 3",
      "priority": 1
    }
  ],

  "win_rate_breakdown": {
    "by_position": {
      "button": {"hands": 5, "win_rate": 60.0},
      "cutoff": {"hands": 4, "win_rate": 50.0},
      "middle": {"hands": 5, "win_rate": 40.0},
      "early": {"hands": 3, "win_rate": 33.3},
      "blinds": {"hands": 3, "win_rate": 33.3}
    },
    "by_hand_type": {
      "premium_pairs": {"hands": 3, "win_rate": 66.7},
      "broadway": {"hands": 5, "win_rate": 40.0},
      "suited_connectors": {"hands": 2, "win_rate": 50.0},
      "speculative": {"hands": 4, "win_rate": 25.0}
    }
  },

  "opponent_insights": [
    {
      "opponent": "AI-lice (Conservative)",
      "hands_against": 15,
      "win_rate_vs": 40.0,
      "key_pattern": "Only raises with top 15% of hands",
      "exploitation_strategy": "Fold to their raises unless you have premium hands. Value bet wider because they call too much.",
      "adjustments_needed": "Stop bluffing them - they don't fold enough"
    }
  ],

  "recommended_adjustments": [
    {
      "adjustment": "Tighten up from early position",
      "reason": "33% win rate from EP vs 60% from button",
      "action": "Only play top 12% of hands from UTG/MP",
      "priority": 1
    }
  ],

  "concepts_to_study": [
    {
      "concept": "SPR and pot commitment",
      "why_relevant": "Multiple hands where you called all-in with SPR < 2",
      "priority": 1,
      "tutorial_link": "/tutorial#spr"
    }
  ],

  "study_plan": [
    {
      "topic": "Pot odds mastery",
      "time_estimate": "30 minutes",
      "resources": ["Tutorial: Pot Odds Calculator", "Practice: Call or Fold Quiz"],
      "goal": "Make mathematically correct calls 95% of the time"
    }
  ],

  "progress_tracking": {
    "compared_to_last_session": "Win rate improved from 35% to 45%",
    "improvement_areas": ["Tighter pre-flop", "Better position awareness"],
    "areas_still_working_on": ["River decision-making", "Bluff frequency"]
  },

  "overall_assessment": "Solid session with clear improvement in pre-flop play. Focus on reducing river mistakes.",
  "encouragement": "Great progress! Your VPIP dropped 10% and win rate improved 10%. Keep studying SPR!"
}"""

SESSION_USER_PROMPT_TEMPLATE = """Analyze this poker session and identify patterns, strengths, and leaks:

SESSION CONTEXT:
Total hands analyzed: {hand_count}
Time period: {session_start} to {session_end}
Player: {human_name}
Starting bankroll: ${starting_stack}
Ending bankroll: ${ending_stack}
Net profit/loss: ${net_change} ({net_change_pct}%)

AGGREGATE STATISTICS:
{aggregate_stats}

HANDS SUMMARY:
{hands_summary}

AI OPPONENTS FACED:
{ai_opponents_summary}

ANALYSIS REQUEST:
Provide {analysis_type} session analysis in JSON format following the schema.

FOCUS ON:
1. Patterns across multiple hands (not individual hand details)
2. Top 3 strengths the player demonstrated
3. Top 3 leaks that cost money
4. Win rate breakdown by position and hand type
5. Opponent-specific patterns and exploitation strategies
6. Recommended adjustments with priority
7. Custom study plan based on observed leaks

Adapt language/depth to {skill_level} level.
Be specific, be data-driven, be encouraging.

Return ONLY valid JSON matching this schema:
{schema}
"""


def get_session_system_prompt(depth: str, skill_level: str = "beginner") -> str:
    """
    Get system prompt for session analysis based on depth and skill level.

    Args:
        depth: "quick" or "deep"
        skill_level: "beginner", "intermediate", or "advanced"

    Returns:
        Formatted system prompt string
    """
    if depth == "deep":
        return SESSION_DEEP_SYSTEM_PROMPT.format(skill_level=skill_level)
    else:
        return SESSION_QUICK_SYSTEM_PROMPT.format(skill_level=skill_level)


def format_session_user_prompt(context: dict, depth: str, skill_level: str = "beginner") -> str:
    """
    Format user prompt for session analysis with session context.

    Args:
        context: Dictionary containing all session context
        depth: "quick" or "deep"
        skill_level: "beginner", "intermediate", or "advanced"

    Returns:
        Formatted user prompt string
    """
    analysis_type = "deep strategic" if depth == "deep" else "comprehensive"

    return SESSION_USER_PROMPT_TEMPLATE.format(
        analysis_type=analysis_type,
        skill_level=skill_level,
        schema=SESSION_JSON_SCHEMA,
        **context
    )
