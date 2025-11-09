# Tests Directory

Test scripts for validating strategy components, parameter optimization, and system functionality.

---

## Directory Structure

```
tests/
├── volume_tests/      # Volume filter parameter testing
├── backtest_tests/    # Backtest validation and strategy tests
└── README.md
```

---

## Volume Tests (`volume_tests/`)

Comprehensive testing of volume filter thresholds (0.0x, 0.5x, 1.2x) across different market conditions.

### test_volume_7year.py
**Purpose:** Long-term validation of volume filters
- **Period:** 2018-2025 (7 years)
- **Tests:** 0.0x, 0.5x, 1.2x volume multipliers
- **Goal:** Determine if volume filter adds value across bull/bear markets

**Key Finding:** 1.2x filter dominates in bear markets (+9.36% advantage in 2018) but underperforms in bull markets (-12.21% in 2021)

### test_volume_all_approaches.py
**Purpose:** Compare all volume filter approaches side-by-side
- **Tests:** No filter, 0.5x, 1.2x, adaptive filter
- **Analysis:** Trade count, win rate, return for each approach
- **Output:** Summary comparison table

### test_volume_comprehensive.py
**Purpose:** Comprehensive volume filter analysis
- **Multiple periods:** Q1-Q4 across years
- **Sensitivity analysis:** How sensitive are results to volume threshold?
- **Market regime analysis:** Performance by VIX levels

### test_volume_filter_075.py
**Purpose:** Test intermediate threshold
- **Tests:** 0.75x volume multiplier
- **Hypothesis:** Sweet spot between 0.5x and 1.2x?

### test_volume_quick.py
**Purpose:** Fast validation run
- **Period:** 3 months recent data
- **Use case:** Quick parameter check during development
- **Runtime:** ~30 seconds (vs hours for 7-year test)

**Usage:**
```bash
cd /long-edge
python tests/volume_tests/test_volume_quick.py
```

---

## Backtest Tests (`backtest_tests/`)

Strategy validation and backtest framework testing.

### test_scaled_exits_2025.py
**Purpose:** Test scaled exits strategy (profit-taking)
- **Strategy:** Take 25% profits at +8%, +15%, +25%
- **Period:** 2025 data
- **Comparison:** vs Smart Exits (hold full position)

**Key Test:** Does profit-taking reduce drawdown without sacrificing returns?

### test_scoring_fast.py
**Purpose:** Fast test of scoring system (abandoned)
- **Tests:** Quality scoring for entry candidates
- **Period:** Short recent data
- **Status:** Scoring system abandoned (Nov 2025) after empirical testing showed losers scored higher than winners

**Historical Note:** This test helped identify that scoring system didn't predict winners.

**Usage:**
```bash
cd /long-edge
python tests/backtest_tests/test_scaled_exits_2025.py
```

---

## Test Results

**JSON Output:** `/backtest-results/experiments/`
**Logs:** `/logs/backtests/experiments/`
**Reports:** `/docs/backtest-reports/`

---

## Testing Best Practices

### Before Running Tests:
1. Verify Alpaca API credentials in `.env`
2. Check cache directory (`/data/cache/`) for existing data
3. Expect 30s-30min runtime depending on test scope

### After Running Tests:
1. Review JSON output in `/backtest-results/`
2. Check logs in `/logs/` for errors
3. Create markdown report in `/docs/backtest-reports/` for significant findings

### Naming Convention:
- `test_[feature]_[scope].py` - e.g., `test_volume_quick.py`
- Scope: quick (days), comprehensive (months), 7year (years)

---

## Integration Tests

For integration tests (API connectivity, data fetching), see:
- `/tests/integration/test_alpaca_integration.py` (root level)
- `/tests/integration/test_dp20_integration.py` (root level)

---

## Related Documentation

- **Backtest Guide:** `/docs/BACKTEST_GUIDE.md`
- **Volume Filter Research:** `/docs/backtest-reports/`
- **Strategy Comparison:** `/docs/backtest-reports/strategy-comparison.md`

---

*Tests are the foundation of strategy validation. Run tests, trust the data, make decisions.*
