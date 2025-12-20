# Phase 4: LLM-Powered Hand Analysis - Implementation Plan

**Created**: December 19, 2025
**Based On**: PHASE4_PROMPTING_STRATEGY.md deep analysis
**Status**: Ready for Implementation
**Estimated Duration**: 10-14 hours (revised from 8-12)

---

## Executive Summary

This plan provides a concrete, step-by-step implementation guide for Phase 4 based on deep analysis of the prompting strategy document. It addresses key architectural decisions, resolves model selection discrepancies, and provides a phased rollout approach to minimize risk and cost.

---

## Critical Decisions & Clarifications

### 1. Model Selection Strategy

**Issue**: Discrepancy between enhancement plan and prompting strategy
- Enhancement plan: Claude Sonnet 3.5 ($0.011/analysis)
- Prompting strategy: Haiku 4.5 ($0.016) + optional Sonnet 4.5 ($0.029)

**Recommendation**: **Two-Tier Approach**
```
┌─────────────────────────────────────────┐
│  Default: Claude Haiku 4.5              │
│  - Cost: $0.016/analysis (46% higher)   │
│  - Speed: ~2 seconds                    │
│  - Quality: Good for 90% of hands       │
└─────────────────────────────────────────┘
              ↓ User clicks "Deep Dive"
┌─────────────────────────────────────────┐
│  Optional: Claude Sonnet 4.5            │
│  - Cost: $0.029/analysis (2x Haiku)     │
│  - Speed: ~3-4 seconds                  │
│  - Quality: Expert-level analysis       │
└─────────────────────────────────────────┘
```

**Cost Comparison** (100 users/day × 10 analyses):
- Haiku only: $160/day = $4,800/month
- Sonnet only: $290/day = $8,700/month
- Hybrid (90% Haiku, 10% Sonnet): $173/day = $5,190/month

**Decision**: Start with Haiku 4.5, add Deep Dive button for Sonnet 4.5

### 2. Skill Level Detection Strategy

**Phase 4A** (MVP - This Phase):
- Default to "beginner" for all users
- Add `skill_level` parameter to API (for future)
- No automatic detection yet

**Phase 4B** (Future Enhancement):
- Track player stats (win rate, VPIP, PFR)
- Auto-detect skill level after 10 hands
- Adapt language complexity automatically

**Rationale**: Keep Phase 4 focused on core LLM integration, defer detection complexity

### 3. Context Management Strategy

**Implementation**:
```python
def _get_history_limit(analysis_count: int) -> int:
    """Determine how many hands to include in context."""
    if analysis_count <= 5:
        return 50  # Full session (up to 50 hands)
    elif analysis_count <= 20:
        return 30  # Last 30 hands
    else:
        return 20  # Last 20 hands (cost control)
```

**Token Budget**:
- Current hand: ~1,500 tokens
- History (per hand): ~150 tokens
- System prompt: ~500 tokens
- Total input (first 5 analyses): ~1,500 + (50 × 150) + 500 = **9,500 tokens**
- Total input (21+ analyses): ~1,500 + (20 × 150) + 500 = **5,000 tokens**

**Cost Impact**:
- Analysis #1-5: 9,500 input + 1,500 output = $0.021 (Haiku)
- Analysis #21+: 5,000 input + 1,500 output = $0.016 (Haiku)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      Frontend                                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  AnalysisModal.tsx                                     │  │
│  │  - "Analyze Hand" button → Quick Analysis (Haiku)     │  │
│  │  - "Deep Dive" button → Expert Analysis (Sonnet)      │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                          ↓ API Call
┌──────────────────────────────────────────────────────────────┐
│                      Backend                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  main.py                                               │  │
│  │  /games/{id}/analysis-llm?depth=quick|deep             │  │
│  └────────────────────────────────────────────────────────┘  │
│                          ↓                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  llm_analyzer.py                                       │  │
│  │  - LLMHandAnalyzer class                               │  │
│  │  - Model router (Haiku vs Sonnet)                      │  │
│  │  - Context builder                                     │  │
│  │  - Quality validator                                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                          ↓                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  anthropic API                                         │  │
│  │  - Haiku 4.5: claude-3-5-haiku-20241022                │  │
│  │  - Sonnet 4.5: claude-3-5-sonnet-20241022              │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                          ↓ Response
┌──────────────────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────────────────┐  │
│  │  analysis_cache.py (In-memory cache)                   │  │
│  │  - Cache by (game_id, hand_number, depth)              │  │
│  │  - TTL: 1 hour                                         │  │
│  │  - Max size: 1000 analyses                             │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Tasks

