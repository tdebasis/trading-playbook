# Strategy Comparison - Exit Methods

**Last Updated:** November 6, 2025
**Purpose:** Compare different exit strategy variations to determine optimal approach

---

## Quick Comparison Table

| Strategy | Return | Win Rate | Trades | Max DD | Avg Hold | Profit Factor | Status |
|----------|--------|----------|--------|--------|----------|---------------|--------|
| **Smart Exits** (Q3 2025) | **+1.87%** | **54.5%** | 11 | -2.34% | 9.6 days | 1.56x | ✅ PASS |
| **Hybrid Trailing** (Q1 2024) | **-1.94%** | **20.0%** | 5 | -2.49% | 11.6 days | 0.39x | ❌ FAIL |
| Scaled Exits | TBD | TBD | TBD | TBD | TBD | TBD | 🔄 Testing |

---

## Strategy Descriptions

### 1. Smart Exits (Adaptive Price Action)

**Philosophy:** Let price action tell us when to exit. Multiple exit rules adapt to market conditions.

**Exit Rules:**
1. **Hard Stop:** -8% (always active)
2. **Trailing Stop:** Adaptive tightening
   - Base: 2× ATR below highest close
   - → 1× ATR at +10% profit
   - → 5% at +15% profit
3. **MA Break:** Close < 5-day SMA (if profit <3%)
4. **Lower High:** Momentum fading after +5%
5. **Time Stop:** 17 days

**Strengths:**
- ✅ Adapts to different market conditions
- ✅ Multiple exit reasons (flexibility)
- ✅ Locks profits on extended moves (trailing)
- ✅ Cuts losers when trend breaks (MA)
- ✅ Catches momentum fades (lower high)

**Weaknesses:**
- ❌ Complex (5 rules to manage)
- ❌ MA break can exit winners too early
- ❌ Requires calculating multiple indicators

**Best For:** Trending markets with clear price action

**Test Results (Q3 2025):**
- Return: +1.87%
- Win Rate: 54.5%
- Trades: 11
- Exit breakdown: TIME 36%, MA_BREAK 18%, LOWER_HIGH 18%, TRAILING 9%, HARD_STOP 9%

---

### 2. Hybrid Trailing (Simpler Adaptive)

**Philosophy:** Let profits run with adaptive trailing stops. Fewer rules, simpler execution.

**Exit Rules:**
1. **Hard Stop:** -8%
2. **Trailing Stop:** Hybrid tightening
   - Base: 2× ATR
   - → 1× ATR at +10%
   - → 5% at +15%
3. **Time Stop:** 15-17 days

**Strengths:**
- ✅ Simple (only 3 rules)
- ✅ Adaptive stops adjust to volatility
- ✅ Easy to code/execute

**Weaknesses:**
- ❌ No trend break detection (MA)
- ❌ No momentum fade detection (lower high)
- ❌ Holds losers full time (no early exit)

**Best For:** Strong trending markets (when entries are solid)

**Test Results (Q1 2024):**
- Return: -1.94%
- Win Rate: 20%
- Trades: 5 (scanner issue)
- Exit breakdown: TIME 60%, HARD_STOP 20%, TRAILING 20%

**Note:** Poor results likely due to bad entries (scanner too restrictive) and choppy Q1 2024 market, not necessarily the exit strategy itself.

---

### 3. Scaled Exits (Profit Taking)

**Philosophy:** Bank profits incrementally, let final piece run for home runs.

**Exit Rules:**
1. **Scale 25% @ +8%** - Lock first gains
2. **Scale 25% @ +15%** - 50% position secured
3. **Scale 25% @ +25%** - 75% secured
4. **Final 25%:** Smart exits logic
   - Trailing stops
   - MA break
   - Time stop: 20 days

**Strengths:**
- ✅ Secures profits (reduces regret)
- ✅ Lowers position risk as price rises
- ✅ Lets final piece capture outliers
- ✅ Psychological edge (always banking wins)

**Weaknesses:**
- ❌ Misses full move if winner runs
- ❌ More complex (tracking partial exits)
- ❌ Transaction costs (more exits)

**Best For:** Choppy markets or lower conviction entries

