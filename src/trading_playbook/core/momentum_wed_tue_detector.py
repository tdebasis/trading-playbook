"""
Momentum-Filtered Wednesday/Tuesday 11 AM Entry strategy.

This strategy combines:
1. Day-of-week edge (Wed/Tue only)
2. Time-of-day edge (11 AM entry)
3. MOMENTUM FILTER (only trade when bouncing UP from morning low)

Data shows this filter improves:
- Win rate: 64.7% → 72.4%
- Avg P&L: $56.64 → $114.45
- Total P&L: $2,888 → $3,318

The key insight: Big losers happen when morning is DOWN (-0.20% avg)
                Big winners happen when morning is UP (+0.11% avg)

Author: Tanam Bam Sinha
"""

from datetime import time
from typing import Optional
import pandas as pd

from trading_playbook.models.signal import DP20Signal


# Default strategy parameters
DEFAULT_PARAMS = {
    'entry_time': time(11, 0),          # 11:00 AM entry
    'exit_time': time(15, 55),          # 3:55 PM exit
    'allowed_days': ['Wednesday', 'Tuesday'],  # Only these days

    # Momentum filters
    'min_bounce_from_low_pct': 0.3,     # Price must be 0.3% above morning low
    'morning_start': time(9, 30),       # Morning window start
    'morning_end': time(11, 0),         # Morning window end
}


def detect_momentum_wed_tue_signal(
    day_bars: pd.DataFrame,
    params: Optional[dict] = None
) -> DP20Signal:
    """
    Detect momentum-filtered Wednesday/Tuesday 11 AM entry signal.

    Strategy Logic:
    1. Check if today is Wednesday or Tuesday
    2. Check if price at 11 AM has bounced > 0.3% from morning low
    3. If both true, enter at 11:00 AM
    4. Exit at end of day

    This momentum filter eliminates trades where morning is weak/down,
    which tend to be the big losers.

    Args:
        day_bars: DataFrame with 2-min bars for one day
                  Must have columns: timestamp, open, high, low, close
        params: Optional strategy parameter overrides

    Returns:
        DP20Signal object with detection results

    Example:
        >>> signal = detect_momentum_wed_tue_signal(day_bars)
        >>> if signal.signal_detected:
        ...     print(f"Entry on {signal.date.strftime('%A')} at 11 AM with {signal.notes}")
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
    day_of_week = trade_date.strftime('%A')

    # Check if today is an allowed day
    if day_of_week not in params['allowed_days']:
        return DP20Signal(
            signal_detected=False,
            date=trade_date,
            notes=f"Wrong day: {day_of_week}"
        )

    # Add time column for filtering
    day_bars = day_bars.copy()
    day_bars['time'] = day_bars['timestamp'].dt.time

    # Find entry bar at/after 11:00 AM
    entry_bars = day_bars[day_bars['time'] >= params['entry_time']]

    if entry_bars.empty:
        return DP20Signal(
            signal_detected=False,
            date=trade_date,
            notes=f"No bars at/after 11 AM"
        )

    entry_bar = entry_bars.iloc[0]
    entry_time = entry_bar['timestamp']
    entry_price = entry_bar['open']

    # Calculate morning low (9:30-11:00)
    morning_bars = day_bars[
        (day_bars['time'] >= params['morning_start']) &
        (day_bars['time'] < params['morning_end'])
    ]

    if morning_bars.empty:
        return DP20Signal(
            signal_detected=False,
            date=trade_date,
            notes="No morning bars"
        )

    morning_low = morning_bars['low'].min()
    morning_open = day_bars.iloc[0]['open']

    # Calculate bounce from morning low
    bounce_from_low = entry_price - morning_low
    bounce_from_low_pct = (bounce_from_low / morning_low) * 100

    # MOMENTUM FILTER: Must be bouncing up from morning low
    if bounce_from_low_pct < params['min_bounce_from_low_pct']:
        return DP20Signal(
            signal_detected=False,
            date=trade_date,
            notes=f"Insufficient bounce: {bounce_from_low_pct:.2f}% (need {params['min_bounce_from_low_pct']:.2f}%)"
        )

    # Calculate morning move for notes
    morning_move = entry_price - morning_open
    morning_move_pct = (morning_move / morning_open) * 100

    # Success! Signal detected with momentum confirmation
    return DP20Signal(
        signal_detected=True,
        date=trade_date,
        notes=f"{day_of_week} 11 AM + Momentum (bounce {bounce_from_low_pct:.2f}%, morning {morning_move_pct:+.2f}%)",
        entry_time=entry_time,
        entry_price=entry_price,
        stop_price=None,  # No stop loss in this strategy
        stop_distance=None
    )