### Task 1: Backend - LLM Analyzer Service (3-4 hours)

**File**: `backend/llm_analyzer.py` (NEW)

**Sub-tasks**:

#### 1.1 Core LLMHandAnalyzer Class
```python
class LLMHandAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.haiku_model = "claude-3-5-haiku-20241022"
        self.sonnet_model = "claude-3-5-sonnet-20241022"

    def analyze_hand(
        self,
        completed_hand: CompletedHand,
        hand_history: List[CompletedHand],
        analysis_count: int,
        depth: str = "quick",  # "quick" or "deep"
        skill_level: str = "beginner"
    ) -> Dict:
        """Main entry point for hand analysis."""
        pass
```

#### 1.2 Context Builder
```python
def _build_context(
    self,
    hand: CompletedHand,
    history: List[CompletedHand],
    analysis_count: int
) -> Dict:
    """
    Build comprehensive context from hand and history.

    Returns:
        {
            "hand_number": int,
            "timestamp": str,
            "total_hands": int,
            "player_stats": {
                "hands_played": int,
                "win_rate": float,
                "vpip": float,
                "pfr": float,
                "biggest_win": int,
                "biggest_loss": int
            },
            "current_hand": {
                "human_name": str,
                "stack_start": int,
                "stack_end": int,
                "hole_cards": List[str],
                "final_action": str,
                "result": str
            },
            "betting_rounds": List[BettingRound],
            "community_cards": List[str],
            "showdown_data": Dict,
            "ai_opponents": List[Dict],
            "recent_hands_summary": str
        }
    """
    pass
```

**Key Implementation Details**:
- Calculate VPIP (Voluntarily Put money In Pot): % hands where player didn't fold pre-flop
- Calculate PFR (Pre-Flop Raise): % hands where player raised pre-flop
- Format betting rounds for LLM readability
- Include AI personality information

#### 1.3 Prompt Builder
```python
def _create_system_prompt(self, skill_level: str, depth: str) -> str:
    """Create system prompt based on skill level and depth."""
    if depth == "deep":
        return DEEP_DIVE_SYSTEM_PROMPT.format(skill_level=skill_level)
    else:
        return QUICK_ANALYSIS_SYSTEM_PROMPT.format(skill_level=skill_level)

def _create_user_prompt(self, context: Dict, skill_level: str, depth: str) -> str:
    """Create user prompt with hand context."""
    # Use templates from PHASE4_PROMPTING_STRATEGY.md
    pass
```

#### 1.4 LLM Caller with Error Handling
```python
def _call_llm(
    self,
    system_prompt: str,
    user_prompt: str,
    depth: str
) -> Dict:
    """Call Anthropic API with error handling."""
    model = self.sonnet_model if depth == "deep" else self.haiku_model

    try:
        response = self.client.messages.create(
            model=model,
            max_tokens=2000 if depth == "deep" else 1500,
            temperature=0.7,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        # Parse JSON response
        content = response.content[0].text
        analysis = self._parse_response(content)

        # Validate quality
        if not self._validate_analysis(analysis):
            raise ValueError("Analysis quality check failed")

        return analysis

    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        raise  # Let caller handle fallback
```

#### 1.5 Response Parser & Validator
```python
def _parse_response(self, response_text: str) -> Dict:
    """Parse LLM JSON response with error handling."""
    try:
        # Try direct JSON parse
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Try extracting from markdown code blocks
        import re
        match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
        if match:
            return json.loads(match.group(1))

        # Cleanup common issues
        cleaned = response_text.strip()
        cleaned = re.sub(r',\s*}', '}', cleaned)  # Remove trailing commas
        cleaned = re.sub(r',\s*]', ']', cleaned)

        return json.loads(cleaned)

def _validate_analysis(self, analysis: Dict) -> bool:
    """Validate analysis meets quality standards."""
    required = ["summary", "player_analysis", "tips_for_improvement"]
    if not all(field in analysis for field in required):
        return False

    if len(analysis["summary"]) < 20:
        return False

    if len(analysis.get("tips_for_improvement", [])) < 1:
        return False

    # Check tips have actionable steps
    for tip in analysis.get("tips_for_improvement", []):
        if "actionable_step" not in tip:
            return False

    return True
```

