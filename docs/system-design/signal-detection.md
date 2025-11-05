# DP20 Signal Detection Implementation

**Version:** 1.0
**Last Updated:** 2025-11-04
**Status:** Design Phase

---

## Purpose

This document provides detailed implementation specifications for the QQQ DP20 (Deep Pullback 20) strategy signal detection logic.

---

## Strategy Quick Reference

**Full Specification:** See [docs/strategies/qqq_dp20_strategy_spec.md](../strategies/qqq_dp20_strategy_spec.md)

**Entry Logic (6 Steps):**
1. **Trend Filter:** Trade only if open > 200-day SMA
2. **Time Window:** Evaluate signals 10:00-10:30 AM ET only
3. **Pullback:** Wait for candle close below EMA20
4. **Reversal:** Wait for candle close back above EMA20
5. **Strength Filter:** (Close - Low)/(High - Low) > 0.60
6. **Confirmation:** Wait one more candle; if closes below EMA20 → invalidate

**Entry Execution:** Open of candle after confirmation

**Exit:** 3:55 PM ET (end-of-day)

**Stop:** Entry - (1.2 × ATR(14))

---

## Implementation Approach

### State Machine vs Boolean Masks

**Two Approaches:**

**1. State Machine (Event-Driven)**
- Track state: WAITING_PULLBACK → PULLBACK → REVERSAL → CONFIRMATION → ENTRY
- Process candles one-by-one
- Suitable for live trading

**2. Boolean Masks (Vectorized)**
- Use pandas boolean indexing
- Process all candles at once
- Suitable for backtesting

**Decision:** Use **Boolean Masks for backtesting** (Phase 1), adapt to State Machine for live trading (Phase 3)

---

## Core Function Signature

```python
def detect_dp20_signal(
    day_bars: pd.DataFrame,
    sma200: float,
    params: dict = None
) -> Optional[dict]:
    """
    Detect DP20 entry signal for a single trading day.

    Args:
        day_bars: DataFrame with 2-min bars for one day (must include ema20, atr14 columns)
        sma200: 200-day SMA value for trend filter
        params: Strategy parameters (optional overrides)

    Returns:
        dict with signal details if detected, None otherwise

    Signal dict structure:
    {
        'signal_detected': True,
        'pullback_time': datetime,
        'reversal_time': datetime,
        'reversal_strength': float,  # Body percentage
        'confirmation_time': datetime,
        'entry_time': datetime,  # Next candle after confirmation
        'entry_price': float,  # Open of entry candle
        'ema20_at_entry': float,
        'atr14_at_entry': float,
        'stop_price': float,
    }
    """
```

---

## Step-by-Step Implementation

### Step 1: Trend Filter

```python
def check_trend_filter(day_bars, sma200):
    """Check if trend filter passes (open > SMA200)."""
    day_open = day_bars.iloc[0]['open']

    if day_open <= sma200:
        return False, f"Trend filter failed: open {day_open:.2f} <= SMA200 {sma200:.2f}"

    return True, "Trend filter passed"
```

---

### Step 2: Time Window Filter

```python
def filter_signal_window(day_bars, start_time=time(10, 0), end_time=time(10, 30)):
    """
    Extract bars within signal evaluation window.

    Default: 10:00 AM - 10:30 AM ET
    """
    signal_bars = day_bars[
        (day_bars['timestamp'].dt.time >= start_time) &
        (day_bars['timestamp'].dt.time <= end_time)
    ].copy()

    if signal_bars.empty:
        return None, "No bars in signal window (10:00-10:30 AM)"

    return signal_bars, f"{len(signal_bars)} bars in signal window"
```

---

### Step 3: Pullback Detection

```python
def detect_pullback(signal_bars):
    """
    Find first candle that closes below EMA20.

    Returns: (pullback_bar, pullback_index) or (None, None)
    """
    # Boolean mask: close < ema20
    pullback_mask = signal_bars['close'] < signal_bars['ema20']

    if not pullback_mask.any():
        return None, None  # No pullback detected

    # Get first pullback bar
    pullback_bars = signal_bars[pullback_mask]
    pullback_bar = pullback_bars.iloc[0]
    pullback_idx = signal_bars.index.get_loc(pullback_bar.name)

    return pullback_bar, pullback_idx
```

