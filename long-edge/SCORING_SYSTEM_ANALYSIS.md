# Scoring System Analysis & Improvement Opportunities

**Date:** 2025-11-06
**Status:** FUNCTIONAL but TOO RESTRICTIVE

---

## Current Performance

- **Comprehensive Test (2018-2022):** 0 trades across all years
- **Single Day Test (May 23, 2025):** 2 candidates (SNOW, GME)
- **2025 YTD:** TBD (currently testing)

**Comparison:** 1.2x volume filter produces 40-80 trades per year

---

## Problem Analysis

The scoring system has **TWO LAYERS** of filters, and candidates must pass BOTH:

### Layer 1: BASE SCREENING (Hard Filters - BEFORE Scoring)
Candidates must pass ALL of these or get rejected immediately:

1. **Trend Filter** (Line 294): `close > SMA20 > SMA50`
   - ❌ **TOO STRICT:** Rejects stocks that are above SMA20 but SMA20 < SMA50
   - Example: Early uptrend recovery where 20-day hasn't crossed 50-day yet

2. **Distance from 52w High** (Line 302): Must be < 25%
   - ✅ **REASONABLE:** Catches strong stocks
   - Could relax to 30% to catch more opportunities

3. **Consolidation Base** (Lines 306-308): Must find 10-90 day base with < 12% range
   - ❌ **TOO STRICT:** Rejects many valid breakouts
   - Growth stocks can have 15-20% consolidations that are still tradeable
   - BNTX rejected on our test day for this reason (no base < 12%)

4. **Breakout Confirmation** (Line 313): `close > consolidation_high`
   - ✅ **GOOD:** This is the core breakout logic

### Layer 2: SCORING THRESHOLDS
After passing Layer 1, candidates are scored 0-10 points and must meet dynamic thresholds:

- **High Volume (1.5-2.0 pts):** Need 2.0 total score (EASY)
- **Medium Volume (1.0 pts):** Need 2.5 total score (REASONABLE)
- **Low Volume (0.5-1.0 pts):** Need 3.0 total score (MODERATE)
- **Very Low Volume (<0.5 pts):** Need 4.0 total score (HARD)

**Scoring Breakdown:**
- Volume: 0-2 pts
- Trend: 0-3 pts (distance from high, MA alignment)
- Base Quality: 0-3 pts (consolidation days, tightness)
- Relative Strength: 0-2 pts (vs SPY - currently hardcoded to 1.0)

---

## Key Issues

### Issue 1: TOO MANY BASE SCREENING REJECTIONS

**The Problem:**
- Most stocks fail Layer 1 (base screening) and NEVER reach scoring
- On our test day: BNTX passed all filters except consolidation (rejected before scoring)
- The consolidation filter (< 12% range) is the main culprit

**Impact:**
- Scoring system never gets a chance to work its magic
- Volume compensation logic is useless if stocks don't reach scoring

**Example:**
```
BNTX on May 23:
✅ Trend: Close > SMA20 > SMA50
✅ Distance: 24.7% from 52w high
❌ Consolidation: No base found with < 12% range
🚫 REJECTED before scoring
```

### Issue 2: Trend Filter Too Strict