**Deliverable**: Fully functional `backend/llm_analyzer.py` with comprehensive error handling

---

### Task 2: Backend - API Endpoint (1-2 hours)

**File**: `backend/main.py`

#### 2.1 Add LLM Analysis Endpoint
```python
from llm_analyzer import LLMHandAnalyzer

# Initialize analyzer
llm_analyzer = LLMHandAnalyzer()

# In-memory cache
analysis_cache: Dict[str, Dict] = {}

@app.get("/games/{game_id}/analysis-llm")
async def get_llm_analysis(
    game_id: str,
    hand_number: Optional[int] = None,
    depth: str = Query("quick", regex="^(quick|deep)$"),
    use_cache: bool = True
):
    """
    Get LLM-powered hand analysis.

    Args:
        game_id: Game ID
        hand_number: Specific hand to analyze (default: last hand)
        depth: "quick" (Haiku) or "deep" (Sonnet)
        use_cache: Whether to use cached analysis

    Returns:
        {
            "analysis": {...},  # Full analysis JSON
            "model_used": "haiku-4.5" | "sonnet-4.5",
            "cost": float,
            "cached": bool,
            "analysis_count": int  # For this game
        }
    """
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get target hand
    if hand_number is not None and hasattr(game, 'hand_history'):
        target_hand = next(
            (h for h in game.hand_history if h.hand_number == hand_number),
            None
        )
    else:
        target_hand = game.last_hand_summary

    if not target_hand:
        raise HTTPException(status_code=404, detail="No hand to analyze")

    # Check cache
    cache_key = f"{game_id}_hand_{target_hand.hand_number}_{depth}"
    if use_cache and cache_key in analysis_cache:
        cached = analysis_cache[cache_key]
        return {
            **cached,
            "cached": True
        }

    # Get analysis count for context management
    analysis_count = getattr(game, 'analysis_count', 0)
    game.analysis_count = analysis_count + 1

    try:
        # Get hand history
        hand_history = game.hand_history if hasattr(game, 'hand_history') else []

        # Call LLM analyzer
        analysis = llm_analyzer.analyze_hand(
            completed_hand=target_hand,
            hand_history=hand_history,
            analysis_count=analysis_count,
            depth=depth,
            skill_level="beginner"  # TODO: Track player skill
        )

        # Calculate cost (for monitoring)
        model = "sonnet-4.5" if depth == "deep" else "haiku-4.5"
        cost = 0.029 if depth == "deep" else 0.016

        # Build response
        result = {
            "analysis": analysis,
            "model_used": model,
            "cost": cost,
            "cached": False,
            "analysis_count": analysis_count + 1
        }

        # Cache result
        analysis_cache[cache_key] = result

        # Track metrics (for cost monitoring)
        _track_analysis_metrics(game_id, model, cost, analysis_count)

        return result

    except Exception as e:
        logger.error(f"LLM analysis failed for game {game_id}: {e}")

        # Fallback to rule-based analysis
        fallback = _generate_analysis(target_hand)
        return {
            "analysis": fallback,
            "model_used": "rule-based-fallback",
            "cost": 0.0,
            "cached": False,
            "error": str(e)
        }
```

#### 2.2 Add Metrics Tracking
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AnalysisMetrics:
    timestamp: str
    game_id: str
    model_used: str
    cost: float
    analysis_count: int
    success: bool

# Global metrics storage
analysis_metrics: List[AnalysisMetrics] = []

def _track_analysis_metrics(game_id: str, model: str, cost: float, count: int):
    """Track analysis metrics for monitoring."""
    metrics = AnalysisMetrics(
        timestamp=datetime.utcnow().isoformat(),
        game_id=game_id,
        model_used=model,
        cost=cost,
        analysis_count=count,
        success=True
    )
    analysis_metrics.append(metrics)

    # Keep last 1000 metrics
    if len(analysis_metrics) > 1000:
        analysis_metrics[:] = analysis_metrics[-1000:]