---

### Step 4: Reversal Detection (with Strength Filter)

```python
def detect_reversal(signal_bars, pullback_idx, strength_threshold=0.60):
    """
    Find first candle after pullback that closes above EMA20 AND passes strength filter.

    Strength filter: (Close - Low) / (High - Low) > threshold

    Returns: (reversal_bar, reversal_index) or (None, None)
    """
    # Only look at bars after pullback
    after_pullback = signal_bars.iloc[pullback_idx + 1:]

    if after_pullback.empty:
        return None, None  # No bars after pullback in window

    # Boolean mask: close > ema20 (reversal condition)
    reversal_mask = after_pullback['close'] > after_pullback['ema20']

    if not reversal_mask.any():
        return None, None  # No reversal detected

    # Check strength filter on reversal candidates
    reversal_candidates = after_pullback[reversal_mask].copy()

    # Calculate body percentage
    reversal_candidates['body_pct'] = (
        (reversal_candidates['close'] - reversal_candidates['low']) /
        (reversal_candidates['high'] - reversal_candidates['low'])
    )

    # Filter by strength
    strong_reversals = reversal_candidates[
        reversal_candidates['body_pct'] > strength_threshold
    ]

    if strong_reversals.empty:
        return None, None  # Reversals detected but none strong enough

    # Take first strong reversal
    reversal_bar = strong_reversals.iloc[0]
    reversal_idx = signal_bars.index.get_loc(reversal_bar.name)

    return reversal_bar, reversal_idx
```

---

### Step 5: Confirmation

```python
def check_confirmation(signal_bars, reversal_idx):
    """
    Check confirmation candle (next candle after reversal).

    Confirmation candle must close > EMA20, otherwise signal invalidated.

    Returns: (confirmation_bar, confirmation_index) or (None, None)
    """
    confirmation_idx = reversal_idx + 1

    # Check if confirmation candle exists in signal window
    if confirmation_idx >= len(signal_bars):
        return None, None  # No confirmation candle in window

    confirmation_bar = signal_bars.iloc[confirmation_idx]

    # Confirmation must close above EMA20
    if confirmation_bar['close'] < confirmation_bar['ema20']:
        return None, None  # Signal invalidated

    return confirmation_bar, confirmation_idx
```

---

### Step 6: Entry Setup

```python
def setup_entry(day_bars, confirmation_bar, params):
    """
    Setup entry details for candle after confirmation.

    Entry: Open of candle after confirmation
    Stop: Entry - (1.2 × ATR)

    Returns: dict with entry details or None if entry bar not found
    """
    # Find entry bar (next candle after confirmation in full day data)
    entry_bars = day_bars[day_bars['timestamp'] > confirmation_bar['timestamp']]

    if entry_bars.empty:
        return None  # No candle after confirmation (rare edge case)

    entry_bar = entry_bars.iloc[0]

    # Calculate stop
    stop_multiplier = params.get('stop_atr_multiplier', 1.2)
    stop_distance = stop_multiplier * entry_bar['atr14']
    stop_price = entry_bar['open'] - stop_distance

    return {
        'entry_time': entry_bar['timestamp'],
        'entry_price': entry_bar['open'],
        'ema20_at_entry': entry_bar['ema20'],
        'atr14_at_entry': entry_bar['atr14'],
        'stop_distance': stop_distance,
        'stop_price': stop_price,
    }
```

---

## Complete Signal Detection Function

