"""
Morning Reversal strategy signal detection.

This strategy exploits the daily pattern:
- Morning fear/panic creates lows (9:30-11:00 AM)
- Afternoon logic/rationality drives recovery
- Entry: Buy when price bounces off 30-min low
- Exit: End of day (3:55 PM)
- No stop loss - trust the daily psychological pattern

Author: Tanam Bam Sinha
"""

from datetime import time
from typing import Optional
import pandas as pd

from trading_playbook.models.signal import DP20Signal


# Default strategy parameters
DEFAULT_PARAMS = {
    'morning_start': time(9, 30),       # Start of morning window
    'morning_end': time(11, 0),         # End of morning window
    'lookback_minutes': 30,             # Rolling low lookback (30 min)
    'bounce_threshold_pct': 0.2,        # 0.2% bounce to confirm reversal
    'exit_time': time(15, 55),          # 3:55 PM exit
}


def detect_morning_reversal_signal(
    day_bars: pd.DataFrame,
    params: Optional[dict] = None
) -> DP20Signal:
    """
    Detect Morning Reversal entry signal for a single trading day.

    Strategy Logic:
    1. Track rolling low during morning window (9:30-11:00 AM)
    2. Wait for price to bounce X% above the rolling low
    3. Enter when bounce threshold is hit
    4. Exit at end of day

    Args:
        day_bars: DataFrame with 2-min bars for one day
                  Must have columns: timestamp, open, high, low, close
        params: Optional strategy parameter overrides

    Returns:
        DP20Signal object (reusing for compatibility) with detection results

    Example:
        >>> signal = detect_morning_reversal_signal(day_bars)
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

    # Add time column for filtering
    day_bars = day_bars.copy()
    day_bars['time'] = day_bars['timestamp'].dt.time

    # Filter to morning window
    morning_bars = day_bars[
        (day_bars['time'] >= params['morning_start']) &
        (day_bars['time'] <= params['morning_end'])
    ].copy()

    if morning_bars.empty:
        return DP20Signal(
            signal_detected=False,
            date=trade_date,
            notes="No bars in morning window"
        )

    # Calculate rolling low
    lookback_periods = params['lookback_minutes'] // 2  # 2-min bars
    morning_bars['rolling_low'] = morning_bars['low'].rolling(
        window=lookback_periods,
        min_periods=1
    ).min()

    # Calculate bounce threshold
    bounce_threshold = params['bounce_threshold_pct'] / 100  # Convert to decimal
    morning_bars['bounce_target'] = morning_bars['rolling_low'] * (1 + bounce_threshold)

    # Find first bar where close exceeds bounce target
    bounce_mask = morning_bars['close'] > morning_bars['bounce_target']

    if not bounce_mask.any():
        return DP20Signal(
            signal_detected=False,
            date=trade_date,
            notes="No bounce detected above rolling low"
        )

    # Get first bounce bar
    bounce_bar = morning_bars[bounce_mask].iloc[0]
    entry_time = bounce_bar['timestamp']
    entry_price = bounce_bar['close']  # Enter at close of bounce bar
    rolling_low_at_entry = bounce_bar['rolling_low']

    # Record the low that triggered entry
    pullback_time = entry_time  # Using this field for compatibility

    # Success! Signal detected
    return DP20Signal(
        signal_detected=True,
        date=trade_date,
        notes=f"Morning reversal: Bounce {bounce_threshold*100:.1f}% off ${rolling_low_at_entry:.2f} low",
        pullback_time=pullback_time,  # Time of rolling low
        entry_time=entry_time,
        entry_price=entry_price,
        stop_price=None,  # No stop loss in this strategy
        stop_distance=None
    )
