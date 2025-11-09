# Test Results Tracker

**Purpose:** Track all backtest results for comparison and analysis

---

## Current Active Tests (2025-11-06)

### Test 1: Comprehensive Volume Filter Test (2018-2025)
- **Status:** Running (Year 5 of 8 - testing 2022)
- **File:** `volume_test_progress.log`
- **Started:** 2025-11-05 ~10:16 PM
- **Command:** `python3 -u test_volume_all_approaches.py 2>&1 | tee volume_test_progress.log`

**Completed Years:**
| Year | No Filter (0.0x) | Soft Filter (0.5x) | Current (1.2x) | Scoring | Winner | Notes |
|------|------------------|-------------------|----------------|---------|--------|-------|
| 2018 | +4.03% (59)     | +4.03% (59)       | +13.39% (41)   | 0%      | 1.2x   | 1.2x advantage: +9.36% |
| 2019 | +8.50% (73)     | +8.50% (73)       | +8.28% (59)    | 0%      | 0.0x   | Minimal difference: -0.22% |
| 2020 | +44.27% (79)    | +44.27% (79)      | +43.15% (53)   | 0%      | 0.0x   | Similar, but 1.2x had better PF (2.77x vs 2.28x) |
| 2021 | +19.02% (78)    | +19.02% (78)      | +6.81% (61)    | 0%      | 0.0x   | **Big divergence: -12.21%** |

**Key Insight:** 1.2x filter dominates bear markets (2018), but underperforms in bull markets (2021)

---

### Test 2: Scaled Exits vs Smart Exits (2025 YTD)
- **Status:** Running TEST 2 (Scaled Exits) - ~50% complete
- **File:** `scaled_exits_full_output.log`
- **Started:** 2025-11-06 ~12:39 AM
- **Period:** Jan 1 - Oct 31, 2025 (10 months)
- **Universe:** 26 symbols
- **Volume Filter:** 1.2x (for both tests)
- **Command:** `python3 -u test_scaled_exits_2025.py 2>&1 | tee scaled_exits_full_output.log`

**TEST 1 COMPLETE - Smart Exits (Baseline):**
- Return: **+12.20%**
- Trades: 56
- Win Rate: 58.9%
- Profit Factor: 1.53x
- Avg Win: +$1,069
- Avg Loss: -$1,003
- Max Drawdown: 5.4%

**TEST 2 - Scaled Exits: RESTARTED (Bug Fixed)**
- **Status:** Running (restarted at 01:05 AM)
- **Bug Fixed:** Changed line 173-181 to use last_valid_date instead of end_date
- **Previous Failure:** -65.63% (positions closed at $0.00 - see `scaled_exits_full_output_FAILED.log`)
- **Current Run:** Using cache from first run, should complete in ~20-25 minutes
- Strategy: 25% out at +8%, +15%, +25%, trail final 25%
- Results: TBD

---

### Test 3: Scoring System (2025 YTD) - FAILED
- **Status:** Completed (FAILED - 0 trades)
- **File:** `scoring_test_v2.log`
- **Date:** 2025-11-06
- **Period:** Jan 1 - Oct 31, 2025
- **Universe:** 26 symbols
- **Thresholds Tested:**
  - v1: 3.0/4.0/5.0/6.0 → 0 trades
  - v2 (relaxed): 2.0/2.5/3.0/4.0 → 0 trades

**Result:** 0 trades (scoring system has bugs, not just strict thresholds)

**Comparison Baselines:**
- No Filter (0.0x): +12.80% (64 trades)
- Soft Filter (0.5x): +12.71% (64 trades)
- Current (1.2x): +12.20% (56 trades)
- Scoring System: +0.00% (0 trades)

**Issue:** Scanner finds candidates (SNOW 8.8/10, GME 7.2/10) but backtester doesn't trade them. Needs debugging.

---

## Historical 2025 YTD Results (Jan-Oct)

### Quick Volume Filter Test (from earlier session)
**Date:** Unknown (before 2025-11-05)
**Period:** Jan 1 - Oct 31, 2025

| Filter | Return | Trades | Notes |
|--------|--------|--------|-------|
| 0.0x   | +12.80% | 64    | Baseline |
| 0.5x   | +12.71% | 64    | Includes PLTR |
| 1.2x   | +12.20% | 56    | Current best |

---

## Quarterly Results Archive

### Q2 2025 (May-July)
- **File:** `q2_2025_results.log`
- **Universe:** 23 symbols
- **Final Equity:** $100,305 (incomplete - no summary stats)

### Q1 2024
- **File:** `q1_2024_results.log`
- (not yet analyzed)

### Q2 2024
- **File:** `q2_2024_results.log`
- (not yet analyzed)

---

## Action Items

1. ✅ Created this tracker file
2. ⏳ Wait for comprehensive test to complete (2022-2025)
3. ⏳ Wait for scaled exits TEST 2 to complete
4. 🔴 Debug scoring system (candidates found but not traded)
5. 📊 Add final results to this file when tests complete
6. 🎯 Make decision: Which volume filter? Which exit strategy?

---

## Notes & Observations

### Volume Filter Insights:
- **1.2x dominates in tough markets** (2018: +9.36% advantage)
- **1.2x underperforms in bull markets** (2021: -12.21% disadvantage)
- **0.5x identical to 0.0x** in all tests so far (not filtering anything meaningful)
- **Scoring system failed** - needs major redesign

### Universe Changes:
- Earlier tests: 23 symbols
- Current tests: 26 symbols
- This may explain small return differences between test runs

### Questions to Answer:
1. Why did earlier 2025 test show ~19% but current shows 12.20%?
   - Different universe? (23 vs 26 symbols)
   - Different date range?
   - Different parameters?
   - Need to verify with logs

---

*Last Updated: 2025-11-06 01:00 AM*
*Next Update: When tests complete*
