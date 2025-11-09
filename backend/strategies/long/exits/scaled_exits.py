"""
Scaled Exits Strategy - Incremental Profit Taking

Implements progressive profit-taking with trailing stops on remaining shares:
1. Scale out 25% at +8% profit (first profit secured)
2. Scale out 25% at +15% profit (lock in more gains)
3. Scale out 25% at +25% profit (secure big win)
4. Final 25% uses trailing stops to capture home runs

Benefits:
- Secures profits incrementally (reduces regret)
- Lowers position risk as price rises
- Lets final piece run for outliers
- Psychological edge: always banking wins

Implements ExitStrategyProtocol for plug-and-play architecture.
"""

from __future__ import annotations
from typing import List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path for interfaces import
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from interfaces import ExitStrategyProtocol, ExitSignal, Position
from strategies.long.registry import register_exit_strategy


@register_exit_strategy('scaled_exits')
class ScaledExits:
    """
    Scaled exit strategy with incremental profit-taking.

    Profit Targets (partial exits):
    1. +8%: Exit 25% (first profit locked)
    2. +15%: Exit 25% (50% of position secured)
    3. +25%: Exit 25% (75% of position secured)

    Final 25% Exit Rules:
    - Hard stop: -8% loss
    - Trailing stop: After first scale-out (2× → 1× ATR as profit grows)
    - Trend break: Close below 5-day MA (after first scale-out)
    - Time stop: 20 days maximum hold

    Designed to balance securing gains with capturing big moves.
    """

    def __init__(self):
        """Initialize scaled exits with default parameters."""
        self._stop_loss_percent = 0.08  # 8% hard stop
        self._time_stop_days = 20  # Longer than smart exits (we scaled out)

        # Profit targets for scaling
        self._scale_1_pct = 8.0   # First 25% exit
        self._scale_2_pct = 15.0  # Second 25% exit
        self._scale_3_pct = 25.0  # Third 25% exit

    @property
    def strategy_name(self) -> str:
        """Return strategy identifier for ExitStrategyProtocol."""
        return 'scaled_exits'

    @property
    def supports_partial_exits(self) -> bool:
        """Scaled exits supports partial position exits."""
        return True

    def get_initial_stop(self, entry_price: float, atr: Optional[float] = None) -> float:
        """
        Calculate initial stop loss price.

        Args:
            entry_price: Entry price for the position
            atr: Optional ATR (not used for initial stop)

        Returns:
            Stop price (8% below entry)
        """
        return entry_price * (1 - self._stop_loss_percent)

    def check_exit(
        self,
        position: Position,
        current_price: float,
        current_date: datetime,
        bars: List  # Recent price bars for calculations
    ) -> ExitSignal:
        """
        Check if position should be exited using scaled exit rules.

        Args:
            position: Current position with entry data
            current_price: Current closing price
            current_date: Current date
            bars: Recent price bars (need at least 10 for ATR, MA calculations)

        Returns:
            ExitSignal indicating whether to exit (full or partial)

        Implementation:
        - Checks profit targets for partial exits (25% each time)
        - After first scale-out, uses trailing stops on remaining shares
        - Updates position.strategy_state with tracking data
        - Handles position.partial_exits list
        """
        # Ensure we have enough bars
        if not bars or len(bars) < 5:
            return ExitSignal.no_exit()

        # Extract bar data
        current_bar = bars[-1]
        current_close = float(getattr(current_bar, 'close', current_price))
        current_low = float(getattr(current_bar, 'low', current_price))

        # Initialize strategy state if needed
        if 'scaled_25_pct' not in position.strategy_state:
            position.strategy_state['scaled_25_pct'] = False
            position.strategy_state['scaled_50_pct'] = False
            position.strategy_state['scaled_75_pct'] = False
            position.strategy_state['highest_close'] = current_close
            position.strategy_state['trailing_stop'] = 0.0
            position.strategy_state['prev_close'] = current_close
            position.strategy_state['initial_shares'] = position.shares

        # Calculate current profit percentage
        profit_pct = ((current_close - position.entry_price) / position.entry_price) * 100

        # PROFIT TARGETS - Partial Exits (use close prices)

        # 1. First 25% at +8%
        if not position.strategy_state['scaled_25_pct'] and profit_pct >= self._scale_1_pct:
            shares_to_sell = position.strategy_state['initial_shares'] // 4
            position.strategy_state['scaled_25_pct'] = True

            return ExitSignal.partial_exit_signal(
                reason=f"SCALE_1",
                price=current_close,
                percent=0.25
            )

        # 2. Second 25% at +15%
        if (position.strategy_state['scaled_25_pct'] and
            not position.strategy_state['scaled_50_pct'] and
            profit_pct >= self._scale_2_pct):

            position.strategy_state['scaled_50_pct'] = True

            return ExitSignal.partial_exit_signal(
                reason=f"SCALE_2",
                price=current_close,
                percent=0.25
            )

        # 3. Third 25% at +25%
        if (position.strategy_state['scaled_50_pct'] and
            not position.strategy_state['scaled_75_pct'] and
            profit_pct >= self._scale_3_pct):

            position.strategy_state['scaled_75_pct'] = True

            return ExitSignal.partial_exit_signal(
                reason=f"SCALE_3",
                price=current_close,
                percent=0.25
            )

        # If no shares left (defensive check)
        if position.shares == 0:
            return ExitSignal.full_exit(
                reason="FULLY_SCALED",
                price=current_close
            )

        # SMART EXITS on remaining shares

        # Calculate ATR for trailing stop
        atr = self._calculate_atr(bars, period=min(10, len(bars)))

        # Update highest close (for trailing stop)
        if current_close > position.strategy_state['highest_close']:
            position.strategy_state['highest_close'] = current_close

            # Tighter trailing as profit grows
            if profit_pct >= 30:
                # Very tight (5% from peak)
                position.strategy_state['trailing_stop'] = position.strategy_state['highest_close'] * 0.95
            elif profit_pct >= 20:
                # Tighter (1× ATR)
                position.strategy_state['trailing_stop'] = position.strategy_state['highest_close'] - atr
            else:
                # Normal (2× ATR)
                position.strategy_state['trailing_stop'] = position.strategy_state['highest_close'] - (atr * 2.0)

        # Calculate 5-day MA
        if len(bars) >= 5:
            sma_5 = sum(float(getattr(b, 'close', 0)) for b in bars[-5:]) / 5
        else:
            sma_5 = current_close

        # EXIT CHECKS (remaining shares)

        # 1. HARD STOP (always active) - check intraday low
        if current_low <= position.stop_price:
            return ExitSignal.full_exit(
                reason="HARD_STOP",
                price=position.stop_price
            )

        # 2. TRAILING STOP (after first scale-out)
        if position.strategy_state['scaled_25_pct']:
            # Only activate if we're above initial scale-out level
            if position.strategy_state['highest_close'] > position.entry_price * 1.08:
                trailing_stop = position.strategy_state['trailing_stop']
                if current_close < trailing_stop:
                    return ExitSignal.full_exit(
                        reason="TRAILING_STOP",
                        price=current_close
                    )

        # 3. TREND BREAK (after first scale-out)
        if position.strategy_state['scaled_25_pct']:
            if current_close < sma_5:
                return ExitSignal.full_exit(
                    reason="MA_BREAK",
                    price=current_close
                )

        # 4. TIME STOP (20 days - longer since we scaled out)
        hold_days = position.hold_days(current_date)
        if hold_days >= self._time_stop_days:
            return ExitSignal.full_exit(
                reason="TIME",
                price=current_close
            )

        # No exit triggered - update tracking
        position.strategy_state['prev_close'] = current_close

        # Update MFE/MAE tracking
        position.update_mfe_mae(current_close)

        return ExitSignal.no_exit()

    def _calculate_atr(self, bars: List, period: int = 10) -> float:
        """
        Calculate Average True Range for volatility-based stops.

        Args:
            bars: List of price bars (need open, high, low, close)
            period: ATR period (default 10 days)

        Returns:
            ATR value in price units
        """
        if len(bars) < period + 1:
            # Fallback: use current bar range
            if bars:
                bar = bars[-1]
                return float(getattr(bar, 'high', 0) - getattr(bar, 'low', 0))
            return 0.0

        true_ranges = []
        for i in range(1, len(bars)):
            high = float(getattr(bars[i], 'high', 0))
            low = float(getattr(bars[i], 'low', 0))
            prev_close = float(getattr(bars[i-1], 'close', 0))

            # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        # Average of last N true ranges
        return sum(true_ranges[-period:]) / min(period, len(true_ranges))


