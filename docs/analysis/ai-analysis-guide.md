# AI-Powered Analysis Guide

**Version:** 1.0
**Last Updated:** 2025-11-04
**Status:** Reference Document

---

## Purpose

This document describes how AI (Claude) can analyze backtest results to provide insights, pattern recognition, and optimization recommendations beyond basic statistics.

---

## Three-Layer Analysis Output

### Layer 1: Trade Journal (Raw Data)
- CSV with 29 columns per trade
- One row per day (including no-trade days)
- Generated automatically by backtest engine

### Layer 2: Summary Statistics
- Expectancy, win rate, profit factor
- Time-of-day breakdowns
- Volatility regime analysis
- Calculated by performance metrics module

### Layer 3: AI Analysis Report (This Layer)
- Pattern recognition
- Optimization suggestions
- Risk warnings
- Narrative insights

**Focus of this document:** Layer 3

---

## AI Analysis Workflow

### Input to AI:
1. Trade journal CSV (or DataFrame)
2. Summary statistics JSON/dict
3. Strategy specification (DP20 rules)

### AI Processing:
1. Load and analyze trade journal
2. Identify patterns and anomalies
3. Cross-reference with strategy rules
4. Generate markdown report with insights

### Output:
- Markdown report with findings
- Actionable recommendations
- Risk warnings

---

## Analysis Categories

### 1. Performance Patterns

**Questions AI Should Answer:**

- Which time buckets perform best/worst?
- Are there day-of-week patterns?
- Does performance degrade over time? (strategy decay)
- Are recent trades different from earlier trades?

**Example Analysis:**
```
**Time-of-Day Pattern Detected:**

Entries between 10:00-10:10 AM significantly outperform later entries:
- 10:00-10:10: 1.80R avg (72% win rate)
- 10:20-10:30: 0.30R avg (50% win rate)

**Hypothesis:** Earlier pullbacks represent stronger intraday trend, while later
pullbacks may be midday chop.

**Recommendation:** Consider narrowing entry window to 10:00-10:15 AM.
Expected impact: Reduce trade count by ~30%, increase expectancy to ~1.5R.
```

---

### 2. Volatility Regime Insights

**Questions AI Should Answer:**

- How does strategy perform in different volatility environments?
- Is there an ATR threshold above which performance degrades?
- Do high-volatility trades have different characteristics?

**Example Analysis:**
```
**Volatility Regime Analysis:**

Strategy shows strong volatility dependency:
- Low volatility (ATR < 0.5%): 1.60R avg, 70% win rate ✓
- High volatility (ATR > 0.7%): 0.20R avg, 40% win rate ✗

**Pattern:** In high volatility, trades frequently get stopped out (-1.0R) or
experience whipsaws (entry, stop, then move in intended direction).

**Recommendation:** Add volatility filter:
- Skip trading days when ATR at entry > 0.75% of price
- Expected impact: Remove 10 worst trades, improve expectancy to 1.45R
```

---

### 3. Stop Loss Analysis

**Questions AI Should Answer:**

- Are stops appropriately placed?
- What percentage of losers are full -1R losses (stopped out)?
- Are there "near miss" stops that would have been winners?
- Is there stop slippage beyond expected?

**Example Analysis:**
```
**Stop Loss Effectiveness:**

Current stops (1.2× ATR) appear well-calibrated:
- 14 of 17 losers (82%) were stopped out at -0.9R to -1.0R ✓
- Only 3 losers exceeded -1.1R (possible slippage or gaps)
- 12 trades (27%) came within 10% of stop but recovered to win

**Near-Miss Analysis:**
Winners that nearly stopped out averaged 2.1R (strong momentum after hold).

**Recommendation:** Keep current 1.2× ATR stop. Consider adding:
- Alert when trade reaches 0.8× stop distance (monitor for slippage)
- Use limit orders for stops to reduce slippage
```

---

### 4. Entry Quality Assessment

**Questions AI Should Answer:**

- Does reversal strength threshold (0.60) matter?
- Do entries closer to EMA20 perform better?
- Is there optimal "distance to EMA" in basis points?

