"""
Daily Breakout Scanner - SCORING SYSTEM with CACHING

Same as daily_breakout_scanner_scoring.py but uses cached data for fast iteration.

Key difference:
- Uses CachedDataClient instead of StockHistoricalDataClient
- First run: Downloads and caches (~7 min)
- Subsequent runs: Loads from cache (~5 seconds)
"""

from datetime import datetime, timedelta
from typing import List, Optional
import logging
import sys
from pathlib import Path

# Add paths
backend_dir = Path(__file__).parent.parent
project_dir = backend_dir.parent
sys.path.insert(0, str(project_dir))

from config.universe import get_universe
from data.cache import CachedDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from scanner.daily_breakout_scanner_scoring import DailyBreakoutCandidate

logger = logging.getLogger(__name__)


class DailyBreakoutScannerScoringCached:
    """Scoring scanner with disk caching for fast iteration."""

    def __init__(self, api_key: str, secret_key: str, universe: str = 'default', cache_dir: str = './cache'):
        # Use cached client instead of regular client
        self.client = CachedDataClient(api_key, secret_key, cache_dir=cache_dir)

        # Same screening criteria as scoring scanner
        self.min_consolidation_days = 10
        self.max_consolidation_days = 90
        self.max_distance_from_high = 25
        self.min_price = 10.0
        self.max_base_volatility = 0.12

        # Watchlist
        self.watchlist = get_universe(universe)
        logger.info(f"Loaded '{universe}' universe: {len(self.watchlist)} stocks")
        logger.info(f"🎯 SCORING MODE with CACHING: {cache_dir}")

    def scan(self, target_date: Optional[datetime] = None) -> List[DailyBreakoutCandidate]:
        """Scan for breakout candidates using scoring + caching."""
        if target_date is None:
            target_date = datetime.now()

        candidates = []

        for symbol in self.watchlist:
            try:
                candidate = self._check_symbol(symbol, target_date)
                if candidate:
                    scoring = candidate.score_with_volume_compensation()
                    if scoring['passes']:
                        candidates.append(candidate)

            except Exception as e:
                logger.warning(f"Error checking {symbol}: {e}")
                continue

        candidates.sort(key=lambda x: x.score(), reverse=True)
        logger.info(f"Found {len(candidates)} candidates using SCORING system")

        return candidates

    def _check_symbol(self, symbol: str, target_date: datetime) -> Optional['DailyBreakoutCandidate']:
        """Check symbol - same logic as scoring scanner."""
        end_date = target_date
        start_date = target_date - timedelta(days=250)

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date
        )

        # This will use cache!
        bars_dict = self.client.get_stock_bars(request)

        # Handle both cached and non-cached responses
        if hasattr(bars_dict, 'data'):
            # Regular Alpaca response
            if symbol not in bars_dict.data:
                return None
            bars = list(bars_dict.data[symbol])
        else:
            # Cached response (dict)
            if symbol not in bars_dict:
                return None
            bars = list(bars_dict[symbol])
        if len(bars) < 200:
            return None

        latest = bars[-1]

        if latest.close < self.min_price:
            return None

        # Calculate indicators
        closes = [b.close for b in bars]
        volumes = [b.volume for b in bars]

        sma_20 = sum(closes[-20:]) / 20
        sma_50 = sum(closes[-50:]) / 50
        sma_200 = sum(closes[-200:]) / 200

        ema_20 = self._calculate_ema(closes, 20)
        ema_50 = self._calculate_ema(closes, 50)
        ema_200 = self._calculate_ema(closes, 200)

        # Trend filter
        if not (latest.close > sma_20 > sma_50):
            return None

        # 52-week high
        highs_52w = [b.high for b in bars[-252:]]
        high_52w = max(highs_52w)
        distance_from_high = ((high_52w - latest.close) / high_52w) * 100

        if distance_from_high > self.max_distance_from_high:
            return None

        # Find consolidation base
        base_result = self._find_consolidation_base(bars)
        if not base_result:
            return None

        consolidation_high, consolidation_days, base_tightness = base_result

        # Check for breakout
        if latest.close <= consolidation_high:
            return None

        # Volume ratio (for scoring, not filtering)
        avg_volume = sum(volumes[-20:]) / 20
        volume_ratio = latest.volume / avg_volume if avg_volume > 0 else 0

        # Relative strength
        spy_change = 1.0
        stock_change = closes[-1] / closes[-20]
        relative_strength = stock_change / spy_change

        return DailyBreakoutCandidate(
            symbol=symbol,
            date=latest.timestamp,
            close=latest.close,
            volume=latest.volume,
            consolidation_high=consolidation_high,
            consolidation_days=consolidation_days,
            breakout_volume_ratio=volume_ratio,
            sma_20=sma_20,
            sma_50=sma_50,
            sma_200=sma_200,
            ema_20=ema_20,
            ema_50=ema_50,
            ema_200=ema_200,
            distance_from_52w_high=distance_from_high,
            base_tightness=base_tightness,
            relative_strength=relative_strength
        )

    def _find_consolidation_base(self, bars) -> Optional[tuple]:
        """Find consolidation base."""
        for lookback in range(self.min_consolidation_days, min(self.max_consolidation_days + 1, len(bars) - 20)):
            base_bars = bars[-(lookback + 1):-1]
            highs = [b.high for b in base_bars]
            lows = [b.low for b in base_bars]

            base_high = max(highs)
            base_low = min(lows)
            base_range = base_high - base_low
            tightness = base_range / base_high

            if tightness <= self.max_base_volatility:
                return (base_high, lookback, tightness)

        return None

    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA."""
        if len(prices) < period:
            return sum(prices) / len(prices)

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period

        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema

        return ema

    def print_cache_stats(self):
        """Print cache statistics."""
        self.client.print_stats()
