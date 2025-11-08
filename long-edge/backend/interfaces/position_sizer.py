"""
Position sizing interface for risk management.

Determines how many shares to buy based on account size and risk rules.
"""

from __future__ import annotations

from typing import Protocol, Optional, runtime_checkable, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .scanner import Candidate


@dataclass
class PositionSize:
    """
    Result of position sizing calculation.

    Contains all information needed to execute a trade with proper
    risk management.
    """

    # Execution details
    shares: int  # Number of shares to buy
    position_value: float  # Dollar value of position (shares × price)

    # Risk metrics
    risk_amount: float  # Dollar amount at risk (stop distance × shares)
    risk_percent: float  # Percentage of account at risk (e.g., 1.0 = 1%)

    # Additional info
    entry_price: float  # Price being entered at
    stop_price: float  # Stop loss price
    max_position_value: float  # Maximum allowed position size

    def __post_init__(self):
        """Validate position size data."""
        if self.shares < 0:
            raise ValueError(f"Shares cannot be negative, got {self.shares}")

        if self.position_value < 0:
            raise ValueError(f"Position value cannot be negative, got {self.position_value}")

        if self.risk_amount < 0:
            raise ValueError(f"Risk amount cannot be negative, got {self.risk_amount}")

        if self.risk_percent < 0 or self.risk_percent > 100:
            raise ValueError(f"Risk percent must be 0-100, got {self.risk_percent}")

    @property
    def stop_distance_percent(self) -> float:
        """Calculate stop distance as percentage of entry price."""
        return ((self.entry_price - self.stop_price) / self.entry_price) * 100

    @property
    def shares_to_stop(self) -> float:
        """Calculate dollar value risked per share."""
        return self.entry_price - self.stop_price

    def to_dict(self) -> dict:
        """Serialize for logging or storage."""
        return {
            'shares': self.shares,
            'position_value': self.position_value,
            'risk_amount': self.risk_amount,
            'risk_percent': self.risk_percent,
            'entry_price': self.entry_price,
            'stop_price': self.stop_price,
            'stop_distance_percent': self.stop_distance_percent,
            'shares_to_stop': self.shares_to_stop,
            'max_position_value': self.max_position_value
        }


@runtime_checkable
class PositionSizerProtocol(Protocol):
    """
    Interface for position sizing strategies.

    Position sizers determine HOW MUCH to buy based on:
    - Account equity
    - Risk tolerance
    - Stop distance
    - Volatility
    - Position limits

    Different strategies:
    - Fixed risk (e.g., 1% per trade)
    - Fixed percent of capital (e.g., 20% per position)
    - Volatility-based (ATR-adjusted)
    - Kelly Criterion
    - Fixed shares (for testing)

    Example:
        >>> from interfaces import PositionSizerProtocol, Candidate, PositionSize
        >>> from strategies import get_position_sizer
        >>>
        >>> sizer: PositionSizerProtocol = get_position_sizer('fixed_risk', risk_percent=1.0)
        >>>
        >>> candidate: Candidate = ...  # From scanner
        >>> account_equity: float = 100_000
        >>>
        >>> size: PositionSize = sizer.calculate_size(
        >>>     account_equity=account_equity,
        >>>     entry_price=candidate.entry_price,
        >>>     stop_price=candidate.suggested_stop,
        >>>     candidate=candidate
        >>> )
        >>>
        >>> print(f"Buy {size.shares} shares, risking ${size.risk_amount} ({size.risk_percent}%)")
    """

    def calculate_size(
        self,
        account_equity: float,
        entry_price: float,
        stop_price: float,
        candidate: "Candidate"
    ) -> PositionSize:
        """
        Calculate position size based on risk rules.

        Args:
            account_equity: Current account value (including cash and positions)
            entry_price: Planned entry price for the position
            stop_price: Planned stop loss price
            candidate: Candidate from scanner (may contain volatility, score, etc.)

        Returns:
            PositionSize with shares and risk metrics

        Implementation Notes:
        - Always round down shares (never exceed max risk)
        - Consider minimum lot sizes (1 share minimum)
        - Account for commissions if applicable
        - Respect position limits (e.g., max 30% of capital per position)
        - Handle edge cases (stop too close, stock too expensive, etc.)
        """
        ...

    @property
    def strategy_name(self) -> str:
        """
        Return position sizing strategy name.

        Examples: 'fixed_risk_1pct', 'fixed_percent_20pct', 'atr_based', 'kelly'

        Used for:
        - Logging and debugging
        - Strategy comparison
        - Results reporting
        """
        ...

    @property
    def max_position_percent(self) -> float:
        """
        Return maximum position size as percentage of account.

        This is a safety limit to prevent over-concentration.

        Examples:
        - 20.0 = Maximum 20% of account in one position
        - 100.0 = No limit (all-in allowed)

        Returns:
            Maximum position size percentage (0-100)
        """
        ...

    @property
    def max_risk_percent(self) -> float:
        """
        Return maximum risk per trade as percentage of account.

        This is the core risk management parameter.

        Examples:
        - 1.0 = Risk 1% of account per trade (conservative)
        - 2.0 = Risk 2% of account per trade (moderate)
        - 5.0 = Risk 5% of account per trade (aggressive)

        Returns:
            Maximum risk percentage (0-100)
        """
        ...
