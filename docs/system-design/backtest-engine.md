# Backtest Engine Architecture

**Version:** 1.0
**Last Updated:** 2025-11-04
**Status:** Design Phase

---

## Purpose

This document describes how the backtest engine simulates the DP20 strategy over historical data, tracking trades from entry to exit including intraday stop loss monitoring.

---

## Design Philosophy

### Vectorized vs Event-Driven

**Backtesting (Phase 1):** Vectorized/batch processing
- Load all data at once
- Use pandas operations (fast, simple)
- Process entire date ranges together
- No need to simulate candle-by-candle

**Live Trading (Future):** Event-driven processing
- Process each candle as it arrives
- Maintain state machine
- React in real-time

**Key Insight:** Same core logic, different execution pattern. Core strategy code works for both.

---

## Backtest Flow

### High-Level Process:

```
1. Load Data
   - Intraday 2-min bars (60 trading days)
   - Daily bars (200+ days for SMA200)
   ↓
2. Calculate Indicators
   - EMA20 (from 2-min close prices)
   - ATR(14) (from 2-min bars)
   - SMA200 (from daily close prices)
   ↓
3. For Each Trading Day:
   a. Check trend filter (open > SMA200)
   b. Detect pullback/reversal signals (10:00-10:30 window)
   c. If signal → simulate entry
   d. If entered → track through EOD
      - Monitor every 2-min bar for stop hit
      - Exit at 3:55 PM or stop price (whichever first)
   e. Record trade to journal
   ↓
4. Aggregate Results
   - Compile all daily trades into journal DataFrame
   - Calculate summary statistics
   ↓
5. Output
   - Trade journal CSV (29 columns)
   - Summary statistics
   - Optional: AI analysis report
```

---

## Core Function Signature

```python
def run_backtest(
    symbol: str,
    start_date: date,
    end_date: date,
    data_fetcher: DataFetcher,
    strategy_params: dict = None
) -> BacktestResults:
    """
    Run DP20 strategy backtest over date range.

    Args:
        symbol: Ticker to backtest (e.g., 'QQQ')
        start_date: First day of backtest
        end_date: Last day of backtest
        data_fetcher: Data source (Alpaca, CSV, etc.)
        strategy_params: Override default parameters

    Returns:
        BacktestResults with:
        - trade_journal: DataFrame (one row per day)
        - summary_stats: dict
        - daily_bars: DataFrame (for debugging)
    """
```

---

## Step 1: Data Loading & Indicator Calculation

### Fetch Data:

```python
# Fetch intraday bars
intraday_df = data_fetcher.fetch_intraday_bars(
    symbol='QQQ',
    start=start_date,
    end=end_date
)

# Fetch daily bars (need 200+ for SMA200)
daily_df = data_fetcher.fetch_daily_bars(
    symbol='QQQ',
    start=start_date - timedelta(days=300),  # Buffer for SMA200
    end=end_date
)
```

### Calculate Indicators:

```python
# Add EMA20 to intraday data
intraday_df['ema20'] = calculate_ema(intraday_df['close'], period=20)

# Add ATR(14) to intraday data
intraday_df['atr14'] = calculate_atr(intraday_df, period=14)

# Add SMA200 to daily data
daily_df['sma200'] = calculate_sma(daily_df['close'], period=200)

# Add date column to intraday for grouping
intraday_df['date'] = intraday_df['timestamp'].dt.date
```

---

## Step 2: Day-by-Day Processing

### Group by Trading Day:

```python
results = []

for trade_date, day_bars in intraday_df.groupby('date'):
    # Get SMA200 for this day
    sma200 = daily_df[daily_df['date'] == trade_date]['sma200'].iloc[0]

    # Process this day
    trade_result = process_trading_day(
        day_bars=day_bars,
        sma200=sma200,
        strategy_params=strategy_params
    )

    results.append(trade_result)

# Combine into journal DataFrame
trade_journal = pd.DataFrame(results)
```

---

## Step 3: Process Single Trading Day

### Function Signature:

```python
def process_trading_day(
    day_bars: pd.DataFrame,
    sma200: float,
    strategy_params: dict
) -> dict:
    """
    Process one trading day, detect signals, simulate trade.

    Returns dict with trade journal row (29 columns).
    """
```

### Logic Flow:

