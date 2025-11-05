"""
Unit tests for DP20 signal detection.

These tests verify each step of the 6-step signal detection process.
We create synthetic data to test specific scenarios.
"""

from datetime import datetime, time
import pandas as pd
import pytest

from trading_playbook.core.dp20_detector import (
    detect_dp20_signal,
    _check_trend_filter,
    _filter_signal_window,
    _detect_pullback,
    _detect_reversal,
    _check_confirmation,
    _setup_entry
)


def create_test_bars(timestamps, opens, highs, lows, closes, ema20s, atr14s):
    """
    Helper to create test DataFrame with required columns.

    This makes it easy to create synthetic data for testing.
    """
    return pd.DataFrame({
        'timestamp': timestamps,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'ema20': ema20s,
        'atr14': atr14s
    })


class TestTrendFilter:
    """Test Step 1: Trend filter logic."""

    def test_trend_filter_passes_when_open_above_sma200(self):
        """Test that trend filter passes when open > SMA200."""
        # Arrange
        bars = create_test_bars(
            timestamps=[datetime(2024, 11, 1, 9, 30)],
            opens=[450.0],  # Above SMA200
            highs=[451.0],
            lows=[449.0],
            closes=[450.5],
            ema20s=[448.0],
            atr14s=[3.0]
        )

        # Act
        passed, msg = _check_trend_filter(bars, sma200=445.0)

        # Assert
        assert passed is True
        assert "passed" in msg.lower()

    def test_trend_filter_fails_when_open_below_sma200(self):
        """Test that trend filter fails when open <= SMA200."""
        # Arrange
        bars = create_test_bars(
            timestamps=[datetime(2024, 11, 1, 9, 30)],
            opens=[440.0],  # Below SMA200
            highs=[441.0],
            lows=[439.0],
            closes=[440.5],
            ema20s=[442.0],
            atr14s=[3.0]
        )

        # Act
        passed, msg = _check_trend_filter(bars, sma200=445.0)

        # Assert
        assert passed is False
        assert "failed" in msg.lower()


class TestTimeWindowFilter:
    """Test Step 2: Time window filtering."""

    def test_signal_window_extracts_correct_bars(self):
        """Test that signal window correctly filters by time."""
        # Arrange: Bars from 9:30 to 11:00
        bars = create_test_bars(
            timestamps=[
                datetime(2024, 11, 1, 9, 30),
                datetime(2024, 11, 1, 10, 0),  # In window
                datetime(2024, 11, 1, 10, 15),  # In window
                datetime(2024, 11, 1, 10, 30),  # In window
                datetime(2024, 11, 1, 11, 0),   # After window
            ],
            opens=[450.0] * 5,
            highs=[451.0] * 5,
            lows=[449.0] * 5,
            closes=[450.5] * 5,
            ema20s=[448.0] * 5,
            atr14s=[3.0] * 5
        )

        # Act
        signal_bars, msg = _filter_signal_window(
            bars,
            start_time=time(10, 0),
            end_time=time(10, 30)
        )

        # Assert
        assert signal_bars is not None
        assert len(signal_bars) == 3  # 10:00, 10:15, 10:30
        assert "3 bars" in msg

    def test_signal_window_returns_none_if_no_bars_in_window(self):
        """Test that empty result when no bars in window."""
        # Arrange: All bars before window
        bars = create_test_bars(
            timestamps=[
                datetime(2024, 11, 1, 9, 30),
                datetime(2024, 11, 1, 9, 45),
            ],
            opens=[450.0] * 2,
            highs=[451.0] * 2,
            lows=[449.0] * 2,
            closes=[450.5] * 2,
            ema20s=[448.0] * 2,
            atr14s=[3.0] * 2
        )

        # Act
        signal_bars, msg = _filter_signal_window(
            bars,
            start_time=time(10, 0),
            end_time=time(10, 30)
        )

        # Assert
        assert signal_bars is None
        assert "No bars" in msg


class TestPullbackDetection:
    """Test Step 3: Pullback detection."""

    def test_pullback_detected_when_close_below_ema20(self):
        """Test that pullback is detected when candle closes below EMA20."""
        # Arrange
        bars = create_test_bars(
            timestamps=[
                datetime(2024, 11, 1, 10, 0),
                datetime(2024, 11, 1, 10, 2),  # Pullback here
                datetime(2024, 11, 1, 10, 4),
            ],
            opens=[450.0, 450.0, 448.0],
            highs=[451.0, 450.5, 449.0],
            lows=[449.0, 447.0, 447.5],
            closes=[450.5, 447.5, 448.5],  # Second close below EMA20
            ema20s=[448.0, 448.0, 448.0],
            atr14s=[3.0, 3.0, 3.0]
        )

        # Act
        pullback_bar, pullback_idx = _detect_pullback(bars)

        # Assert
        assert pullback_bar is not None
        assert pullback_idx == 1  # Second bar
        assert pullback_bar['close'] == 447.5

    def test_no_pullback_when_all_closes_above_ema20(self):
        """Test that no pullback when all bars close above EMA20."""
        # Arrange
        bars = create_test_bars(
            timestamps=[
                datetime(2024, 11, 1, 10, 0),
                datetime(2024, 11, 1, 10, 2),
                datetime(2024, 11, 1, 10, 4),
            ],
            opens=[450.0, 450.0, 451.0],
            highs=[451.0, 451.5, 452.0],
            lows=[449.0, 449.5, 450.0],
            closes=[450.5, 451.0, 451.5],  # All above EMA20
            ema20s=[448.0, 448.0, 448.0],
            atr14s=[3.0, 3.0, 3.0]
        )

        # Act
        pullback_bar, pullback_idx = _detect_pullback(bars)

        # Assert
        assert pullback_bar is None
        assert pullback_idx is None


