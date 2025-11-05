# Performance Metrics & Analysis

**Version:** 1.0
**Last Updated:** 2025-11-04
**Status:** Reference Document

---

## Purpose

This document defines all performance metrics used to evaluate the DP20 strategy, including calculation methods and interpretation guidelines.

---

## Trade Journal Schema (29 Columns)

Full schema documented in [qqq_pullback_strategy.md](../strategies/qqq_pullback_strategy.md)

**Key columns for analysis:**
- `trade_date`, `entered?`, `entry_price`, `eod_exit_price`
- `stop_price`, `risk_per_share`, `R_multiple`
- `entry_bucket`, `atr_pct_of_price`
- `gross_pnl`, `net_pnl`

---

## Core Performance Metrics

### 1. Expectancy (Primary Metric)

**Definition:** Average R-multiple across all trades

**Formula:**
```
Expectancy = Σ(R_multiple) / N
where N = number of trades
```

**Interpretation:**
- `E > 1.0`: Profitable strategy (avg win > avg risk)
- `E = 0.5`: Each trade wins 0.5R on average
- `E < 0`: Losing strategy

**Why it matters:** Expectancy is position-size independent. Tells you the edge per trade.

**Calculation:**
```python
trades = df[df['entered'] == True]
expectancy = trades['R_multiple'].mean()
```

---

### 2. Win Rate

**Definition:** Percentage of trades that are profitable

**Formula:**
```
Win Rate = (Winners / Total Trades) × 100%
```

**Calculation:**
```python
winners = trades[trades['net_pnl'] > 0]
win_rate = len(winners) / len(trades)
```

**Interpretation:**
- High win rate (>60%) + low expectancy → small wins, big losses
- Low win rate (<40%) + high expectancy → big wins, small losses
- Target: >55% for this mean-reversion style strategy

---

### 3. Average R-Multiple (Same as Expectancy)

**By Outcome:**
```python
avg_winner_r = trades[trades['R_multiple'] > 0]['R_multiple'].mean()
avg_loser_r = trades[trades['R_multiple'] <= 0]['R_multiple'].mean()
```

**Interpretation:**
- Ideal: `avg_winner_r` > 2R, `avg_loser_r` ~ -0.5R (stopped out early)
- Red flag: `avg_loser_r` < -1.5R (stops too wide or slippage issues)

---

### 4. Profit Factor

**Definition:** Ratio of gross profit to gross loss

**Formula:**
```
Profit Factor = Gross Profit / Gross Loss
```

**Calculation:**
```python
gross_profit = trades[trades['net_pnl'] > 0]['net_pnl'].sum()
gross_loss = abs(trades[trades['net_pnl'] <= 0]['net_pnl'].sum())
profit_factor = gross_profit / gross_loss
```

**Interpretation:**
- `PF > 2.0`: Excellent
- `PF > 1.5`: Good
- `PF > 1.0`: Profitable (but marginal)
- `PF < 1.0`: Losing strategy

---

### 5. Maximum Drawdown

**Definition:** Largest peak-to-trough decline in cumulative P&L

**Calculation:**
```python
trades['cumulative_pnl'] = trades['net_pnl'].cumsum()
trades['running_max'] = trades['cumulative_pnl'].cummax()
trades['drawdown'] = trades['cumulative_pnl'] - trades['running_max']
max_drawdown = trades['drawdown'].min()
```

**Interpretation:**
- Important for position sizing
- If max DD = -$500, ensure account can handle 2-3x that

---

### 6. Consecutive Losses (Streak)

**Definition:** Maximum number of losing trades in a row

**Calculation:**
```python
def max_consecutive_losses(trades):
    trades['is_loser'] = trades['net_pnl'] <= 0
    streaks = []
    current_streak = 0

    for is_loser in trades['is_loser']:
        if is_loser:
            current_streak += 1
        else:
            if current_streak > 0:
                streaks.append(current_streak)
            current_streak = 0

    return max(streaks) if streaks else 0
```

**Interpretation:**
- Critical for risk of ruin calculations
- If max streak = 5, position sizing must account for 5+ loss scenario

---

## Time-of-Day Analysis

### Purpose
DP20 entry window is 10:00-10:30 AM. Does entry time within this window matter?

### Analysis Method

**1. Bucket Entries:**
```python
def bucket_time(entry_time):
    minute = entry_time.minute + (entry_time.hour - 10) * 60
    if minute < 10:
        return "10:00-10:10"
    elif minute < 20:
        return "10:10-10:20"
    else:
        return "10:20-10:30"

trades['entry_bucket'] = trades['entry_time_et'].apply(bucket_time)
```

**2. Calculate Stats by Bucket:**
```python
time_analysis = trades.groupby('entry_bucket').agg({
    'R_multiple': ['mean', 'std', 'count'],
    'entered': 'count'
}).round(2)
```

**3. Interpret Results:**

Example:
```
entry_bucket   | avg_R | count | win_rate
10:00-10:10    |  1.8  |  18   |  72%      ← Best
10:10-10:20    |  0.9  |  15   |  60%      ← OK
10:20-10:30    |  0.3  |  12   |  50%      ← Worst
```

**Insight:** Earlier entries perform better → consider narrowing window to 10:00-10:15

---

## Volatility Regime Analysis

### Purpose
Does strategy perform differently in low vs high volatility environments?

### Analysis Method

**1. Calculate Volatility Metric:**
```python
trades['atr_pct_of_price'] = trades['atr_14_2m_at_entry'] / trades['entry_price']
```

