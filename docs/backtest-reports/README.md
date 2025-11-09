# Backtest Reports Index

**Purpose:** Historical record of all backtest runs for the Daily Momentum strategy and its variations. Each report documents strategy configuration, performance metrics, trade details, and lessons learned.

**Last Updated:** November 6, 2025

---

## Quick Performance Summary

| Report | Period | Strategy | Return | Win Rate | Trades | Status |
|--------|--------|----------|--------|----------|--------|--------|
| [Smart Exits Q3 2025](./2025-08-10-smart-exits.md) | Aug-Oct 2025 | Smart Exits | **+1.87%** | 54.5% | 11 | ✅ PASS |
| [Hybrid Trailing Q1 2024](./2024-Q1-hybrid-trailing.md) | Jan-Mar 2024 | Hybrid Trailing | **-1.94%** | 20.0% | 5 | ❌ FAIL |
| Q2 2024 | Apr-Jun 2024 | TBD | TBD | TBD | TBD | 🔄 Pending |
| Q2 2025 | Apr-Jun 2025 | TBD | TBD | TBD | TBD | 🔄 Pending |
| Bear Market 2022 | 2022 | TBD | TBD | TBD | TBD | 🔄 Pending |

---

## Report Categories

### 📈 Production Strategy Tests
Main strategy variations tested for live trading consideration:

- **[Smart Exits Q3 2025](./2025-08-10-smart-exits.md)** - Adaptive trailing stops, MA breaks, momentum detection
  - Result: +1.87%, 54.5% win rate (PASS)
  - Status: Yellow light - needs more data

- **[Hybrid Trailing Q1 2024](./2024-Q1-hybrid-trailing.md)** - Earlier version with hybrid trailing only
  - Result: -1.94%, 20% win rate (FAIL)
  - Status: Red light - do not trade

### 🧪 Scanner Development Tests
Iterative improvements to entry logic:

- **Step 1: Volume Only** - Testing volume filter effectiveness
- **Step 2: EMA20** - Adding trend filter
- **Step 3: Wider Base** - Relaxing consolidation requirements
- **Final Validation** - Complete scanner with all filters

### 📊 Market Regime Tests
Strategy performance across different market conditions:

- **Bear Market 2022** - How strategy performs in downtrend
- **Q1-Q4 2024** - Full year coverage
- **Q1-Q2 2025** - Recent performance

### 🔬 Exit Strategy Comparisons
Testing different exit methodologies:

- **Smart Exits** - Adaptive (2x→1x ATR, MA breaks)
- **Scaled Exits** - Profit-taking (25% at +8%, +15%, +25%)
- **Let Winners Run** - Wider stops, longer holds
- **Stop Loss Comparison** - 6% vs 8% vs 10%

---

## Best Performers

### By Return
1. 🥇 **Smart Exits Q3 2025:** +1.87% (11 trades)
2. 🥈 TBD
3. 🥉 TBD

### By Win Rate
1. 🥇 **Smart Exits Q3 2025:** 54.5% (6W/11T)
2. 🥈 TBD
3. 🥉 TBD

### By Trade Count
1. 🥇 **Smart Exits Q3 2025:** 11 trades (3 months)
2. 🥈 **Hybrid Trailing Q1 2024:** 5 trades (3 months)
3. 🥉 TBD

---

## Worst Performers

### By Return
1. ❌ **Hybrid Trailing Q1 2024:** -1.94% (5 trades, 20% WR)

### By Win Rate
1. ❌ **Hybrid Trailing Q1 2024:** 20% (1W/5T)

---

## Strategy Evolution Timeline

```
2024 Q1: Hybrid Trailing
  ├─ Result: -1.94%, 20% WR ❌
  ├─ Issue: Scanner too restrictive (5 trades only)
  └─ Lesson: Need more setups, better entry confirmation

2024 Q2-Q4: Scanner Refinements
  ├─ Testing volume filters
  ├─ Testing EMA20 trend confirmation
  ├─ Testing wider base patterns
  └─ Goal: Increase trade frequency

2025 Q3: Smart Exits
  ├─ Result: +1.87%, 54.5% WR ✅
  ├─ Added: MA break exits
  ├─ Added: Lower high detection
  └─ Status: Promising, needs validation

2025 Q4: Scaled Exits (In Progress)
  ├─ Strategy: Take 25% profits at +8%, +15%, +25%
  ├─ Trail final 25% with smart logic
  └─ Status: Currently testing
```

---

## Common Strategy Elements

All strategies share these core components:

### Universe
27 hand-picked growth stocks:
- **Tech/Semi:** NVDA, AMD, INTC, ASML, TSMC, MU, PLTR, SNOW, CRWD, NET, DDOG, ZS
- **Mega-Caps:** AAPL, MSFT, GOOGL, AMZN, META
- **Biotech:** MRNA, BNTX, SAVA, SGEN
- **Fintech:** SHOP, SQ, COIN, RBLX
- **Meme:** GME, AMC, PTON, SNAP, TSLA

### Entry Logic (Daily Breakout Scanner)
1. Price >$10 (no penny stocks)
2. Trend: Close > SMA20 > SMA50
3. Relative Strength: Within 25% of 52-week high
4. Base: 10-90 day consolidation, <12% volatility
5. Breakout: Close > consolidation high
6. Volume: 1.2x average (0.8x mega-caps)