```python
def detect_dp20_signal(day_bars, sma200, params=None):
    """
    Full DP20 signal detection for one trading day.

    Combines all 6 steps.
    """
    if params is None:
        params = {}

    result = {
        'signal_detected': False,
        'notes': '',
    }

    # Step 1: Trend filter
    trend_ok, msg = check_trend_filter(day_bars, sma200)
    if not trend_ok:
        result['notes'] = msg
        return result

    # Step 2: Time window filter
    signal_bars, msg = filter_signal_window(day_bars)
    if signal_bars is None:
        result['notes'] = msg
        return result

    # Step 3: Pullback detection
    pullback_bar, pullback_idx = detect_pullback(signal_bars)
    if pullback_bar is None:
        result['notes'] = "No pullback detected (no close below EMA20)"
        return result

    result['pullback_time'] = pullback_bar['timestamp']

    # Step 4: Reversal detection (with strength filter)
    reversal_bar, reversal_idx = detect_reversal(
        signal_bars,
        pullback_idx,
        strength_threshold=params.get('reversal_strength_threshold', 0.60)
    )

    if reversal_bar is None:
        result['notes'] = "No strong reversal detected"
        return result

    result['reversal_time'] = reversal_bar['timestamp']
    result['reversal_strength'] = (
        (reversal_bar['close'] - reversal_bar['low']) /
        (reversal_bar['high'] - reversal_bar['low'])
    )

    # Step 5: Confirmation
    confirmation_bar, confirmation_idx = check_confirmation(signal_bars, reversal_idx)

    if confirmation_bar is None:
        result['notes'] = "Signal invalidated: confirmation candle closed below EMA20"
        return result

    result['confirmation_time'] = confirmation_bar['timestamp']

    # Step 6: Entry setup
    entry_details = setup_entry(day_bars, confirmation_bar, params)

    if entry_details is None:
        result['notes'] = "No entry bar found after confirmation"
        return result

    # Success! Signal detected
    result['signal_detected'] = True
    result.update(entry_details)
    result['notes'] = "Valid DP20 signal detected"

    return result
```

---

## Edge Cases & Handling

### 1. **Multiple Pullbacks in Window**

**Scenario:** Price dips below EMA20 twice in 10:00-10:30 window

**Handling:** Take first pullback only (strategy rule: first valid signal)

```python
# Already handled by: pullback_bars.iloc[0]
# Takes first occurrence
```

### 2. **Reversal Without Confirmation Bar**

**Scenario:** Reversal at 10:28, no time for confirmation before 10:30

**Handling:** No signal (confirmation required)

```python
if confirmation_idx >= len(signal_bars):
    return None, None  # Handled in check_confirmation
```

### 3. **Weak Reversal (< 60% Body)**

**Scenario:** Price closes above EMA20 but with small body

**Handling:** Keep looking for next reversal with strong body

```python
# Filtered out in detect_reversal:
strong_reversals = reversal_candidates[
    reversal_candidates['body_pct'] > strength_threshold
]
```

### 4. **Gap Through EMA20**

**Scenario:** Price gaps from below EMA20 to well above (no close AT EMA20)

**Handling:** Still valid reversal (close > EMA20 is sufficient)

```python
# Logic: close > ema20 (no requirement for close NEAR ema20)
reversal_mask = after_pullback['close'] > after_pullback['ema20']
```

### 5. **Confirmation Candle Dips Below EMA20**

**Scenario:** Confirmation candle low < EMA20 but close > EMA20

**Handling:** Valid (only close matters)

```python
# Check: confirmation_bar['close'] > confirmation_bar['ema20']
# (Low is not checked)
```

---

## Parameter Tuning

### Default Parameters:

```python
DEFAULT_PARAMS = {
    'signal_window_start': time(10, 0),   # 10:00 AM ET
    'signal_window_end': time(10, 30),     # 10:30 AM ET
    'reversal_strength_threshold': 0.60,   # 60% body
    'stop_atr_multiplier': 1.2,            # 1.2× ATR for stop
    'exit_time': time(15, 55),             # 3:55 PM ET
}
```

### Tunable Parameters:

**For Optimization Studies:**

1. **Time Window:**
   - Narrower: 10:00-10:15 (fewer trades, higher quality?)
   - Wider: 10:00-11:00 (more trades, lower quality?)

2. **Reversal Strength:**
   - Stricter: 0.70 (stronger reversals only)
   - Looser: 0.50 (more signals)