**Example Analysis:**
```
**Entry Quality Insights:**

Reversal strength filter (60% body threshold) appears effective:
- Trades with reversal strength > 0.70: 1.8R avg (15 trades)
- Trades with reversal strength 0.60-0.70: 0.9R avg (30 trades)

**Pattern:** Stronger reversals (larger bodies) indicate more conviction,
leading to better follow-through.

**Distance to EMA:**
- Entries within 20 bps of EMA20: 1.6R avg ✓
- Entries >50 bps from EMA20: 0.5R avg ✗

**Recommendation:** Consider tightening reversal strength to 0.65 or adding
filter for max distance to EMA20 (e.g., entry price within 0.3% of EMA20).
```

---

### 5. Losing Streak Analysis

**Questions AI Should Answer:**

- What was longest losing streak?
- Were losing streaks clustered in time (market regime change)?
- What were characteristics of losing-streak trades?

**Example Analysis:**
```
**Losing Streak Identified:**

5-trade losing streak occurred Sep 15-21 (all losses, no trades skipped):
- All 5 trades were in high volatility environment (ATR > 0.7%)
- All 5 stopped out at -1.0R (no EOD exits)
- Market context: Fed announcement week, elevated VIX

**Risk Implication:**
With 5-trade streak and 1.0R risk per trade, need to survive -5R drawdown.
At $100 risk per trade, requires $500 buffer minimum.

**Recommendation:**
- Reduce position size or pause trading during major Fed events
- Consider adaptive position sizing based on recent win rate
```

---

### 6. Exit Timing Analysis

**Questions AI Should Answer:**

- Is 3:55 PM exit optimal?
- Do trades continue moving favorably after 3:55 PM?
- Would earlier exit improve consistency?

**Example Analysis:**
```
**Exit Timing Review:**

EOD exit at 3:55 PM appears reasonable:
- 18 trades (40%) were winning at 3:00 PM but gave back profits by 3:55 PM
- Average give-back: 0.4R
- 10 trades (22%) gained additional 0.6R between 3:00-3:55 PM

**Net effect:** Slight benefit to 3:55 PM vs 3:00 PM (~+0.1R per trade)

**MFE Analysis:**
Trades captured 68% of maximum favorable move on average, suggesting
exits are reasonable (not leaving huge profits on table).

**Recommendation:** Keep 3:55 PM exit. Optionally test profit target at 2.5R
for trades that reach this level earlier in the day.
```

---

### 7. Optimization Suggestions

**Based on all above analyses, prioritize recommendations:**

```
## Optimization Priority

**High Priority (Implement Next):**
1. **Add volatility filter:** Skip days when ATR > 0.75% of price
   - Impact: +0.25R expectancy, -10 trades
   - Effort: Low (1 line of code)

2. **Narrow time window to 10:00-10:15 AM:**
   - Impact: +0.30R expectancy, -12 trades
   - Effort: Low (change parameter)

**Medium Priority (Test Later):**
3. **Tighten reversal strength to 0.65:**
   - Impact: +0.15R expectancy, -8 trades
   - Effort: Low (change parameter)

4. **Add distance-to-EMA filter (< 0.3%):**
   - Impact: +0.20R expectancy, -7 trades
   - Effort: Low (add check in signal detection)

**Low Priority (Monitor):**
5. Test profit target at 2.5R
6. Test alternative exit times (3:00 PM vs 3:55 PM)
7. Adaptive position sizing based on vol regime
```

---

## AI Analysis Implementation

### Option A: Separate Analysis Script

```bash
# Run backtest first
python -m trading_playbook.cli.backtest --output trades.csv

# Then analyze with AI
python -m trading_playbook.cli.analyze trades.csv --ai-report
```

**Pros:**
- Keeps backtest engine simple
- AI analysis is optional
- Easy to iterate on analysis logic

**Cons:**
- Two-step process
- Need to save intermediate files

---

### Option B: Integrated Analysis

```python
# In backtest.py
results = run_backtest(...)

# Automatically generate AI analysis
if args.ai_analysis:
    report = generate_ai_analysis(results.trade_journal, results.summary_stats)
    print(report)
    save_report(report, 'output/analysis_report.md')
```

**Pros:**
- One-step workflow
- No intermediate files needed

