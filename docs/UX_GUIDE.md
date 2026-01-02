# Phase 4.5 User Guide

**Updated**: December 2025
**Features**: Session Analysis, Simplified Hand Analysis, Blind Progression, Quit Confirmation

---

## What's New in Phase 4.5

### 1. Simplified Hand Analysis
- **Single Analysis Type**: Hand analysis now uses Claude Haiku 4.5 exclusively
- **No More Choices**: Removed the "Quick vs Deep" toggle for individual hands
- **Faster**: Get instant insights after every hand (~2 seconds)
- **Cost**: ~$0.016 per analysis

**How to Use:**
1. Play a hand
2. Click **Settings** → **Analyze Hand**
3. Review AI-powered insights instantly

### 2. Session Analysis (NEW!)
Analyze patterns across multiple hands to identify your strengths and leaks.

**Two Analysis Modes:**

| Mode | Model | Speed | Cost | Best For |
|------|-------|-------|------|----------|
| **Quick** | Haiku 4.5 | 2-3s | $0.018 | Overall stats, top strengths/leaks |
| **Deep** | Sonnet 4.5 | 5-10s | $0.032 | Detailed patterns, GTO comparison |

**How to Use:**
1. Play at least 10 hands
2. Click **Settings** → **Session Analysis**
3. Choose **Quick** (recommended) or **Deep Dive**
4. Review insights:
   - Win rate, VPIP, PFR statistics
   - Top 3 strengths you're demonstrating
   - Top 3 leaks costing you money
   - Recommended adjustments
   - Concepts to study

**When to Use Each:**
- **Quick**: Check after 10-20 hands for general progress
- **Deep**: Use after 20+ hands when you want detailed analysis with specific hand examples

### 3. Blind Progression
Blinds now **double every 10 hands** to increase challenge:

| Hands | Blinds |
|-------|--------|
| 1-10 | $5/$10 |
| 11-20 | $10/$20 |
| 21-30 | $20/$40 |
| 31-40 | $40/$80 |
| 41+ | Continues doubling |

**Strategy Tips:**
- Tighten up as blinds increase relative to stack
- Be more aggressive from late position
- Pay attention to SPR (Stack-to-Pot Ratio) warnings

### 4. Quit Confirmation
When you quit after playing 5+ hands, you'll be asked:

**"Would you like to analyze your session before leaving?"**

**Options:**
1. **Analyze Session First** - Get Quick analysis, then decide
2. **Just Quit** - Skip analysis and return to lobby
3. **Cancel** - Keep playing

---

## Feature Comparison

### Hand Analysis vs Session Analysis

| Feature | Hand Analysis | Session Analysis |
|---------|---------------|------------------|
| **Scope** | Single hand | 10-50 hands |
| **Focus** | Specific decisions | Patterns & tendencies |
| **Speed** | 2 seconds | 2-10 seconds |
| **Cost** | $0.016/hand | $0.018-$0.032 total |
| **Depth Options** | None (Haiku only) | Quick or Deep |
| **Best For** | Learning from mistakes | Identifying leaks |

---

## How to Get the Most Value

### For Beginners
1. **After each hand**: Review Hand Analysis to learn from mistakes
2. **After 20 hands**: Use **Quick Session Analysis** to spot patterns
3. **Focus**: Study the top 1-2 concepts recommended

### For Intermediate Players
1. **After tough decisions**: Use Hand Analysis
2. **After 30 hands**: Use **Deep Session Analysis**
3. **Track progress**: Compare win rate across sessions

### For Advanced Players
1. **Selectively analyze**: Only critical hands
2. **After 50+ hands**: Use Deep Session Analysis with focus on:
   - Win rate breakdown by position
   - GTO baseline comparisons
   - Opponent exploitation strategies

---

## Cost Management

**Daily Budget Planning:**

| Usage Pattern | Daily Cost |
|---------------|------------|
| 10 hands analyzed + 1 session | ~$0.18 |
| 20 hands analyzed + 2 sessions | ~$0.36 |
| Session analysis only (every 20 hands) | ~$0.05 |

**Tips to Save:**
- Use Hand Analysis sparingly (only after difficult hands)
- Rely on Session Analysis every 20-30 hands
- Choose **Quick** for most sessions

---

## Troubleshooting

### "LLM analysis not available"
**Solution**: Add your Anthropic API key to `backend/.env`:
```bash
echo "ANTHROPIC_API_KEY=your_key_here" > backend/.env
```
Get your key at: https://console.anthropic.com/

### "Rate limit: Wait 30s"
**Cause**: Hand analysis has a 30-second cooldown per game
**Solution**: Wait or use Session Analysis instead

### "No hands to analyze"
**Cause**: Haven't played any hands yet
**Solution**: Play at least 1 hand for Hand Analysis, 10 hands for Session Analysis

### Session Analysis shows errors
**Check:**
1. API key is valid
2. Backend is running
3. You've played at least 10 hands

---

## API Key Setup

1. Get your API key: https://console.anthropic.com/
2. Create `backend/.env` file:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```
3. Restart backend server:
   ```bash
   cd backend && python main.py
   ```

**Security Note**: Never commit `.env` files to git. The `.gitignore` is already configured.

---

## FAQ

**Q: Why did you remove Deep Dive for hand analysis?**
A: Our evaluation showed Deep Dive was overkill for single hands. Session Analysis is where deep analysis shines.

**Q: What's the difference between Quick and Deep session analysis?**
A: Quick gives you overall stats and top 3 strengths/leaks (~2s). Deep provides specific hand examples, GTO comparisons, and detailed breakdown (~5-10s).

**Q: How many hands before I get useful session analysis?**
A: Minimum 10 hands, but 20-30 hands gives better pattern detection.

**Q: Can I analyze old hands?**
A: Not currently - analysis is for the current session only.

**Q: Do blinds ever stop increasing?**
A: No, they double every 10 hands indefinitely. This encourages aggressive play as the game progresses.

**Q: What if I don't have an API key?**
A: Basic rule-based analysis still works, but you won't get LLM-powered insights.

---

## What's Next

Phase 4.5 completes the AI coaching features. Future enhancements may include:
- Historical session tracking
- Personalized study plans
- Interactive follow-up questions
- Hand replay with AI narration

---

**Questions or Issues?** Check the main [README.md](../README.md) or [STATUS.md](../STATUS.md) for more details.