```python
def process_trading_day(day_bars, sma200, params):
    # Default: no trade
    result = {
        'trade_date': day_bars['date'].iloc[0],
        'trend_valid': False,
        'entered': False,
        # ... 26 more columns
    }

    # Step 1: Trend filter
    day_open = day_bars.iloc[0]['open']
    result['trend_valid'] = (day_open > sma200)
    result['sma200_daily_at_open'] = sma200

    if not result['trend_valid']:
        result['notes'] = 'Trend filter failed: open < SMA200'
        return result

    # Step 2: Detect signal in time window (10:00-10:30)
    signal_bars = day_bars[
        (day_bars['timestamp'].dt.time >= time(10, 0)) &
        (day_bars['timestamp'].dt.time <= time(10, 30))
    ]

    signal = detect_dp20_signal(signal_bars, params)

    if signal is None:
        result['notes'] = 'No signal in 10:00-10:30 window'
        return result

    # Step 3: Signal detected! Simulate entry
    entry_bar = get_entry_bar(day_bars, signal['confirmation_time'])

    if entry_bar is None:
        result['notes'] = 'Entry bar not found'
        return result

    # Fill in entry details
    result['entered'] = True
    result['entry_time_et'] = entry_bar['timestamp']
    result['entry_price'] = entry_bar['open']
    result['ema20_at_entry'] = entry_bar['ema20']
    result['atr_14_2m_at_entry'] = entry_bar['atr14']

    # Calculate stop
    stop_distance = 1.2 * entry_bar['atr14']
    stop_price = entry_bar['open'] - stop_distance
    result['stop_distance'] = stop_distance
    result['stop_price'] = stop_price

    # Step 4: Track position through end of day
    position_bars = day_bars[day_bars['timestamp'] >= entry_bar['timestamp']]

    exit_result = simulate_position(position_bars, entry_bar['open'], stop_price, params)

    # Fill in exit details
    result.update(exit_result)

    return result
```

---

## Step 4: Signal Detection Within Day

```python
def detect_dp20_signal(signal_window_bars, params):
    """
    Detect DP20 entry signal in 10:00-10:30 window.

    Returns dict with signal details or None if no signal.
    """
    # Track state
    pullback_detected = False
    reversal_bar = None

    for idx, bar in signal_window_bars.iterrows():
        # Looking for pullback (close < EMA20)
        if not pullback_detected:
            if bar['close'] < bar['ema20']:
                pullback_detected = True
            continue

        # Looking for reversal (close > EMA20 after pullback)
        if bar['close'] > bar['ema20']:
            # Check strength filter
            body_pct = (bar['close'] - bar['low']) / (bar['high'] - bar['low'])

            if body_pct > params.get('reversal_strength_threshold', 0.60):
                reversal_bar = bar
                break

    if reversal_bar is None:
        return None

    # Need confirmation candle (next bar)
    confirmation_idx = signal_window_bars.index.get_loc(reversal_bar.name) + 1

    if confirmation_idx >= len(signal_window_bars):
        return None  # No confirmation bar in window

    confirmation_bar = signal_window_bars.iloc[confirmation_idx]

    # Confirmation must close > EMA20
    if confirmation_bar['close'] < confirmation_bar['ema20']:
        return None  # Invalidated

    return {
        'pullback_time': pullback_detected_time,  # Track this in loop
        'reversal_time': reversal_bar['timestamp'],
        'reversal_strength': body_pct,
        'confirmation_time': confirmation_bar['timestamp'],
        'ema20': confirmation_bar['ema20'],
        'atr14': confirmation_bar['atr14'],
    }
```

---

## Step 5: Position Simulation (Entry → Exit)

```python
def simulate_position(position_bars, entry_price, stop_price, params):
    """
    Simulate holding position from entry to exit.

    Checks for:
    - Stop loss hit (any bar's low <= stop_price)
    - End-of-day exit (3:55 PM)

    Returns dict with exit details.
    """
    exit_time_target = time(15, 55)  # 3:55 PM ET

    for idx, bar in position_bars.iterrows():
        # Check stop hit
        if bar['low'] <= stop_price:
            return {
                'exit_reason': 'stop_loss',
                'eod_exit_time': bar['timestamp'],
                'eod_exit_price': stop_price,  # Assume filled at stop
                'stopped_out': True,
                'notes': f'Stopped out at {bar["timestamp"]}'
            }

        # Check EOD exit time
        if bar['timestamp'].time() >= exit_time_target:
            return {
                'exit_reason': 'eod',
                'eod_exit_time': bar['timestamp'],
                'eod_exit_price': bar['close'],
                'stopped_out': False,
                'notes': 'EOD exit at 3:55 PM'
            }

    # Should never reach here (bars go until 4:00 PM)
    # But handle edge case
    last_bar = position_bars.iloc[-1]
    return {
        'exit_reason': 'market_close',
        'eod_exit_time': last_bar['timestamp'],
        'eod_exit_price': last_bar['close'],
        'stopped_out': False,
        'notes': 'Exited at market close'
    }
```