class TestReversalDetection:
    """Test Step 4: Reversal detection with strength filter."""

    def test_strong_reversal_detected(self):
        """Test that strong reversal (body > 60%) is detected."""
        # Arrange
        bars = create_test_bars(
            timestamps=[
                datetime(2024, 11, 1, 10, 0),
                datetime(2024, 11, 1, 10, 2),  # Pullback
                datetime(2024, 11, 1, 10, 4),  # Strong reversal
            ],
            opens=[450.0, 450.0, 448.0],
            highs=[451.0, 450.5, 451.0],
            lows=[449.0, 447.0, 447.5],
            closes=[450.0, 447.5, 450.75],  # Third bar: strong bullish
            ema20s=[448.0, 448.0, 448.0],
            atr14s=[3.0, 3.0, 3.0]
        )

        # Calculate expected body %: (450.75 - 447.5) / (451.0 - 447.5) = 92.8%

        # Act
        reversal_bar, reversal_idx = _detect_reversal(
            bars,
            pullback_idx=1,  # Pullback at index 1
            strength_threshold=0.60
        )

        # Assert
        assert reversal_bar is not None
        assert reversal_idx == 2
        assert reversal_bar['close'] == 450.75

    def test_weak_reversal_not_detected(self):
        """Test that weak reversal (body < 60%) is rejected."""
        # Arrange
        bars = create_test_bars(
            timestamps=[
                datetime(2024, 11, 1, 10, 0),
                datetime(2024, 11, 1, 10, 2),  # Pullback
                datetime(2024, 11, 1, 10, 4),  # Weak reversal
            ],
            opens=[450.0, 450.0, 448.0],
            highs=[451.0, 450.5, 451.0],
            lows=[449.0, 447.0, 447.5],
            closes=[450.0, 447.5, 449.0],  # Third bar: closes above EMA but weak body
            ema20s=[448.0, 448.0, 448.0],
            atr14s=[3.0, 3.0, 3.0]
        )

        # Calculate body %: (449.0 - 447.5) / (451.0 - 447.5) = 42.8% (< 60%)

        # Act
        reversal_bar, reversal_idx = _detect_reversal(
            bars,
            pullback_idx=1,
            strength_threshold=0.60
        )

        # Assert
        assert reversal_bar is None  # Weak reversal rejected


class TestConfirmation:
    """Test Step 5: Confirmation logic."""

    def test_confirmation_passes_when_next_candle_closes_above_ema20(self):
        """Test that confirmation passes when next candle closes above EMA20."""
        # Arrange
        bars = create_test_bars(
            timestamps=[
                datetime(2024, 11, 1, 10, 0),
                datetime(2024, 11, 1, 10, 2),  # Reversal
                datetime(2024, 11, 1, 10, 4),  # Confirmation
            ],
            opens=[450.0, 449.0, 450.0],
            highs=[451.0, 451.0, 451.5],
            lows=[449.0, 448.0, 449.5],
            closes=[450.0, 450.5, 451.0],  # Confirmation closes above EMA20
            ema20s=[448.0, 448.0, 448.0],
            atr14s=[3.0, 3.0, 3.0]
        )

        # Act
        confirmation_bar, confirmation_idx = _check_confirmation(
            bars,
            reversal_idx=1
        )

        # Assert
        assert confirmation_bar is not None
        assert confirmation_idx == 2
        assert confirmation_bar['close'] == 451.0

    def test_confirmation_fails_when_next_candle_closes_below_ema20(self):
        """Test that confirmation fails (invalidates signal) if closes below EMA20."""
        # Arrange
        bars = create_test_bars(
            timestamps=[
                datetime(2024, 11, 1, 10, 0),
                datetime(2024, 11, 1, 10, 2),  # Reversal
                datetime(2024, 11, 1, 10, 4),  # Confirmation fails
            ],
            opens=[450.0, 449.0, 448.0],
            highs=[451.0, 451.0, 449.0],
            lows=[449.0, 448.0, 446.0],
            closes=[450.0, 450.5, 447.0],  # Confirmation closes below EMA20
            ema20s=[448.0, 448.0, 448.0],
            atr14s=[3.0, 3.0, 3.0]
        )

        # Act
        confirmation_bar, confirmation_idx = _check_confirmation(
            bars,
            reversal_idx=1
        )

        # Assert
        assert confirmation_bar is None  # Signal invalidated