# Module-level documentation
__doc_examples__ = """
Usage Examples:

1. Basic Usage:
    >>> from strategies import get_exit_strategy
    >>> from interfaces import Position, ExitSignal
    >>>
    >>> exit_strategy = get_exit_strategy('scaled_exits')
    >>> position = Position(symbol='NVDA', entry_date=..., entry_price=100.0, shares=400, ...)
    >>> signal = exit_strategy.check_exit(position, 108.0, datetime.now(), recent_bars)
    >>>
    >>> if signal.should_exit:
    >>>     if signal.partial_exit:
    >>>         shares_to_exit = int(position.shares * signal.exit_percent)
    >>>         print(f"Partial exit: {shares_to_exit} shares at ${signal.exit_price} ({signal.reason})")
    >>>     else:
    >>>         print(f"Full exit at ${signal.exit_price} ({signal.reason})")

2. Handling Partial Exits:
    >>> # Position starts with 400 shares
    >>> position = Position(..., shares=400, ...)
    >>>
    >>> # At +8% profit, SCALE_1 triggers
    >>> signal = exit_strategy.check_exit(position, 108.0, date, bars)
    >>> if signal.partial_exit and signal.reason == "SCALE_1":
    >>>     shares_to_exit = int(400 * 0.25)  # 100 shares
    >>>     position.add_partial_exit(date, shares_to_exit, 108.0, "SCALE_1")
    >>>     # position.shares now 300
    >>>
    >>> # At +15%, SCALE_2 triggers
    >>> signal = exit_strategy.check_exit(position, 115.0, date, bars)
    >>> if signal.partial_exit and signal.reason == "SCALE_2":
    >>>     shares_to_exit = int(400 * 0.25)  # 100 shares (of original)
    >>>     position.add_partial_exit(date, shares_to_exit, 115.0, "SCALE_2")
    >>>     # position.shares now 200
    >>>
    >>> # Remaining shares use trailing stops

3. Comparison with Smart Exits:
    >>> smart_exits = get_exit_strategy('smart_exits')
    >>> scaled_exits = get_exit_strategy('scaled_exits')
    >>>
    >>> # Smart exits: All-or-nothing (let winners run, cut losers)
    >>> # Scaled exits: Bank profits incrementally, trail with remainder
    >>>
    >>> print(f"Smart exits supports partial: {smart_exits.supports_partial_exits}")  # False
    >>> print(f"Scaled exits supports partial: {scaled_exits.supports_partial_exits}")  # True
"""
