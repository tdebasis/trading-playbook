# Daily Momentum Hybrid Trailing - Q1 2024 Test

**Test Date:** January 2 - March 31, 2024 (60 trading days)
**Status:** ❌ FAIL
**Return:** -1.94% (-$1,940)
**Win Rate:** 20% (1W / 4L / 5 total)
**Max Drawdown:** -2.49%

---

## Executive Summary

The Hybrid Trailing strategy **failed** in Q1 2024 with a -1.94% loss and dismal 20% win rate. Only 5 trades over 3 months indicates scanner too restrictive or poor market environment for breakouts. The single winner (NVDA +5.9%) was overwhelmed by 4 losers, including a -8% hard stop on BNTX.

**Verdict:** Strategy failed validation. Low trade count and poor win rate suggest either entry logic needs refinement or Q1 2024 was not conducive to breakout strategies.

---

## Strategy Configuration

### Entry Logic (Daily Breakout Scanner)

**Universe:**
27 growth stocks (Tech, Semiconductors, Mega-Caps, Biotech, Fintech)

**Filters:**
1. **Price Quality:** >$10
2. **Trend Filter:** Close > SMA20 > SMA50
3. **Relative Strength:** Within 25% of 52-week high
4. **Base Pattern:** 10-90 day consolidation with <12% volatility
5. **Breakout:** Close > consolidation high
6. **Volume:** 1.2x average (or 0.8x for mega-caps)

**Timeframe:** Daily (End-of-Day)

### Exit Logic (Hybrid Trailing)

**Exit Rules:**
1. **Hard Stop:** -8% from entry
2. **Trailing Stop:** Hybrid tightening system:
   - Base: 2× ATR below highest close
   - Tightens to 1× ATR at +10% profit
   - Tightens to 5% at +15% profit
3. **Time Stop:** 15-17 days maximum hold (varies by version)

**Note:** This appears to be an earlier version before "Smart Exits" with fewer exit rules (no MA break, no lower high detection).

### Risk Management

- **Starting Capital:** $100,000
- **Position Sizing:** 30% capital per trade
- **Max Positions:** 3 concurrent
- **Max Risk Per Trade:** 8% position risk

---

## Performance Metrics

### Returns
- **Total Return:** -$1,940 (-1.94%)
- **Annualized:** ~-7.8% (extrapolated)
- **Best Trade:** NVDA +$1,237 (+5.9%)
- **Worst Trade:** BNTX -$2,400 (-8.0%)

### Trade Statistics
- **Total Trades:** 5 (only!)
- **Winners:** 1 (20%)
- **Losers:** 4 (80%)
- **Average Win:** +$1,237 (+5.9%)
- **Average Loss:** -$794 (-2.3%)
- **Profit Factor:** 0.39x (terrible)
- **Expectancy:** -$388 per trade

### Risk Metrics
- **Max Drawdown:** -2.49% (-$2,492)
- **Drawdown Date:** January 12, 2024
- **Recovery:** Never recovered (ended down)
- **Volatility:** Long flat periods (no trades)

### Time Analysis
- **Average Hold:** 11.6 days
- **Winner Hold:** 3 days (NVDA quick profit)
- **Loser Hold:** 13.8 days average (too long)
- **Time Stops:** 3 out of 5 trades (60%) hit time limit

---

## Trade Details

### The Winner

| Symbol | Entry → Exit | P&L | Hold | Exit Reason |
|--------|--------------|-----|------|-------------|
| NVDA | $522.53 → $553.46 | +$1,237 (+5.9%) | 3 days | TRAILING_STOP |

**Analysis:** NVDA was the only success - caught a strong 3-day move and trailing stop locked in +5.9% profit. This shows the exit logic CAN work when entry is good.

### The Losers

| # | Symbol | Entry → Exit | P&L | Hold | Exit Reason |
|---|--------|--------------|-----|------|-------------|
| 1 | BNTX | $112.35 → $103.36 | -$2,400 (-8.0%) | 9 days | HARD_STOP |
| 2 | AMZN | $171.81 → $169.51 | -$396 (-1.3%) | 15 days | TIME |
| 3 | META | $474.99 → $473.32 | -$72 (-0.4%) | 15 days | TIME |
| 4 | MSFT | $425.22 → $420.72 | -$311 (-1.1%) | 16 days | END_OF_TEST |

