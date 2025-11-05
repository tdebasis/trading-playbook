"""
Caching wrapper for DataFetcher.

This is a decorator/wrapper that adds file-based caching to any DataFetcher.
Uses parquet format for efficient storage and fast loading.

This minimizes API calls and costs - once data is fetched, it's cached locally.
"""

from datetime import date
from pathlib import Path
from typing import List
import pandas as pd

from trading_playbook.core.data_fetcher import DataFetcher, DataFetchError
from trading_playbook.models.market_data import Bar, TimeFrame


class CachedDataFetcher(DataFetcher):
    """
    Decorator that wraps another DataFetcher and adds file-based caching.

    This implements the Decorator pattern - it wraps an existing DataFetcher
    and adds caching behavior without modifying the original.

    Cache structure:
        cache_dir/
            intraday/
                QQQ_2024-11-01_2Min.parquet
                QQQ_2024-11-02_2Min.parquet
            daily/
                QQQ_2024-01-01_2024-03-31.parquet

    Args:
        fetcher: The underlying DataFetcher to wrap
        cache_dir: Directory to store cached data (default: ./data/cache)

    Example:
        >>> alpaca_fetcher = AlpacaDataFetcher(api_key, secret_key)
        >>> cached_fetcher = CachedDataFetcher(alpaca_fetcher, cache_dir="./data/cache")
        >>> # First call fetches from API and caches
        >>> bars = cached_fetcher.fetch_intraday_bars("QQQ", date(2024, 11, 1), TimeFrame.MINUTE_2)
        >>> # Second call loads from cache (much faster, free)
        >>> bars = cached_fetcher.fetch_intraday_bars("QQQ", date(2024, 11, 1), TimeFrame.MINUTE_2)
    """

    def __init__(self, fetcher: DataFetcher, cache_dir: str = "./data/cache"):
        """Initialize the cached fetcher."""
        self.fetcher = fetcher
        self.cache_dir = Path(cache_dir)
        self.intraday_cache_dir = self.cache_dir / "intraday"
        self.daily_cache_dir = self.cache_dir / "daily"

        # Create cache directories if they don't exist
        self.intraday_cache_dir.mkdir(parents=True, exist_ok=True)
        self.daily_cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_intraday_bars(
        self,
        symbol: str,
        date: date,
        timeframe: TimeFrame
    ) -> List[Bar]:
        """
        Fetch intraday bars with caching.

        Checks cache first. If not found, fetches from underlying source and caches.
        """
        # Build cache file path
        # Example: QQQ_2024-11-01_2Min.parquet
        cache_file = self.intraday_cache_dir / f"{symbol}_{date.isoformat()}_{timeframe.value}.parquet"

        # Try to load from cache
        if cache_file.exists():
            try:
                df = pd.read_parquet(cache_file)
                return self._dataframe_to_bars(df)
            except Exception as e:
                # Cache corrupted, delete and re-fetch
                cache_file.unlink()

        # Not in cache, fetch from underlying source
        bars = self.fetcher.fetch_intraday_bars(symbol, date, timeframe)

        # Cache the data for next time
        if bars:  # Only cache if we got data
            try:
                df = self._bars_to_dataframe(bars)
                df.to_parquet(cache_file)
            except Exception as e:
                # Failed to cache, but we still have the data
                pass

        return bars

    def fetch_daily_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Fetch daily bars with caching.

        Checks cache first. If not found, fetches from underlying source and caches.
        """
        # Build cache file path
        # Example: QQQ_2024-01-01_2024-03-31.parquet
        cache_file = (
            self.daily_cache_dir /
            f"{symbol}_{start_date.isoformat()}_{end_date.isoformat()}.parquet"
        )

        # Try to load from cache
        if cache_file.exists():
            try:
                df = pd.read_parquet(cache_file)
                return df
            except Exception as e:
                # Cache corrupted, delete and re-fetch
                cache_file.unlink()

        # Not in cache, fetch from underlying source
        df = self.fetcher.fetch_daily_bars(symbol, start_date, end_date)

        # Cache the data for next time
        if not df.empty:  # Only cache if we got data
            try:
                df.to_parquet(cache_file)
            except Exception as e:
                # Failed to cache, but we still have the data
                pass

        return df

    def _bars_to_dataframe(self, bars: List[Bar]) -> pd.DataFrame:
        """Convert list of Bar objects to DataFrame for caching."""
        data = []
        for bar in bars:
            data.append({
                'timestamp': bar.timestamp,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'vwap': bar.vwap,
                'trade_count': bar.trade_count
            })

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df

    def _dataframe_to_bars(self, df: pd.DataFrame) -> List[Bar]:
        """Convert cached DataFrame back to list of Bar objects."""
        bars = []
        for timestamp, row in df.iterrows():
            bar = Bar(
                timestamp=timestamp,
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
                vwap=row.get('vwap'),
                trade_count=row.get('trade_count')
            )
            bars.append(bar)

        return bars

    def clear_cache(self):
        """
        Clear all cached data.

        Useful for testing or when you want to force a fresh fetch.
        """
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.intraday_cache_dir.mkdir(parents=True, exist_ok=True)
            self.daily_cache_dir.mkdir(parents=True, exist_ok=True)
