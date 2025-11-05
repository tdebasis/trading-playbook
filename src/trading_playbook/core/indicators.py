"""
Technical indicators for trading strategies.

This module provides pure functions for calculating common technical indicators.
All functions are stateless and testable - like static utility methods in Java.

Author: Tanam Bam Sinha
"""

import pandas as pd
import numpy as np
from typing import Union


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA).

    EMA gives more weight to recent prices compared to older prices.
    Formula: EMA(today) = (Price(today) × K) + (EMA(yesterday) × (1 − K))
    where K = 2 / (period + 1)

    Args:
        prices: Series of prices (typically closing prices)
        period: Number of periods for EMA calculation (e.g., 20 for EMA20)

    Returns:
        Series of EMA values, same length as input prices

    Example:
        >>> prices = pd.Series([10, 11, 12, 13, 14])
        >>> ema = calculate_ema(prices, period=3)
        >>> # First value will be NaN until enough data, then EMA kicks in

    Note:
        - First (period-1) values will be NaN
        - Pandas ewm() handles the exponential weighting
        - adjust=False gives standard EMA formula
    """
    if prices.empty:
        return pd.Series(dtype=float)

    if period <= 0:
        raise ValueError(f"Period must be positive, got {period}")

    # Pandas exponential weighted mean (ewm)
    # span=period gives us standard EMA formula
    # adjust=False uses recursive formula (standard EMA)
    ema = prices.ewm(span=period, adjust=False).mean()

    return ema


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate Simple Moving Average (SMA).

    SMA is the arithmetic mean of prices over the specified period.
    Each price has equal weight (unlike EMA which weights recent prices more).

    Formula: SMA = (Price1 + Price2 + ... + PriceN) / N

    Args:
        prices: Series of prices (typically closing prices)
        period: Number of periods to average (e.g., 200 for 200-day SMA)

    Returns:
        Series of SMA values, same length as input prices

    Example:
        >>> prices = pd.Series([10, 20, 30, 40, 50])
        >>> sma = calculate_sma(prices, period=3)
        >>> # sma[2] = (10+20+30)/3 = 20
        >>> # sma[3] = (20+30+40)/3 = 30

    Note:
        - First (period-1) values will be NaN
        - This is a simple rolling mean
    """
    if prices.empty:
        return pd.Series(dtype=float)

    if period <= 0:
        raise ValueError(f"Period must be positive, got {period}")

    # Pandas rolling window mean
    # min_periods=period ensures we don't calculate SMA until we have enough data
    sma = prices.rolling(window=period, min_periods=period).mean()

    return sma


def calculate_atr(bars: pd.DataFrame, period: int) -> pd.Series:
    """
    Calculate Average True Range (ATR) - a volatility indicator.

    ATR measures market volatility by calculating the average of true ranges
    over a specified period.

    True Range is the greatest of:
    1. Current High - Current Low
    2. Absolute value of (Current High - Previous Close)
    3. Absolute value of (Current Low - Previous Close)

    Then ATR is the EMA of True Range over the period.

    Args:
        bars: DataFrame with columns 'high', 'low', 'close' (OHLC data)
        period: Number of periods for ATR calculation (typically 14)

    Returns:
        Series of ATR values, same length as input bars

    Example:
        >>> bars = pd.DataFrame({
        ...     'high': [100, 102, 104],
        ...     'low': [98, 100, 102],
        ...     'close': [99, 101, 103]
        ... })
        >>> atr = calculate_atr(bars, period=2)

    Raises:
        ValueError: If required columns are missing or period is invalid

    Note:
        - First value will be NaN (no previous close)
        - ATR is always positive
        - Higher ATR = higher volatility
    """
    # Validate input
    required_columns = ['high', 'low', 'close']
    missing_columns = [col for col in required_columns if col not in bars.columns]

    if missing_columns:
        raise ValueError(f"DataFrame missing required columns: {missing_columns}")

    if bars.empty:
        return pd.Series(dtype=float)

    if period <= 0:
        raise ValueError(f"Period must be positive, got {period}")

    # Get the columns we need
    high = bars['high']
    low = bars['low']
    close = bars['close']

    # Calculate True Range components
    # Component 1: Current high - current low
    range_hl = high - low

    # Component 2: Absolute value of (current high - previous close)
    # shift(1) gets previous row's value
    prev_close = close.shift(1)
    range_hc = (high - prev_close).abs()

    # Component 3: Absolute value of (current low - previous close)
    range_lc = (low - prev_close).abs()

    # True Range is the maximum of these three components
    # pd.concat creates DataFrame with all three components as columns
    # max(axis=1) gets row-wise maximum
    true_range = pd.concat([range_hl, range_hc, range_lc], axis=1).max(axis=1)

    # ATR is the Exponential Moving Average of True Range
    # Using EMA instead of SMA is standard for ATR
    atr = true_range.ewm(span=period, adjust=False).mean()

    return atr


# Utility function for debugging/validation
def validate_price_data(prices: Union[pd.Series, pd.DataFrame]) -> bool:
    """
    Validate that price data is suitable for indicator calculations.

    Checks for common data quality issues:
    - Empty data
    - NaN values (except at the start/end which is OK)
    - Negative prices
    - Infinite values

    Args:
        prices: Price data (Series or DataFrame)

    Returns:
        True if data is valid, False otherwise

    Example:
        >>> prices = pd.Series([100, 101, 102])
        >>> validate_price_data(prices)
        True
        >>> bad_prices = pd.Series([100, -1, 102])  # Negative price
        >>> validate_price_data(bad_prices)
        False
    """
    if prices.empty:
        return False

    # Check for infinite values
    if isinstance(prices, pd.Series):
        if np.isinf(prices).any():
            return False
        # Check for negative values (prices should be positive)
        if (prices < 0).any():
            return False
    elif isinstance(prices, pd.DataFrame):
        if np.isinf(prices).any().any():
            return False
        if (prices < 0).any().any():
            return False

    return True