@app.get("/admin/analysis-metrics")
async def get_analysis_metrics():
    """Get analysis cost and usage metrics."""
    total_cost = sum(m.cost for m in analysis_metrics)
    haiku_count = sum(1 for m in analysis_metrics if "haiku" in m.model_used)
    sonnet_count = sum(1 for m in analysis_metrics if "sonnet" in m.model_used)

    return {
        "total_analyses": len(analysis_metrics),
        "total_cost": round(total_cost, 2),
        "haiku_analyses": haiku_count,
        "sonnet_analyses": sonnet_count,
        "avg_cost": round(total_cost / len(analysis_metrics), 4) if analysis_metrics else 0,
        "cost_today": _calculate_daily_cost(),
        "alert": total_cost > 100.0  # Alert if >$100 spent
    }

def _calculate_daily_cost() -> float:
    """Calculate cost for today."""
    today = datetime.utcnow().date()
    daily_metrics = [
        m for m in analysis_metrics
        if datetime.fromisoformat(m.timestamp).date() == today
    ]
    return round(sum(m.cost for m in daily_metrics), 2)
```

**Deliverable**: API endpoint with caching, error handling, and metrics tracking

---

### Task 3: Backend - Environment & Dependencies (0.5 hours)

#### 3.1 Update requirements.txt
```bash
# Add to backend/requirements.txt
anthropic>=0.39.0  # Claude API client (Haiku 4.5 + Sonnet 4.5)
```

#### 3.2 Create .env.example
```bash
# backend/.env.example
ANTHROPIC_API_KEY=sk-ant-api03-...
LLM_MODEL_QUICK=claude-3-5-haiku-20241022
LLM_MODEL_DEEP=claude-3-5-sonnet-20241022
LLM_CACHE_ENABLED=true
LLM_FALLBACK_TO_RULES=true
LLM_MAX_COST_PER_DAY=100.0
```

#### 3.3 Installation Command
```bash
cd backend && pip install anthropic
```

**Deliverable**: Environment setup complete

---

### Task 4: Frontend - Updated Analysis Modal (2-3 hours)

**File**: `frontend/components/AnalysisModal.tsx`

#### 4.1 Add Two-Tier Analysis Buttons
```tsx
export function AnalysisModal({ isOpen, onClose, gameId, handNumber }: Props) {
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [depth, setDepth] = useState<'quick' | 'deep'>('quick');
  const [cost, setCost] = useState(0);

  const handleAnalyze = async (analysisDepth: 'quick' | 'deep') => {
    setLoading(true);
    setDepth(analysisDepth);

    try {
      const response = await fetch(
        `${API_BASE_URL}/games/${gameId}/analysis-llm?depth=${analysisDepth}`
      );
      const data = await response.json();

      setAnalysis(data.analysis);
      setCost(data.cost);
    } catch (error) {
      console.error('Analysis failed:', error);
      // Show error message
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/80" onClick={onClose} />

          {/* Modal */}
          <motion.div className="relative bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg shadow-2xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">

            {/* Header */}
            <div className="bg-gradient-to-r from-green-700 to-green-600 p-6">
              <h2 className="text-2xl font-bold text-white">
                🎓 Hand Analysis & Coaching
              </h2>
              <p className="text-green-100 mt-1">
                Powered by Claude AI {depth === 'deep' ? 'Sonnet 4.5' : 'Haiku 4.5'}
              </p>
            </div>

            {/* Action Buttons */}
            {!analysis && (
              <div className="p-6 space-y-4">
                <button
                  onClick={() => handleAnalyze('quick')}
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-lg font-semibold flex items-center justify-center gap-2"
                >
                  {loading && depth === 'quick' ? (
                    <>⏳ Analyzing...</>
                  ) : (
                    <>⚡ Quick Analysis (2s, $0.016)</>
                  )}
                </button>

                <button
                  onClick={() => handleAnalyze('deep')}
                  disabled={loading}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white py-4 rounded-lg font-semibold flex items-center justify-center gap-2"
                >
                  {loading && depth === 'deep' ? (
                    <>⏳ Analyzing...</>
                  ) : (
                    <>🔬 Deep Dive Analysis (4s, $0.029)</>
                  )}
                </button>

                <p className="text-center text-sm text-gray-400">
                  Quick Analysis: Good for most hands<br/>
                  Deep Dive: Expert-level breakdown with GTO concepts
                </p>
              </div>
            )}

            {/* Analysis Content */}
            {analysis && (
              <div className="p-6 overflow-y-auto max-h-[70vh] space-y-6">
                {/* ... render analysis JSON ... */}
              </div>
            )}

          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

#### 4.2 Render Analysis JSON

**Key Sections to Render**:
1. Summary
2. Round-by-Round Breakdown (new!)
3. Your Performance (good decisions + questionable decisions)
4. AI Opponent Insights
5. Concepts to Study (with tutorial links)
6. Tips for Improvement
7. Discussion Questions

**Component Structure**:
```tsx
<div className="space-y-6">
  <SummarySection summary={analysis.summary} />
  <RoundByRoundSection rounds={analysis.round_by_round} />
  <PlayerPerformanceSection performance={analysis.player_analysis} />
  <AIOpponentInsightsSection insights={analysis.ai_opponent_insights} />
  <ConceptsToStudySection concepts={analysis.concepts_to_study} />
  <TipsSection tips={analysis.tips_for_improvement} />
  <DiscussionQuestionsSection questions={analysis.discussion_questions} />
  <EncouragementSection message={analysis.encouragement} />
</div>
```

**Deliverable**: Beautiful, comprehensive analysis modal with two-tier analysis

---

### Task 5: Frontend - API Client (0.5 hours)

**File**: `frontend/lib/api.ts`

```tsx
export async function getHandAnalysisLLM(
  gameId: string,
  options: {
    depth?: 'quick' | 'deep',
    handNumber?: number,
    useCache?: boolean
  } = {}
): Promise<{
  analysis: any,
  model_used: string,
  cost: number,
  cached: boolean,
  analysis_count: number
}> {
  const params = new URLSearchParams();
  if (options.depth) params.set('depth', options.depth);
  if (options.handNumber) params.set('hand_number', options.handNumber.toString());
  if (options.useCache !== undefined) params.set('use_cache', options.useCache.toString());

  const response = await fetch(
    `${API_BASE_URL}/games/${gameId}/analysis-llm?${params}`
  );

  if (!response.ok) {
    throw new Error(`Analysis failed: ${response.statusText}`);
  }

  return response.json();
}
```

**Deliverable**: API client method for LLM analysis

---

### Task 6: Testing (2-3 hours)

#### 6.1 Backend Unit Tests

**File**: `backend/tests/test_llm_analysis.py` (NEW)

```python
import pytest
from unittest.mock import Mock, patch
from llm_analyzer import LLMHandAnalyzer
from game.poker_engine import CompletedHand

def test_context_builder_includes_all_fields():
    """Verify context has all required fields."""
    analyzer = LLMHandAnalyzer()

    # Create mock hand and history
    hand = Mock(spec=CompletedHand)
    history = [Mock(spec=CompletedHand) for _ in range(10)]

    context = analyzer._build_context(hand, history, analysis_count=1)

    # Check required fields
    assert "hand_number" in context
    assert "player_stats" in context
    assert "current_hand" in context
    assert "betting_rounds" in context
    assert "ai_opponents" in context

def test_history_limit_based_on_analysis_count():
    """Verify context limits history correctly."""
    analyzer = LLMHandAnalyzer()

    history = [Mock() for _ in range(100)]

    # First 5 analyses: full history
    context1 = analyzer._build_context(Mock(), history, analysis_count=1)
    assert len(context1["recent_hands"]) <= 50

    # 21+ analyses: last 20 hands
    context2 = analyzer._build_context(Mock(), history, analysis_count=25)
    assert len(context2["recent_hands"]) <= 20

@patch('anthropic.Anthropic')
def test_llm_analysis_endpoint_success(mock_anthropic):
    """Verify /analysis-llm endpoint works."""
    # Mock LLM response
    mock_response = Mock()
    mock_response.content = [Mock(text='{"summary": "Test analysis"}')]
    mock_anthropic.return_value.messages.create.return_value = mock_response

    # Create game, play hand
    game_id = create_game(...)
    play_hand(game_id, ...)

    # Call endpoint
    response = client.get(f"/games/{game_id}/analysis-llm?depth=quick")

    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert data["model_used"] == "haiku-4.5"
    assert data["cost"] > 0

def test_analysis_caching():
    """Verify analysis is cached."""
    game_id = create_game(...)

    # First call
    response1 = client.get(f"/games/{game_id}/analysis-llm")
    assert response1.json()["cached"] == False

    # Second call (should be cached)
    response2 = client.get(f"/games/{game_id}/analysis-llm")
    assert response2.json()["cached"] == True

@patch('anthropic.Anthropic')
def test_llm_failure_falls_back_to_rule_based(mock_anthropic):
    """Verify graceful fallback on LLM error."""
    # Mock API error
    mock_anthropic.return_value.messages.create.side_effect = Exception("API error")

    game_id = create_game(...)
    play_hand(game_id, ...)

    # Should still return analysis (fallback)
    response = client.get(f"/games/{game_id}/analysis-llm")
    assert response.status_code == 200
    assert response.json()["model_used"] == "rule-based-fallback"

def test_quality_validation():
    """Verify quality checks reject bad responses."""
    analyzer = LLMHandAnalyzer()

    # Missing required fields
    bad_analysis = {"summary": "Test"}
    assert analyzer._validate_analysis(bad_analysis) == False

    # Missing actionable steps
    bad_analysis2 = {
        "summary": "Test",
        "player_analysis": {},
        "tips_for_improvement": [{"tip": "Test"}]  # No actionable_step
    }
    assert analyzer._validate_analysis(bad_analysis2) == False

    # Valid analysis
    good_analysis = {
        "summary": "Good hand analysis here",
        "player_analysis": {},
        "tips_for_improvement": [{
            "tip": "Calculate pot odds",
            "actionable_step": "Before calling, ask..."
        }]
    }
    assert analyzer._validate_analysis(good_analysis) == True
```

**Test Coverage**:
- ✅ Context building
- ✅ History limiting
- ✅ LLM API integration
- ✅ Caching
- ✅ Error handling & fallback
- ✅ Quality validation
- ✅ Cost tracking

#### 6.2 Integration Tests

**File**: `backend/tests/test_llm_integration.py` (NEW)

```python
def test_end_to_end_quick_analysis():
    """Test full flow: create game → play hand → analyze with Haiku."""
    # Requires ANTHROPIC_API_KEY in environment
    pytest.skip("Requires API key and costs money")

    # Create game
    game_id = create_game(player_name="Test", ai_count=3)

    # Play one hand
    play_hand_to_completion(game_id)

    # Get analysis
    response = client.get(f"/games/{game_id}/analysis-llm?depth=quick")

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert "analysis" in data
    assert "summary" in data["analysis"]
    assert "round_by_round" in data["analysis"]
    assert len(data["analysis"]["tips_for_improvement"]) > 0

def test_end_to_end_deep_dive_analysis():
    """Test full flow with Sonnet Deep Dive."""
    pytest.skip("Requires API key and costs money")

    # Same as above but depth=deep
    # Verify Sonnet model used, longer analysis
```

#### 6.3 Manual Testing Checklist

- [ ] Set `ANTHROPIC_API_KEY` environment variable
- [ ] Start backend: `python backend/main.py`
- [ ] Start frontend: `cd frontend && npm run dev`
- [ ] Play one hand
- [ ] Click "Analyze Hand" → "Quick Analysis"
- [ ] Verify analysis displays correctly
- [ ] Verify round-by-round breakdown
- [ ] Verify tips have actionable steps
- [ ] Click "Deep Dive Analysis"
- [ ] Verify deeper, more technical analysis
- [ ] Refresh page → verify analysis cached (instant load)
- [ ] Check `/admin/analysis-metrics` endpoint
- [ ] Verify cost tracking working

**Deliverable**: Comprehensive test suite (8+ tests)

---

### Task 7: Prompt Templates (1 hour)

**File**: `backend/llm_prompts.py` (NEW)

#### 7.1 System Prompts

```python
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
```

#### 7.2 User Prompt Template

```python
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
Provide comprehensive {analysis_type} analysis in JSON format following the schema.
- Adapt language/depth to {skill_level} level
- Prioritize actionable insights
- Include what-if scenarios for close decisions
- Suggest 2-3 concepts to study with tutorial links
- End with encouragement and specific next steps

Remember: Be specific, be actionable, be encouraging.
"""
```

**Deliverable**: Comprehensive prompt templates

---

## Rollout Strategy

### Phase 4A: Core Implementation (MVP) ✅ THIS PHASE
**Duration**: 8-10 hours
**Goal**: Basic LLM analysis working end-to-end

**Deliverables**:
- ✅ LLMHandAnalyzer class (Haiku + Sonnet)
- ✅ API endpoint `/analysis-llm`
- ✅ Updated AnalysisModal (two-tier buttons)
- ✅ Caching + error handling
- ✅ Cost tracking
- ✅ 8+ tests passing
- ✅ Manual testing complete

**Success Criteria**:
- User can get Quick Analysis in <3 seconds
- User can get Deep Dive in <5 seconds
- Analysis displays correctly with all sections
- Fallback to rule-based on error
- Cost tracked via `/admin/analysis-metrics`

### Phase 4B: Skill Level Detection (Future)
**Duration**: 3-4 hours
**Goal**: Automatic skill detection after 10 hands

**Features**:
- Track VPIP, PFR, win rate, mistake patterns
- Auto-detect beginner/intermediate/advanced
- Adapt language complexity automatically
- Show skill progression to user

### Phase 4C: Advanced Features (Future)
**Duration**: 4-6 hours
**Goal**: Enhanced coaching experience

**Features**:
- Session summaries (analyze last 10 hands together)
- Pattern detection ("You overvalue top pair 70% of the time")
- Interactive follow-up ("Ask me anything about this hand")
- Personalized coaching plans

---

## Cost Management

### Daily Cost Monitoring

```python
# Run daily (cron job or scheduled task)
def check_daily_cost():
    metrics = get_daily_metrics()

    if metrics["cost_today"] > 100:
        send_alert(f"⚠️ Daily cost exceeded $100: ${metrics['cost_today']}")

    if metrics["cost_today"] > 50:
        # Warn users: "High usage today. Quick Analysis recommended."
        pass
```

### Rate Limiting

```python
# Add to main.py
from fastapi import HTTPException
import time

# Rate limit: 1 analysis per 30 seconds per game
last_analysis_time = {}

@app.get("/games/{game_id}/analysis-llm")
async def get_llm_analysis(game_id: str, ...):
    # Check rate limit
    now = time.time()
    last_time = last_analysis_time.get(game_id, 0)

    if now - last_time < 30:
        wait_time = 30 - (now - last_time)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit: Wait {wait_time:.0f}s before next analysis"
        )

    last_analysis_time[game_id] = now

    # ... rest of endpoint
```

### Cost Optimization Strategies

1. **Aggressive Caching**: Never regenerate analysis for same hand
2. **History Limiting**: Reduce tokens after 20 analyses (already implemented)
3. **Haiku Default**: 90% of analyses use Haiku (2x cheaper than Sonnet)
4. **Rate Limiting**: Prevent spam (1 per 30s per user)
5. **Cost Alerts**: Alert at $50/day, hard limit at $100/day

**Expected Cost** (100 users/day × 10 analyses, 90% Haiku, 10% Sonnet):
- Haiku: 900 × $0.016 = $14.40/day
- Sonnet: 100 × $0.029 = $2.90/day
- **Total: $17.30/day = $519/month** ✅ Well under budget

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **API costs spiral** | Medium | High | Caching, rate limiting, cost alerts at $50/day |
| **LLM provides bad advice** | Low | Medium | Quality validation, fallback to rules |
| **API downtime** | Low | Medium | Graceful fallback to rule-based analysis |
| **Slow response times** | Low | Low | Use Haiku (2s), show loading spinner |
| **Context too long** | Medium | Low | History limiting (20-50 hands max) |
| **JSON parsing fails** | Medium | Low | Regex cleanup, markdown extraction |

---

## Success Metrics

### Technical Metrics
- ✅ Quick Analysis: <3s response time (Haiku)
- ✅ Deep Dive: <5s response time (Sonnet)
- ✅ 95% quality validation pass rate
- ✅ <1% fallback to rule-based
- ✅ Cache hit rate >80% (don't regenerate)

### Business Metrics
- 📊 Analysis request rate: % of hands analyzed
- 📊 Deep Dive usage: % that upgrade to Sonnet
- 📊 User satisfaction: Thumbs up/down rating
- 📊 Cost per active user: <$1/user/day
- 📊 Retention: Do users come back for more games?

### Learning Outcomes
- 📈 Win rate improvement: Track before/after LLM analysis usage
- 📈 Mistake reduction: Fewer repeated errors
- 📈 Concept understanding: Do users click tutorial links?

---

## Timeline

| Task | Hours | Dependencies | Deliverable |
|------|-------|--------------|-------------|
| **1. Backend - LLM Analyzer** | 3-4h | None | `llm_analyzer.py` working |
| **2. Backend - API Endpoint** | 1-2h | Task 1 | `/analysis-llm` endpoint |
| **3. Backend - Environment** | 0.5h | Task 1 | Dependencies installed |
| **4. Frontend - Modal** | 2-3h | Task 2 | Updated UI with 2 buttons |
| **5. Frontend - API Client** | 0.5h | Task 2 | `getHandAnalysisLLM()` |
| **6. Testing** | 2-3h | Tasks 1-5 | 8+ tests passing |
| **7. Prompt Templates** | 1h | None | System/user prompts |
| **Total** | **10-14h** | | **Phase 4A Complete** |

---

## Pre-Implementation Checklist

Before starting Phase 4A implementation:

- [ ] Phase 3 (Hand History) confirmed complete
- [ ] Review PHASE4_PROMPTING_STRATEGY.md thoroughly
- [ ] Get Anthropic API key (https://console.anthropic.com/)
- [ ] Confirm $100/day budget for initial testing
- [ ] Set up cost monitoring dashboard
- [ ] Plan rollback strategy if costs exceed budget
- [ ] Review existing rule-based analysis to understand fallback
- [ ] Test prompt templates in Claude.ai web interface first

---

## Post-Implementation Checklist

After completing Phase 4A:

- [ ] All 8+ tests passing
- [ ] Manual testing complete (played 5+ hands, analyzed both quick & deep)
- [ ] Cost tracking working (`/admin/analysis-metrics` endpoint)
- [ ] Cache working (second analysis instant)
- [ ] Fallback tested (disable API key → rule-based works)
- [ ] Rate limiting tested (spam analysis button → 429 error)
- [ ] Documentation updated (STATUS.md, HISTORY.md)
- [ ] Commit with message: "Phase 4: LLM-powered hand analysis (Haiku + Sonnet)"
- [ ] Deploy to staging environment
- [ ] Monitor costs for 24 hours before prod release

---

## Questions to Answer Before Starting

1. **Budget Confirmation**: Are we comfortable with $17-20/day ($500-600/month) for LLM analysis?
2. **API Key**: Do we have Anthropic API key with billing enabled?
3. **Model Selection**: Confirm Haiku 4.5 + Sonnet 4.5 (not Sonnet 3.5 from enhancement plan)?
4. **Fallback Strategy**: Is rule-based analysis acceptable as fallback, or should we block analysis?
5. **Cost Alerts**: Who receives alerts when cost exceeds $50/day?
6. **User Feedback**: How do we collect feedback on analysis quality (thumbs up/down)?
7. **Skill Detection**: Is Phase 4B (auto skill detection) needed for MVP, or can we defer?

---

## Next Steps

1. **Review this plan** with team/stakeholders
2. **Answer pre-implementation questions**
3. **Get API key and set up billing**
4. **Start with Task 7** (prompt templates) - test in Claude.ai first
5. **Then implement Tasks 1-6 sequentially**
6. **Test thoroughly before marking Phase 4 complete**

---

**End of Implementation Plan**

Ready to execute? Let's build amazing LLM-powered poker coaching! 🚀🃏🤖
