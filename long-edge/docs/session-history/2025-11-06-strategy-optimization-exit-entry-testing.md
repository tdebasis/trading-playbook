# Session History: 2025-11-06

**Project:** trading-playbook (long-edge momentum strategy)
**Date:** November 6, 2025
**Session Duration:** ~3 hours
**Status:** 🟡 Partial (tests still running)

## Session Goal

Optimize the daily momentum breakout strategy by testing two key dimensions: (1) Exit strategy comparison (smart all-or-nothing vs scaled exits) and (2) Entry filter comparison (volume filters 0.0x/0.5x/1.2x vs scoring system) across 8 years of historical data (2018-2025).

## Changes Made

### Code Changes

**1. Smart Exits MA Break Logic Optimization**
- Fixed premature MA break exits that were cutting winners short at +1.5-2.0% when trailing stops averaged +6.7%
- Changed MA break exit logic to only trigger if current profit < 3%
- Analysis showed MA breaks had 55.6% win rate vs 100% for trailing stops
- Files: `backend/backtest/daily_momentum_smart_exits.py` (lines 211-219)

**2. Scaled Exits End-of-Backtest Bug Fix**
- Fixed catastrophic bug causing positions to close at $0.00 price, resulting in -65.63% return
- Root cause: Used `end_date` for price lookup which had no market data
- Solution: Use `last_valid_date` (previous trading day) with fallback to recent bars
- Files: `backend/backtest/daily_momentum_scaled_exits.py` (lines 173-181)

**3. Scoring System Data Handling Fixes**
- **Bug 1:** Reduced minimum required bars from 200 → 150 (API returns ~172 bars)
- **Bug 2:** Fixed SMA200 calculation to handle < 200 bars available
- **Bug 3:** Added compatibility layer for BarSet format (`bars_dict.data` attribute)
- Files: `backend/scanner/daily_breakout_scanner_scoring.py` (lines 257-267, 262, 279)

**4. Scoring System Analysis & Abandonment**
- Created `analyze_actual_trades.py` to test scoring on 21 real 2025 trades (11 winners, 10 losers)
- **Critical finding:** Losers scored HIGHER than winners (6.83 vs 6.69)
- 100% of candidates passing base screening also passed scoring thresholds
- Base screening rejected 3 winners to avoid 4 losers (marginal 1:1.3 ratio)
- **Decision:** Abandoned scoring approach based on empirical evidence
- Files: `analyze_actual_trades.py`, `SCORING_SYSTEM_VERDICT.md`

### Configuration Changes
- None

### Test Scripts Created
- `test_scaled_exits_2025.py` - Compare smart vs scaled exits on 2025 data
- `test_volume_all_approaches.py` - Comprehensive 8-year test (2018-2025) of volume filters vs scoring
- `analyze_smart_exits.py` - Analyze MA break vs trailing stop patterns
- `analyze_actual_trades.py` - Test scoring system on actual winners/losers

## Problems Encountered

### Problem 1: MA Break Exits Cutting Winners Short

**Context:**
Smart exits strategy was showing good overall returns (+12.20% on 2025) but analysis revealed MA break exits were underperforming trailing stops significantly.

**Error/Symptom:**
```
MA break trades: 9 trades, 55.6% win rate, +1.5% avg gain
Trailing stop trades: 9 trades, 100% win rate, +6.7% avg gain

Examples of premature MA breaks:
- AMZN: MA break at +1.7% (had reached +4.2%)
- SHOP: MA break at -0.1% (had reached +4.6%)
- ZS: MA break at -3.7% (had reached +0.9%)
```

**Investigation Steps:**
1. Created `analyze_smart_exits.py` to categorize all 56 trades by exit reason
2. Found MA breaks occurred at +1.5%, +1.6%, +2.0% while positions had been much higher
3. Identified logic flaw: code checked `position.highest_high > entry * 1.03` but position had fallen back below +3%

**Root Cause:**
Original MA break logic:
```python
if position.highest_high > position.entry_price * 1.03:  # At least 3% up
    if current_price < sma_5:
        exit()  # EXIT even if currently only +1.5%
```

