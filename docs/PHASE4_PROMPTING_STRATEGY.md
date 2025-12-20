# Phase 4: LLM Prompting Strategy

**Last Updated**: 2025-12-19
**Models**: Claude Haiku 4.5 (primary), Claude Sonnet 4.5 (optional Deep Dive)
**Cost Target**: $0.016/analysis (Haiku), $0.029/analysis (Sonnet)

---

## 1. Teaching Philosophy

### Hybrid Approach: Socratic + Directive

**Socratic Method** (for player decisions):
- Ask questions to guide thinking
- Help player discover insights themselves
- Build critical thinking skills
- Example: "What were your pot odds when you called here? Was it +EV given your hand strength?"

**Directive Method** (for clear mistakes):
- Tell them what they should have done
- Explain why with concrete reasoning
- Provide specific action steps
- Example: "This was a fold. With 15% equity and 40% pot odds, you're losing money long-term."

**Encouraging Tone** (always):
- Positive framing even for mistakes
- Celebrate good decisions
- Frame errors as learning opportunities
- Example: "Nice aggressive play! Let's explore when this strategy works best..."

---

## 2. Skill Level Detection & Adaptation

### Auto-Detection Criteria

**Beginner** (default for first 10 hands):
- Win rate < 45%
- High variance in bet sizing
- Frequent pot odds mistakes
- Doesn't adjust to SPR

**Intermediate** (after 10 hands if criteria met):
- Win rate 45-55%
- Understands pot odds
- Some SPR awareness
- Occasionally adjusts to opponents

**Advanced** (after 20 hands if criteria met):
- Win rate > 55%
- Consistent bet sizing strategy
- Strong SPR understanding
- Actively exploits opponent tendencies

### Language & Complexity by Level

**Beginner:**
- Explain all poker terms: "SPR (Stack-to-Pot Ratio) means..."
- Avoid GTO terminology
- Use analogies: "Your hand was like bringing a knife to a gunfight"
- Focus on ONE key lesson per hand
- Simple math: "You needed 33% equity but only had 20%"

**Intermediate:**
- Some jargon OK: "SPR was 3.5, so you're pot-committed"
- Introduce advanced concepts: "Consider your perceived range here"
- Multiple lessons per hand
- Show calculations: "EV = (0.35 × $200) - (0.65 × $100) = +$5"

**Advanced:**
- Full technical language: "Your 3-bet sizing was exploitable against this opponent's calling range"
- GTO concepts: "Optimal strategy here is to balance your range with 70% value, 30% bluffs"
- Range analysis: "Given your pre-flop action, villain puts you on..."
- EV calculations with ICM considerations

---

## 3. Context Management

### History Limits (Cost Control)

| Analysis # | Hands Included | Tokens | Cost (Haiku) |
|------------|----------------|--------|--------------|
| 1-5 | Full session (all hands) | ~8,500 | $0.016 |
| 6-20 | Last 30 hands | ~5,000 | $0.012 |
| 21+ | Last 20 hands | ~3,500 | $0.010 |

### What to Include in Context

**Current Hand (Always):**
- Hand number, timestamp
- Player's hole cards, final action, stack changes
- Round-by-round betting actions
- Community cards
- Showdown results (if reached)
- AI opponents' actions and reasoning

**Historical Context:**
- Aggregated stats: "You've folded 65% of hands today"
- Pattern detection: "You're playing tighter than average"
- Win rate, biggest wins/losses
- Tendency analysis: "You often call when you should fold draws"

**AI Opponent Context:**
- Personality types revealed: "AI-lice is Conservative, expects strong hands"
- Recent actions: "AI-ron has raised 5 of last 7 hands (likely Maniac)"

**What-If Scenarios (Selective):**
- Only for close decisions (within 5% EV)
- Show alternative outcome: "If you had called, you would have won $150 (flush on river)"
- But don't make them feel bad: "However, your fold was reasonable given the information"

---

## 4. Output Schema

### JSON Structure

```json
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
```

---

## 5. System Prompt Template

### For Haiku 4.5 (Quick Analysis)

```
You are an expert poker coach analyzing Texas Hold'em hands for a {skill_level} player.

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
```

### For Sonnet 4.5 (Deep Dive)