---

## Step 6: Calculate Trade Metrics

After simulating entry and exit, calculate performance metrics:

```python
def calculate_trade_metrics(trade_result):
    """Add calculated metrics to trade result dict."""

    if not trade_result['entered']:
        return trade_result  # No trade, no metrics

    entry = trade_result['entry_price']
    exit_price = trade_result['eod_exit_price']
    stop = trade_result['stop_price']
    shares = trade_result.get('shares', 20)  # Fixed size

    # P&L calculations
    trade_result['gross_pnl'] = (exit_price - entry) * shares
    trade_result['fees_slippage'] = 0.0  # TODO: estimate
    trade_result['net_pnl'] = trade_result['gross_pnl'] - trade_result['fees_slippage']

    # Risk metrics
    trade_result['risk_per_share'] = entry - stop
    trade_result['R_multiple'] = (exit_price - entry) / trade_result['risk_per_share']

    # Analysis metrics
    ema20 = trade_result['ema20_at_entry']
    trade_result['dist_to_ema_bps'] = ((entry - ema20) / ema20) * 10000

    atr = trade_result['atr_14_2m_at_entry']
    trade_result['atr_pct_of_price'] = atr / entry

    # Time bucketing
    entry_time = trade_result['entry_time_et']
    trade_result['entry_bucket'] = bucket_time(entry_time)  # e.g., "10:00-10:10"

    # Bars since open
    market_open = entry_time.replace(hour=9, minute=30, second=0)
    minutes_since_open = (entry_time - market_open).total_seconds() / 60
    trade_result['bars_since_open'] = int(minutes_since_open / 2)

    return trade_result
```

---

## Step 7: Summary Statistics

```python
def calculate_summary_stats(trade_journal):
    """Calculate performance metrics from trade journal."""

    # Filter to actual trades (entered = True)
    trades = trade_journal[trade_journal['entered'] == True]

    if len(trades) == 0:
        return {'error': 'No trades taken'}

    # Basic stats
    total_trades = len(trades)
    winners = trades[trades['net_pnl'] > 0]
    losers = trades[trades['net_pnl'] <= 0]

    summary = {
        'total_trades': total_trades,
        'winners': len(winners),
        'losers': len(losers),
        'win_rate': len(winners) / total_trades,

        # R-multiple stats
        'avg_r_multiple': trades['R_multiple'].mean(),
        'median_r_multiple': trades['R_multiple'].median(),
        'std_r_multiple': trades['R_multiple'].std(),

        # Expectancy
        'expectancy': trades['R_multiple'].mean(),  # Same as avg R

        # P&L stats
        'total_pnl': trades['net_pnl'].sum(),
        'avg_pnl': trades['net_pnl'].mean(),
        'max_win': trades['net_pnl'].max(),
        'max_loss': trades['net_pnl'].min(),

        # Drawdown (simplified)
        'max_consecutive_losses': calculate_max_consecutive_losses(trades),
    }

    # Time-of-day analysis
    summary['by_time_bucket'] = trades.groupby('entry_bucket').agg({
        'R_multiple': ['mean', 'count'],
        'entered': 'count'
    }).to_dict()

    # Volatility regime analysis
    trades['vol_regime'] = pd.qcut(
        trades['atr_pct_of_price'],
        q=3,
        labels=['low', 'medium', 'high']
    )

    summary['by_volatility'] = trades.groupby('vol_regime').agg({
        'R_multiple': ['mean', 'count']
    }).to_dict()

    return summary
```

---

## Edge Cases & Considerations

### 1. **Indicator Warm-up Period**

**Problem:** EMA20 needs 20 bars to stabilize, ATR needs 14 bars

