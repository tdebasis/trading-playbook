"""
Unit tests for CachedDataFetcher.

These tests verify the caching behavior without hitting real APIs.
We use a mock fetcher to simulate API responses.
"""

from datetime import date, datetime
from pathlib import Path
import tempfile
import pytest
import pandas as pd

from trading_playbook.core.data_fetcher import DataFetcher
from trading_playbook.models.market_data import Bar, TimeFrame
from trading_playbook.adapters.cached_fetcher import CachedDataFetcher


class MockDataFetcher(DataFetcher):
    """
    Mock implementation of DataFetcher for testing.

    This simulates an API without actually making network calls.
    We can control exactly what data it returns and count how many times it's called.
    """

    def __init__(self):
        self.intraday_call_count = 0
        self.daily_call_count = 0

    def fetch_intraday_bars(self, symbol: str, date: date, timeframe: TimeFrame):
        """Return mock intraday data."""
        self.intraday_call_count += 1

        # Return 3 mock bars
        return [
            Bar(
                timestamp=datetime(2024, 11, 1, 9, 30),
                open=450.0,
                high=451.0,
                low=449.5,
                close=450.5,
                volume=1000000
            ),
            Bar(
                timestamp=datetime(2024, 11, 1, 9, 32),
                open=450.5,
                high=451.5,
                low=450.0,
                close=451.0,
                volume=1100000
            ),
            Bar(
                timestamp=datetime(2024, 11, 1, 9, 34),
                open=451.0,
                high=452.0,
                low=450.5,
                close=451.5,
                volume=1200000
            )
        ]

    def fetch_daily_bars(self, symbol: str, start_date: date, end_date: date):
        """Return mock daily data."""
        self.daily_call_count += 1

        # Return 3 days of mock data
        data = [
            {
                'timestamp': datetime(2024, 11, 1),
                'open': 450.0,
                'high': 455.0,
                'low': 448.0,
                'close': 453.0,
                'volume': 50000000
            },
            {
                'timestamp': datetime(2024, 11, 4),
                'open': 453.0,
                'high': 456.0,
                'low': 452.0,
                'close': 455.0,
                'volume': 55000000
            },
            {
                'timestamp': datetime(2024, 11, 5),
                'open': 455.0,
                'high': 458.0,
                'low': 454.0,
                'close': 457.0,
                'volume': 52000000
            }
        ]

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df