```
You are an expert poker coach providing DEEP ANALYSIS of a Texas Hold'em hand for a {skill_level} player.

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
```

---

## 6. User Prompt Template

### Structure

```
Analyze this poker hand and provide {analysis_type} coaching:

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
Provide comprehensive {analysis_type} analysis in JSON format following the schema.
- Adapt language/depth to {skill_level} level
- Prioritize actionable insights
- Include what-if scenarios for close decisions
- Suggest 2-3 concepts to study with tutorial links
- End with encouragement and specific next steps

Remember: Be specific, be actionable, be encouraging.
```

---

## 7. Error Handling & Quality Control

### Fallback Strategy

1. **Invalid JSON Response:**
   - Try extracting JSON from markdown code blocks
   - Regex cleanup: remove trailing commas, fix quotes
   - If still fails → fallback to rule-based analysis

2. **Missing Required Fields:**
   - Fill in with defaults: `"summary": "Analysis unavailable"`
   - Show user a message: "Partial analysis available"

3. **API Timeout/Error:**
   - Cache previous attempt for retry
   - Fallback to rule-based analysis
   - Show user: "AI analysis unavailable - showing rule-based insights"

4. **Rate Limiting:**
   - 1 analysis per 30 seconds per user
   - Queue requests if rate limited
   - Show user: "Analysis queued - ready in 15 seconds"

### Quality Checks (Before Showing to User)

```python
def validate_analysis(analysis: dict) -> bool:
    """Check if LLM analysis meets quality standards."""

    # Required fields present
    required = ["summary", "player_analysis", "tips_for_improvement"]
    if not all(field in analysis for field in required):
        return False

    # Minimum content length
    if len(analysis["summary"]) < 20:
        return False

    # At least one tip
    if len(analysis.get("tips_for_improvement", [])) < 1:
        return False

    # Tips have actionable steps
    for tip in analysis.get("tips_for_improvement", []):
        if "actionable_step" not in tip:
            return False

    return True
```

---

## 8. Cost Monitoring

### Track Per Request

```python
@dataclass
class AnalysisMetrics:
    model_used: str  # "haiku-4.5" or "sonnet-4.5"
    input_tokens: int
    output_tokens: int
    cost: float
    duration_ms: int
    cache_hit: bool
    skill_level: str
    hand_number: int
    timestamp: str
```

### Daily/Monthly Aggregation

- Total analyses requested
- Haiku vs Sonnet split
- Average tokens per analysis
- Total cost
- Cache hit rate
- Alert if cost > $100/day

---

## 9. Success Metrics

### Track User Engagement

1. **Analysis request rate**: % of hands analyzed
2. **Deep Dive usage**: % of analyses that upgrade to Sonnet
3. **Time spent reading**: Average seconds in AnalysisModal
4. **Feedback**: Thumbs up/down on analyses
5. **Concept clicks**: How many click tutorial links

### Track Learning Outcomes

1. **Win rate improvement**: Before/after using analysis
2. **Mistake reduction**: Track repeated errors flagged by LLM
3. **Skill progression**: Beginner → Intermediate → Advanced

### Track Cost Efficiency

1. **Cost per active user**
2. **Cost per skill level increase**
3. **Haiku quality score** (user feedback)
4. **Sonnet upgrade value** (was it worth 2x cost?)

---

## 10. Future Enhancements (Post-Launch)

### After we validate Haiku quality:

1. **Adaptive model selection**: Auto-use Sonnet for complex hands
2. **Multi-hand batch analysis**: Session summaries with insights across multiple hands
3. **Personalized coaching**: "Your pattern: You overvalue top pair. Here's why..."
4. **Interactive follow-up**: User can ask questions about the analysis
5. **Replay with commentary**: Animated replay with LLM narration

---

## Summary

**Primary Model**: Haiku 4.5 ($0.016/analysis)
**Optional Upgrade**: Sonnet 4.5 via "Deep Dive" ($0.029/analysis)
**Teaching**: Hybrid Socratic + Directive, always encouraging
**Context**: Full history (5-50 hands) with intelligent limiting
**Quality**: Structured JSON, validated before display
**Cost Control**: Caching, rate limiting, monitoring

**Goal**: Help players learn poker through personalized, actionable, encouraging AI coaching at an affordable cost.
