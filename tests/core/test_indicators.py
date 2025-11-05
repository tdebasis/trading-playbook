"""
Unit tests for technical indicators.

These tests verify that our indicator calculations are correct by comparing
against known values and expected behaviors.

Like JUnit tests in Java - each test is independent and focused.
"""

import pandas as pd
import numpy as np
import pytest
from trading_playbook.core.indicators import (
    calculate_ema,
    calculate_sma,
    calculate_atr,
    validate_price_data
)


class TestSMA:
    """Test cases for Simple Moving Average."""

    def test_sma_basic_calculation(self):
        """Test SMA with simple known values."""
        # Arrange: Create test data
        prices = pd.Series([10, 20, 30, 40, 50])

        # Act: Calculate 3-period SMA
        sma = calculate_sma(prices, period=3)

        # Assert: Check known values
        # First 2 values should be NaN (not enough data)
        assert pd.isna(sma.iloc[0])
        assert pd.isna(sma.iloc[1])

        # Third value: (10+20+30)/3 = 20
        assert sma.iloc[2] == 20.0

        # Fourth value: (20+30+40)/3 = 30
        assert sma.iloc[3] == 30.0

        # Fifth value: (30+40+50)/3 = 40
        assert sma.iloc[4] == 40.0

    def test_sma_empty_input(self):
        """Test SMA handles empty Series gracefully."""
        prices = pd.Series(dtype=float)
        sma = calculate_sma(prices, period=10)
        assert sma.empty

    def test_sma_invalid_period(self):
        """Test SMA raises error for invalid period."""
        prices = pd.Series([10, 20, 30])

        with pytest.raises(ValueError):
            calculate_sma(prices, period=0)

        with pytest.raises(ValueError):
            calculate_sma(prices, period=-5)

    def test_sma_period_longer_than_data(self):
        """Test SMA when period exceeds data length."""
        prices = pd.Series([10, 20, 30])
        sma = calculate_sma(prices, period=10)  # Period > data length

        # All values should be NaN (not enough data)
        assert all(pd.isna(sma))


class TestEMA:
    """Test cases for Exponential Moving Average."""

    def test_ema_basic_calculation(self):
        """Test EMA with simple values."""
        # Arrange
        prices = pd.Series([22, 24, 23, 25, 24, 26, 25])

        # Act
        ema = calculate_ema(prices, period=3)

        # Assert: EMA should exist and be reasonable
        assert len(ema) == len(prices)

        # EMA values should be between min and max of prices
        assert ema.min() >= prices.min()
        assert ema.max() <= prices.max()

        # EMA should smooth out fluctuations (less volatile than raw prices)
        # Standard deviation of EMA should be less than prices
        ema_no_nan = ema.dropna()
        if len(ema_no_nan) > 1:
            assert ema_no_nan.std() <= prices.std()

    def test_ema_converges_for_constant_price(self):
        """Test EMA converges to price when price is constant."""
        # If price is constant, EMA should equal that price
        prices = pd.Series([100.0] * 50)
        ema = calculate_ema(prices, period=20)

        # After warmup period, EMA should be very close to 100
        assert abs(ema.iloc[-1] - 100.0) < 0.01

    def test_ema_empty_input(self):
        """Test EMA handles empty Series."""
        prices = pd.Series(dtype=float)
        ema = calculate_ema(prices, period=10)
        assert ema.empty

    def test_ema_invalid_period(self):
        """Test EMA raises error for invalid period."""
        prices = pd.Series([10, 20, 30])

        with pytest.raises(ValueError):
            calculate_ema(prices, period=0)