class TestEntrySetup:
    """Test Step 6: Entry setup."""

    def test_entry_setup_calculates_correctly(self):
        """Test that entry price and stop are calculated correctly."""
        # Arrange
        confirmation_bar = pd.Series({
            'timestamp': datetime(2024, 11, 1, 10, 10),
            'close': 450.0,
            'ema20': 448.0
        })

        full_day_bars = create_test_bars(
            timestamps=[
                datetime(2024, 11, 1, 10, 8),
                datetime(2024, 11, 1, 10, 10),  # Confirmation
                datetime(2024, 11, 1, 10, 12),  # Entry bar
            ],
            opens=[449.0, 450.0, 450.5],  # Entry at 450.5
            highs=[450.0, 451.0, 451.5],
            lows=[448.0, 449.0, 450.0],
            closes=[449.5, 450.0, 451.0],
            ema20s=[448.0, 448.0, 448.0],
            atr14s=[3.0, 3.0, 3.0]  # ATR = 3.0
        )

        params = {'stop_atr_multiplier': 1.2}

        # Act
        entry_details = _setup_entry(full_day_bars, confirmation_bar, params)

        # Assert
        assert entry_details is not None
        assert entry_details['entry_price'] == 450.5
        assert entry_details['atr14_at_entry'] == 3.0
        assert abs(entry_details['stop_distance'] - 3.6) < 0.01  # 1.2 * 3.0
        assert abs(entry_details['stop_price'] - 446.9) < 0.01  # 450.5 - 3.6


class TestFullSignalDetection:
    """Integration tests for complete signal detection."""

    def test_complete_valid_signal(self):
        """Test that a complete valid DP20 signal is detected."""
        # Arrange: Create a full day with valid setup
        bars = create_test_bars(
            timestamps=[
                datetime(2024, 11, 1, 9, 30),   # Day open (above SMA200)
                datetime(2024, 11, 1, 10, 0),   # Signal window starts
                datetime(2024, 11, 1, 10, 2),   # Pullback
                datetime(2024, 11, 1, 10, 4),   # Reversal (strong)
                datetime(2024, 11, 1, 10, 6),   # Confirmation
                datetime(2024, 11, 1, 10, 8),   # Entry bar
            ],
            opens=[450.0, 450.5, 450.0, 448.0, 450.0, 450.5],
            highs=[451.0, 451.0, 450.5, 451.0, 451.5, 452.0],
            lows=[449.0, 449.5, 447.0, 447.5, 449.5, 450.0],
            closes=[450.5, 450.0, 447.5, 450.75, 451.0, 451.5],
            ema20s=[448.0] * 6,
            atr14s=[3.0] * 6
        )

        # Act
        signal = detect_dp20_signal(bars, sma200=445.0)

        # Assert
        assert signal.signal_detected is True
        assert signal.entry_price == 450.5
        assert signal.stop_price < signal.entry_price
        assert "Valid" in signal.notes

    def test_no_signal_when_trend_filter_fails(self):
        """Test that no signal when open below SMA200."""
        # Arrange
        bars = create_test_bars(
            timestamps=[datetime(2024, 11, 1, 9, 30)],
            opens=[440.0],  # Below SMA200
            highs=[441.0],
            lows=[439.0],
            closes=[440.5],
            ema20s=[442.0],
            atr14s=[3.0]
        )

        # Act
        signal = detect_dp20_signal(bars, sma200=445.0)

        # Assert
        assert signal.signal_detected is False
        assert "Trend filter failed" in signal.notes

    def test_no_signal_when_no_pullback(self):
        """Test that no signal when no pullback occurs."""
        # Arrange: All bars close above EMA20
        bars = create_test_bars(
            timestamps=[
                datetime(2024, 11, 1, 9, 30),
                datetime(2024, 11, 1, 10, 0),
                datetime(2024, 11, 1, 10, 2),
            ],
            opens=[450.0, 450.5, 451.0],
            highs=[451.0, 451.5, 452.0],
            lows=[449.0, 450.0, 450.5],
            closes=[450.5, 451.0, 451.5],  # All above EMA20
            ema20s=[448.0, 448.0, 448.0],
            atr14s=[3.0, 3.0, 3.0]
        )

        # Act
        signal = detect_dp20_signal(bars, sma200=445.0)

        # Assert
        assert signal.signal_detected is False
        assert "No pullback" in signal.notes


# Run tests with: poetry run pytest tests/core/test_dp20_detector.py -v
