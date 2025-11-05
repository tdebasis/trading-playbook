"""
Market data models.

These are immutable data classes representing market data.
Think of them as Java records or data classes.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TimeFrame(Enum):
    """Time frame for market data bars.

    This enum defines the supported time frames for fetching market data.
    """
    MINUTE_1 = "1Min"
    MINUTE_2 = "2Min"
    MINUTE_5 = "5Min"
    MINUTE_15 = "15Min"
    HOUR_1 = "1Hour"
    DAY_1 = "1Day"


@dataclass(frozen=True)
class Bar:
    """
    Represents a single OHLCV (Open, High, Low, Close, Volume) bar.

    This is immutable (frozen=True) to prevent accidental modifications.
    Like a Java record or final class with only getters.

    Attributes:
        timestamp: When this bar occurred (already in ET timezone)
        open: Opening price
        high: Highest price during the period
        low: Lowest price during the period
        close: Closing price
        volume: Number of shares traded
        vwap: Volume Weighted Average Price (optional, provided by Alpaca)
        trade_count: Number of trades (optional, provided by Alpaca)

    Example:
        >>> bar = Bar(
        ...     timestamp=datetime(2024, 11, 1, 9, 30),
        ...     open=450.00,
        ...     high=450.50,
        ...     low=449.75,
        ...     close=450.25,
        ...     volume=1000000
        ... )
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    trade_count: Optional[int] = None

    def __post_init__(self):
        """Validate the bar data after initialization."""
        if self.high < self.low:
            raise ValueError(f"High ({self.high}) cannot be less than low ({self.low})")

        if self.high < self.open or self.high < self.close:
            raise ValueError(f"High ({self.high}) must be >= open and close")

        if self.low > self.open or self.low > self.close:
            raise ValueError(f"Low ({self.low}) must be <= open and close")

        if self.volume < 0:
            raise ValueError(f"Volume ({self.volume}) cannot be negative")
