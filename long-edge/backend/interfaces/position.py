"""
Position data model for trading systems.

Standardized position tracking across all strategies and execution environments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class Position:
    """
    Standardized position representation across all strategies.

    This is the core data structure for tracking trades. It's used in:
    - Backtests (simulated positions)
    - Paper trading (virtual positions)
    - Live trading (real positions)

    All exit strategies work with this Position model, making them
    interchangeable and testable.
    """

    # Core identification
    symbol: str
    entry_date: datetime
    entry_price: float
    shares: int

    # Risk management
    stop_price: float  # Current stop loss price (can be updated for trailing stops)

    # Exit tracking
    exit_date: datetime | None = None
    exit_price: float | None = None
    exit_reason: str | None = None

    # Performance tracking
    max_favorable_excursion: float = 0.0  # Highest profit % reached
    max_adverse_excursion: float = 0.0  # Worst loss % reached (negative)

    # Strategy-specific state (extensible)
    # Exit strategies use this to track state (e.g., highest_high for trailing stops)
    # Examples: {'highest_high': 105.50, 'scaled_25_pct': True, 'ma_break_active': False}
    strategy_state: Dict[str, any] = field(default_factory=dict)

    # Partial exit tracking (for scaled exits)
    partial_exits: List[Dict] = field(default_factory=list)
    # Each partial exit: {'date': datetime, 'shares': int, 'price': float, 'reason': str}

    def __post_init__(self):
        """Validate position data."""
        if self.shares <= 0:
            raise ValueError(f"Shares must be positive, got {self.shares}")

        if self.entry_price <= 0:
            raise ValueError(f"Entry price must be positive, got {self.entry_price}")

        if self.stop_price <= 0:
            raise ValueError(f"Stop price must be positive, got {self.stop_price}")

        if self.stop_price >= self.entry_price:
            raise ValueError(
                f"Stop ({self.stop_price}) must be below entry ({self.entry_price})"
            )

    @property
    def is_open(self) -> bool:
        """Check if position is still open."""
        return self.exit_date is None

    @property
    def is_closed(self) -> bool:
        """Check if position is closed."""
        return self.exit_date is not None

    @property
    def original_shares(self) -> int:
        """Get original share count (before any partial exits)."""
        total_exited = sum(exit['shares'] for exit in self.partial_exits)
        return self.shares + total_exited

    def unrealized_pnl(self, current_price: float) -> float:
        """
        Calculate unrealized P&L for open position.

        Args:
            current_price: Current market price

        Returns:
            Unrealized profit/loss in dollars
        """
        if self.is_closed:
            return 0.0

        return (current_price - self.entry_price) * self.shares

    def unrealized_pnl_percent(self, current_price: float) -> float:
        """
        Calculate unrealized P&L as percentage.

        Args:
            current_price: Current market price

        Returns:
            Unrealized profit/loss as percentage (e.g., 5.5 for +5.5%)
        """
        if self.is_closed:
            return 0.0

        return ((current_price - self.entry_price) / self.entry_price) * 100

    def realized_pnl(self) -> float:
        """
        Calculate realized P&L (after exit).

        Includes P&L from partial exits.

        Returns:
            Realized profit/loss in dollars, or 0.0 if position still open
        """
        if not self.is_closed:
            return 0.0

        # P&L from final exit
        final_pnl = (self.exit_price - self.entry_price) * self.shares

        # Add P&L from partial exits
        for exit_info in self.partial_exits:
            partial_pnl = (exit_info['price'] - self.entry_price) * exit_info['shares']
            final_pnl += partial_pnl

        return final_pnl

    def realized_pnl_percent(self) -> float:
        """
        Calculate realized P&L as percentage.

        Returns:
            Realized profit/loss as percentage of entry value
        """
        if not self.is_closed:
            return 0.0

        entry_value = self.entry_price * self.original_shares
        return (self.realized_pnl() / entry_value) * 100

    def hold_days(self, current_date: datetime | None = None) -> int:
        """
        Calculate days position has been held.

        Args:
            current_date: Current date (for open positions), defaults to now

        Returns:
            Number of calendar days held
        """
        end_date = self.exit_date if self.is_closed else (current_date or datetime.now())
        return (end_date.date() - self.entry_date.date()).days

    def r_multiple(self) -> float | None:
        """
        Calculate R-multiple (profit/loss in units of initial risk).

        R-multiple is a risk-adjusted performance metric:
        - 1R = profit equal to initial risk
        - 2R = profit equal to 2x initial risk
        - -1R = loss equal to initial risk

        Returns:
            R-multiple, or None if position still open
        """
        if not self.is_closed:
            return None

        initial_risk = self.entry_price - self.stop_price
        if initial_risk <= 0:
            return None

        pnl_per_share = self.realized_pnl() / self.original_shares
        return pnl_per_share / initial_risk

    def update_mfe_mae(self, current_price: float) -> None:
        """
        Update max favorable/adverse excursion tracking.

        This should be called on every price update to track:
        - MFE: How far in your favor the position moved
        - MAE: How far against you the position moved

        Useful for:
        - Optimizing stops (how much heat can you tolerate?)
        - Optimizing targets (how much profit do trades typically give?)

        Args:
            current_price: Current market price
        """
        current_pnl_pct = self.unrealized_pnl_percent(current_price)

        # Update MFE (highest profit reached)
        if current_pnl_pct > self.max_favorable_excursion:
            self.max_favorable_excursion = current_pnl_pct

        # Update MAE (worst loss reached)
        if current_pnl_pct < self.max_adverse_excursion:
            self.max_adverse_excursion = current_pnl_pct

    def add_partial_exit(
        self,
        exit_date: datetime,
        shares: int,
        price: float,
        reason: str
    ) -> None:
        """
        Record a partial exit (scaled exit strategies).

        Args:
            exit_date: When partial exit occurred
            shares: How many shares exited
            price: Exit price
            reason: Exit reason (e.g., "SCALE_1", "SCALE_2")

        Raises:
            ValueError: If trying to exit more shares than held
        """
        if shares > self.shares:
            raise ValueError(
                f"Cannot exit {shares} shares, only {self.shares} shares held"
            )

        if shares <= 0:
            raise ValueError(f"Shares must be positive, got {shares}")

        self.partial_exits.append({
            'date': exit_date,
            'shares': shares,
            'price': price,
            'reason': reason
        })

        self.shares -= shares

    def to_dict(self) -> dict:
        """
        Serialize position for database storage or API response.

        Returns:
            Dictionary with all position data
        """
        return {
            'symbol': self.symbol,
            'entry_date': self.entry_date.isoformat(),
            'entry_price': self.entry_price,
            'shares': self.shares,
            'original_shares': self.original_shares,
            'stop_price': self.stop_price,
            'exit_date': self.exit_date.isoformat() if self.exit_date else None,
            'exit_price': self.exit_price,
            'exit_reason': self.exit_reason,
            'max_favorable_excursion': self.max_favorable_excursion,
            'max_adverse_excursion': self.max_adverse_excursion,
            'is_open': self.is_open,
            'hold_days': self.hold_days(),
            'realized_pnl': self.realized_pnl() if self.is_closed else None,
            'realized_pnl_percent': self.realized_pnl_percent() if self.is_closed else None,
            'r_multiple': self.r_multiple(),
            'partial_exits': self.partial_exits,
            'strategy_state': self.strategy_state
        }
