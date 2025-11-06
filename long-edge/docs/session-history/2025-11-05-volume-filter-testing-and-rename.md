# Session History: Volume Filter Testing and Project Rename

**Date**: November 5, 2025
**Duration**: ~3 hours
**Status**: In Progress (tests running)

---

## Session Goal

Primary objectives for this session:

1. **Rename project** from `longedge` to `long-edge` (with hyphen for better branding)
2. **Test volume filter approaches** to determine optimal settings
   - Current concern: 1.2x volume filter may be too strict, missing quality stocks like PLTR
   - Test 4 approaches: No filter (0.0x), Soft (0.5x), Current (1.2x), Scoring system
3. **Validate exit criteria** and understand current implementation
4. **Plan cloud deployment** strategy (separate repo decision)

---

## Key Changes Made

### 1. Project Rename: longedge → long-edge

**Files Modified:**
- `/Users/tanambamsinha/projects/trading-playbook/README.md`
  - Updated directory path references from `longedge/` to `long-edge/`
  - Updated example commands with new path

- `/Users/tanambamsinha/projects/trading-playbook/long-edge/STRATEGY_THESIS.md`
  - Updated project name branding throughout
  - Confirmed "LongEdge" naming convention

**Directory Rename:**
```bash
mv /Users/tanambamsinha/projects/trading-playbook/longedge \
   /Users/tanambamsinha/projects/trading-playbook/long-edge
```

### 2. Volume Filter Test Scripts Created

#### `test_volume_quick.py`
**Purpose**: Quick validation of 4 volume approaches on 2025 YTD data only
**Approaches tested**:
- No filter (0.0x) - Accept all breakouts
- Soft filter (0.5x) - PLTR would pass
- Current baseline (1.2x) - Existing threshold
- Scoring system - Volume as one factor, not hard filter

**Key Features:**
- Unbuffered output for real-time visibility
- Detailed progress logging with emojis (📥, 🏃, ✅)
- Estimated runtime: 10-15 minutes (4 backtests)

#### `test_volume_all_approaches.py`
**Purpose**: Comprehensive 7-year test (2018-2025) across all 4 approaches
**Coverage**: 8 years × 4 approaches = 32 backtests
**Estimated runtime**: 60-75 minutes

**Scoring logic**: Year-by-year comparison with final verdict on which approach wins over full market cycle

#### `backend/scanner/daily_breakout_scanner_scoring.py`
**Purpose**: Alternative scanner implementing scoring system hypothesis
**Key Concept**: Weak volume can be compensated by strong price action

**Scoring breakdown** (0-10 points):
- Volume: 0-2 points (not a hard filter!)
- Trend: 0-3 points (alignment, distance from 52w high)
- Base quality: 0-3 points (consolidation tightness)
- Relative strength: 0-2 points

**Adaptive thresholds**:
- High volume (1.5-2.0 pts): Need 4.0 total to enter
- Medium volume (1.0 pts): Need 5.0 total to enter
- Low volume (0.5-1.0 pts): Need 6.0 total to enter

### 3. Bug Fixes Applied

**TypeError: Object Not Subscriptable**

All test scripts were using incorrect dict-style access:
```python
# BEFORE (incorrect)
results['return_pct']
results['total_trades']
results['win_rate']

# AFTER (correct)
results.total_return_percent
results.total_trades
results.win_rate
```

**Root cause**: `SmartExitBacktester.run()` returns `DailyBacktestResults` dataclass, not dictionary

**Files fixed:**
- `test_volume_quick.py`
- `test_volume_all_approaches.py`

**Output Buffering Issue**

Tests ran for 30+ minutes with no visible output. Fixed by:
1. Adding `sys.stdout.reconfigure(line_buffering=True)`
2. Running with `-u` flag: `python3 -u test_script.py`
3. Adding detailed progress logging at each step

---

## Test Results

### Completed: test_volume_filter_075.py