class TestCachedDataFetcher:
    """Test cases for CachedDataFetcher."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_fetcher(self):
        """Create a mock fetcher."""
        return MockDataFetcher()

    @pytest.fixture
    def cached_fetcher(self, mock_fetcher, temp_cache_dir):
        """Create a cached fetcher with mock underlying fetcher."""
        return CachedDataFetcher(mock_fetcher, cache_dir=temp_cache_dir)

    def test_intraday_first_call_fetches_from_source(self, cached_fetcher, mock_fetcher):
        """Test that first call fetches from underlying source."""
        # Act
        bars = cached_fetcher.fetch_intraday_bars(
            "QQQ",
            date(2024, 11, 1),
            TimeFrame.MINUTE_2
        )

        # Assert
        assert len(bars) == 3
        assert mock_fetcher.intraday_call_count == 1  # Called once

    def test_intraday_second_call_uses_cache(self, cached_fetcher, mock_fetcher):
        """Test that second call loads from cache, doesn't hit source."""
        # Arrange: First call to populate cache
        bars1 = cached_fetcher.fetch_intraday_bars(
            "QQQ",
            date(2024, 11, 1),
            TimeFrame.MINUTE_2
        )

        # Act: Second call should use cache
        bars2 = cached_fetcher.fetch_intraday_bars(
            "QQQ",
            date(2024, 11, 1),
            TimeFrame.MINUTE_2
        )

        # Assert
        assert len(bars2) == 3
        assert mock_fetcher.intraday_call_count == 1  # Still only called once!

        # Verify data is the same
        assert bars1[0].timestamp == bars2[0].timestamp
        assert bars1[0].close == bars2[0].close

    def test_intraday_cache_file_created(self, cached_fetcher, temp_cache_dir):
        """Test that cache file is created in correct location."""
        # Act
        cached_fetcher.fetch_intraday_bars(
            "QQQ",
            date(2024, 11, 1),
            TimeFrame.MINUTE_2
        )

        # Assert
        cache_file = Path(temp_cache_dir) / "intraday" / "QQQ_2024-11-01_2Min.parquet"
        assert cache_file.exists()

    def test_daily_first_call_fetches_from_source(self, cached_fetcher, mock_fetcher):
        """Test that first daily call fetches from underlying source."""
        # Act
        df = cached_fetcher.fetch_daily_bars(
            "QQQ",
            date(2024, 11, 1),
            date(2024, 11, 5)
        )

        # Assert
        assert len(df) == 3
        assert mock_fetcher.daily_call_count == 1

    def test_daily_second_call_uses_cache(self, cached_fetcher, mock_fetcher):
        """Test that second daily call loads from cache."""
        # Arrange: First call to populate cache
        df1 = cached_fetcher.fetch_daily_bars(
            "QQQ",
            date(2024, 11, 1),
            date(2024, 11, 5)
        )

        # Act: Second call should use cache
        df2 = cached_fetcher.fetch_daily_bars(
            "QQQ",
            date(2024, 11, 1),
            date(2024, 11, 5)
        )

        # Assert
        assert len(df2) == 3
        assert mock_fetcher.daily_call_count == 1  # Still only called once!

        # Verify data is the same
        assert df1.iloc[0]['close'] == df2.iloc[0]['close']

    def test_daily_cache_file_created(self, cached_fetcher, temp_cache_dir):
        """Test that daily cache file is created."""
        # Act
        cached_fetcher.fetch_daily_bars(
            "QQQ",
            date(2024, 11, 1),
            date(2024, 11, 5)
        )

        # Assert
        cache_file = (
            Path(temp_cache_dir) / "daily" / "QQQ_2024-11-01_2024-11-05.parquet"
        )
        assert cache_file.exists()

    def test_different_dates_create_different_cache_files(self, cached_fetcher, mock_fetcher):
        """Test that different dates create separate cache files."""
        # Act
        cached_fetcher.fetch_intraday_bars("QQQ", date(2024, 11, 1), TimeFrame.MINUTE_2)
        cached_fetcher.fetch_intraday_bars("QQQ", date(2024, 11, 4), TimeFrame.MINUTE_2)

        # Assert: Should have called source twice (different dates)
        assert mock_fetcher.intraday_call_count == 2

    def test_different_symbols_create_different_cache_files(self, cached_fetcher, mock_fetcher):
        """Test that different symbols create separate cache files."""
        # Act
        cached_fetcher.fetch_intraday_bars("QQQ", date(2024, 11, 1), TimeFrame.MINUTE_2)
        cached_fetcher.fetch_intraday_bars("SPY", date(2024, 11, 1), TimeFrame.MINUTE_2)

        # Assert: Should have called source twice (different symbols)
        assert mock_fetcher.intraday_call_count == 2

    def test_clear_cache_removes_all_files(self, cached_fetcher, temp_cache_dir):
        """Test that clear_cache removes all cached files."""
        # Arrange: Create some cached data
        cached_fetcher.fetch_intraday_bars("QQQ", date(2024, 11, 1), TimeFrame.MINUTE_2)
        cached_fetcher.fetch_daily_bars("QQQ", date(2024, 11, 1), date(2024, 11, 5))

        cache_dir = Path(temp_cache_dir)
        assert (cache_dir / "intraday").exists()
        assert (cache_dir / "daily").exists()

        # Act
        cached_fetcher.clear_cache()

        # Assert: Directories should be empty (recreated but empty)
        assert (cache_dir / "intraday").exists()
        assert (cache_dir / "daily").exists()
        assert len(list((cache_dir / "intraday").iterdir())) == 0
        assert len(list((cache_dir / "daily").iterdir())) == 0


# Run tests with: poetry run pytest tests/adapters/test_cached_fetcher.py -v
