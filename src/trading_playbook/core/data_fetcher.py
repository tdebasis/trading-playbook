"""
Data fetcher interface (Port in Hexagonal Architecture).

This defines the contract that any data source adapter must implement.
The core business logic depends on this interface, not on specific implementations.

Like a Java interface - we code against abstractions, not implementations.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List
import pandas as pd
from trading_playbook.models.market_data import Bar, TimeFrame


class DataFetcher(ABC):
    """
    Abstract interface for fetching market data.

    Any data source (Alpaca, Polygon, CSV files, etc.) must implement this interface.
    This allows us to swap data sources without changing core business logic.

    Think of this as a Java interface that defines the contract.
    """

    @abstractmethod
    def fetch_intraday_bars(
        self,
        symbol: str,
        date: date,
        timeframe: TimeFrame
    ) -> List[Bar]:
        """
        Fetch intraday bars for a specific symbol and date.

        Args:
            symbol: Stock symbol (e.g., "QQQ")
            date: Trading date to fetch data for
            timeframe: Bar interval (e.g., TimeFrame.MINUTE_2)

        Returns:
            List of Bar objects for the trading day

        Raises:
            DataFetchError: If data cannot be fetched

        Example:
            >>> bars = fetcher.fetch_intraday_bars(
            ...     symbol="QQQ",
            ...     date=date(2024, 11, 1),
            ...     timeframe=TimeFrame.MINUTE_2
            ... )
            >>> len(bars)
            195  # Full trading day of 2-min bars
        """
        pass

    @abstractmethod
    def fetch_daily_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Fetch daily bars for a date range.

        This is used for calculating longer-period indicators like SMA200.

        Args:
            symbol: Stock symbol (e.g., "QQQ")
            start_date: First date to fetch (inclusive)
            end_date: Last date to fetch (inclusive)

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
            Index is timestamp (datetime)

        Raises:
            DataFetchError: If data cannot be fetched

        Example:
            >>> df = fetcher.fetch_daily_bars(
            ...     symbol="QQQ",
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 3, 31)
            ... )
            >>> len(df)
            60  # ~60 trading days in Q1
        """
        pass


class DataFetchError(Exception):
    """
    Raised when data cannot be fetched.

    This is a domain-specific exception that wraps underlying errors
    (network issues, API errors, etc.) into a single exception type
    that the business logic can handle.
    """
    pass
