# Momentum Hunter - Backtesting Guide

## What Makes This Different

**Traditional Backtesting:**
```python
# Rule-based: "If volume > 2x and price > EMA, buy"
if volume_ratio > 2.0 and price > ema20:
    buy()
```

**Momentum Hunter Backtesting:**
```python
# AI-based: Claude analyzes context and decides
decision = claude.make_decision(candidates, catalysts, market_conditions)
# Returns: "FDA approval is strong (8/10) but stock already ran 40%,
#          entry now = chasing, poor R/R → HOLD, wait for pullback"
```

**The difference:** We're testing Claude's intelligence, not just rule-based signals.

---

## How It Works

### 1. Historical Replay Architecture

The backtester simulates what Claude would have decided on past trading days:

```
For each historical trading day:
  1. Fetch market data as it appeared that day
  2. Scan for momentum candidates (volume spikes, price moves)
  3. Analyze news catalysts (FDA, earnings, etc.)
  4. Build same context Claude sees in live trading
  5. Ask Claude: "What would you do?"
  6. Simulate executing Claude's decision
  7. Track position throughout the day
  8. Check stops/targets using intraday data
  9. Close at end of day
  10. Record results
```

### 2. What Gets Tested

✅ **Claude's decision-making** - Does the AI choose good trades?
✅ **Catalyst detection** - Does news analysis improve results?
✅ **Risk management** - Do stops/targets work as designed?
✅ **Position sizing** - Is 2% risk per trade effective?
✅ **Win rate & profit factor** - Is the system profitable?
✅ **Drawdown management** - How bad can losses get?

---

## Running a Backtest

### Basic Usage

```bash
# Test last 30 days (default)
python backtest.py

# Test last 60 days
python backtest.py --days 60

# Test specific date range
python backtest.py --start 2024-10-01 --end 2024-11-01

# Custom capital
python backtest.py --capital 50000

# Custom max positions
python backtest.py --max-positions 5

# Save to custom file
python backtest.py --output my_backtest.json
```

### Example Output

```
================================================================================
MOMENTUM HUNTER - HISTORICAL BACKTEST
================================================================================

Period: 2024-10-01 to 2024-11-01
Starting Capital: $100,000.00
Max Positions: 3

This will:
  - Replay historical market conditions
  - Ask Claude to make decisions on each day
  - Simulate trade execution and management
  - Calculate performance metrics

⚠️  Note: This will use Claude API credits (est. $5-20 depending on period)
================================================================================

Continue with backtest? (y/n): y

================================================================================
STARTING HISTORICAL BACKTEST
================================================================================
Period: 2024-10-01 to 2024-11-01
Starting Capital: $100,000
Max Positions: 3
================================================================================

📅 2024-10-01
--------------------------------------------------------------------------------
Found 12 candidates
🤖 Claude Decision: BUY NVAX
   Confidence: 8/10
   Reasoning: FDA approval catalyst is strong (9/10). Stock showing healthy...

  📈 Simulated BUY: NVAX x 500 @ $16.50
     Stop: $15.80, Target: $18.50

📅 2024-10-02
--------------------------------------------------------------------------------
  ✅ CLOSED: NVAX @ $18.48 (profit_target)
     P&L: +$990.00 (+12.0%)
📊 EOD Equity: $100,990

...

================================================================================
BACKTEST RESULTS
================================================================================

Period: 2024-10-01 to 2024-11-01
Starting Capital: $100,000.00
Ending Capital:   $105,420.00
Total Return:     +$5,420.00 (+5.42%)

📊 TRADE STATISTICS
--------------------------------------------------------------------------------
Total Trades:     23
Winning Trades:   14
Losing Trades:    9
Win Rate:         60.9%

💰 P&L BREAKDOWN
--------------------------------------------------------------------------------
Total Profit:     $8,240.00
Total Loss:       $2,820.00
Profit Factor:    2.92
Average Win:      $588.57
Average Loss:     $313.33
Average Trade:    +$235.65

📈 BEST/WORST
--------------------------------------------------------------------------------
Best Trade:       +$1,240.00
Worst Trade:      -$580.00
Max Drawdown:     $1,120.00 (1.12%)

================================================================================
✅ ASSESSMENT: System shows promise for live trading
   Consider paper trading to validate further.
================================================================================

✅ Backtest complete! Results saved to backtest_results.json
```

---

## Understanding the Results

### Key Metrics

**Win Rate**
- Target: > 55%
- Good: > 60%
- Excellent: > 65%
- What it means: Percentage of trades that were profitable

**Profit Factor**
- Target: > 1.5
- Good: > 2.0
- Excellent: > 2.5
- What it means: Total profit ÷ Total loss (how much you make per $1 lost)

**Total Return**
- Target: Positive overall
- What it means: Did Claude make money?

