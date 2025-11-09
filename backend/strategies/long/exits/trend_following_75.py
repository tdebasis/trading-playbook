"""
Trend Following 75/25 Exit Strategy - Let Winners Run

Philosophy: Take 25% profit early (psychological win), then let 75% ride for the big moves (+30-100%).

Exit Rules:
1. ONE partial exit: 25% at +10% profit (quick win)
2. Final 75% rides until trend breaks:
   - Close below 10-day EMA (trend weakening)
   - OR close drops 10% from highest close (trailing stop)
   - OR hard stop -8% (safety net)
3. NO time stops - let trends run for months if they want
4. Exit at NEXT day's close (avoid gap risk)

Target: Capture +50%, +100%, +200% moves while securing some profit.

Implements ExitStrategyProtocol for plug-and-play architecture.

Author: Claude AI + Tanam Bam Sinha
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


@register_exit_strategy('trend_following_75')
class TrendFollowing75:
    """
    Trend following exit strategy: 25% profit-taking, 75% ride the trend.

    Key Features:
    - Single 25% exit at +10% (lock quick win)
    - Remaining 75% uses only trend-based exits
    - NO time stops (let winners run for months)
    - Exit based on price action, not calendar

    Exit Triggers for Final 75%:
    1. Hard stop: -8% from entry (safety)
    2. Trend break: Close below 10-day EMA
    3. Trailing stop: Close drops 10% from highest close
    4. Move stop to breakeven once +10% (reduce risk)

    Designed to catch +30-100% moves while taking early profit.
    """

    def __init__(self):
        """Initialize trend following exits with parameters."""
        self._stop_loss_percent = 0.08  # 8% hard stop
        self._partial_exit_trigger = 10.0  # Take 25% at +10%
        self._partial_exit_percent = 0.25  # Exit 25% of position
        self._trailing_stop_percent = 0.10  # 10% trail from high
        self._ema_period = 10  # 10-day EMA for trend
        self._move_to_breakeven_pct = 10.0  # Move stop to breakeven at +10%

    @property
    def strategy_name(self) -> str:
        """Return strategy identifier for ExitStrategyProtocol."""
        return 'trend_following_75'

    @property
    def supports_partial_exits(self) -> bool:
        """Supports one partial exit (25% at +10%)."""
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
        Check if position should be exited using trend following rules.

        Args:
            position: Current position with entry data
            current_price: Current closing price
            current_date: Current date
            bars: Recent price bars (need at least 10 for EMA)

        Returns:
            ExitSignal indicating whether to exit (full or partial)

        Implementation:
        - Takes 25% at +10% (one time only)
        - Moves stop to breakeven after +10%
        - Rides remaining 75% using trend indicators
        - NO time stop - exits based on price action only
        """
        # Ensure we have enough bars
        if not bars or len(bars) < 10:
            return ExitSignal.no_exit()

        # Extract bar data
        current_bar = bars[-1]
        current_close = float(getattr(current_bar, 'close', current_price))
        current_low = float(getattr(current_bar, 'low', current_price))

        # Initialize strategy state if needed
        if 'partial_exit_taken' not in position.strategy_state:
            position.strategy_state['partial_exit_taken'] = False
            position.strategy_state['highest_close'] = current_close
            position.strategy_state['trailing_stop'] = 0.0
            position.strategy_state['breakeven_stop_active'] = False
            position.strategy_state['initial_shares'] = position.shares

        # Calculate current profit percentage
        profit_pct = ((current_close - position.entry_price) / position.entry_price) * 100

        # === PARTIAL EXIT: 25% at +10% (ONE TIME ONLY) ===
        if not position.strategy_state['partial_exit_taken'] and profit_pct >= self._partial_exit_trigger:
            position.strategy_state['partial_exit_taken'] = True

            # Also activate breakeven stop
            position.strategy_state['breakeven_stop_active'] = True
            position.stop_price = position.entry_price  # Move stop to breakeven

            return ExitSignal.partial_exit_signal(
                reason=f"PROFIT_TAKE_25",
                price=current_close,
                percent=self._partial_exit_percent
            )

        # If no shares left (defensive check)
        if position.shares == 0:
            return ExitSignal.full_exit(
                reason="FULLY_EXITED",
                price=current_close
            )

        # === MOVE STOP TO BREAKEVEN after +10% ===
        if profit_pct >= self._move_to_breakeven_pct and not position.strategy_state['breakeven_stop_active']:
            position.strategy_state['breakeven_stop_active'] = True
            position.stop_price = position.entry_price  # Protect principal

        # === UPDATE TRAILING STOP ===
        # Track highest close since entry
        if current_close > position.strategy_state['highest_close']:
            position.strategy_state['highest_close'] = current_close
            # Trailing stop: 10% below highest close
            position.strategy_state['trailing_stop'] = current_close * (1 - self._trailing_stop_percent)

        # Calculate 10-day EMA
        ema_10 = self._calculate_ema(bars, period=self._ema_period)

        # === EXIT CHECKS (for remaining shares) ===

        # 1. HARD STOP (check intraday low)
        # Use breakeven stop if active, otherwise original stop
        active_stop = position.stop_price
        if current_low <= active_stop:
            return ExitSignal.full_exit(
                reason="HARD_STOP" if not position.strategy_state['breakeven_stop_active'] else "BREAKEVEN_STOP",
                price=active_stop
            )

        # 2. TRAILING STOP (after partial exit taken)
        # Only activate trailing stop once we've taken 25% profit
        if position.strategy_state['partial_exit_taken']:
            trailing_stop = position.strategy_state['trailing_stop']
            if trailing_stop > 0 and current_close < trailing_stop:
                return ExitSignal.full_exit(
                    reason="TRAILING_STOP",
                    price=current_close
                )

        # 3. TREND BREAK: Close below 10-day EMA
        # Only check after partial exit (let initial position develop)
        if position.strategy_state['partial_exit_taken']:
            if current_close < ema_10:
                return ExitSignal.full_exit(
                    reason="TREND_BREAK_EMA10",
                    price=current_close
                )

        # NO TIME STOP - let trends run!

        # No exit triggered - update MFE/MAE tracking
        position.update_mfe_mae(current_close)

        return ExitSignal.no_exit()

    def _calculate_ema(self, bars: List, period: int = 10) -> float:
        """
        Calculate Exponential Moving Average.

        Args:
            bars: List of price bars
            period: EMA period (default 10 days)

        Returns:
            EMA value
        """
        if len(bars) < period:
            # Fallback to simple average
            closes = [float(getattr(b, 'close', 0)) for b in bars]
            return sum(closes) / len(closes) if closes else 0.0

        # Get closing prices
        closes = [float(getattr(b, 'close', 0)) for b in bars]

        # EMA multiplier: 2 / (period + 1)
        multiplier = 2.0 / (period + 1)

        # Start with SMA of first period values
        ema = sum(closes[:period]) / period

        # Calculate EMA for remaining values
        for close in closes[period:]:
            ema = (close - ema) * multiplier + ema

        return ema


