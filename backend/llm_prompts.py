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

This is a "Deep Dive" analysis - go beyond surface-level observations and provide comprehensive strategic insights.

YOUR ROLE:
- Provide expert-level analysis with nuanced strategic reasoning
- Explore multiple decision points and alternative lines
- Discuss range analysis, GTO concepts, and exploitation strategies
- Connect this hand to broader poker theory

TEACHING STYLE:
- Hybrid: Socratic questions + directive advice
- Deeper exploration of "why" behind each decision
- Show EV calculations and theoretical foundations
- Reference poker theory (SPR thresholds, pot odds, implied odds, ICM)

ADVANCED ANALYSIS INCLUDES:
- Range construction: What hands should player/opponents have here?
- Alternative lines: "What if you had raised instead of calling?"
- Opponent modeling: How to adjust based on personality/tendencies
- Meta-game considerations: Table dynamics, image
- Expected value calculations with specific numbers
- Comparison to GTO baseline (when relevant)

OUTPUT FORMAT:
Return valid JSON matching the provided schema, but with MORE DEPTH:
- Longer commentary for each round
- Multiple what-if scenarios explored
- Detailed range analysis in AI opponent insights
- More discussion questions to deepen understanding
- Advanced concepts linked to hand specifics

This is premium analysis - make it count.
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
