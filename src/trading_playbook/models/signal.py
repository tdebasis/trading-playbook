"""
Signal models for trading strategies.

These represent detected entry signals with all relevant metadata.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DP20Signal:
    """
    Represents a detected DP20 entry signal.

    This captures all the important data points from the signal detection process.
    Immutable (frozen=True) to prevent accidental modifications.

    Attributes:
        signal_detected: Whether a valid signal was found
        date: Trading date
        notes: Human-readable explanation (e.g., "No pullback detected")

        # Signal progression timestamps
        pullback_time: When price first closed below EMA20 (optional)
        reversal_time: When price closed back above EMA20 with strength (optional)
        reversal_strength: Body percentage of reversal candle (optional)
        confirmation_time: When confirmation candle closed (optional)

        # Entry details
        entry_time: When to enter (open of next candle) (optional)
        entry_price: Entry price (optional)
        ema20_at_entry: EMA20 value at entry (optional)
        atr14_at_entry: ATR14 value at entry (optional)
        stop_distance: Distance from entry to stop (optional)
        stop_price: Stop loss price (optional)

    Example:
        >>> signal = DP20Signal(
        ...     signal_detected=True,
        ...     date=date(2024, 11, 1),
        ...     notes="Valid DP20 signal detected",
        ...     entry_time=datetime(2024, 11, 1, 10, 32),
        ...     entry_price=450.25,
        ...     stop_price=447.80
        ... )
    """
    signal_detected: bool
    date: datetime
    notes: str

    # Optional fields (present only when signal detected)
    pullback_time: Optional[datetime] = None
    reversal_time: Optional[datetime] = None
    reversal_strength: Optional[float] = None
    confirmation_time: Optional[datetime] = None
    entry_time: Optional[datetime] = None
    entry_price: Optional[float] = None
    ema20_at_entry: Optional[float] = None
    atr14_at_entry: Optional[float] = None
    stop_distance: Optional[float] = None
    stop_price: Optional[float] = None

    def __str__(self) -> str:
        """Human-readable string representation."""
        if not self.signal_detected:
            return f"DP20Signal({self.date.date()}): No signal - {self.notes}"

        return (
            f"DP20Signal({self.date.date()}): "
            f"Entry @ {self.entry_time.time()} "
            f"${self.entry_price:.2f}, "
            f"Stop ${self.stop_price:.2f}"
        )