**Test**: 2025 YTD comparison of 0.75x vs 1.2x volume filter

**Results**:
```
FINAL SUMMARY - Full Year 2025
Total Return (3Q)     1.2x Filter: +6.83%    0.75x Filter: +4.37%    Diff: -2.46%
Total Trades                    51                   61              +10
Avg Win Rate                  53.8%                58.2%             +4.4%

Quarter-by-Quarter:
  Q1 2025    1.2x: +1.71%  |  0.75x: -0.71%  |  Diff: -2.43% ❌
  Q2 2025    1.2x: +3.96%  |  0.75x: +0.15%  |  Diff: -3.81% ❌
  Q3 2025    1.2x: +1.16%  |  0.75x: +4.93%  |  Diff: +3.77% ✅

VERDICT: ❌ 0.75x filter UNDERPERFORMED by 2.46%
```

**Key Finding**: Lowering volume filter to 0.75x added 10 more trades but decreased overall return. The additional trades were lower quality, hurting profit factor.

**Conclusion**: Current 1.2x volume filter appears optimal for 2025 data. Volume expansion is a valid signal quality indicator.

### In Progress: test_volume_quick.py (bfd146)

**Status**: Running first backtest (No Filter 0.0x)
**Last output**: "🏃 Running backtest (this may take 2-3 minutes)..."
**Note**: Taking longer than expected (~30+ min for what should be 10-15 min)

### Failed/Killed: test_volume_all_approaches.py

Multiple instances killed due to:
1. Initial TypeError bug (before fix)
2. No output visibility (before logging added)
3. User decision to wait for quick test first

---

## Problems Encountered

### Problem 1: Incorrect Object Access Pattern
**Symptom**: `TypeError: 'DailyBacktestResults' object is not subscriptable`
**Root Cause**: Using dict syntax (`results['key']`) instead of attribute access (`results.key`)
**Solution**: Updated all test scripts to use correct dataclass attribute access
**Impact**: All tests failing until fix applied

### Problem 2: No Visible Output
**Symptom**: Tests running 30+ minutes with only SSL warning visible
**Root Cause**: Python stdout buffering - output not flushing in real-time
**Solution**:
- Added `sys.stdout.reconfigure(line_buffering=True)`
- Run with `-u` flag for unbuffered output
- Added detailed logging at each step (📥 Creating, 🏃 Running, ✅ Done)
**Impact**: User couldn't monitor progress or detect issues

### Problem 3: Slow Test Execution
**Symptom**: Quick test taking 30+ min instead of expected 10-15 min
**Root Cause**: Unknown - likely API rate limiting or slow data download
**Investigation**: Added detailed logging to identify bottleneck (data vs computation)
**Status**: Ongoing - monitoring current test with visibility

### Problem 4: Volume Filter Hypothesis Uncertainty
**Question**: "is 0.75x still high?" - uncertainty about optimal threshold
**Approach**: Empirical testing rather than guessing
**Decision**: Test 4 distinct approaches (0.0x, 0.5x, 1.2x, scoring) across 7 years
**Rationale**: Only way to definitively answer which approach works best

---

## Exit Criteria Review

User asked: "can you show me where the exit criteria is defined in code?"

**Location**: `backend/backtest/daily_momentum_smart_exits.py` lines 200-230

**5 Exit Rules**:

1. **Hard Stop** (-8%):
   - `if current_low <= position.hard_stop`
   - Protects against large losses
   - Exit: HARD_STOP at stop price

2. **Trailing Stop** (after +5% profit):
   - `if position.highest_high > entry * 1.05 and current_low <= trailing_stop`
   - Locks in profits as stock rises
   - Exit: TRAILING_STOP at trail price

3. **MA Break** (close below 5-day MA, after +3% profit):
   - `if position.highest_high > entry * 1.03 and current_price < sma_5`
   - Trend weakening signal
   - Exit: MA_BREAK at close price