**Solution:**
- Start backtest from day 10 (after indicators stabilize)
- Or: Fetch extra data before backtest start
- Document in backtest results: "First 10 days excluded for indicator warm-up"

### 2. **Gaps & Missing Data**

**Problem:** Market holidays, data gaps, halts

**Solution:**
- Validate data completeness per day (expect 195 bars)
- If <95% complete → skip day, log warning
- Track skipped days in results

### 3. **Multiple Signals Same Day**

**Problem:** DP20 might trigger multiple times in 10:00-10:30 window

**Solution:**
- Take first valid signal only
- Strategy rule: "one trade per day max"
- Record first signal time, ignore subsequent

### 4. **Stop Loss Slippage**

**Problem:** Real stop may fill worse than stop price (gaps down)

**Solution:**
- Phase 1: Assume filled at stop price (optimistic)
- Phase 2: Add slippage model (e.g., 0.02% worse)
- Phase 3: Analyze actual fills in paper trading

### 5. **EOD Exit Execution**

**Problem:** Exit at 3:55 PM - what price?

**Options:**
- Use close of 3:54-3:56 bar (our approach)
- Use MOC (Market On Close) price (need special data)
- Estimate slippage (0.01%)

**Decision:** Use close of 3:54-3:56 bar, document assumption

---

## Output Format

### Trade Journal CSV (29 columns):

```csv
trade_date,trend_valid,sma200_daily_at_open,entry_window,first_close_below_time,reversal_candle_time,reversal_strength_ok,confirmation_candle_time,entered?,entry_time_et,entry_price,shares,ema20_at_entry,atr_14_2m_at_entry,atr_pct_of_price,stop_distance,stop_price,entry_bucket,bars_since_open,eod_exit_time,eod_exit_price,gross_pnl,fees_slippage,net_pnl,risk_per_share,R_multiple,dist_to_ema_bps,notes,chart_link_entry
2025-09-03,TRUE,420.5,10:00-10:30,10:12:00,10:16:00,TRUE,10:18:00,TRUE,10:20:00,435.20,20,435.00,0.42,0.00096,0.50,434.70,10:20-10:30,25,15:54:00,437.50,46.00,0.00,46.00,0.50,4.60,45.8,"Clean reversal",
2025-09-04,TRUE,420.8,10:00-10:30,,,,,FALSE,,,20,,,,,,,,,,,,,"No reversal after pullback",
```

### Summary Statistics JSON:

```json
{
  "total_trades": 45,
  "winners": 28,
  "losers": 17,
  "win_rate": 0.622,
  "avg_r_multiple": 1.2,
  "expectancy": 1.2,
  "total_pnl": 2340.50,
  "by_time_bucket": {
    "10:00-10:10": {"mean": 1.8, "count": 18},
    "10:10-10:20": {"mean": 0.9, "count": 15},
    "10:20-10:30": {"mean": 0.3, "count": 12}
  },
  "by_volatility": {
    "low": {"mean": 1.6, "count": 20},
    "medium": {"mean": 1.0, "count": 15},
    "high": {"mean": 0.2, "count": 10}
  }
}
```

---

## Performance Optimization

### Vectorization Opportunities:

**Slow (iterative):**
```python
for idx, bar in df.iterrows():  # SLOW
    if bar['close'] < bar['ema20']:
        pullback = True
```

**Fast (vectorized):**
```python
df['below_ema'] = df['close'] < df['ema20']
pullback_bars = df[df['below_ema']]
```

**For DP20:** Some logic needs iteration (state tracking), but use vectorization where possible.

---

## Testing Strategy

### Unit Tests:

1. **Test indicator calculations** (EMA, ATR, SMA) against known values
2. **Test signal detection** with synthetic data (known pullback/reversal)
3. **Test stop loss tracking** (bar hits stop vs doesn't)
4. **Test metric calculations** (R-multiple, P&L formulas)

### Integration Tests:

1. **End-to-end backtest** on small dataset (1 week)
2. **Validate output format** (29 columns present, types correct)
3. **Edge case handling** (no trades, all trades, missing data)

---

**Related Documents:**
- [Architecture Overview](./architecture-overview.md)
- [Data Pipeline](./data-pipeline.md)
- [Signal Detection](./signal-detection.md)
- [Performance Metrics](../analysis/performance-metrics.md)