**Cons:**
- Adds complexity to backtest engine
- AI analysis always coupled with backtest

**Recommendation:** Start with Option A, can add Option B later

---

## AI Analysis Function Signature

```python
def generate_ai_analysis(
    trade_journal: pd.DataFrame,
    summary_stats: dict,
    strategy_spec: dict
) -> str:
    """
    Generate AI-powered analysis report.

    Args:
        trade_journal: DataFrame with all trades (29 columns)
        summary_stats: Dict with calculated metrics
        strategy_spec: Dict with strategy parameters

    Returns:
        Markdown-formatted analysis report
    """
```

---

## Example AI Prompt Template

When calling Claude API for analysis:

```
You are a quantitative trading analyst. Analyze this backtest data for the DP20 strategy.

**Strategy Rules:**
- Entry: Pullback to EMA20, reversal with >60% body, confirmation
- Time window: 10:00-10:30 AM ET
- Stop: 1.2× ATR
- Exit: 3:55 PM ET

**Backtest Data:**
{trade_journal_summary}

**Summary Statistics:**
{summary_stats_json}

**Analysis Tasks:**
1. Identify performance patterns (time-of-day, volatility regimes)
2. Assess stop loss effectiveness (MAE analysis)
3. Evaluate entry quality (reversal strength, distance to EMA)
4. Analyze losing streaks and risk implications
5. Provide prioritized optimization recommendations

**Output Format:**
Markdown report with:
- Key findings (bullet points)
- Detailed pattern analysis
- Risk warnings
- Actionable recommendations (prioritized)
```

---

## Output Example

```markdown
# DP20 Strategy Analysis Report
**Period:** 2025-09-01 to 2025-11-04 (45 trading days)
**Generated:** 2025-11-04 17:30 ET

## 🎯 Key Findings

1. **Positive Edge Confirmed:** Expectancy of 1.20R indicates profitable strategy
2. **Time-of-Day Dependency:** Earlier entries (10:00-10:10) significantly outperform
3. **Volatility Sensitivity:** Performance degrades sharply in high volatility (ATR > 0.7%)
4. **Well-Calibrated Stops:** 82% of losers stopped out at expected -1.0R

## 📊 Performance Patterns

### Time-of-Day Analysis
[Detailed analysis as shown above...]

### Volatility Regime Impact
[Detailed analysis as shown above...]

## ⚠️ Risk Considerations

### Losing Streak
- Maximum consecutive losses: 5 trades
- Occurred during Fed announcement week (high volatility)
- Required $500 drawdown buffer at $100/trade risk

### Position Sizing Implications
With 1.20R expectancy and 5-trade max streak:
- Required capital: $5,000 minimum (10× max streak)
- Recommended: $10,000 (20× max streak for safety)

## 💡 Optimization Recommendations

[Prioritized list as shown above...]

## 📈 Next Steps

1. Implement volatility filter (high priority)
2. Test narrowed time window on new data
3. Re-run backtest with optimizations
4. Compare before/after expectancy

---

*Analysis generated by Claude AI*
*Review recommendations carefully before implementation*
```

---

## Limitations & Considerations

**AI Analysis Cannot:**
- Predict future performance
- Account for regime changes
- Guarantee optimization improvements
- Replace human judgment

**AI Analysis Can:**
- Identify patterns in historical data
- Suggest testable hypotheses
- Flag potential issues
- Prioritize optimization efforts

**Always:**
- Validate AI suggestions with out-of-sample testing
- Document all parameter changes
- Beware of overfitting (too many optimizations)
- Re-test after market regime changes

---

## Cost Considerations

**Using Claude API:**
- Cost: ~$0.01-0.05 per analysis (Haiku model)
- Can batch analyses (weekly/monthly)
- Cost-effective for deep insights

**Local vs API:**
- Local: Free, but need to craft prompts manually
- API: Small cost, fully automated

**Recommendation:** Start with manual analysis (copy/paste to Claude.ai), automate later if valuable

---

**Related Documents:**
- [Performance Metrics](./performance-metrics.md)
- [Backtest Engine](../system-design/backtest-engine.md)
- [DP20 Strategy Spec](../strategies/qqq_dp20_strategy_spec.md)
