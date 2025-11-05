"""
DP20 (Deep Pullback 20) signal detection.

This implements the 6-step entry logic for the QQQ DP20 strategy.
Uses vectorized pandas operations for efficient backtesting.

Author: Tanam Bam Sinha
"""

from datetime import time
from typing import Optional, Tuple
import pandas as pd

from trading_playbook.models.signal import DP20Signal


# Default strategy parameters
DEFAULT_PARAMS = {
    'signal_window_start': time(10, 0),    # 10:00 AM ET
    'signal_window_end': time(10, 30),      # 10:30 AM ET
    'reversal_strength_threshold': 0.60,    # 60% body
    'stop_atr_multiplier': 1.2,             # 1.2x ATR for stop
    'exit_time': time(15, 55),              # 3:55 PM ET
}


def detect_dp20_signal(
    day_bars: pd.DataFrame,
    sma200: float,
    params: Optional[dict] = None
) -> DP20Signal:
    """
    Detect DP20 entry signal for a single trading day.

    This is the main entry point for signal detection. It orchestrates
    all 6 steps of the DP20 strategy logic.

    Args:
        day_bars: DataFrame with 2-min bars for one day
                  Must have columns: timestamp, open, high, low, close,
                  ema20, atr14
        sma200: 200-day SMA value for trend filter
        params: Optional strategy parameter overrides

    Returns:
        DP20Signal object with detection results

    Example:
        >>> signal = detect_dp20_signal(day_bars, sma200=450.0)
        >>> if signal.signal_detected:
        ...     print(f"Entry at {signal.entry_time}: ${signal.entry_price}")
    """
    if params is None:
        params = DEFAULT_PARAMS.copy()
    else:
        # Merge with defaults
        merged_params = DEFAULT_PARAMS.copy()
        merged_params.update(params)
        params = merged_params

    # Get trading date from first bar
    trade_date = day_bars.iloc[0]['timestamp']

    # Step 1: Trend filter
    trend_ok, msg = _check_trend_filter(day_bars, sma200)
    if not trend_ok:
        return DP20Signal(
            signal_detected=False,
            date=trade_date,
            notes=msg
        )

    # Step 2: Time window filter
    signal_bars, msg = _filter_signal_window(
        day_bars,
        params['signal_window_start'],
        params['signal_window_end']
    )
    if signal_bars is None:
        return DP20Signal(
            signal_detected=False,
            date=trade_date,
            notes=msg
        )

    # Step 3: Pullback detection
    pullback_bar, pullback_idx = _detect_pullback(signal_bars)
    if pullback_bar is None:
        return DP20Signal(
            signal_detected=False,
            date=trade_date,
            notes="No pullback detected (no close below EMA20)"
        )

    # Step 4: Reversal detection (with strength filter)
    reversal_bar, reversal_idx = _detect_reversal(
        signal_bars,
        pullback_idx,
        params['reversal_strength_threshold']
    )
    if reversal_bar is None:
        return DP20Signal(
            signal_detected=False,
            date=trade_date,
            notes="No strong reversal detected",
            pullback_time=pullback_bar['timestamp']
        )

    # Calculate reversal strength
    reversal_strength = (
        (reversal_bar['close'] - reversal_bar['low']) /
        (reversal_bar['high'] - reversal_bar['low'])
    )

    # Step 5: Confirmation
    confirmation_bar, confirmation_idx = _check_confirmation(signal_bars, reversal_idx)
    if confirmation_bar is None:
        return DP20Signal(
            signal_detected=False,
            date=trade_date,
            notes="Signal invalidated: confirmation candle closed below EMA20",
            pullback_time=pullback_bar['timestamp'],
            reversal_time=reversal_bar['timestamp'],
            reversal_strength=reversal_strength
        )

    # Step 6: Entry setup
    entry_details = _setup_entry(day_bars, confirmation_bar, params)
    if entry_details is None:
        return DP20Signal(
            signal_detected=False,
            date=trade_date,
            notes="No entry bar found after confirmation",
            pullback_time=pullback_bar['timestamp'],
            reversal_time=reversal_bar['timestamp'],
            reversal_strength=reversal_strength,
            confirmation_time=confirmation_bar['timestamp']
        )

    # Success! Valid signal detected
    return DP20Signal(
        signal_detected=True,
        date=trade_date,
        notes="Valid DP20 signal detected",
        pullback_time=pullback_bar['timestamp'],
        reversal_time=reversal_bar['timestamp'],
        reversal_strength=reversal_strength,
        confirmation_time=confirmation_bar['timestamp'],
        entry_time=entry_details['entry_time'],
        entry_price=entry_details['entry_price'],
        ema20_at_entry=entry_details['ema20_at_entry'],
        atr14_at_entry=entry_details['atr14_at_entry'],
        stop_distance=entry_details['stop_distance'],
        stop_price=entry_details['stop_price']
    )