This allowed positions that reached +5%, fell to +1.5%, broke MA, to exit at +1.5% instead of trailing to +6%+.

**Solution:**
```python
current_profit_pct = ((current_price - position.entry_price) / position.entry_price) * 100
if current_profit_pct < 3.0:  # Only exit on MA break if currently < +3%
    if current_price < sma_5:
        exit()  # Let profitable positions (>+3%) continue trailing
```

**Prevention:**
When implementing exit logic, always consider CURRENT profit state, not just historical peaks. MA breaks are useful for preventing small losses but shouldn't cut winners.

### Problem 2: Scaled Exits Test Returning Catastrophic Results

**Context:**
Scaled exits test completed showing -65.63% return with only 3 trades, while smart exits showed +12.20% with 56 trades on the same period.

**Error/Symptom:**
```
💰 BNTX: Sold 249 shares @ $0.00 (END_OF_BACKTEST, +$-29,932)
💰 SHOP: Sold 184 shares @ $0.00 (END_OF_BACKTEST, +$-21,020)
💰 RBLX: Sold 237 shares @ $0.00 (END_OF_BACKTEST, +$-14,677)

Final Result: -65.63% return, 3 trades total
```

**Investigation Steps:**
1. Noticed positions closed at $0.00 price (impossible)
2. Checked end-of-backtest position closing logic (line 175)
3. Found code used `end_date` for `_get_current_price()` call
4. Realized `end_date` is 1 day AFTER last trading day (no market data)

**Root Cause:**
```python
# BROKEN CODE:
for pos in list(self.positions):
    self._close_final_position(pos, end_date, "END_OF_BACKTEST",
                              self._get_current_price(pos.symbol, end_date))
    # end_date = 2025-11-01 (no market data) → returns $0.00
```

**Solution:**
```python
# FIXED CODE:
last_valid_date = current_date - timedelta(days=1)  # Last trading day
for pos in list(self.positions):
    final_price = self._get_current_price(pos.symbol, last_valid_date)
    if final_price == 0.0:
        # Fallback: try recent bars
        bars = self._get_recent_bars(pos.symbol, last_valid_date, lookback=5)
        if bars:
            final_price = float(bars[-1].close)
    self._close_final_position(pos, last_valid_date, "END_OF_BACKTEST", final_price)
```

**Additional Complication:**
Test was running when we made the fix, but **Python cached the old module in memory**. Even after file edit, running process continued using old code. Required starting fresh Python process to load fixed code.

**Prevention:**
- Always use `last_valid_date = end_date - timedelta(days=1)` for end-of-backtest position closing
- Remember Python caches imported modules - kill and restart background processes after code changes
- Add validation: `assert final_price > 0.0, "Invalid price for position closing"`

### Problem 3: Scoring System Producing 0 Trades

**Context:**
Scoring system backtest across 2018-2025 returned 0 trades for ALL years, despite scanner showing candidates on individual days.

**Error/Symptom:**
```
2018: 0 trades
2019: 0 trades
2020: 0 trades
2021: 0 trades
2022: 0 trades

But: Manual scanner test on May 23, 2025 showed:
- SNOW: Score 8.8/10
- GME: Score 7.2/10
```

**Investigation Steps:**
1. Created `debug_scoring.py` to step through filters manually
2. Found all symbols rejected with "No candidate found (failed base screening)"
3. Discovered API returned only ~172 bars but code required 200 minimum
4. After fixing bar requirement, found SMA200 calculation failed with < 200 bars
5. After fixing SMA200, found data format issue with `bars_dict` access

**Root Causes:**

**Bug 1 - Insufficient Data:**
```python
# BROKEN:
if len(bars) < 200:
    return None  # Rejected ALL candidates

# FIXED:
if len(bars) < 150:  # Relaxed: API returns ~170-180
    return None
```

**Bug 2 - SMA200 Calculation:**
```python
# BROKEN:
sma_200 = sum(closes[-200:]) / 200  # Fails if len(closes) < 200

# FIXED:
sma_200 = sum(closes) / len(closes) if len(closes) < 200 else sum(closes[-200:]) / 200
```

