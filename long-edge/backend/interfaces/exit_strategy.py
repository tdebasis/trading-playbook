"""
Exit strategy interface for trading systems.

Defines the standard contract for all exit logic implementations.
"""

from __future__ import annotations

from typing import Protocol, Optional, List, runtime_checkable, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass

if TYPE_CHECKING:
    from .position import Position


@dataclass
class ExitSignal:
    """
    Signal indicating whether and how to exit a position.

    This is returned by exit strategies to communicate exit decisions
    to the execution system.
    """

    # Exit decision
    should_exit: bool

    # Exit details (populated if should_exit=True)
    reason: str | None = None  # "stop_hit", "target_hit", "ma_break", "time_stop", etc.
    exit_price: float | None = None  # Price to exit at

    # Partial exit support (for scaled exits)
    partial_exit: bool = False  # True if only exiting part of position
    exit_percent: float = 1.0  # 1.0 = full exit, 0.25 = 25% exit, etc.

    def __post_init__(self):
        """Validate exit signal data."""
        if self.should_exit and self.reason is None:
            raise ValueError("Exit reason is required when should_exit=True")

        if self.should_exit and self.exit_price is None:
            raise ValueError("Exit price is required when should_exit=True")

        if self.exit_percent <= 0 or self.exit_percent > 1.0:
            raise ValueError(f"Exit percent must be 0-1, got {self.exit_percent}")

        if self.partial_exit and self.exit_percent == 1.0:
            raise ValueError("Partial exit requires exit_percent < 1.0")

    @classmethod
    def no_exit(cls) -> "ExitSignal":
        """Factory for no-exit signal (convenience method)."""
        return cls(should_exit=False)

    @classmethod
    def full_exit(cls, reason: str, price: float) -> "ExitSignal":
        """Factory for full exit signal (convenience method)."""
        return cls(
            should_exit=True,
            reason=reason,
            exit_price=price,
            partial_exit=False,
            exit_percent=1.0
        )

    @classmethod
    def partial_exit_signal(
        cls,
        reason: str,
        price: float,
        percent: float
    ) -> "ExitSignal":
        """Factory for partial exit signal (convenience method)."""
        return cls(
            should_exit=True,
            reason=reason,
            exit_price=price,
            partial_exit=True,
            exit_percent=percent
        )


@runtime_checkable
class ExitStrategyProtocol(Protocol):
    """
    Interface for position exit strategies.

    Exit strategies determine when and how to close positions. They can
    implement simple rules (stop/target) or complex price action logic
    (trailing stops, MA breaks, momentum exhaustion, etc.).

    Example:
        >>> from interfaces import ExitStrategyProtocol, ExitSignal, Position
        >>> from strategies import get_exit_strategy
        >>>
        >>> exit_strategy: ExitStrategyProtocol = get_exit_strategy('smart_exits')
        >>>
        >>> position: Position = ...  # Current position
        >>> current_price: float = 105.50
        >>> bars: List = ...  # Recent price bars for calculations
        >>>
        >>> signal: ExitSignal = exit_strategy.check_exit(
        >>>     position, current_price, datetime.now(), bars
        >>> )
        >>>
        >>> if signal.should_exit:
        >>>     print(f"Exit {signal.exit_percent*100}% at {signal.exit_price} ({signal.reason})")
    """

    def check_exit(
        self,
        position: "Position",
        current_price: float,
        current_date: datetime,
        bars: List  # Recent price bars for MA, ATR, etc. calculations
    ) -> ExitSignal:
        """
        Check if position should be exited.

        This method is called:
        - During backtests: Once per day (end of day close)
        - During live trading: Intraday for stop checks, EOD for profit-taking

        Args:
            position: Current position with entry data and tracking state
            current_price: Latest price (close for EOD, current for intraday)
            current_date: Current datetime
            bars: Recent price bars needed for calculations (e.g., last 20 days for MAs)
                 Each bar should have: open, high, low, close, volume

        Returns:
            ExitSignal indicating whether to exit (and how much)

        Implementation Notes:
        - Use position.strategy_state to store stateful tracking (e.g., highest_high)
        - Update position.max_favorable_excursion and max_adverse_excursion
        - For partial exits, return multiple signals over time
        - Always check stops before profit targets (risk management first)
        """
        ...

    @property
    def strategy_name(self) -> str:
        """
        Return unique exit strategy identifier.

        Examples: 'smart_exits', 'scaled_exits', 'fixed_stop_target'

        Used for:
        - Database storage (tracking which exit logic was used)
        - Results reporting
        - Strategy comparison
        """
        ...

    @property
    def supports_partial_exits(self) -> bool:
        """
        Indicate whether this strategy can return partial exit signals.

        Returns:
            True if strategy implements scaled/partial exits
            False if strategy only does full position exits

        This helps:
        - Execution systems know if they need to handle partial exits
        - Backtests properly calculate position sizing
        - UI show appropriate exit tracking
        """
        ...

    def get_initial_stop(self, entry_price: float, atr: float | None = None) -> float:
        """
        Calculate initial stop loss price for a new position.

        Args:
            entry_price: Entry price for the position
            atr: Optional Average True Range for volatility-based stops

        Returns:
            Stop loss price

        Examples:
        - Fixed percent: entry_price * 0.92 (8% stop)
        - ATR-based: entry_price - (2 * atr)
        - Support level: previous_low - 0.01
        """
        ...