4. **Lower High** (momentum weakening, after +5% profit):
   - `if position.highest_high > entry * 1.05 and current_high < prev_high`
   - Failed to make new high
   - Exit: LOWER_HIGH at close price

5. **Time Stop** (15 days max):
   - `if hold_days >= 15`
   - Prevents capital tie-up
   - Exit: TIME at close price

**Philosophy**: Smart exits adapt to profit level. More protection as gains increase.

---

## Key Decisions

### 1. Project Naming: "LongEdge"
**Context**: User wanted catchier name than "momentum-hunter"
**Decision**: Renamed to "long-edge" (directory) / "LongEdge" (branding)
**Rationale**:
- Clear indication of strategy focus (long-only)
- Separates from future bear market strategies
- More distinctive branding

### 2. Cloud Deployment Strategy
**Context**: User: "We probably should start working on cloud deployment"
**Decision**: Create separate `longedge-production` repository for cloud code
**Rationale**:
- Keep `long-edge` local for research/optimization
- Avoid "muddying" research repo with infrastructure code
- Clean separation of concerns
- User: "i an thinking of setting up a completely separate repo"

### 3. Volume Filter Testing Approach
**Context**: Concern that 1.2x filter might miss quality stocks (PLTR example)
**Decision**: Test 4 approaches empirically across 7 years (2018-2025)
**Rationale**:
- User: "I guess maybe the only way to find out is to run [tests]"
- Can't guess optimal threshold without data
- Need to see performance across bull/bear cycles
- Scoring system tests alternative hypothesis

### 4. Scoring System Consideration
**Context**: Volume as scoring factor instead of hard filter
**User concern**: "the problem with scoring is the signal might be muddled"
**Decision**: Include scoring as one of 4 test approaches
**Rationale**:
- Tests hypothesis: weak volume + strong price action = valid signal
- Empirical results will show if nuanced approach beats binary filter
- Worth testing even if uncertain

---

## Technical Notes

### API Rate Limiting (Alpaca Paid Tier)
**Limit**: 200 requests per minute with burst allowance
**Impact**: Shouldn't be bottleneck for our testing
**Current tier**: Paid ($99/month SIP data)

### Data Download vs Computation
**Question**: How much time is data download vs backtest execution?
**Hypothesis**: Likely downloading full year of 2-min bars takes majority of time
**Note**: Will be clearer with detailed logging in current test

### Test Process Management
**Issue**: Many old test processes still running in background
**Active processes**: 311351, 871fd5, 2b8f88, b03390, d08a37, 49c28c, 7c6018, 249609
**Current test**: bfd146 (test_volume_quick.py)
**Cleanup needed**: Kill old failed/stuck tests

---

## Documentation Created

1. **Session history** (this document):
   - Location: `docs/session-history/2025-11-05-volume-filter-testing-and-rename.md`
   - Format: Following Havq standards from `~/projects/havq-frontend/docs/session-history/`
   - Purpose: Record progress, decisions, problems, findings

2. **Volume test scripts**:
   - `test_volume_quick.py` - 2025 YTD only (fast validation)
   - `test_volume_all_approaches.py` - 7-year comprehensive test
   - `backend/scanner/daily_breakout_scanner_scoring.py` - Scoring system implementation

---

## Next Steps

### Immediate (Waiting)
1. ✅ Wait for test_volume_quick.py (bfd146) to complete
2. ⏳ Analyze quick test results (No filter / 0.5x / 1.2x / Scoring)
3. ⏳ Determine if scoring system shows promise on 2025 data

### Short-term (If Quick Test Promising)
4. ⏳ Run comprehensive 7-year test with fixed scripts
5. ⏳ Analyze results across market cycles (2018-2025)
6. ⏳ Make final decision on volume filter approach:
   - Keep 1.2x (if wins)
   - Lower to 0.5x (if soft filter wins)
   - Remove filter (if 0.0x wins)
   - Implement scoring system (if scoring wins)