# Module-level documentation
__doc_examples__ = """
Usage Examples:

1. Basic Usage:
    >>> from strategies import get_exit_strategy
    >>> exit_strategy = get_exit_strategy('trend_following_75')
    >>>
    >>> position = Position(symbol='NVDA', entry_price=100.0, shares=400, ...)
    >>> signal = exit_strategy.check_exit(position, 110.0, datetime.now(), recent_bars)
    >>>
    >>> # At +10%, takes 25% profit
    >>> if signal.partial_exit and signal.reason == "PROFIT_TAKE_25":
    >>>     print("Taking 25% profit at +10%, letting 75% ride the trend!")

2. Comparison with Scaled Exits:
    >>> # Scaled Exits: Takes 25% at +8%, +15%, +25% (75% total profit-taking)
    >>> # Trend Following 75: Takes 25% at +10%, rides remaining 75% to trend end
    >>>
    >>> # Example on NVDA going from $100 → $150 (+50%):
    >>> #
    >>> # Scaled Exits:
    >>> #   - 25% exit at $108 (+8%)
    >>> #   - 25% exit at $115 (+15%)
    >>> #   - 25% exit at $125 (+25%)
    >>> #   - 25% exit at $148 (trailing stop)
    >>> #   - Avg exit: ~$124 (+24%)
    >>> #
    >>> # Trend Following 75:
    >>> #   - 25% exit at $110 (+10%)
    >>> #   - 75% exit at $148 (trailing stop)
    >>> #   - Avg exit: ~$139 (+39%)
    >>> #
    >>> # Difference: +15 percentage points on the same trade!

3. Handling Big Moves:
    >>> # On a +100% runner (e.g., NET $100 → $200):
    >>> #
    >>> # Scaled Exits:
    >>> #   - Exits 75% by +25% ($125)
    >>> #   - Only 25% rides to $190+
    >>> #   - Avg exit: ~$140 (+40%)
    >>> #
    >>> # Trend Following 75:
    >>> #   - Exits 25% at $110 (+10%)
    >>> #   - 75% rides full move to $190+
    >>> #   - Avg exit: ~$170 (+70%)
    >>> #
    >>> # This is how to hit 40%+ annual returns!

4. Risk Management:
    >>> # Stop moves to breakeven once +10% reached
    >>> # This protects the 75% remaining from turning into a loss
    >>> #
    >>> # Before +10%: Stop at -8% (risking $8 on $100 entry)
    >>> # After +10%: Stop at breakeven ($100, risking $0)
    >>> #
    >>> # Worst case after taking 25% profit:
    >>> #   - Small loss on 75% remaining
    >>> #   - But already banked +10% on 25%
    >>> #   - Net result: small profit or small loss, never big loss

5. Why No Time Stop:
    >>> # Time stops killed performance in previous tests
    >>> # Many trades exited at +5-8% due to 20-day limit
    >>> # Those stocks often went to +30-50%+ over months
    >>> #
    >>> # Trend Following 75: Let time work FOR you, not against you
    >>> # Exit when trend breaks, not when calendar says so
"""