class TestATR:
    """Test cases for Average True Range."""

    def test_atr_basic_calculation(self):
        """Test ATR with simple OHLC data."""
        # Arrange: Create sample OHLC data
        bars = pd.DataFrame({
            'high':  [105, 110, 108, 112, 115],
            'low':   [95,  100, 102, 105, 108],
            'close': [100, 105, 107, 110, 112]
        })

        # Act
        atr = calculate_atr(bars, period=3)

        # Assert
        assert len(atr) == len(bars)

        # ATR should be positive (volatility measure)
        atr_no_nan = atr.dropna()
        assert all(atr_no_nan > 0)

        # ATR should be less than max price range
        # (ATR averages out the ranges)
        max_range = (bars['high'] - bars['low']).max()
        assert atr.max() <= max_range

    def test_atr_missing_columns(self):
        """Test ATR raises error when required columns missing."""
        # Missing 'close' column
        bars = pd.DataFrame({
            'high': [100, 101],
            'low': [98, 99]
        })

        with pytest.raises(ValueError, match="missing required columns"):
            calculate_atr(bars, period=14)

    def test_atr_empty_dataframe(self):
        """Test ATR handles empty DataFrame."""
        bars = pd.DataFrame(columns=['high', 'low', 'close'])
        atr = calculate_atr(bars, period=14)
        assert atr.empty

    def test_atr_invalid_period(self):
        """Test ATR raises error for invalid period."""
        bars = pd.DataFrame({
            'high': [100, 101],
            'low': [98, 99],
            'close': [99, 100]
        })

        with pytest.raises(ValueError):
            calculate_atr(bars, period=0)

    def test_atr_first_value_behavior(self):
        """Test ATR calculation behavior with first bar.

        The first bar's true range is simply (high - low) since there's
        no previous close. EMA starts calculating from this first value,
        so the first ATR value is valid (not NaN).
        """
        bars = pd.DataFrame({
            'high': [105, 110, 108],
            'low': [95, 100, 102],
            'close': [100, 105, 107]
        })

        atr = calculate_atr(bars, period=2)

        # First value should be valid (high - low for first bar)
        # For first bar: True Range = 105 - 95 = 10
        assert atr.iloc[0] == 10.0

        # All ATR values should be positive
        assert all(atr > 0)


class TestValidatePriceData:
    """Test cases for price data validation utility."""

    def test_validate_good_data(self):
        """Test validation passes for good data."""
        prices = pd.Series([100.0, 101.5, 102.0, 103.5])
        assert validate_price_data(prices) is True

    def test_validate_empty_data(self):
        """Test validation fails for empty data."""
        prices = pd.Series(dtype=float)
        assert validate_price_data(prices) is False

    def test_validate_negative_prices(self):
        """Test validation fails for negative prices."""
        prices = pd.Series([100, 101, -50, 103])
        assert validate_price_data(prices) is False

    def test_validate_infinite_values(self):
        """Test validation fails for infinite values."""
        prices = pd.Series([100, 101, np.inf, 103])
        assert validate_price_data(prices) is False

    def test_validate_dataframe(self):
        """Test validation works with DataFrame."""
        bars = pd.DataFrame({
            'high': [100, 101, 102],
            'low': [98, 99, 100],
            'close': [99, 100, 101]
        })
        assert validate_price_data(bars) is True


class TestIntegrationScenarios:
    """Integration tests combining multiple indicators."""

    def test_indicators_on_real_scenario(self):
        """Test all indicators on realistic price data."""
        # Arrange: Simulate 30 days of QQQ prices
        np.random.seed(42)  # Reproducible random data
        base_price = 450.0
        prices = base_price + np.cumsum(np.random.randn(30) * 2)  # Random walk
        prices = pd.Series(prices)

        # Create OHLC from prices (simulate intraday)
        bars = pd.DataFrame({
            'high': prices + np.random.rand(30) * 2,
            'low': prices - np.random.rand(30) * 2,
            'close': prices
        })

        # Act: Calculate all indicators
        ema20 = calculate_ema(bars['close'], period=20)
        sma20 = calculate_sma(bars['close'], period=20)
        atr14 = calculate_atr(bars, period=14)

        # Assert: All indicators should be calculated
        assert len(ema20) == len(prices)
        assert len(sma20) == len(prices)
        assert len(atr14) == len(prices)

        # EMA and SMA should be similar (both 20-period averages)
        # Check the last value (after warmup)
        assert abs(ema20.iloc[-1] - sma20.iloc[-1]) < 10.0  # Within $10

        # ATR should be positive
        assert atr14.dropna().min() > 0


# Run tests with: poetry run pytest tests/core/test_indicators.py -v