**Test Results:** Currently testing (no data yet)

---

## Key Differences

| Feature | Smart Exits | Hybrid Trailing | Scaled Exits |
|---------|-------------|-----------------|--------------|
| **Exit Rules** | 5 (complex) | 3 (simple) | 4 + scales (most complex) |
| **Profit Taking** | None (all-or-nothing) | None | Yes (25% increments) |
| **Trend Detection** | Yes (MA break) | No | Yes (on final 25%) |
| **Momentum Detection** | Yes (lower high) | No | Yes (on final 25%) |
| **Partial Exits** | No | No | Yes (3 scale-outs) |
| **Time Stop** | 17 days | 15-17 days | 20 days (longer) |
| **Best Use Case** | Trending markets | Simple execution | Choppy markets |

---

## Performance Analysis

### Smart Exits vs Hybrid Trailing (Different Periods)

**Note:** Cannot directly compare (different test periods), but can draw insights:

| Metric | Smart Exits Q3 2025 | Hybrid Trailing Q1 2024 | Winner |
|--------|---------------------|-------------------------|--------|
| Return | +1.87% | -1.94% | Smart Exits |
| Win Rate | 54.5% | 20.0% | Smart Exits |
| Trade Count | 11 | 5 | Smart Exits |
| Max DD | -2.34% | -2.49% | Smart Exits |
| Profit Factor | 1.56x | 0.39x | Smart Exits |

**Conclusion:** Smart Exits clearly superior, but period difference matters.

**Q1 2024 Issues:**
- Scanner too restrictive (5 trades)
- Possible choppy market
- BNTX biotech disaster (-8%)

**Q3 2025 Success:**
- More trades (11)
- Better market regime?
- MA/LOWER_HIGH exits added value

---

## Exit Reason Analysis

### Smart Exits (Q3 2025)
- **TIME (36%):** 4 trades - Hit 17-day limit
- **MA_BREAK (18%):** 2 trades - Trend reversed
- **LOWER_HIGH (18%):** 2 trades - Momentum faded
- **TRAILING_STOP (9%):** 1 trade - Profit locked
- **HARD_STOP (9%):** 1 trade - Risk limit
- **END_OF_TEST (18%):** 2 trades - Still open

**Insight:** Multiple exit types firing = strategy working as designed.

### Hybrid Trailing (Q1 2024)
- **TIME (60%):** 3 trades - Hit limit (sideways)
- **HARD_STOP (20%):** 1 trade - BNTX disaster
- **TRAILING_STOP (20%):** 1 trade - NVDA winner

**Insight:** Too many time stops = entries lacking follow-through.

---

## Risk-Adjusted Returns

### Sharpe Ratio Comparison

**Smart Exits Q3 2025:**
- Return: +1.87% (3 months)
- Max DD: -2.34%
- Return/DD: 0.80

**Hybrid Trailing Q1 2024:**
- Return: -1.94%
- Max DD: -2.49%
- Return/DD: -0.78 (negative)

**Winner:** Smart Exits (positive risk-adjusted returns)

---

## When to Use Each Strategy

### Use Smart Exits When:
✅ Strong trending market (breakouts have follow-through)
✅ You want adaptive exits (price action driven)
✅ Willing to manage 5 exit rules
✅ High conviction entries

**Example:** Bull market, tech sector leading, clean breakouts

### Use Hybrid Trailing When:
✅ Simple execution preferred
✅ Very strong trends (entries are perfect)
✅ Don't need early exit signals

**Example:** Parabolic moves, momentum surges

**Caution:** Q1 2024 test failed, may not be robust enough

### Use Scaled Exits When:
✅ Choppy market (uncertainty)
✅ Want to secure profits incrementally
✅ Lower conviction on extended moves
✅ Psychological comfort from banking wins

**Example:** Range-bound market, sector rotation, earnings season

---

## Hypothetical Same-Period Comparison

**If all three strategies ran Q3 2025 (hypothetical):**

| Strategy | Expected Return | Expected WR | Rationale |
|----------|----------------|-------------|-----------|
| Smart Exits | +1.87% | 54.5% | Actual result |
| Hybrid Trailing | +0.5% to +1.0% | 45-50% | Fewer exit rules, some winners exit too late |
| Scaled Exits | +1.2% to +1.5% | 55-60% | Secures profits, but misses full moves |