**Max Drawdown**
- Target: < 15%
- Good: < 10%
- Excellent: < 5%
- What it means: Worst peak-to-valley equity drop

**Average Win vs Average Loss**
- Target: Avg Win > 2x Avg Loss
- What it means: Risk/reward ratio in practice

### Minimum Viable Performance

To consider live trading, you need:
- ✅ 30+ trades (statistically significant)
- ✅ Win rate > 55%
- ✅ Profit factor > 1.5
- ✅ Positive total return
- ✅ Max drawdown < 15%

If you hit these targets, the system is worth paper trading.

---

## What the Results File Contains

The `backtest_results.json` file has:

```json
{
  "start_date": "2024-10-01T00:00:00",
  "end_date": "2024-11-01T00:00:00",
  "starting_capital": 100000.0,
  "ending_capital": 105420.0,
  "total_return": 5420.0,
  "total_return_percent": 5.42,

  "total_trades": 23,
  "winning_trades": 14,
  "losing_trades": 9,
  "win_rate": 60.87,

  "profit_factor": 2.92,
  "avg_win": 588.57,
  "avg_loss": 313.33,

  "trades": [
    {
      "symbol": "NVAX",
      "entry_date": "2024-10-01T09:35:00",
      "entry_price": 16.50,
      "exit_date": "2024-10-02T11:23:00",
      "exit_price": 18.48,
      "exit_reason": "profit_target",
      "shares": 500,
      "stop_loss": 15.80,
      "profit_target": 18.50,
      "pnl": 990.0,
      "pnl_percent": 12.0,
      "claude_reasoning": "FDA approval catalyst is strong...",
      "catalyst_type": "FDA",
      "catalyst_strength": 9.0
    },
    // ... more trades
  ],

  "daily_equity": {
    "2024-10-01": 100000.0,
    "2024-10-02": 100990.0,
    // ... daily values
  }
}
```

You can analyze this to:
- See every trade Claude made
- Read Claude's reasoning for each decision
- Track equity curve over time
- Identify patterns in wins vs losses
- Understand which catalyst types work best

---

## Comparing to Live Trading

### Backtesting vs Paper Trading vs Live

**Historical Backtest (This Tool)**
- ✅ Fast - test months in minutes
- ✅ Cheap - no market waiting
- ✅ Tests Claude's intelligence
- ❌ Limited historical data access
- ❌ Potential look-ahead bias
- ❌ Can't perfectly simulate fills

**Paper Trading (run.py)**
- ✅ Real market conditions
- ✅ Real-time catalyst detection
- ✅ Exact fill simulation
- ✅ Proves system works before risking money
- ❌ Slow - need to wait for trades
- ❌ Must run during market hours

**Live Trading (run.py --live)**
- ✅ Real profits
- ✅ Real validation
- ❌ Real risk
- ❌ Requires proven track record

### Recommended Path

1. **Week 1: Historical Backtest** (This tool)
   - Test last 60-90 days
   - Verify win rate > 55%, profit factor > 1.5
   - Analyze Claude's reasoning
   - If fails → refine prompts, try again

2. **Weeks 2-5: Paper Trading** (run.py)
   - Run system live during market hours
   - Let it make 30+ real-time decisions
   - Verify backtest results hold up
   - If fails → back to step 1

3. **Month 2+: Live Trading** (run.py --live)
   - Start with $1k-5k (small capital)
   - Monitor closely
   - Scale gradually if successful

---

## API Cost Estimates

Claude API calls during backtesting:

**30-day backtest:**
- ~20 trading days
- ~1-3 decisions per day
- ~40-60 API calls total
- Cost: **$2-8**

**60-day backtest:**
- ~40 trading days
- ~1-3 decisions per day
- ~80-120 API calls total
- Cost: **$5-15**

**90-day backtest:**
- ~60 trading days
- ~1-3 decisions per day
- ~120-180 API calls total
- Cost: **$8-20**

Cheap compared to potential insights!

---

## Limitations & Caveats

### What This Tests Well

✅ Claude's decision quality
✅ Risk/reward ratios
✅ Stop/target placement
✅ Overall profitability
✅ Win rate & profit factor

### What This Doesn't Test Perfectly

⚠️ **Exact fill prices** - Uses simulated market orders, not limit orders
⚠️ **Slippage** - Assumes fills at exact stop/target prices
⚠️ **Partial fills** - Assumes full position fills immediately
⚠️ **Extended hours** - Only tests regular market hours
⚠️ **Black swan events** - Past performance ≠ future results
⚠️ **Market regime changes** - Bull vs bear markets behave differently

### Important Notes

