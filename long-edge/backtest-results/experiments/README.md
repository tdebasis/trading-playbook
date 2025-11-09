# Experimental Backtest Results

This folder contains results from strategy variations, parameter sweeps, and iterative development tests.

## Strategy Comparisons

### Exit Strategy Variations
- **smart_exits_results.json** - Adaptive trailing stops + MA breaks + momentum detection
  - Q3 2025: +1.87%, 54.5% WR (PASS)
  - Report: `/long-edge/docs/backtest-reports/2025-08-10-smart-exits.md`

- **hybrid_trailing_results.json** - Simpler trailing stop logic
  - Result: TBD

- **let_winners_run_results.json** - Wider stops, longer time limits
  - Result: TBD

- **stop_loss_comparison_results.json** - Testing 6% vs 8% vs 10% stops
  - Result: TBD

## Scanner Development Iterations

Progressive refinement of entry logic:

- **step1_volume_results.json** - Volume filter only
- **step2_ema20_results.json** - Added EMA20 trend filter
- **step3_wider_base_results.json** - Relaxed consolidation requirements
- **final_validation_results.json** - Complete scanner with all filters

## Time Period Tests

- **10_day_backtest_results.json** - Short validation run
- **3_month_sequential_results.json** - Rolling 3-month windows
- **daily_3_month_results.json** - Daily timeframe test

## Other

- **annualized_returns.json** - Performance extrapolations
- **backtest_past.json** / **backtest_real_past.json** - Early development tests

## See Also

For strategy comparison analysis: `/long-edge/docs/backtest-reports/strategy-comparison.md`
