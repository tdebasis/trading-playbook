"""
Data caching layer for Alpaca market data.

Caches downloaded data to local parquet files for fast iteration.
Cache key: {symbol}_{start_date}_{end_date}.parquet

Usage:
    from data.cache import CachedDataClient

    client = CachedDataClient(api_key, secret_key, cache_dir='./cache')
    bars = client.get_stock_bars(request)  # Auto-caches
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.models import BarSet, Bar

logger = logging.getLogger(__name__)


class CachedDataClient:
    """Wrapper around Alpaca client that caches data to disk."""

    def __init__(self, api_key: str, secret_key: str, cache_dir: str = './cache'):
        self.client = StockHistoricalDataClient(api_key, secret_key)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Stats
        self.cache_hits = 0
        self.cache_misses = 0

    def get_stock_bars(self, request: StockBarsRequest) -> BarSet:
        """
        Get stock bars, using cache if available.

        Returns BarSet just like the real Alpaca client.
        """
        symbols = request.symbol_or_symbols
        if isinstance(symbols, str):
            symbols = [symbols]

        # Build cache key
        start_str = request.start.strftime('%Y%m%d')
        end_str = request.end.strftime('%Y%m%d')
        timeframe = str(request.timeframe)

        result_data = {}

        for symbol in symbols:
            cache_file = self.cache_dir / f"{symbol}_{start_str}_{end_str}_{timeframe}.parquet"

            if cache_file.exists():
                # Load from cache
                self.cache_hits += 1
                logger.debug(f"Cache HIT: {symbol} {start_str}-{end_str}")

                df = pd.read_parquet(cache_file)

                # Convert DataFrame back to list of Bar objects
                # Create simple Bar-like objects with attributes
                bars = []
                for _, row in df.iterrows():
                    class SimpleBar:
                        pass
                    bar = SimpleBar()
                    bar.symbol = symbol
                    bar.timestamp = row['timestamp']
                    bar.open = row['open']
                    bar.high = row['high']
                    bar.low = row['low']
                    bar.close = row['close']
                    bar.volume = row['volume']
                    bar.trade_count = row.get('trade_count', 0)
                    bar.vwap = row.get('vwap', row['close'])
                    bars.append(bar)

                result_data[symbol] = bars

            else:
                # Fetch from API
                self.cache_misses += 1
                logger.debug(f"Cache MISS: {symbol} {start_str}-{end_str} - Downloading...")

                # Fetch just this symbol
                single_request = StockBarsRequest(
                    symbol_or_symbols=[symbol],
                    timeframe=request.timeframe,
                    start=request.start,
                    end=request.end
                )

                response = self.client.get_stock_bars(single_request)

                if symbol in response:
                    bars = list(response[symbol])
                    result_data[symbol] = bars

                    # Save to cache
                    df = pd.DataFrame([{
                        'timestamp': bar.timestamp,
                        'open': bar.open,
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'volume': bar.volume,
                        'trade_count': bar.trade_count if hasattr(bar, 'trade_count') else 0,
                        'vwap': bar.vwap if hasattr(bar, 'vwap') else bar.close
                    } for bar in bars])

                    df.to_parquet(cache_file, index=False)
                    logger.debug(f"Cached: {symbol} ({len(bars)} bars)")

        # Return a simple object with .data attribute to match Alpaca API
        class CachedBarSet:
            def __init__(self, data):
                self.data = data

        return CachedBarSet(result_data)

    def print_stats(self):
        """Print cache statistics."""
        total = self.cache_hits + self.cache_misses
        if total > 0:
            hit_rate = (self.cache_hits / total) * 100
            print(f"\n📊 Cache Stats:")
            print(f"   Hits: {self.cache_hits}")
            print(f"   Misses: {self.cache_misses}")
            print(f"   Hit Rate: {hit_rate:.1f}%")
            print(f"   Cache Dir: {self.cache_dir}\n")