**Analysis:**
- **BNTX disaster:** Immediate -8% hard stop (worst loss)
- **Time stops:** 3 trades went nowhere for 15+ days (dead capital)
- **Choppy entries:** All Feb/March entries failed to follow through

---

## Equity Curve Analysis

**Starting Capital:** $100,000
**Peak Capital:** $100,000 (Day 1)
**Ending Capital:** $98,060
**Max Drawdown:** -$2,492 (-2.49%, January 12)

**Key Observations:**
1. **Started at peak** - Never recovered from early losses
2. **Long flat periods** - Weeks without trades (capital idle)
3. **Three distinct periods:**
   - Jan 3-12: -$1,162 (BNTX stop, NVDA win)
   - Feb 5-20: -$467 (AMZN, META time stops)
   - Mar 15-31: -$311 (MSFT still open)

**Drawdown Periods:**
- Jan 3-12: -2.49% (BNTX -8% hit)
- Never recovered

---

## Analysis & Findings

### What Went Wrong ❌

1. **Only 5 Trades in 3 Months**
   - Scanner way too restrictive
   - Missed opportunities sitting in cash
   - Need 15-20 trades minimum for statistically valid test

2. **Terrible Win Rate (20%)**
   - 4 out of 5 trades lost money
   - Suggests: Poor entry timing or bad market environment
   - Below 40% is unacceptable for breakout strategy

3. **BNTX Catastrophic Loss**
   - First trade hit -8% hard stop
   - Biotech stock (high volatility, bad for breakouts?)
   - Started test with immediate loss (psychological hit)

4. **Time Stops Dominating**
   - 60% of trades hit time limit
   - Means: Entries had no follow-through
   - Breakouts fizzled → sideways → exit

5. **Q1 2024 Market Regime**
   - Possible choppy/range-bound period
   - Breakouts failing across the board
   - Need to check SPY performance same period

### What Worked (Barely) ✅

1. **NVDA Winner**
   - Trailing stop caught +5.9% in 3 days
   - Shows system CAN work with strong trend
   - Entry timing was good on this one