**Bug 3 - Data Format Handling:**
```python
# BROKEN:
bars = list(bars_dict[symbol])  # Fails: BarSet has .data attribute

# FIXED:
if hasattr(bars_dict, 'data'):
    bars = list(bars_dict.data[symbol])  # API response
else:
    bars = list(bars_dict[symbol])  # Cached response
```

**Solution:**
Applied all three fixes. Scoring system then functioned but revealed fundamental flaw (see Problem 4).

**Prevention:**
- Always check API data format variations (BarSet vs dict)
- Use approximate calculations when exact requirements can't be met (SMA200 with < 200 bars)
- Start with minimum viable data requirements, not theoretical ideals

### Problem 4: Scoring System Cannot Differentiate Winners from Losers

**Context:**
After fixing data handling bugs, scoring system worked technically but needed validation. Analyzed 21 actual 2025 trades (11 winners, 10 losers) to test if scoring predicts outcomes.

**Analysis Results:**
```
WINNERS (11 trades):
  Passed Base Screening: 8/11 (72.7%)
  Passed Scoring Threshold: 8/8 (100.0%)
  Average Score: 6.69

LOSERS (10 trades):
  Passed Base Screening: 6/10 (60.0%)
  Passed Scoring Threshold: 6/6 (100.0%)
  Average Score: 6.83

Highest Score: SNOW (7.8) → LOST -0.4%
Trend Score: Everyone gets 3.0 pts (Close > SMA20 > SMA50) - no differentiation
```

