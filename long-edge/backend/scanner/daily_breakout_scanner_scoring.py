"""
Daily Breakout Scanner - SCORING SYSTEM VERSION

Key difference from standard scanner:
- Volume is NOT a hard filter
- Volume becomes a scoring factor (0-2 points)
- Entry requires minimum TOTAL score, not minimum volume
- Weak volume CAN be compensated by strong price action

This tests the hypothesis: "Quality stocks (PLTR) accumulate quietly,
price action matters more than volume."
"""

from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass
import logging
import sys
from pathlib import Path

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Add parent directory to path for config import
backend_dir = Path(__file__).parent.parent
project_dir = backend_dir.parent
sys.path.insert(0, str(project_dir))

from config.universe import get_universe

logger = logging.getLogger(__name__)


@dataclass
class DailyBreakoutCandidate:
    """A stock breaking out of consolidation on daily timeframe."""
    symbol: str
    date: datetime

    # Price action
    close: float
    volume: int

    # Breakout metrics
    consolidation_high: float
    consolidation_days: int
    breakout_volume_ratio: float

    # Trend strength - SMA values
    sma_20: float
    sma_50: float
    sma_200: float

    # Trend strength - EMA values
    ema_20: float
    ema_50: float
    ema_200: float

    distance_from_52w_high: float

    # Pattern quality
    base_tightness: float
    relative_strength: float

    def score_with_volume_compensation(self, use_ema: bool = False) -> dict:
        """
        Calculate score where WEAK VOLUME requires STRONGER PRICE ACTION.

        Key Logic:
        - Volume: 0-2 points (not a filter!)
        - Trend: 0-3 points
        - Base: 0-3 points
        - RS: 0-2 points

        CRITICAL: If volume < 1.0 points, need higher total score to enter
        - High volume (1.5-2.0 pts): Need 4.0 total
        - Medium volume (1.0 pts): Need 5.0 total
        - Low volume (0.5-1.0 pts): Need 6.0 total
        """
        score = 0.0
        breakdown = {}

        ma_20 = self.ema_20 if use_ema else self.sma_20
        ma_50 = self.ema_50 if use_ema else self.sma_50

        # 1. VOLUME (0-2 points) - Now a scoring factor, not filter!
        volume_score = 0.0
        if self.breakout_volume_ratio >= 2.0:
            volume_score = 2.0  # Explosive
        elif self.breakout_volume_ratio >= 1.5:
            volume_score = 1.5  # Strong
        elif self.breakout_volume_ratio >= 1.2:
            volume_score = 1.0  # Normal
        elif self.breakout_volume_ratio >= 0.8:
            volume_score = 0.7  # Quiet accumulation (PLTR-style)
        elif self.breakout_volume_ratio >= 0.5:
            volume_score = 0.3  # Very quiet (needs strong price action)
        else:
            volume_score = 0.0  # Too quiet (likely dying)

        breakdown['volume'] = volume_score
        score += volume_score

        # 2. TREND QUALITY (0-3 points)
        trend_score = 0.0
        if self.close > ma_20 > ma_50:
            trend_score += 1.5  # Proper trend alignment
        elif self.close > ma_20:
            trend_score += 0.5  # At least above 20-day

        if self.distance_from_52w_high <= 15:
            trend_score += 1.5  # Within 15% of 52w high (strong)
        elif self.distance_from_52w_high <= 25:
            trend_score += 0.75  # Within 25% of high (ok)

        breakdown['trend'] = trend_score
        score += trend_score

        # 3. BASE QUALITY (0-3 points)
        base_score = 0.0
        if 15 <= self.consolidation_days <= 60:
            base_score += 1.5  # Ideal consolidation (3-12 weeks)
        elif 7 <= self.consolidation_days <= 90:
            base_score += 0.75  # Acceptable

        if self.base_tightness <= 0.05:
            base_score += 1.5  # Very tight (ideal)
        elif self.base_tightness <= 0.08:
            base_score += 1.0  # Tight (good)
        elif self.base_tightness <= 0.12:
            base_score += 0.5  # Acceptable for growth

        breakdown['base'] = base_score
        score += base_score

        # 4. RELATIVE STRENGTH (0-2 points)
        rs_score = 0.0
        if self.relative_strength >= 1.5:
            rs_score = 2.0  # Outperforming significantly
        elif self.relative_strength >= 1.0:
            rs_score = 1.0  # Keeping pace

        breakdown['rs'] = rs_score
        score += rs_score

        # CRITICAL: Determine required threshold based on volume
        if volume_score >= 1.5:
            required_score = 4.0  # High volume = normal threshold
        elif volume_score >= 1.0:
            required_score = 5.0  # Medium volume = need stronger price
        elif volume_score >= 0.5:
            required_score = 6.0  # Low volume = need MUCH stronger price
        else:
            required_score = 8.0  # Very low volume = nearly impossible

        return {
            'total': score,
            'breakdown': breakdown,
            'required': required_score,
            'passes': score >= required_score,
            'volume_tier': 'high' if volume_score >= 1.5 else 'medium' if volume_score >= 1.0 else 'low'
        }

    def score(self, use_ema: bool = False) -> float:
        """Legacy score method for compatibility."""
        result = self.score_with_volume_compensation(use_ema)
        return result['total']

    def __repr__(self):
        scoring = self.score_with_volume_compensation()
        return (f"DailyBreakout({self.symbol} on {self.date.strftime('%Y-%m-%d')}: "
                f"${self.close:.2f}, Score: {scoring['total']:.1f}/10 "
                f"(need {scoring['required']:.1f}, {'PASS' if scoring['passes'] else 'FAIL'}), "
                f"Vol: {self.breakout_volume_ratio:.1f}x)")