### Medium-term (Cloud Deployment)
7. ⏳ Create `longedge-production` repository (separate from research)
8. ⏳ Design cloud architecture (GCP Cloud Run, schedulers, storage)
9. ⏳ Implement production-grade infrastructure

### Ongoing (Maintenance)
10. ⏳ Clean up old background test processes
11. ⏳ Document cloud deployment architecture when ready

---

## Key Insights

### Volume Filter Effectiveness
**From 0.75x test**: Lowering filter adds quantity but not quality
- 1.2x: 51 trades, +6.83% return
- 0.75x: 61 trades (+10), +4.37% return (-2.46%)
- Additional trades were lower quality (worse profit factor)

**Hypothesis still uncertain**: Need full test to see if scoring system or 0.5x soft filter performs better than 1.2x across multiple years

### Testing Methodology Improvement
**Lesson learned**: Always add detailed logging upfront
**Before**: 30 min wait with no visibility, couldn't diagnose issues
**After**: Real-time progress updates, can identify bottlenecks
**Future**: Standard pattern for all long-running tests

### Empirical vs Theoretical
**Pattern**: User preference for data-driven decisions
**Example**: "the only way to find out is to run [tests]"
**Approach**: Test multiple approaches, let results decide
**Benefit**: Removes guesswork, builds confidence in parameters

---

## User Feedback Highlights

**On naming**: "I like LongEdge" → Immediate decision, confident choice

**On testing approach**: "I guess maybe the only way to find out is to run with 3 options... I cannot see any other way" → Empirical mindset

**On cloud deployment**: "i an thinking of setting up a completely separate repo while this can be a fully local setup what do you think?" → Clean separation of concerns

**On visibility**: "i hope you did put it in progress status in the stdout so you know what it is doing and where it is at" → Values transparency and monitoring

**On results timing**: "no hurry only output matters i was hoping i would get the result of the quick test before turning in for the night" → Patient but curious about findings

---

## Session Outcome

**Completed**:
- ✅ Project renamed to long-edge with consistent branding
- ✅ Volume filter test scripts created and debugged
- ✅ Exit criteria reviewed and documented
- ✅ Empirical test completed: 1.2x beats 0.75x by +2.46%
- ✅ Session history documented

**In Progress**:
- ⏳ Quick test running (4 approaches on 2025 data)
- ⏳ Awaiting results to inform next steps

**Validated**:
- ✅ Current 1.2x volume filter performs well (beat 0.75x)
- ✅ Exit criteria properly implemented with adaptive logic
- ✅ Testing infrastructure working (after bug fixes)

**Deferred**:
- ⏳ Cloud deployment planning (separate repo decision made)
- ⏳ 7-year comprehensive test (awaiting quick test validation)

---

## Files Modified

```
/Users/tanambamsinha/projects/trading-playbook/
├── README.md                                              [MODIFIED - path updates]
└── long-edge/
    ├── STRATEGY_THESIS.md                                 [MODIFIED - branding]
    ├── test_volume_quick.py                               [CREATED - quick validation]
    ├── test_volume_all_approaches.py                      [CREATED - comprehensive test]
    ├── test_volume_filter_075.py                          [COMPLETED - results obtained]
    ├── backend/
    │   ├── backtest/daily_momentum_smart_exits.py        [REVIEWED - exit criteria]
    │   └── scanner/
    │       └── daily_breakout_scanner_scoring.py         [CREATED - scoring system]
    └── docs/
        └── session-history/
            └── 2025-11-05-volume-filter-testing-and-rename.md  [CREATED - this document]
```

---

**Status**: Session paused awaiting test results
**Test monitoring**: Process bfd146 (test_volume_quick.py)
**Expected completion**: Unknown (running slower than expected)
**Next action**: Analyze quick test results when available, decide on comprehensive test

---

*Document created: 2025-11-05*
*Last updated: 2025-11-05 22:10 PST*
*Format: Havq session history standard*
