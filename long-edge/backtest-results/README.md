# Backtest Results Archive

This directory contains raw JSON output from all backtest runs. Results are organized by year and experiment type.

## Directory Structure

```
backtest-results/
├── 2024/          # Calendar year 2024 tests
├── 2025/          # Calendar year 2025 tests
└── experiments/   # Strategy variations and parameter tests
```

## Using These Results

Each JSON file contains:
- Trade-by-trade details (entry, exit, P&L)
- Summary statistics (win rate, profit factor, etc.)
- Strategy configuration (entry rules, exit rules, position sizing)

## Related Documentation

For human-readable analysis of these results, see:
- `/long-edge/docs/backtest-reports/` - Detailed markdown reports
- `/long-edge/docs/backtest-reports/strategy-comparison.md` - Side-by-side comparisons

## File Naming Convention

- `qX_YYYY_results.json` - Quarterly tests (q1_2024, q2_2025, etc.)
- `{strategy_name}_results.json` - Strategy variations (smart_exits, hybrid_trailing, etc.)
- `{experiment_name}_results.json` - Specific tests (step1_volume, final_validation, etc.)