class DailyBreakoutScannerScoring:
    """
    Scanner with SCORING SYSTEM instead of hard volume filter.

    Key Difference:
    - No min_volume_ratio filter
    - Volume is scored (0-2 points)
    - Low volume requires higher total score
    """

    def __init__(self, api_key: str, secret_key: str, universe: str = 'default'):
        self.client = StockHistoricalDataClient(api_key, secret_key)

        # Screening criteria (VOLUME REMOVED AS FILTER)
        self.min_consolidation_days = 10
        self.max_consolidation_days = 90
        self.max_distance_from_high = 25
        self.min_price = 10.0
        self.max_base_volatility = 0.12

        # NO min_volume_ratio - this is the key difference!

        # Watchlist
        self.watchlist = get_universe(universe)
        logger.info(f"Loaded '{universe}' universe: {len(self.watchlist)} stocks")
        logger.info("🎯 SCORING MODE: Volume is a scoring factor, not a filter")

    def scan(self, target_date: Optional[datetime] = None) -> List[DailyBreakoutCandidate]:
        """
        Scan for breakout candidates using SCORING system.

        Returns candidates that pass score threshold (adjusted by volume).
        """
        if target_date is None:
            target_date = datetime.now()

        candidates = []

        for symbol in self.watchlist:
            try:
                candidate = self._check_symbol(symbol, target_date)
                if candidate:
                    # Check if passes scoring threshold
                    scoring = candidate.score_with_volume_compensation()
                    if scoring['passes']:
                        candidates.append(candidate)
                        logger.info(f"✅ {symbol}: {scoring['total']:.1f}/{scoring['required']:.1f} "
                                  f"(vol {scoring['breakdown']['volume']:.1f}pts, {scoring['volume_tier']} tier)")
                    else:
                        logger.debug(f"❌ {symbol}: {scoring['total']:.1f}/{scoring['required']:.1f} "
                                   f"(vol {scoring['breakdown']['volume']:.1f}pts)")

            except Exception as e:
                logger.warning(f"Error checking {symbol}: {e}")
                continue

        # Sort by score
        candidates.sort(key=lambda x: x.score(), reverse=True)

        logger.info(f"Found {len(candidates)} candidates using SCORING system")
        return candidates

    def _check_symbol(self, symbol: str, target_date: datetime) -> Optional[DailyBreakoutCandidate]:
        """Check if symbol meets criteria (NO volume filter)."""

        # Fetch 200 days of daily data
        end_date = target_date
        start_date = target_date - timedelta(days=250)

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date
        )

        bars_dict = self.client.get_stock_bars(request)
        if symbol not in bars_dict:
            return None

        bars = bars_dict[symbol]
        if len(bars) < 200:
            return None

        # Get latest bar
        latest = bars[-1]

        # Price filter
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

        # Trend filter (still required)
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

        # Volume ratio (NOT filtered, just calculated for scoring)
        avg_volume = sum(volumes[-20:]) / 20
        volume_ratio = latest.volume / avg_volume if avg_volume > 0 else 0

        # Relative strength (simplified)
        spy_change = 1.0  # Would need actual SPY data
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