**2. Create Terciles (Low/Med/High):**
```python
trades['vol_regime'] = pd.qcut(
    trades['atr_pct_of_price'],
    q=3,
    labels=['low', 'medium', 'high']
)
```

**3. Calculate Stats by Regime:**
```python
vol_analysis = trades.groupby('vol_regime').agg({
    'R_multiple': ['mean', 'std', 'count']
}).round(2)
```

**4. Interpret Results:**

Example:
```
vol_regime | avg_R | count
low        |  1.6  |  20     ← Best (stable moves)
medium     |  1.0  |  15     ← OK
high       |  0.2  |  10     ← Worst (whipsaws)
```

**Insight:** Avoid trading when ATR > 0.8% of price (high vol filter)

---

## Advanced Metrics

### MAE (Maximum Adverse Excursion)

**Definition:** How far did the trade go against you?

**Purpose:** Understand if stops are appropriately placed

**Calculation:**
```python
# For each trade, find worst price from entry to exit
def calculate_mae(position_bars, entry_price):
    worst_price = position_bars['low'].min()
    mae = entry_price - worst_price
    return mae

trades['mae'] = trades.apply(lambda row: calculate_mae(...), axis=1)
trades['mae_R'] = trades['mae'] / trades['risk_per_share']
```

**Analysis:**
```python
# How many trades came within X% of stop?
within_50pct = trades[trades['mae_R'] > 0.5].shape[0]
within_90pct = trades[trades['mae_R'] > 0.9].shape[0]

print(f"{within_50pct} trades reached 50% of stop distance")
print(f"{within_90pct} trades reached 90% of stop distance")
```

**Insight:** If many trades reach 90% of stop but don't get stopped out → stops might be too tight

---

### MFE (Maximum Favorable Excursion)

**Definition:** How far did the trade go in your favor?

**Purpose:** Understand profit-taking opportunities

**Calculation:**
```python
def calculate_mfe(position_bars, entry_price):
    best_price = position_bars['high'].max()
    mfe = best_price - entry_price
    return mfe

trades['mfe'] = trades.apply(lambda row: calculate_mfe(...), axis=1)
trades['mfe_R'] = trades['mfe'] / trades['risk_per_share']
```

**Analysis:**
```python
# Compare MFE to actual exit
trades['captured_pct'] = trades['R_multiple'] / trades['mfe_R']

avg_captured = trades['captured_pct'].mean()
print(f"On average, captured {avg_captured:.0%} of available move")
```

**Insight:** If capturing <50% → consider profit targets or trailing stops

---

## Statistical Significance

### Sample Size Requirements

**For reliable expectancy:**
- Minimum: 30 trades
- Preferred: 100+ trades
- Gold standard: 500+ trades

**For time-of-day buckets:**
- Minimum: 10 trades per bucket
- Preferred: 30+ per bucket

### Confidence Intervals

**Expectancy 95% CI:**
```python
from scipy import stats

mean = trades['R_multiple'].mean()
std = trades['R_multiple'].std()
n = len(trades)

ci_95 = stats.t.interval(
    confidence=0.95,
    df=n-1,
    loc=mean,
    scale=std/np.sqrt(n)
)

print(f"Expectancy: {mean:.2f}R (95% CI: {ci_95[0]:.2f} to {ci_95[1]:.2f})")
```

**Interpretation:**
- If CI includes 0 → not statistically significant
- If CI = [0.8, 1.6] → true expectancy likely between these values

---

## Report Template

### Summary Statistics:

```
DP20 Strategy Backtest Results
Period: 2025-09-01 to 2025-11-04 (45 trading days)

=== Core Metrics ===
Total Trades: 45
Winners: 28 (62.2%)
Losers: 17 (37.8%)

Expectancy: 1.20R (95% CI: 0.95 to 1.45)
Total P&L: $2,340.50
Average Trade: $52.01

Profit Factor: 1.82
Max Drawdown: -$890.00 (-0.89%)
Max Consecutive Losses: 5

=== Time-of-Day Analysis ===
10:00-10:10: 1.80R avg (18 trades, 72% win rate) ✓ Best
10:10-10:20: 0.90R avg (15 trades, 60% win rate)
10:20-10:30: 0.30R avg (12 trades, 50% win rate) ✗ Worst

=== Volatility Regime Analysis ===
Low Vol (ATR < 0.5%): 1.60R avg (20 trades) ✓ Best
Med Vol (ATR 0.5-0.7%): 1.00R avg (15 trades)
High Vol (ATR > 0.7%): 0.20R avg (10 trades) ✗ Worst

=== Risk Metrics ===
Avg Winner: +2.20R
Avg Loser: -0.60R
Win/Loss Ratio: 3.67

MAE Analysis: 12 trades (27%) reached within 10% of stop
MFE Analysis: Captured 68% of available move on average
```

---

## Optimization Insights

### Parameter Tuning Based on Metrics

**If Win Rate < 50%:**
- Tighten entry filters (higher reversal strength threshold)
- Narrow time window (take only best setups)

**If Expectancy < 0.5R:**
- Widen stops (reduce premature stop-outs)
- Earlier exit time (avoid end-of-day reversals)

**If Max Drawdown too large:**
- Reduce position size
- Add volatility filter
- Limit trades per week

**If High Vol regime performs poorly:**
- Add filter: skip days when ATR > 0.8% of price
- Or: reduce position size in high vol

---

**Related Documents:**
- [AI Analysis Guide](./ai-analysis-guide.md)
- [DP20 Strategy Spec](../strategies/qqq_dp20_strategy_spec.md)
- [Backtest Engine](../system-design/backtest-engine.md)