1. **Historical data limitations** - We use Alpaca's free historical data, which may have gaps
2. **Look-ahead bias** - We try to avoid it, but perfect point-in-time data is hard
3. **Catalyst detection** - News analysis on historical data may differ from real-time
4. **Overfitting risk** - Don't over-optimize based on backtest results

**Bottom line:** Use backtest for directional confidence, but validate with paper trading before going live.

---

## Interpreting Claude's Decisions

The backtest logs Claude's reasoning for each decision. Look for:

### Good Decision Patterns

✅ "Strong catalyst (FDA approval 9/10) with clear entry at support"
✅ "High volume + news + technical setup aligns, taking trade"
✅ "Risk/reward 3:1, catalyst strength 8/10, high confidence"

### Red Flag Patterns

❌ "Weak catalyst, chasing momentum, passing"
❌ "Stock already ran 40%, poor entry, HOLD"
❌ "Market conditions deteriorating, reducing exposure"

If Claude is consistently reasoning well but still losing, it might be:
- Market conditions (choppy/ranging)
- Strategy doesn't fit current regime
- Risk parameters too tight
- Need longer testing period

If Claude's reasoning seems weak:
- Refine prompts in `backend/brain/claude_engine.py`
- Adjust catalyst detection rules
- Modify risk parameters

---

## Troubleshooting

### "No candidates found" for most days

**Cause:** Market was quiet, or scanner criteria too strict
**Fix:** This is normal! Some days have no opportunities. If it's EVERY day:
- Lower `min_relative_volume` in scanner config
- Widen `min_price` / `max_price` range
- Check if you're testing during market crash (all stocks down)

### "Could not fetch quote for {symbol}"

**Cause:** Historical data not available for that symbol
**Fix:** This is logged as a warning and skipped. Normal for some tickers.

### "Backtest returns are wildly different from paper trading"

**Cause:** Historical data quality, or market regime changed
**Fix:**
- Run longer backtest (90+ days)
- Compare date ranges (was backtest during bull run, paper trading during crash?)
- Trust paper trading more than backtest

### "Claude keeps saying HOLD"

**Cause:** Claude is being selective (this is GOOD)
**Fix:** Don't force trades. Selective = better win rate. If it's extreme:
- Check if market is closed/crashed
- Review candidates being presented
- Ensure catalysts are being detected

---

## Next Steps After Backtesting

### If Results Are Good (Win rate > 55%, Profit Factor > 1.5)

1. **Run paper trading** for 30 days
2. **Compare results** - do they match backtest?
3. **Analyze differences** - what changed?
4. **If paper trading confirms** → consider small live capital

### If Results Are Poor

1. **Analyze losing trades** - read Claude's reasoning
2. **Identify patterns** - what types of trades lose?
3. **Refine prompts** - improve Claude's decision rules
4. **Adjust risk params** - tighter stops? Different R/R?
5. **Backtest again** - did changes improve?

### Iterative Improvement Loop

```
Backtest → Analyze → Refine → Backtest → Paper Trade → Live
    ↑                                                      ↓
    └──────────────────────────────────────────────────────┘
```

---

## Advanced: Analyzing Backtest Data

Load the JSON results for deeper analysis:

```python
import json
import pandas as pd

# Load results
with open('backtest_results.json') as f:
    results = json.load(f)

# Convert trades to DataFrame
trades_df = pd.DataFrame(results['trades'])

# Analyze by catalyst type
catalyst_performance = trades_df.groupby('catalyst_type').agg({
    'pnl': ['sum', 'mean', 'count'],
    'pnl_percent': 'mean'
})
print(catalyst_performance)

# Analyze by day of week
trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
trades_df['day_of_week'] = trades_df['entry_date'].dt.day_name()
day_performance = trades_df.groupby('day_of_week')['pnl'].mean()
print(day_performance)

# Plot equity curve
equity_df = pd.DataFrame(
    list(results['daily_equity'].items()),
    columns=['date', 'equity']
)
equity_df['date'] = pd.to_datetime(equity_df['date'])
equity_df.plot(x='date', y='equity', title='Equity Curve')
```

Insights you might find:
- FDA trades outperform earnings trades
- Mondays have lower win rate
- First hour trades work better than mid-day
- Certain symbols appear in multiple winners

Use these insights to refine the system!

---

## Summary

**Historical Backtesting:**
- Tests Claude's intelligence on past data
- Fast, cheap way to validate strategy
- Provides directional confidence
- NOT a guarantee of future performance

**Use it to:**
- Prove the concept before paper trading
- Identify major flaws early
- Understand Claude's decision patterns
- Build confidence in the system

**Don't use it to:**
- Replace paper trading
- Over-optimize parameters
- Guarantee future returns
- Skip live validation

**Next step:** Run `python backtest.py` and see what Claude would have done!

---

**Built with 🧠 by Claude AI + Tanam Bam Sinha**
**January 2025**
