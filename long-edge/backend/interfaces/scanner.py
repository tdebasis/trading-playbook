"""
Scanner interface for trading strategies.

Defines the standard contract for all entry signal scanners.
"""

from __future__ import annotations
from typing import Protocol, List, Optional, runtime_checkable
from datetime import datetime, date
from dataclasses import dataclass, field


@dataclass
class Candidate:
    """
    Standardized candidate output from any scanner.

    This is the contract between scanners and execution systems. All scanners
    must convert their internal representations to this format.
    """

    # Core identification
    symbol: str
    scan_date: date
    score: float  # 0-10 quality score (higher = better setup)

    # Entry information
    entry_price: float  # Suggested entry price

    # Risk management
    suggested_stop: float  # Suggested stop loss price
    suggested_target: Optional[float] = None  # Optional profit target

    # Strategy-specific data (extensible)
    # Use this dict to store any additional metrics specific to your strategy
    # Examples: consolidation_days, volume_ratio, rsi, etc.
    strategy_data: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate candidate data."""
        if self.score < 0 or self.score > 10:
            raise ValueError(f"Score must be 0-10, got {self.score}")

        if self.entry_price <= 0:
            raise ValueError(f"Entry price must be positive, got {self.entry_price}")

        if self.suggested_stop <= 0:
            raise ValueError(f"Stop price must be positive, got {self.suggested_stop}")

        if self.suggested_stop >= self.entry_price:
            raise ValueError(
                f"Stop ({self.suggested_stop}) must be below entry ({self.entry_price})"
            )

    def risk_percent(self) -> float:
        """Calculate risk as percentage of entry price."""
        return ((self.entry_price - self.suggested_stop) / self.entry_price) * 100

    def risk_reward_ratio(self) -> Optional[float]:
        """Calculate risk/reward ratio if target is set."""
        if self.suggested_target is None:
            return None

        risk = self.entry_price - self.suggested_stop
        reward = self.suggested_target - self.entry_price

        if risk <= 0:
            return None

        return reward / risk

    def to_dict(self) -> dict:
        """
        Serialize for database storage or API response.

        Returns:
            Dictionary with all candidate data including strategy_data.
        """
        return {
            'symbol': self.symbol,
            'scan_date': self.scan_date.isoformat(),
            'score': self.score,
            'entry_price': self.entry_price,
            'suggested_stop': self.suggested_stop,
            'suggested_target': self.suggested_target,
            'risk_percent': self.risk_percent(),
            'risk_reward_ratio': self.risk_reward_ratio(),
            **self.strategy_data  # Flatten strategy-specific data
        }


@runtime_checkable
class ScannerProtocol(Protocol):
    """
    Interface for all trading strategy scanners.

    Any scanner that implements this interface can be used interchangeably
    in backtests, cloud services, and live trading systems.

    Example:
        >>> from interfaces import ScannerProtocol, Candidate
        >>> from strategies import get_scanner
        >>>
        >>> scanner: ScannerProtocol = get_scanner('daily_breakout', api_key, secret)
        >>> candidates: List[Candidate] = scanner.scan()
        >>>
        >>> for candidate in candidates:
        >>>     if candidate.score >= 8.0:
        >>>         print(f"Strong setup: {candidate.symbol} @ {candidate.entry_price}")
    """

    def scan(self, scan_date: Optional[datetime] = None) -> List[Candidate]:
        """
        Scan for trading opportunities.

        Args:
            scan_date: Date to scan (default: today/most recent market day).
                      Allows historical scanning for backtesting.

        Returns:
            List of Candidate objects sorted by score (best first).
            Returns empty list if no candidates found.

        Raises:
            ValueError: If scan_date is invalid or data unavailable.
            ConnectionError: If market data source is unavailable.
        """
        ...

    @property
    def strategy_name(self) -> str:
        """
        Return unique strategy identifier.

        Examples: 'daily_breakout', 'momentum_20', 'gap_and_go'

        This is used for:
        - Database storage (tracking which strategy generated candidates)
        - Strategy selection in cloud services
        - Results reporting and comparison
        """
        ...

    @property
    def timeframe(self) -> str:
        """
        Return trading timeframe.

        Examples: 'daily', 'intraday', '4hour', '60min'

        Helps execution systems understand:
        - When to check for signals
        - How to manage positions
        - Which data feeds to use
        """
        ...

    @property
    def universe(self) -> List[str]:
        """
        Return list of symbols this scanner monitors.

        Returns:
            List of stock symbols (e.g., ['NVDA', 'TSLA', 'AMD'])

        Note: Some scanners may have dynamic universes (e.g., top 100 by volume).
        In that case, return the current universe or a representative sample.
        """
        ...