def _check_trend_filter(day_bars: pd.DataFrame, sma200: float) -> Tuple[bool, str]:
    """
    Step 1: Check if trend filter passes (open > SMA200).

    The market must open above the 200-day SMA for us to consider trades.
    This ensures we're trading in an uptrend.

    Args:
        day_bars: DataFrame with day's bars
        sma200: 200-day SMA value

    Returns:
        (passed, message) tuple
    """
    day_open = day_bars.iloc[0]['open']

    if day_open <= sma200:
        return False, f"Trend filter failed: open {day_open:.2f} <= SMA200 {sma200:.2f}"

    return True, f"Trend filter passed: open {day_open:.2f} > SMA200 {sma200:.2f}"


def _filter_signal_window(
    day_bars: pd.DataFrame,
    start_time: time,
    end_time: time
) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Step 2: Extract bars within signal evaluation window.

    We only look for signals during a specific time window (default 10:00-10:30 AM).
    This focuses on the morning session after initial volatility settles.

    Args:
        day_bars: DataFrame with day's bars
        start_time: Window start time (e.g., time(10, 0))
        end_time: Window end time (e.g., time(10, 30))

    Returns:
        (signal_bars DataFrame or None, message) tuple
    """
    # Filter by time
    signal_bars = day_bars[
        (day_bars['timestamp'].dt.time >= start_time) &
        (day_bars['timestamp'].dt.time <= end_time)
    ].copy()

    if signal_bars.empty:
        return None, f"No bars in signal window ({start_time}-{end_time})"

    return signal_bars, f"{len(signal_bars)} bars in signal window"


def _detect_pullback(
    signal_bars: pd.DataFrame
) -> Tuple[Optional[pd.Series], Optional[int]]:
    """
    Step 3: Find first candle that closes below EMA20.

    A pullback indicates temporary weakness. We wait for this before
    looking for the reversal.

    Args:
        signal_bars: DataFrame with bars in signal window

    Returns:
        (pullback_bar Series or None, pullback_index or None) tuple
    """
    # Boolean mask: close < ema20
    pullback_mask = signal_bars['close'] < signal_bars['ema20']

    if not pullback_mask.any():
        return None, None  # No pullback detected

    # Get first pullback bar
    pullback_bars = signal_bars[pullback_mask]
    pullback_bar = pullback_bars.iloc[0]

    # Get index position in signal_bars
    pullback_idx = signal_bars.index.get_loc(pullback_bar.name)

    return pullback_bar, pullback_idx


def _detect_reversal(
    signal_bars: pd.DataFrame,
    pullback_idx: int,
    strength_threshold: float
) -> Tuple[Optional[pd.Series], Optional[int]]:
    """
    Step 4: Find first candle after pullback that closes above EMA20
    AND passes strength filter.

    Strength filter: (Close - Low) / (High - Low) > threshold
    This ensures the reversal candle has a strong bullish body.

    Args:
        signal_bars: DataFrame with bars in signal window
        pullback_idx: Index of pullback bar
        strength_threshold: Minimum body percentage (e.g., 0.60 = 60%)

    Returns:
        (reversal_bar Series or None, reversal_index or None) tuple
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
    # Body % = (Close - Low) / (High - Low)
    # High body % means close is near the high (bullish)
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

    # Get index position in signal_bars
    reversal_idx = signal_bars.index.get_loc(reversal_bar.name)

    return reversal_bar, reversal_idx


def _check_confirmation(
    signal_bars: pd.DataFrame,
    reversal_idx: int
) -> Tuple[Optional[pd.Series], Optional[int]]:
    """
    Step 5: Check confirmation candle (next candle after reversal).

    Confirmation candle must close > EMA20, otherwise signal invalidated.
    This prevents whipsaws - we need two consecutive closes above EMA20.

    Args:
        signal_bars: DataFrame with bars in signal window
        reversal_idx: Index of reversal bar

    Returns:
        (confirmation_bar Series or None, confirmation_index or None) tuple
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


def _setup_entry(
    day_bars: pd.DataFrame,
    confirmation_bar: pd.Series,
    params: dict
) -> Optional[dict]:
    """
    Step 6: Setup entry details for candle after confirmation.

    Entry: Open of candle after confirmation
    Stop: Entry - (stop_atr_multiplier x ATR)

    Args:
        day_bars: Full day's DataFrame (not just signal window)
        confirmation_bar: The confirmation candle
        params: Strategy parameters

    Returns:
        dict with entry details or None if entry bar not found
    """
    # Find entry bar (next candle after confirmation in full day data)
    entry_bars = day_bars[day_bars['timestamp'] > confirmation_bar['timestamp']]

    if entry_bars.empty:
        return None  # No candle after confirmation (rare edge case)

    entry_bar = entry_bars.iloc[0]

    # Calculate stop
    stop_multiplier = params['stop_atr_multiplier']
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
