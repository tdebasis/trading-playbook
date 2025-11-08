"""
Smart Exits Strategy - Price Action Based

Implements professional exit rules based on price action rather than fixed targets:
1. Trailing stop (ATR-based, tightens with profit)
2. Trend break (close below 5-day MA)
3. Momentum weakening (lower close after +5% gain)
4. Hard stop (-8% maximum loss)
5. Time stop (17 days maximum hold)

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
from strategies import register_exit_strategy


@register_exit_strategy('smart_exits')
class SmartExits:
    """
    Smart exit strategy based on price action and trailing stops.

    Exit Triggers (in priority order):
    1. Hard stop: -8% loss (uses intraday low)
    2. Trailing stop: ATR-based, tightens as profit grows
       - 0-10% profit: 2× ATR trail
       - 10-15% profit: 1× ATR trail
       - 15%+ profit: 5% trail
    3. Trend break: Close below 5-day MA (only if current profit < 3%)
    4. Lower close: Momentum weakening after 5%+ gain
    5. Time stop: 17 days maximum hold

    Designed to let winners run while cutting losers quickly.
    """

    def __init__(self):
        """Initialize smart exits with default parameters."""
        self._stop_loss_percent = 0.08  # 8% hard stop
        self._time_stop_days = 17
        self._trail_activation_percent = 5.0  # Start trailing after 5% gain
        self._ma_break_profit_threshold = 3.0  # Only use MA break if profit < 3%

    @property
    def strategy_name(self) -> str:
        """Return strategy identifier for ExitStrategyProtocol."""
        return 'smart_exits'

    @property
    def supports_partial_exits(self) -> bool:
        """Smart exits does full position exits only."""
        return False

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
        Check if position should be exited using smart exit rules.

        Args:
            position: Current position with entry data
            current_price: Current closing price
            current_date: Current date
            bars: Recent price bars (need at least 10 for ATR, MA calculations)

        Returns:
            ExitSignal indicating whether to exit

        Implementation:
        - Updates position.strategy_state with tracking data
        - Checks exits in priority order
        - Returns first triggered exit
        """
        # Ensure we have enough bars
        if not bars or len(bars) < 5:
            return ExitSignal.no_exit()

        # Extract bar data
        current_bar = bars[-1]
        current_close = float(getattr(current_bar, 'close', current_price))
        current_low = float(getattr(current_bar, 'low', current_price))

        # Initialize strategy state if needed
        if 'highest_close' not in position.strategy_state:
            position.strategy_state['highest_close'] = current_close
            position.strategy_state['trailing_stop'] = 0.0
            position.strategy_state['prev_close'] = current_close

        # Calculate ATR (Average True Range)
        atr = self._calculate_atr(bars, period=min(10, len(bars)))

        # Update highest close (for trailing stop)
        if current_close > position.strategy_state['highest_close']:
            position.strategy_state['highest_close'] = current_close

            # Update trailing stop based on profit level
            profit_pct = ((position.strategy_state['highest_close'] - position.entry_price) / position.entry_price) * 100

            if profit_pct >= 15:
                # Very tight trail (5% from peak)
                position.strategy_state['trailing_stop'] = position.strategy_state['highest_close'] * 0.95
            elif profit_pct >= 10:
                # Tighter trail (1× ATR)
                position.strategy_state['trailing_stop'] = position.strategy_state['highest_close'] - atr
            else:
                # Normal trail (2× ATR)
                position.strategy_state['trailing_stop'] = position.strategy_state['highest_close'] - (atr * 2.0)

        # Calculate 5-day MA
        if len(bars) >= 5:
            sma_5 = sum(float(getattr(b, 'close', 0)) for b in bars[-5:]) / 5
        else:
            sma_5 = current_close

        # EXIT CHECKS (in priority order)

        # 1. HARD STOP (always active) - check intraday low
        if current_low <= position.stop_price:
            return ExitSignal.full_exit(
                reason="HARD_STOP",
                price=position.stop_price
            )

        # 2. TRAILING STOP (after 5%+ profit)
        highest_close = position.strategy_state['highest_close']
        if highest_close > position.entry_price * (1 + self._trail_activation_percent / 100):
            trailing_stop = position.strategy_state['trailing_stop']
            if current_close < trailing_stop:
                return ExitSignal.full_exit(
                    reason="TRAILING_STOP",
                    price=current_close
                )

        # 3. TREND BREAK (MA break, only if current profit < 3%)
        current_profit_pct = ((current_close - position.entry_price) / position.entry_price) * 100
        if current_profit_pct < self._ma_break_profit_threshold:
            if current_close < sma_5:
                return ExitSignal.full_exit(
                    reason="MA_BREAK",
                    price=current_close
                )

        # 4. LOWER CLOSE (momentum weakening after 5%+ gain)
        if highest_close > position.entry_price * (1 + self._trail_activation_percent / 100):
            prev_close = position.strategy_state.get('prev_close', 0)
            if prev_close > 0 and current_close < prev_close:
                return ExitSignal.full_exit(
                    reason="LOWER_HIGH",
                    price=current_close
                )

        # 5. TIME STOP (17 days max)
        hold_days = position.hold_days(current_date)
        if hold_days >= self._time_stop_days:
            return ExitSignal.full_exit(
                reason="TIME",
                price=current_close
            )

        # No exit triggered - update tracking for next day
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
    >>> exit_strategy = get_exit_strategy('smart_exits')
    >>> position = Position(symbol='NVDA', entry_date=..., entry_price=100.0, ...)
    >>> signal = exit_strategy.check_exit(position, 105.0, datetime.now(), recent_bars)
    >>>
    >>> if signal.should_exit:
    >>>     print(f"Exit at ${signal.exit_price} ({signal.reason})")

2. In Backtest:
    >>> exit_strategy = get_exit_strategy('smart_exits')
    >>> for date in trading_days:
    >>>     for position in open_positions:
    >>>         bars = get_recent_bars(position.symbol, date, lookback=10)
    >>>         signal = exit_strategy.check_exit(position, bars[-1].close, date, bars)
    >>>         if signal.should_exit:
    >>>             close_position(position, signal.exit_price, signal.reason)

3. Custom Parameters (future enhancement):
    >>> exit_strategy = SmartExits()
    >>> exit_strategy._stop_loss_percent = 0.10  # 10% hard stop
    >>> exit_strategy._time_stop_days = 20  # 20 day time stop
"""