**Best Case Scenario:**
- Scaled Exits might have higher win rate (more exits = more winners)
- Smart Exits might have higher return (captures full moves)

**Need Real Data:** Run all three on same period for valid comparison.

---

## Recommendations

### For Live Trading (Current State)

**1st Choice: Smart Exits** ✅
- Proven positive in Q3 2025
- Most robust (5 exit rules)
- Handles various scenarios

**2nd Choice: Scaled Exits** 🔄
- Test in progress
- Psychologically easier (bank wins)
- Lower risk profile

**3rd Choice: Hybrid Trailing** ❌
- Failed Q1 2024
- Needs validation on multiple periods
- Too simple (missing key exits)

### For Further Testing

1. **Run all three strategies on Q4 2024** (same period comparison)
2. **Test on bear market** (see which protects best)
3. **Test on bull market** (see which captures most)
4. **50+ trades each** for statistical significance

### Parameter Optimization

**Smart Exits:**
- Test 20-day time stop (vs 17)
- Test 6% hard stop (vs 8%)
- Test 3-day MA (vs 5-day)

**Scaled Exits:**
- Test different scale levels: +10%, +20%, +30%?
- Test different percentages: 30/30/40 instead of 25/25/25/25?
- Test 2-scale vs 3-scale vs 4-scale

---

## Lessons Learned

### From Smart Exits Success (Q3 2025)
1. ✅ Multiple exit rules provide flexibility
2. ✅ MA break catches trend reversals
3. ✅ Lower high detects momentum fades
4. ✅ 17-day time stop prevents dead capital
5. ✅ Entry quality matters more than exit strategy

### From Hybrid Trailing Failure (Q1 2024)
1. ❌ Too few exit rules = holds losers too long
2. ❌ Scanner restrictions hurt (only 5 trades)
3. ❌ Time stops dominating = bad entries
4. ❌ No trend break detection = missed signals
5. ❌ Q1 2024 may have been bad period (retest needed)

### General Insights
1. **Sample size matters:** 5 trades insufficient, need 30+
2. **Market regime matters:** Breakouts need trending markets
3. **Exit strategy can't fix bad entries:** GIGO principle
4. **Trade frequency important:** Sitting in cash = opportunity cost
5. **Adaptive > Fixed:** Market conditions change, exits should too

---

## Next Steps

### Immediate Actions
1. ✅ Complete Scaled Exits test (Q3 2025)
2. ✅ Run all three strategies on Q4 2024 (apples-to-apples)
3. ✅ Test Smart Exits on Q1 2024 (vs Hybrid Trailing)

### Medium Term
1. Parameter sweeps for each strategy
2. Machine learning optimization (gradient-free)
3. Walk-forward validation (avoid overfitting)
4. Portfolio of strategies (combine best of each)

### Questions to Answer
1. **Does Scaled Exits reduce drawdown?** (vs Smart)
2. **Which works best in bear markets?**
3. **What's the optimal number of scale-outs?** (2? 3? 4?)
4. **Can we combine strategies?** (Scale on weak setups, Smart on strong?)

---

## Conclusion

**Current Winner:** **Smart Exits** (only strategy with positive validated results)

**Key Findings:**
- Smart Exits: +1.87%, 54.5% WR, 1.56x PF ✅
- Hybrid Trailing: -1.94%, 20% WR, 0.39x PF ❌
- Scaled Exits: Testing in progress 🔄

**Recommendation:** Use **Smart Exits** for live trading (yellow light - needs more validation). Continue testing Scaled Exits as alternative. Improve or abandon Hybrid Trailing.

**Confidence Level:**
- Smart Exits: **Moderate** (1 test, 11 trades)
- Scaled Exits: **Unknown** (no data yet)
- Hybrid Trailing: **Low** (failed 1 test, tiny sample)

**Next Report:** Q4 2024 three-way comparison (all strategies, same period)

---

*Report Generated: November 6, 2025*
*Data Sources: smart_exits_results.json, q1_2024_results.json*
*Status: Partial comparison (different test periods)*