2. **Hard Stop Protection**
   - BNTX limited to -8% (didn't run away)
   - System protected capital from worse losses

3. **Time Stop Prevented Worse**
   - AMZN, META could have gone -8% too
   - Time stop cut small losses early

### Edge Quality Assessment 📊

**Verdict:** **NO EDGE DETECTED**

- Win rate 20% (need >45%)
- Profit factor 0.39x (need >1.2x)
- Expectancy -$388 per trade (losing system)
- Sample size tiny (5 trades)

**Confidence Level:** **FAIL** - Do not trade this configuration

---

## Key Findings & Insights

### 1. Scanner Too Restrictive

**Problem:** Only 5 breakouts found in 60 trading days across 27 stocks.

**Expected:** Should find 15-20 setups minimum (1 every 3-4 days).

**Possible Causes:**
- Consolidation filters too tight (10-90 days, <12% vol)
- Relative strength filter rejecting too many
- Market had few quality bases in Q1 2024

**Fix:** Relax filters or expand universe to 50+ stocks.

### 2. Entry Timing Issues

**Observation:** 4 out of 5 entries immediately failed or went sideways.

**Analysis by Date:**
- **Jan 3 (BNTX):** Instant failure (-8% in 9 days)
- **Jan 9 (NVDA):** Only winner (perfect timing)
- **Feb 5 (AMZN, META):** Both flat for 15 days
- **Mar 15 (MSFT):** Immediate weakness

**Hypothesis:** Entries happening on weak breakouts without confirmation.

**Fix Needed:** Add volume thrust requirement or wait for follow-through day.

### 3. Hybrid Trailing Not Tested Properly

The trailing stop only triggered once (NVDA). Can't evaluate effectiveness with 1 sample.

**Need:** 20+ trades with various profit levels to test tightening logic.

### 4. Market Regime Mattered

Q1 2024 may have been poor environment for breakouts. To validate:
- Need to test same strategy on Q1 2023, Q1 2025
- Check if other quarters perform better
- If all quarters fail → strategy broken

---

## Comparison to Other Tests

*(Note: No direct comparison data for same strategy different period)*

**vs Smart Exits Q3 2025:**
- Smart Exits: +1.87%, 54.5% win rate, 11 trades
- Hybrid Trailing Q1 2024: -1.94%, 20% win rate, 5 trades

**Difference:**
1. Smart Exits had more trades (11 vs 5)
2. Smart Exits had better market (or better scanner)
3. Smart Exits added MA break and lower high exits

**Conclusion:** Either Q1 2024 was terrible for breakouts, or Smart Exits is superior strategy.

---

## Next Steps & Recommendations

### Do NOT Trade This Configuration

**Critical Issues:**
1. ❌ Win rate 20% (unacceptable)
2. ❌ Profit factor 0.39x (losing system)
3. ❌ Only 5 trades (can't validate)

### Required Fixes Before Retest

1. **Expand Universe**
   - Add 20-30 more stocks (to 50 total)
   - Include mid-caps (more volatility)
   - Test on Nasdaq 100 stocks

2. **Relax Scanner Filters**
   - Reduce consolidation requirement to 5-60 days
   - Allow up to 15% volatility in base
   - Lower volume requirement to 1.0x

3. **Add Entry Confirmation**
   - Require 2nd day above breakout
   - Volume surge >2x on breakout day
   - Gap up after breakout (strength signal)

4. **Test Across Multiple Periods**
   - Q2, Q3, Q4 2024
   - Bull market (2023)
   - Bear market (2022)
   - Need 50+ trades for validation

5. **Upgrade to Smart Exits**
   - Add MA break exit
   - Add lower high detection
   - Smart Exits clearly better (Q3 2025 proof)

### Questions to Answer

1. **Was Q1 2024 just a bad period?**
   - Test same strategy Q2-Q4 2024
   - If all quarters fail → strategy broken

2. **Is scanner finding best setups?**
   - Manual review of rejected candidates
   - Are we missing obvious breakouts?

3. **Should we abandon biotech stocks?**
   - BNTX was worst loss
   - Too volatile for daily breakouts?

4. **What was SPY doing Q1 2024?**
   - If SPY was down, breakouts won't work
   - Need trending market for momentum

---

## Lessons Learned

### For Strategy Development

1. **Sample Size Matters**
   - 5 trades is not enough to validate
   - Need minimum 30 trades, ideally 50+
   - Don't trust results with <20 trades

2. **Scanner Restrictions Hurt**
   - Being too selective = missed opportunities
   - Better to have 30 setups and pick best 10
   - Sitting in cash is lost opportunity cost

3. **Market Regime Crucial**
   - Breakout strategies need trending market
   - Choppy/sideways market kills breakouts
   - Must test across bull, bear, sideways periods

4. **First Loss Sets Tone**
   - BNTX -8% on day 3 = started in hole
   - Hard to recover from early drawdown
   - Psychological impact on testing

### For Future Tests

1. ✅ Run longer periods (6-12 months minimum)
2. ✅ Demand 30+ trades for validation
3. ✅ Test across different market regimes
4. ✅ Always check SPY performance for context
5. ✅ Upgrade to Smart Exits (better rules)

---

## Conclusion

The **Hybrid Trailing strategy FAILED** in Q1 2024 with a -1.94% loss, 20% win rate, and only 5 trades. This test is **inconclusive** due to tiny sample size, but early indications are poor.

**Critical Issues:**
- ❌ Scanner too restrictive (only 5 setups)
- ❌ Win rate 20% (4/5 losers)
- ❌ No statistical significance (need 10x more trades)

**Possible Explanations:**
1. Q1 2024 was choppy market (bad for breakouts)
2. Entry logic needs improvement (no confirmation)
3. Scanner filters too tight (rejecting good setups)
4. Biotech stocks don't work (BNTX disaster)

**Recommendation:** **DO NOT TRADE.** Expand universe, relax filters, upgrade to Smart Exits, and retest on 6-12 months before considering live.

**Status for Production:** **RED** - Failed validation. Needs major overhaul before retry.

---

*Report Generated: November 6, 2025*
*Data Source: q1_2024_results.json*
*Next Action: Test Smart Exits on Q1 2024 for comparison*