3. **Stop Multiplier:**
   - Tighter: 1.0× ATR (less risk, more stops hit)
   - Wider: 1.5× ATR (more risk, fewer stops hit)

4. **Exit Time:**
   - Earlier: 3:00 PM (avoid close volatility)
   - Later: 3:59 PM (capture full day move)

**Important:** Document all parameter changes in backtest results!

---

## Testing Strategy

### Unit Test Cases:

**1. Test Trend Filter:**
```python
def test_trend_filter_pass():
    # open > sma200
    assert check_trend_filter(bars_with_open_440, sma200=435) == (True, ...)

def test_trend_filter_fail():
    # open < sma200
    assert check_trend_filter(bars_with_open_430, sma200=435) == (False, ...)
```

**2. Test Pullback Detection:**
```python
def test_pullback_detected():
    # bars with close < ema20
    result = detect_pullback(bars_with_pullback)
    assert result[0] is not None

def test_no_pullback():
    # all bars close > ema20
    result = detect_pullback(bars_without_pullback)
    assert result[0] is None
```

**3. Test Reversal with Strength Filter:**
```python
def test_strong_reversal():
    # body_pct = 0.75 (> 0.60 threshold)
    result = detect_reversal(bars, pullback_idx=5, strength_threshold=0.60)
    assert result[0] is not None

def test_weak_reversal():
    # body_pct = 0.40 (< 0.60 threshold)
    result = detect_reversal(bars, pullback_idx=5, strength_threshold=0.60)
    assert result[0] is None
```

**4. Test Confirmation Invalidation:**
```python
def test_confirmation_invalidates():
    # confirmation candle closes below ema20
    result = check_confirmation(bars_with_invalid_conf, reversal_idx=10)
    assert result[0] is None
```

**5. Test Full Signal Detection:**
```python
def test_complete_signal():
    signal = detect_dp20_signal(day_bars_with_valid_setup, sma200=435)
    assert signal['signal_detected'] == True
    assert 'entry_time' in signal
    assert 'stop_price' in signal
```

### Integration Test:

**Test with Real Historical Day:**
```python
def test_signal_detection_on_real_day():
    # Use known day where signal occurred
    # 2025-09-03: QQQ had clear DP20 setup
    day_bars = load_historical_day('2025-09-03')
    sma200 = 420.5

    signal = detect_dp20_signal(day_bars, sma200)

    # Verify signal was detected
    assert signal['signal_detected'] == True

    # Verify entry time in reasonable range
    entry_time = signal['entry_time'].time()
    assert time(10, 0) <= entry_time <= time(11, 0)
```

---

## Visualization for Debugging

### Plot Day with Signal Markers:

```python
def plot_signal_detection(day_bars, signal):
    """
    Plot 2-min bars with EMA20 and signal markers.

    Useful for visual debugging.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot price
    ax.plot(day_bars['timestamp'], day_bars['close'], label='Close', color='black')

    # Plot EMA20
    ax.plot(day_bars['timestamp'], day_bars['ema20'], label='EMA20', color='blue', linestyle='--')

    if signal['signal_detected']:
        # Mark pullback
        ax.axvline(signal['pullback_time'], color='red', linestyle=':', label='Pullback')

        # Mark reversal
        ax.axvline(signal['reversal_time'], color='green', linestyle=':', label='Reversal')

        # Mark entry
        ax.axvline(signal['entry_time'], color='purple', linewidth=2, label='Entry')
        ax.axhline(signal['entry_price'], color='purple', linestyle='--', alpha=0.5)

        # Mark stop
        ax.axhline(signal['stop_price'], color='red', linestyle='--', alpha=0.5, label='Stop')

    ax.legend()
    ax.set_title(f"DP20 Signal Detection - {day_bars.iloc[0]['date']}")
    ax.set_xlabel("Time (ET)")
    ax.set_ylabel("Price")
    plt.tight_layout()
    plt.show()
```

---

**Related Documents:**
- [Architecture Overview](./architecture-overview.md)
- [Backtest Engine](./backtest-engine.md)
- [DP20 Strategy Spec](../strategies/qqq_dp20_strategy_spec.md)