### Risk Management
- Starting Capital: $100,000
- Position Size: 30% per trade (~$30k)
- Max Positions: 3 concurrent
- Max Risk: 8% per position = 2.4% portfolio risk

### Timeframe
- Analysis: Daily EOD bars
- Execution: End-of-day entries and exits

---

## Exit Strategy Variations

### Hybrid Trailing (Q1 2024)
- Hard stop: -8%
- Trailing: 2× ATR → 1× ATR → 5%
- Time stop: 15-17 days

**Result:** FAILED (-1.94%, 20% WR)

### Smart Exits (Q3 2025)
- Hard stop: -8%
- Trailing: 2× ATR → 1× ATR → 5%
- MA break: Close < 5-day SMA
- Lower high: Momentum fading after +5%
- Time stop: 17 days

**Result:** PASSED (+1.87%, 54.5% WR)

### Scaled Exits (Testing)
- Scale 25% @ +8%, +15%, +25%
- Trail final 25% with smart logic
- Time stop: 20 days

**Result:** Pending

---

## How to Use These Reports

### For Strategy Development
1. **Compare exit strategies** across same period
2. **Identify what works** (entry timing, exit rules)
3. **Learn from failures** (Q1 2024 lessons)
4. **Track improvements** over time

### For Live Trading Decisions
1. **Check latest report status** (Green/Yellow/Red light)
2. **Review recent win rate** (need >45%)
3. **Verify trade count** (need 30+ for confidence)
4. **Assess market regime** (is current market similar?)

### For Research Questions
- **"Do scaled exits beat smart exits?"** → Compare same period reports
- **"Does strategy work in bear markets?"** → Check bear_market_2022 report
- **"How many trades per quarter?"** → Review trade count column
- **"What's the typical drawdown?"** → Check max DD in each report

---

## Report Format

Each report includes:

1. **Executive Summary**
   - Quick verdict (Pass/Fail)
   - Key metrics (Return, Win Rate, Max DD)
   - One-sentence assessment

2. **Strategy Configuration**
   - Entry rules
   - Exit rules
   - Risk management

3. **Performance Metrics**
   - Returns, win rate, profit factor
   - Trade statistics
   - Time analysis

4. **Trade Details**
   - Top winners/losers
   - Exit reason distribution
   - Symbol performance

5. **Analysis & Findings**
   - What worked
   - What didn't
   - Key insights

6. **Next Steps**
   - Recommended improvements
   - Questions to investigate
   - Parameter adjustments

---

## Pending Reports

Reports to be created from existing data:

- [ ] Q2 2024 (q2_2024_results.json)
- [ ] Q2 2025 (q2_2025_results.json)
- [ ] Bear Market 2022 (bear_market_2022_results.json)
- [ ] Let Winners Run (let_winners_run_results.json)
- [ ] 3-Month Sequential (3_month_sequential_results.json)
- [ ] Step 1: Volume Filter (step1_volume_results.json)
- [ ] Step 2: EMA20 (step2_ema20_results.json)
- [ ] Step 3: Wider Base (step3_wider_base_results.json)
- [ ] Final Validation (final_validation_results.json)
- [ ] Stop Loss Comparison (stop_loss_comparison_results.json)
- [ ] Daily 3-Month (daily_3_month_results.json)
- [ ] 10-Day Backtest (10_day_backtest_results.json)

---

## Strategy Comparison Report

**Coming Soon:** [Strategy Comparison](./strategy-comparison.md)

Side-by-side comparison of:
- Smart Exits vs Scaled Exits vs Fixed Exits
- Performance across different market regimes
- Risk-adjusted returns (Sharpe, Sortino)
- Recommended use cases for each

---

## Key Takeaways (So Far)

### ✅ What's Working
1. **Smart Exits strategy** shows promise (+1.87%, 54.5% WR in Q3 2025)
2. **Exit logic matters** - Smart exits >Hybrid trailing
3. **AAPL trades well** - 100% win rate in Q3 2025 (3/3)
4. **Hard stops protect** - Limit losses to -8%

### ❌ What's Not Working
1. **Scanner too restrictive** - Q1 2024 only found 5 setups
2. **Biotech stocks risky** - BNTX worst loss (-8%)
3. **Small sample sizes** - Need 30+ trades for validation
4. **Time stops frequent** - Many trades go sideways

### 🔍 What We're Learning
1. **Market regime matters** - Breakouts need trending markets
2. **Entry quality > Exit strategy** - Good entries make exits easy
3. **Trade frequency important** - Sitting in cash = opportunity cost
4. **Win rate target: 50%+** - Below 45% indicates broken strategy

---

## Contributing

When adding new reports:

1. Use the report template format (see existing reports)
2. Name files: `YYYY-MM-DD-strategy-name.md` or `YYYY-QX-strategy-name.md`
3. Update this README index (add to Quick Summary table)
4. Include all trades, not just winners
5. Be honest about failures (we learn more from losses!)

---

## Questions or Feedback?

- **Data Issues?** Check source JSON files in project root
- **Strategy Questions?** See `docs/STRATEGY_THESIS.md`
- **Want to Add Reports?** Follow format in existing reports

---

*This is a living document. Reports added as backtests complete.*
*Last updated: November 6, 2025*
