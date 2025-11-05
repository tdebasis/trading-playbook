"""
Backtest engine for DP20 strategy.

This runs the strategy across historical data and tracks all trades.
Uses vectorized processing where possible for speed.

Author: Tanam Bam Sinha
"""

from datetime import date, datetime, time, timedelta
from typing import List, Optional
import pandas as pd

from trading_playbook.core.data_fetcher import DataFetcher
from trading_playbook.core.indicators import calculate_ema, calculate_sma, calculate_atr
from trading_playbook.core.dp20_detector import detect_dp20_signal
from trading_playbook.models.market_data import TimeFrame
from trading_playbook.models.signal import DP20Signal
from trading_playbook.models.trade import Trade, BacktestResults, ExitReason


class DP20Backtest:
    """
    Backtest engine for the DP20 strategy.

    This orchestrates the entire backtesting process:
    1. Fetch historical data day-by-day
    2. Calculate indicators
    3. Detect signals
    4. Simulate trades with stop loss tracking
    5. Calculate performance metrics

    Args:
        data_fetcher: DataFetcher implementation (e.g., CachedDataFetcher)
        symbol: Symbol to backtest (e.g., "QQQ")
        shares_per_trade: Number of shares to trade (default: 100)

    Example:
        >>> backtest = DP20Backtest(cached_fetcher, "QQQ", shares_per_trade=100)
        >>> results = backtest.run(start_date=date(2024, 1, 1), end_date=date(2024, 3, 31))
        >>> print(results.summary())
    """

    def __init__(self, data_fetcher: DataFetcher, symbol: str, shares_per_trade: int = 100):
        self.data_fetcher = data_fetcher
        self.symbol = symbol
        self.shares_per_trade = shares_per_trade

    def run(
        self,
        start_date: date,
        end_date: date,
        strategy_params: Optional[dict] = None
    ) -> BacktestResults:
        """
        Run backtest across date range.

        Args:
            start_date: First date to test
            end_date: Last date to test
            strategy_params: Optional DP20 strategy parameter overrides

        Returns:
            BacktestResults with all trades and statistics
        """
        print(f"\n{'='*80}")
        print(f"RUNNING BACKTEST: {self.symbol}")
        print(f"Period: {start_date} to {end_date}")
        print(f"Shares per trade: {self.shares_per_trade}")
        print(f"{'='*80}\n")

        trades = []

        # Get list of trading days
        trading_days = self._get_trading_days(start_date, end_date)
        print(f"Scanning {len(trading_days)} trading days for signals...\n")

        # Calculate SMA200 for the period
        # Fetch enough daily data to calculate SMA200
        sma200_start = start_date - timedelta(days=300)
        daily_df = self.data_fetcher.fetch_daily_bars(self.symbol, sma200_start, end_date)
        sma200_series = calculate_sma(daily_df['close'], period=200)

        # Process each trading day
        for i, trade_date in enumerate(trading_days, 1):
            print(f"[{i}/{len(trading_days)}] {trade_date}...", end=" ")

            # Get SMA200 value for this date
            sma200 = self._get_sma200_for_date(sma200_series, trade_date)
            if sma200 is None:
                print("Skip (no SMA200)")
                continue

            # Fetch and prepare day data
            day_data = self._prepare_day_data(trade_date)
            if day_data is None or day_data.empty:
                print("Skip (no data)")
                continue

            # Detect signal
            signal = detect_dp20_signal(day_data, sma200, strategy_params)

            if signal.signal_detected:
                print(f"SIGNAL @ {signal.entry_time.time()}")

                # Simulate trade
                trade = self._simulate_trade(day_data, signal)
                trades.append(trade)

                # Show trade result
                win_loss = "WIN" if trade.is_winner() else "LOSS"
                print(f"  -> {win_loss}: ${trade.pnl:+.2f} ({trade.exit_reason.value})")
            else:
                print("No signal")

        # Create results
        results = BacktestResults(
            trades=trades,
            start_date=datetime.combine(start_date, time(0, 0)),
            end_date=datetime.combine(end_date, time(0, 0)),
            symbol=self.symbol
        )

        return results

    def _get_trading_days(self, start_date: date, end_date: date) -> List[date]:
        """
        Get list of trading days in range.

        We fetch daily data and extract the dates.
        This automatically excludes weekends/holidays.
        """
        daily_df = self.data_fetcher.fetch_daily_bars(self.symbol, start_date, end_date)
        trading_days = [d.date() for d in daily_df.index]
        return trading_days

    def _get_sma200_for_date(self, sma200_series: pd.Series, trade_date: date) -> Optional[float]:
        """Get SMA200 value for a specific date."""
        # Find the SMA200 value on or before this date
        trade_datetime = datetime.combine(trade_date, time(0, 0))

        # Filter to dates on or before trade_date
        available_sma = sma200_series[sma200_series.index <= trade_datetime]

        if available_sma.empty:
            return None

        # Get most recent SMA200
        sma200 = available_sma.iloc[-1]

        # Check if it's valid (not NaN)
        if pd.isna(sma200):
            return None

        return float(sma200)

    def _prepare_day_data(self, trade_date: date) -> Optional[pd.DataFrame]:
        """
        Fetch and prepare data for one trading day.

        Fetches 2-min bars and calculates all required indicators.
        """
        # Fetch intraday bars
        bars = self.data_fetcher.fetch_intraday_bars(
            self.symbol,
            trade_date,
            TimeFrame.MINUTE_2
        )

        if not bars:
            return None

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'timestamp': bar.timestamp,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume
            }
            for bar in bars
        ])

        # Calculate indicators
        df['ema20'] = calculate_ema(df['close'], period=20)
        df['atr14'] = calculate_atr(df, period=14)

        return df

    def _simulate_trade(self, day_data: pd.DataFrame, signal: DP20Signal) -> Trade:
        """
        Simulate a trade from entry to exit.

        This is where we track:
        1. Entry at signal.entry_price
        2. Stop loss tracking bar-by-bar
        3. End-of-day exit if not stopped out

        Returns completed Trade object.
        """
        entry_time = signal.entry_time
        entry_price = signal.entry_price
        stop_price = signal.stop_price

        # Get all bars after entry
        after_entry = day_data[day_data['timestamp'] >= entry_time].copy()

        # Track MAE (Maximum Adverse Excursion) and MFE (Maximum Favorable Excursion)
        mae = 0.0  # Worst drawdown
        mfe = 0.0  # Best profit

        # Check each bar for stop hit
        for idx, bar in after_entry.iterrows():
            # Calculate unrealized P&L at this bar's low (worst case)
            unrealized_pnl_low = bar['low'] - entry_price

            # Calculate unrealized P&L at this bar's high (best case)
            unrealized_pnl_high = bar['high'] - entry_price

            # Update MAE/MFE
            mae = min(mae, unrealized_pnl_low)
            mfe = max(mfe, unrealized_pnl_high)

            # Check if stop was hit
            # Stop is hit if the bar's low touches or goes below stop price
            if bar['low'] <= stop_price:
                # Stopped out
                return Trade(
                    symbol=self.symbol,
                    entry_time=entry_time,
                    entry_price=entry_price,
                    exit_time=bar['timestamp'],
                    exit_price=stop_price,  # Assume we exit at stop price
                    exit_reason=ExitReason.STOP_LOSS,
                    shares=self.shares_per_trade,
                    stop_price=stop_price,
                    signal_date=signal.date,
                    pullback_time=signal.pullback_time,
                    reversal_time=signal.reversal_time,
                    reversal_strength=signal.reversal_strength,
                    mae=mae * self.shares_per_trade,
                    mfe=mfe * self.shares_per_trade
                )

        # Not stopped out, exit at end of day (3:55 PM)
        # Find the bar closest to 3:55 PM
        exit_time_target = time(15, 55)
        eod_bars = after_entry[after_entry['timestamp'].dt.time >= exit_time_target]

        if eod_bars.empty:
            # Use last bar of the day
            exit_bar = after_entry.iloc[-1]
        else:
            # Use first bar at or after 3:55 PM
            exit_bar = eod_bars.iloc[0]

        exit_price = exit_bar['close']

        return Trade(
            symbol=self.symbol,
            entry_time=entry_time,
            entry_price=entry_price,
            exit_time=exit_bar['timestamp'],
            exit_price=exit_price,
            exit_reason=ExitReason.END_OF_DAY,
            shares=self.shares_per_trade,
            stop_price=stop_price,
            signal_date=signal.date,
            pullback_time=signal.pullback_time,
            reversal_time=signal.reversal_time,
            reversal_strength=signal.reversal_strength,
            mae=mae * self.shares_per_trade,
            mfe=mfe * self.shares_per_trade
        )
