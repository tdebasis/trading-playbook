"""
Alpaca API adapter for fetching market data.

This is the concrete implementation of DataFetcher interface using Alpaca API.
It's a peripheral adapter - can be swapped out for a different data source
without changing the core business logic.
"""

from datetime import date, datetime, time, timedelta
from typing import List, Optional
import pandas as pd
import pytz
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame as AlpacaTimeFrame, TimeFrameUnit

from trading_playbook.core.data_fetcher import DataFetcher, DataFetchError
from trading_playbook.models.market_data import Bar, TimeFrame


class AlpacaDataFetcher(DataFetcher):
    """
    Alpaca API implementation of DataFetcher.

    This adapter translates our domain models to/from Alpaca's API.
    All Alpaca-specific code lives here - the core doesn't know about Alpaca.

    Args:
        api_key: Alpaca API key
        secret_key: Alpaca secret key
        paper: If True, use paper trading endpoint (default: True)

    Example:
        >>> fetcher = AlpacaDataFetcher(
        ...     api_key="PK...",
        ...     secret_key="...",
        ...     paper=True
        ... )
        >>> bars = fetcher.fetch_intraday_bars("QQQ", date(2024, 11, 1), TimeFrame.MINUTE_2)
    """

    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        """Initialize Alpaca client."""
        self.client = StockHistoricalDataClient(
            api_key=api_key,
            secret_key=secret_key
        )
        self.paper = paper
        self.et_tz = pytz.timezone('America/New_York')
        self.utc_tz = pytz.UTC

    def fetch_intraday_bars(
        self,
        symbol: str,
        date: date,
        timeframe: TimeFrame
    ) -> List[Bar]:
        """
        Fetch intraday bars from Alpaca for a specific trading day.

        Alpaca returns data in UTC, we convert to ET for consistency.
        """
        try:
            # Convert our TimeFrame enum to Alpaca TimeFrame
            alpaca_timeframe = self._convert_timeframe(timeframe)

            # Build time range for the trading day
            # Market hours: 9:30 AM - 4:00 PM ET
            start_time = datetime.combine(date, time(9, 30))  # 9:30 AM
            end_time = datetime.combine(date, time(16, 0))    # 4:00 PM

            # Localize to ET timezone
            start_time = self.et_tz.localize(start_time)
            end_time = self.et_tz.localize(end_time)

            # Convert to UTC for Alpaca API
            start_utc = start_time.astimezone(self.utc_tz)
            end_utc = end_time.astimezone(self.utc_tz)

            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=alpaca_timeframe,
                start=start_utc,
                end=end_utc
            )

            # Fetch data
            response = self.client.get_stock_bars(request)

            # Convert to our Bar model
            bars = []
            if symbol in response.data:
                for alpaca_bar in response.data[symbol]:
                    # Convert UTC timestamp to ET
                    timestamp_et = alpaca_bar.timestamp.astimezone(self.et_tz)

                    bar = Bar(
                        timestamp=timestamp_et.replace(tzinfo=None),  # Remove tz info for simplicity
                        open=float(alpaca_bar.open),
                        high=float(alpaca_bar.high),
                        low=float(alpaca_bar.low),
                        close=float(alpaca_bar.close),
                        volume=int(alpaca_bar.volume),
                        vwap=float(alpaca_bar.vwap) if alpaca_bar.vwap else None,
                        trade_count=int(alpaca_bar.trade_count) if alpaca_bar.trade_count else None
                    )
                    bars.append(bar)

            return bars

        except Exception as e:
            raise DataFetchError(
                f"Failed to fetch intraday bars for {symbol} on {date}: {str(e)}"
            ) from e

    def fetch_daily_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Fetch daily bars from Alpaca for a date range.

        Returns a DataFrame indexed by timestamp.
        """
        try:
            # Build time range
            start_time = datetime.combine(start_date, time(0, 0))
            end_time = datetime.combine(end_date, time(23, 59))

            # Localize to ET and convert to UTC
            start_time = self.et_tz.localize(start_time).astimezone(self.utc_tz)
            end_time = self.et_tz.localize(end_time).astimezone(self.utc_tz)

            # Create request for daily bars
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=AlpacaTimeFrame(1, TimeFrameUnit.Day),
                start=start_time,
                end=end_time
            )

            # Fetch data
            response = self.client.get_stock_bars(request)

            # Convert to DataFrame
            if symbol not in response.data or len(response.data[symbol]) == 0:
                # Return empty DataFrame with correct columns
                return pd.DataFrame(
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                ).set_index('timestamp')

            bars_data = []
            for alpaca_bar in response.data[symbol]:
                # Convert to ET timezone
                timestamp_et = alpaca_bar.timestamp.astimezone(self.et_tz)

                bars_data.append({
                    'timestamp': timestamp_et.replace(tzinfo=None),
                    'open': float(alpaca_bar.open),
                    'high': float(alpaca_bar.high),
                    'low': float(alpaca_bar.low),
                    'close': float(alpaca_bar.close),
                    'volume': int(alpaca_bar.volume)
                })

            df = pd.DataFrame(bars_data)
            df.set_index('timestamp', inplace=True)
            return df

        except Exception as e:
            raise DataFetchError(
                f"Failed to fetch daily bars for {symbol} "
                f"from {start_date} to {end_date}: {str(e)}"
            ) from e

    def _convert_timeframe(self, timeframe: TimeFrame) -> AlpacaTimeFrame:
        """
        Convert our TimeFrame enum to Alpaca's TimeFrame.

        This is an internal translation layer between our domain model
        and Alpaca's API.
        """
        mapping = {
            TimeFrame.MINUTE_1: AlpacaTimeFrame(1, TimeFrameUnit.Minute),
            TimeFrame.MINUTE_2: AlpacaTimeFrame(2, TimeFrameUnit.Minute),
            TimeFrame.MINUTE_5: AlpacaTimeFrame(5, TimeFrameUnit.Minute),
            TimeFrame.MINUTE_15: AlpacaTimeFrame(15, TimeFrameUnit.Minute),
            TimeFrame.HOUR_1: AlpacaTimeFrame(1, TimeFrameUnit.Hour),
            TimeFrame.DAY_1: AlpacaTimeFrame(1, TimeFrameUnit.Day),
        }

        if timeframe not in mapping:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        return mapping[timeframe]