**The Problem:**
- Requires `close > SMA20 > SMA50` (both conditions)
- Rejects stocks in early uptrend where SMA20 hasn't crossed SMA50 yet
- These early entries can be the best (catch the move before it's obvious)

**Better Approach:**
- Primary: `close > SMA20` (price in uptrend)
- Optional boost in scoring if `SMA20 > SMA50` (mature trend)

### Issue 3: Relative Strength Not Calculated

**The Problem:**
- RS currently hardcoded to 1.0 (Line 321-322)
- Missing 0-2 points of scoring potential
- Can't differentiate leaders from laggards

**Fix:**
- Fetch SPY data and calculate real RS
- Or use a simpler proxy (close vs SMA200 distance)

### Issue 4: Scoring Thresholds May Still Be Strict

**Current Thresholds (v2 - "relaxed"):**
- High volume: 2.0 total
- Medium volume: 2.5 total
- Low volume: 3.0 total
- Very low: 4.0 total

**Maximum Possible Score:**
- Volume: 2.0
- Trend: 3.0
- Base: 3.0
- RS: 2.0
- **Total: 10.0 points**

**Analysis:**
- A stock with 0.7 volume (quiet accumulation) needs 3.0 total
- With broken RS (0 pts), needs 3.0 from trend + base
- This is achievable BUT base filter rejects most before scoring

---

## Recommended Improvements

### Priority 1: RELAX BASE SCREENING FILTERS

These changes allow more candidates to REACH the scoring system:

**A. Relax Consolidation Range** (Line 345-355)
```python
# CURRENT: max_base_volatility = 0.12 (12%)
# PROPOSED: max_base_volatility = 0.18 (18%)
```
- **Rationale:** Growth stocks often consolidate 15-20% (still tradeable)
- **Impact:** 2-3x more candidates reach scoring
- **Risk:** Low (scoring will filter weak setups)

**B. Make Trend Filter More Lenient** (Line 294)
```python
# CURRENT: if not (latest.close > sma_20 > sma_50)
# PROPOSED: if not (latest.close > sma_20)
```
- **Rationale:** Catch early uptrends, let scoring evaluate maturity
- **Impact:** Award 1.5 pts for `SMA20 > SMA50`, 0.5 pts for just `close > SMA20`
- **Risk:** Minimal (trend quality captured in scoring)

**C. Increase Distance from High** (Line 302)
```python
# CURRENT: max_distance_from_high = 25%
# PROPOSED: max_distance_from_high = 30%
```
- **Rationale:** Catch stocks recovering from deeper pullbacks
- **Impact:** 10-20% more candidates
- **Risk:** Very low (distance already scored)

### Priority 2: FIX RELATIVE STRENGTH

**Implement Real RS Calculation:**
```python
# Fetch SPY data for same period
spy_bars = self._get_spy_bars(start_date, end_date)
spy_change = spy_bars[-1].close / spy_bars[-20].close
stock_change = closes[-1] / closes[-20]
relative_strength = stock_change / spy_change
```

**Alternative (Simpler):**
```python
# Use distance from SMA200 as RS proxy
if latest.close > sma_200:
    distance_pct = ((latest.close - sma_200) / sma_200) * 100
    if distance_pct >= 10:
        rs_score = 2.0  # Well above long-term MA
    elif distance_pct >= 5:
        rs_score = 1.0  # Above long-term MA
else:
    rs_score = 0.0  # Below long-term MA
```

### Priority 3: LOWER SCORING THRESHOLDS (If Still Needed)

Only do this AFTER relaxing base filters. Try:

```python
# Even more relaxed thresholds (v3):
if volume_score >= 1.5:
    required_score = 1.5  # High volume = very easy
elif volume_score >= 1.0:
    required_score = 2.0  # Medium volume = easy
elif volume_score >= 0.5:
    required_score = 2.5  # Low volume = moderate
else:
    required_score = 3.5  # Very low = need good setup
```

---

## Expected Impact

### With Priority 1 Changes (Relax Base Filters):

**Before:**
- 2018-2022: 0 trades (everything rejected in base screening)
- May 23: 2 candidates (BNTX rejected for consolidation)

**After:**
- 2018-2022: 20-40 trades/year (estimate)
- May 23: 3 candidates (BNTX now included)

**Key Insight:** Most value comes from GETTING CANDIDATES TO SCORING, not from adjusting score thresholds.

### With Priority 2 (Fix RS):

- Better differentiation between leaders and laggards
- 0-2 additional points per candidate
- Higher quality trade selection

### With Priority 3 (Lower Thresholds):

- If still getting < 30 trades/year after P1+P2, lower thresholds
- Target: 40-60 trades/year (similar to 1.2x filter)

---

## Comparison: Scoring vs 1.2x Volume Filter

### 1.2x Volume Filter (Simple):
- **Single hard filter:** Volume ≥ 1.2x average
- **Pros:** Simple, catches big moves
- **Cons:** Misses quiet accumulation (PLTR-style)
- **Performance:** 40-80 trades/year, mixed results

### Scoring System (Complex):
- **Multi-factor:** Volume, trend, base, RS
- **Pros:** Nuanced, volume compensation, quality focus
- **Cons:** Currently too restrictive, complex to tune
- **Performance:** 0-2 trades/year (TOO STRICT)

### The Sweet Spot:
- Relax base screening to get 40-60 candidates/year reaching scoring
- Let scoring system select best 30-40 trades
- This combines breadth (enough opportunities) with quality (scoring filter)

---

## Testing Plan

1. **Apply Priority 1 changes** (relax base filters)
2. **Re-run 2025 YTD test** (Jan-Oct)
3. **Compare results:**
   - Scoring (improved) vs 1.2x vs 0.0x
   - Number of trades, win rate, return
4. **If still < 30 trades:** Apply Priority 3 (lower thresholds)
5. **If 30-60 trades:** Success! Analyze quality vs 1.2x
6. **If > 80 trades:** Tighten thresholds slightly

---

## Action Items

- [ ] Create `daily_breakout_scanner_scoring_v3.py` with relaxed filters
- [ ] Update consolidation range: 12% → 18%
- [ ] Update trend filter: require only `close > SMA20`
- [ ] Update distance from high: 25% → 30%
- [ ] Implement real RS calculation (or simple proxy)
- [ ] Test on 2025 YTD
- [ ] Compare vs 1.2x baseline

---

## Bottom Line

**The scoring system's CONCEPT is sound** (volume compensation, multi-factor analysis), but **the IMPLEMENTATION is too restrictive**.

**The main bottleneck is BASE SCREENING, not scoring thresholds.** Most stocks never reach the scoring system because they fail the consolidation filter.

**Fix:** Relax base filters → Get more candidates to scoring → Let the scoring system do its job → Compare quality vs simple 1.2x filter.

---

*Analysis by: Claude Code*
*Date: 2025-11-06*