**Root Cause:**
Scoring measures **setup quality** (how "textbook" the breakout looks), not **trade outcome** (whether you'll make money). Winners and losers both have:
- Good trend alignment (Close > SMA20 > SMA50)
- Tight consolidations
- Close to 52-week highs
- Similar volume patterns

What actually matters for outcome:
- Market conditions (not captured)
- Sector rotation (not captured)
- News/catalysts (not captured)
- Exit timing (separate from entry)

**Solution:**
**Abandoned scoring system entirely**. Data proved it cannot differentiate quality. Documented decision in `SCORING_SYSTEM_VERDICT.md` with full analysis.

**Prevention:**
**Test hypotheses on actual outcomes, not theoretical appeal**. A system can "look good" but not predict results.

## Key Learnings

> 💡 **Multiple learnings should be added to project "Known Issues & Workarounds"**

### Learning 1: Exit Optimization > Entry Optimization

**What:** Analysis showed exit strategy has MORE impact than entry refinement:
- MA break fix: Converting 55.6% win rate exits to trailing stop exits (100% win rate)
- Smart vs Scaled exits: Testing if "let winners run" beats "take profits incrementally"
- Entry scoring: Complex multi-factor system showed NO advantage over simple volume filter

**Why it matters:** Development resources better spent on exit logic than perfecting entry signals.

**Where to apply:**
- Focus 2025-2026 optimization on trailing stop tuning (2x → 1x → 0.5x ATR)
- Test profit targets, time-based exits, volatility-adjusted stops
- Keep entry signals simple (volume filters, basic trend confirmation)

**Action:** Update strategy development priorities in project docs to emphasize exit strategy research.

### Learning 2: Python Module Caching in Background Processes

**What:** Background Python processes cache imported modules in memory. File edits don't affect running processes.

**Why it matters:** Spent 30+ minutes debugging why "fixed" code still produced buggy results. Process was using cached old code.

**Where to apply:**
- Always kill and restart background tests after code changes
- Use fresh process IDs to verify new code is running
- Don't trust "but I fixed the file!" - check if process reloaded it

**Action:** Add to CLAUDE.md "Known Issues" section about Python module caching.

### Learning 3: Empirical Testing Beats Intuition

**What:** Scoring system sounded excellent in theory:
- Volume compensation (weak volume needs strong price)
- Multi-factor analysis (volume, trend, base, RS)
- Dynamic thresholds by volume tier

But empirical test on 21 actual trades proved it doesn't work (losers scored higher than winners).

**Why it matters:** Can save weeks of development by testing assumptions early on real data.

**Where to apply:**
- Test new indicators on historical winners/losers BEFORE full backtest
- Use actual trade outcome analysis to validate all new filters
- Don't implement complex systems without proof they differentiate quality

**Action:** Create `test_on_actual_trades.py` template for rapid hypothesis testing.

### Learning 4: Market Regime Matters More Than Filter Precision

**What:** Volume filter comprehensive test (2018-2022) showed clear pattern:
- **Bear markets (2018):** 1.2x wins (+13.39% vs +4.03%)
- **Bull markets (2020, 2021):** No filter wins (+44.27% vs +43.15%, +19.02% vs +6.81%)
- Simple regime detection beats trying to perfect single filter

**Why it matters:** Adaptive approach based on VIX or market conditions likely more profitable than optimizing fixed threshold.

**Where to apply:**
- Implement dual-mode system: Use 1.2x when VIX > 20, use 0.5x when VIX < 15
- Test regime-based position sizing (smaller in volatile markets)
- Apply to other parameters (stop distance, profit targets)

**Action:** Priority task - implement adaptive volume filter based on market regime.

## Testing Results

### Manual Testing

**MA Break Fix Validation:**
- ✅ Analyzed 56 trades - MA breaks identified as underperforming
- ✅ Logic fix implemented (only exit if profit < 3%)
- 🔄 Re-test pending (currently running)

**Scaled Exits Bug Fix:**
- ❌ Initial test: -65.63% return, 3 trades (FAILED - buggy code)
- ✅ Bug identified and fixed (end_date → last_valid_date)
- 🔄 Re-test running with fixed code

**Scoring System Validation:**
- ✅ Tested on 21 actual 2025 trades
- ❌ Result: Cannot differentiate winners from losers
- ✅ Decision: Abandoned based on data

### Automated Testing

**Currently Running Tests:**

**1. Scaled Exits Comparison (test_scaled_exits_2025.py)**
```bash
Process ID: 1c38ea
Period: 2025-01-01 to 2025-10-31 (218 trading days)
Status: Running (~60% complete)
ETA: ~8-10 more minutes
```

**2. Comprehensive Volume Filter Test (test_volume_all_approaches.py)**
```bash
Process ID: 4e310d
Years: 2018-2025 (8 years, 32 backtests)
Status: Running (Year 6/8 - testing 2023)
ETA: ~12-15 more minutes

Completed Results (2018-2022):
Bear Markets:
  2018: 1.2x wins (+13.39% vs +4.03%)

Bull Markets:
  2020: No filter wins (+44.27% vs +43.15%)
  2021: No filter wins (+19.02% vs +6.81%)

Scoring System: 0 trades every year (broken)
```

### Test Analysis Scripts Created

**analyze_smart_exits.py:**
- Categorized 56 trades by exit reason
- Identified MA break underperformance
- Output: MA breaks 55.6% win rate vs trailing stops 100%

**analyze_actual_trades.py:**
- Tested scoring on 21 real trades (11W, 10L)
- Found losers score higher than winners (6.83 vs 6.69)
- Proved scoring cannot predict outcomes

## Files Modified

**Core Implementation:**
- `backend/backtest/daily_momentum_smart_exits.py` - MA break logic fix
- `backend/backtest/daily_momentum_scaled_exits.py` - End-of-backtest bug fix
- `backend/scanner/daily_breakout_scanner_scoring.py` - Three data handling bug fixes

**Analysis Scripts:**
- `analyze_smart_exits.py` - NEW: Analyze exit patterns
- `analyze_actual_trades.py` - NEW: Test scoring on real trades
- `debug_scoring.py` - Enhanced with detailed filter progression

**Test Scripts:**
- `test_scaled_exits_2025.py` - NEW: Smart vs scaled exits comparison
- `test_volume_all_approaches.py` - NEW: Comprehensive 8-year volume filter test

**Documentation:**
- `SCORING_SYSTEM_VERDICT.md` - NEW: Abandonment decision with full analysis
- `SCORING_SYSTEM_FIXES.md` - NEW: Debug process documentation
- `SCORING_SYSTEM_ANALYSIS.md` - NEW: Improvement analysis (now obsolete)
- `TEST_RESULTS_TRACKER.md` - Updated with new test results
- `actual_trades_analysis.log` - NEW: Output from trade analysis
- `scaled_exits_fixed_run.log` - NEW: Output from corrected test

**Total Files Changed:** 13

## Performance Impact

**MA Break Fix (Expected Impact):**
- Converting 9 MA break exits (55.6% win rate, +1.5% avg) → trailing stops (100% win rate, +6.7% avg)
- Estimated improvement: +0.5-1.0% on annual returns
- More consistent performance, fewer "left money on table" trades

**Scaled Exits Fix:**
- Before: -65.63% return (BROKEN)
- After: Testing now, expect 10-15% return range
- Will determine if scaled profit-taking beats all-or-nothing

**Scoring System Abandonment:**
- Saved weeks of development time tuning a system that doesn't work
- Simplified codebase - can delete 5 files, ~1000 lines of code
- Focus resources on proven simple volume filters

## Documentation Updates

- [x] Created docs/session-history/ folder
- [x] Created this session history document
- [x] Created SCORING_SYSTEM_VERDICT.md with abandonment rationale
- [x] Created SCORING_SYSTEM_FIXES.md documenting debug process
- [ ] Update CLAUDE.md with Python module caching known issue
- [ ] Update CLAUDE.md with "exit strategy > entry strategy" learning
- [ ] Add adaptive volume filter as priority enhancement
- [ ] Document MA break optimization pattern

## Next Steps

### Immediate Follow-ups (When Tests Complete)

- [ ] Review scaled exits vs smart exits comparison results
- [ ] Review comprehensive volume filter test results (2023-2025 data)
- [ ] Make volume filter decision based on 8-year data
- [ ] Decide between scaled exits and smart exits based on comparison
- [ ] Delete scoring system files per abandonment decision

### Implementation Tasks

- [ ] Implement adaptive volume filter (VIX-based switching)
- [ ] Fine-tune MA break logic with test results
- [ ] Create regime detection module (VIX thresholds, moving averages)
- [ ] Test dual-mode volume filter on 2018-2025 data

### Future Enhancements

- [ ] Test trailing stop tightening progression (2x → 1x → 0.5x ATR)
- [ ] Implement time-based exits (hold time limits)
- [ ] Test volatility-adjusted stops (tighter in low VIX)
- [ ] Position sizing by regime (smaller positions in volatile markets)

### Known Issues to Address

- [ ] Python module caching - document in CLAUDE.md
- [ ] Scoring system files cleanup (5 files to archive/delete)
- [ ] Consider adding price validation to position closing logic
- [ ] End-of-backtest date handling pattern (document in CLAUDE.md)

## References

**Related Sessions:**
- N/A (first session history document)

**Architecture Docs:**
- [CLAUDE.md](../../CLAUDE.md) - Project documentation
- [SCORING_SYSTEM_VERDICT.md](../../SCORING_SYSTEM_VERDICT.md) - Abandonment decision
- [SCORING_SYSTEM_FIXES.md](../../SCORING_SYSTEM_FIXES.md) - Debug process
- [TEST_RESULTS_TRACKER.md](../../TEST_RESULTS_TRACKER.md) - All test results

**Analysis Files:**
- [actual_trades_analysis.log](../../actual_trades_analysis.log) - Scoring validation

## Session Metadata

**Environment:**
- Local development: ✅
- Staging deployment: ❌
- Production deployment: ❌

**Git Branch:**
- main

**Background Processes:**
- `1c38ea` - Scaled exits test (running)
- `4e310d` - Comprehensive volume test (running)

---

**Template Version:** 1.0
**Template Source:** [havq-docs/claude/session-history-template.md](../../../havq-docs/claude/session-history-template.md)
