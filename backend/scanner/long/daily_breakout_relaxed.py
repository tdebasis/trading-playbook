"""
Daily Breakout Scanner - RELAXED Parameters

Relaxed version with wider criteria to catch more opportunities:
- Relaxed volume filter (0.8x vs 1.2x)
- Wider distance from 52w high (40% vs 25%)
- Shorter min consolidation (5d vs 10d)
- Higher volatility tolerance (18% vs 12%)

Target: 40-80 trades over 6 months

Author: Claude AI + Tanam Bam Sinha
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

# Import interfaces and registration
sys.path.insert(0, str(backend_dir))
from interfaces import Candidate
from strategies import register_scanner

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
    consolidation_high: float  # High of the base pattern
    consolidation_days: int     # Length of consolidation
    breakout_volume_ratio: float  # Today's volume vs avg

    # Trend strength - SMA values
    sma_20: float  # 20-day simple moving average
    sma_50: float  # 50-day simple moving average
    sma_200: float  # 200-day simple moving average

    # Trend strength - EMA values
    ema_20: float  # 20-day exponential moving average
    ema_50: float  # 50-day exponential moving average
    ema_200: float  # 200-day exponential moving average

    distance_from_52w_high: float  # % below 52-week high

    # Pattern quality
    base_tightness: float  # Volatility during consolidation (lower is better)
    relative_strength: float  # Outperformance vs market

    def score(self, use_ema: bool = False) -> float:
        """
        Calculate breakout quality score (0-10).

        Scoring:
        - Trend: 3 points (price > MA20 > MA50, near 52w high)
        - Volume: 2 points (2x+ volume expansion)
        - Base: 3 points (tight consolidation, 3+ weeks)
        - Strength: 2 points (RS vs market)

        Args:
            use_ema: If True, score based on EMA. If False, score based on SMA (default).
        """
        score = 0.0

        # Choose which moving averages to use for scoring
        ma_20 = self.ema_20 if use_ema else self.sma_20
        ma_50 = self.ema_50 if use_ema else self.sma_50

        # 1. Trend Quality (3 points max)
        if self.close > ma_20 > ma_50:
            score += 1.5  # Proper trend alignment
        elif self.close > ma_20:
            score += 0.5  # At least above 20-day

        if self.distance_from_52w_high <= 15:
            score += 1.5  # Within 15% of 52-week high
        elif self.distance_from_52w_high <= 25:
            score += 0.75  # Within 25% of high

        # 2. Volume Expansion (2 points max)
        if self.breakout_volume_ratio >= 2.0:
            score += 2.0  # 2x+ volume = strong
        elif self.breakout_volume_ratio >= 1.2:
            score += 1.0  # 1.5x volume = decent

        # 3. Base Quality (3 points max)
        if 15 <= self.consolidation_days <= 60:
            score += 1.5  # Ideal consolidation length (3-12 weeks)
        elif 7 <= self.consolidation_days <= 90:
            score += 0.75  # Acceptable length

        if self.base_tightness <= 0.05:  # 5% volatility
            score += 1.5  # Very tight base (ideal)
        elif self.base_tightness <= 0.08:  # 8% volatility
            score += 1.0  # Tight base (good)
        elif self.base_tightness <= 0.12:  # 12% volatility
            score += 0.5  # Acceptable for growth stocks

        # 4. Relative Strength (2 points max)
        if self.relative_strength >= 1.5:
            score += 2.0  # Outperforming market significantly
        elif self.relative_strength >= 1.0:
            score += 1.0  # At least keeping pace with market

        return min(score, 10.0)

    def __repr__(self):
        return (f"DailyBreakout({self.symbol} on {self.date.strftime('%Y-%m-%d')}: "
                f"${self.close:.2f}, Score: {self.score():.1f}/10, "
                f"Vol: {self.breakout_volume_ratio:.1f}x, "
                f"{self.distance_from_52w_high:.1f}% from high)")


@register_scanner('daily_breakout_relaxed')
class DailyBreakoutScannerRelaxed:
    """
    Scans for daily breakout opportunities in Minervini/O'Neil style.

    Strategy:
    - Find stocks in Stage 2 uptrend (price > SMA20 > SMA50)
    - Near 52-week highs (within 15-25%)
    - Consolidating in tight base (3-12 weeks, <5% volatility)
    - Breaking above base on 1.5x+ volume

    Implements ScannerProtocol for plug-and-play architecture.
    """

    def __init__(self, api_key: str, secret_key: str, universe: str = 'default'):
        self.client = StockHistoricalDataClient(api_key, secret_key)
        self._universe_name = universe

        # Screening criteria - RELAXED
        self.min_consolidation_days = 5   # Catch quick tight bases
        self.max_consolidation_days = 90  # At most 3 months
        self.min_volume_ratio = 0.8       # Relaxed - catch PLTR-style moves on 0.7x volume
        self.max_distance_from_high = 40  # Catch mid-Stage 2 breakouts
        self.min_price = 10.0             # Avoid penny stocks
        self.max_base_volatility = 0.18   # Allow growth stock volatility

        # Watchlist - now loaded from config file
        # Options: 'default', 'tech', 'high_vol', 'mega_caps', 'extended'
        self.watchlist = get_universe(universe)
        logger.info(f"Loaded '{universe}' universe: {len(self.watchlist)} stocks")

    @property
    def strategy_name(self) -> str:
        """Return strategy identifier for ScannerProtocol."""
        return 'daily_breakout_relaxed'

    @property
    def timeframe(self) -> str:
        """Return trading timeframe for ScannerProtocol."""
        return 'daily'

    @property
    def universe(self) -> List[str]:
        """Return list of symbols monitored for ScannerProtocol."""
        return self.watchlist

    def scan(self, scan_date: Optional[datetime] = None) -> List[DailyBreakoutCandidate]:
        """
        Scan for daily breakout candidates.

        Args:
            scan_date: Date to scan (default: today). For backtesting, pass historical date.

        Returns:
            List of breakout candidates, sorted by score (best first)
        """
        scan_date = scan_date or datetime.now()

        logger.info(f"\n{'='*80}")
        logger.info(f"DAILY BREAKOUT SCAN - {scan_date.strftime('%Y-%m-%d')}")
        logger.info(f"{'='*80}\n")
        logger.info(f"Scanning {len(self.watchlist)} symbols for breakouts...")

        candidates = []

        for symbol in self.watchlist:
            try:
                candidate = self._analyze_symbol(symbol, scan_date)
                if candidate:
                    candidates.append(candidate)
                    logger.info(f"  ✅ {symbol}: Score {candidate.score():.1f}/10")
                else:
                    logger.debug(f"  ❌ {symbol}: No breakout")
            except Exception as e:
                logger.warning(f"  ⚠️  {symbol}: Error - {e}")

        # Sort by score (best first)
        candidates.sort(key=lambda c: c.score(), reverse=True)

        logger.info(f"\n📊 Found {len(candidates)} breakout candidates")
        if candidates:
            logger.info("Top 3:")
            for i, c in enumerate(candidates[:3], 1):
                logger.info(f"  {i}. {c}")

        return candidates

    def scan_standardized(self, scan_date: Optional[datetime] = None) -> List[Candidate]:
        """
        Scan for opportunities and return standardized Candidate objects.

        This method implements the ScannerProtocol interface by converting
        internal DailyBreakoutCandidate objects to the standardized Candidate format.

        Args:
            scan_date: Date to scan (default: today)

        Returns:
            List of standardized Candidate objects sorted by score (best first)
        """
        # Use existing scan logic
        internal_candidates = self.scan(scan_date)

        # Convert to standardized format
        return [self._to_candidate(c) for c in internal_candidates]

    def _to_candidate(self, internal: DailyBreakoutCandidate) -> Candidate:
        """
        Convert internal DailyBreakoutCandidate to standardized Candidate.

        This adapter method preserves all internal data in the strategy_data dict
        while providing the standard interface for execution systems.

        Args:
            internal: Internal candidate representation

        Returns:
            Standardized Candidate object
        """
        # Calculate suggested stop (8% below entry)
        suggested_stop = internal.close * 0.92

        # No fixed target - let exit strategy determine
        suggested_target = None

        return Candidate(
            symbol=internal.symbol,
            scan_date=internal.date.date(),
            score=internal.score(),
            entry_price=internal.close,
            suggested_stop=suggested_stop,
            suggested_target=suggested_target,
            strategy_data={
                # Price action
                'volume': internal.volume,
                'close': internal.close,

                # Breakout metrics
                'consolidation_high': internal.consolidation_high,
                'consolidation_days': internal.consolidation_days,
                'breakout_volume_ratio': internal.breakout_volume_ratio,

                # Trend strength - SMA
                'sma_20': internal.sma_20,
                'sma_50': internal.sma_50,
                'sma_200': internal.sma_200,

                # Trend strength - EMA
                'ema_20': internal.ema_20,
                'ema_50': internal.ema_50,
                'ema_200': internal.ema_200,

                # Position metrics
                'distance_from_52w_high': internal.distance_from_52w_high,

                # Pattern quality
                'base_tightness': internal.base_tightness,
                'relative_strength': internal.relative_strength,

                # Scoring breakdown (for analysis)
                'score_sma': internal.score(use_ema=False),
                'score_ema': internal.score(use_ema=True),
            }
        )

    def _calculate_ema(self, bars: list, period: int) -> float:
        """
        Calculate Exponential Moving Average.

        EMA gives more weight to recent prices, making it more responsive
        to new price action than SMA.
        """
        if len(bars) < period:
            return 0.0

        closes = [float(b.close) for b in bars]

        # Start with SMA for first value
        ema = sum(closes[:period]) / period
        multiplier = 2 / (period + 1)

        # Calculate EMA for remaining values
        for close in closes[period:]:
            ema = (close * multiplier) + (ema * (1 - multiplier))

        return ema

    def _analyze_symbol(self, symbol: str, scan_date: datetime) -> Optional[DailyBreakoutCandidate]:
        """
        Analyze a single symbol for breakout setup.

        Returns:
            DailyBreakoutCandidate if meets criteria, None otherwise
        """
        # Fetch 6 months of daily data (enough for 50-day MA and 52-week high)
        start_date = scan_date - timedelta(days=180)

        request = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Day,
            start=start_date,
            end=scan_date
        )

        bars_response = self.client.get_stock_bars(request)

        if symbol not in bars_response.data or not bars_response.data[symbol]:
            return None

        bars = list(bars_response.data[symbol])

        if len(bars) < 50:  # Need at least 50 days for MA calculations
            return None

        # Current bar (scan date)
        current_bar = bars[-1]

        # Price filters
        if current_bar.close < self.min_price:
            return None

        # Calculate all moving averages (both SMA and EMA)
        sma_20 = sum(b.close for b in bars[-20:]) / 20
        sma_50 = sum(b.close for b in bars[-50:]) / 50
        sma_200 = sum(b.close for b in bars[-200:]) / 200 if len(bars) >= 200 else 0.0

        ema_20 = self._calculate_ema(bars, 20)
        ema_50 = self._calculate_ema(bars, 50)
        ema_200 = self._calculate_ema(bars, 200) if len(bars) >= 200 else 0.0

        # Check trend: price > SMA20 > SMA50
        # (Using SMA for now based on Step 2 results - EMA didn't help much)
        if not (current_bar.close > sma_20 and sma_20 > sma_50):
            return None

        # Calculate 52-week high
        high_52w = max(b.high for b in bars)
        distance_from_high = ((high_52w - current_bar.close) / high_52w) * 100

        if distance_from_high > self.max_distance_from_high:
            return None

        # Find consolidation base
        base_result = self._find_consolidation_base(bars)
        if not base_result:
            return None

        consolidation_high, consolidation_days, base_tightness = base_result

        # Check if breaking above consolidation high
        if current_bar.close <= consolidation_high:
            return None  # Not breaking out yet

        # Calculate volume ratio
        avg_volume = sum(b.volume for b in bars[-20:-1]) / 19  # Avg of previous 20 days (excluding today)
        volume_ratio = current_bar.volume / avg_volume if avg_volume > 0 else 0

        if volume_ratio < self.min_volume_ratio:
            return None

        # Calculate relative strength (simplified - compare to SPY later if needed)
        price_change_20d = ((current_bar.close - bars[-20].close) / bars[-20].close) * 100
        relative_strength = max(0.0, price_change_20d / 10)  # Normalize to ~1.0 for 10% gain

        # Create candidate
        return DailyBreakoutCandidate(
            symbol=symbol,
            date=scan_date,
            close=float(current_bar.close),
            volume=int(current_bar.volume),
            consolidation_high=float(consolidation_high),
            consolidation_days=consolidation_days,
            breakout_volume_ratio=float(volume_ratio),
            sma_20=float(sma_20),
            sma_50=float(sma_50),
            sma_200=float(sma_200),
            ema_20=float(ema_20),
            ema_50=float(ema_50),
            ema_200=float(ema_200),
            distance_from_52w_high=float(distance_from_high),
            base_tightness=float(base_tightness),
            relative_strength=float(relative_strength)
        )

    def _find_consolidation_base(self, bars: list) -> Optional[tuple]:
        """
        Find the most recent consolidation base.

        A consolidation base is:
        - 10-90 days of sideways movement
        - Low volatility (<8% range)
        - Before the current breakout

        Returns:
            (consolidation_high, days, tightness) or None
        """
        # Look back at most 90 days
        lookback = min(90, len(bars) - 1)

        # Start from current bar and look backwards
        for length in range(self.min_consolidation_days, lookback):
            # Get bars in potential base (excluding current bar)
            base_bars = bars[-(length+1):-1]

            if not base_bars:
                continue

            # Calculate base metrics
            base_high = max(b.high for b in base_bars)
            base_low = min(b.low for b in base_bars)
            base_range = base_high - base_low
            base_tightness = base_range / base_high if base_high > 0 else 1.0

            # Check if base is tight enough
            if base_tightness <= self.max_base_volatility:
                return (base_high, length, base_tightness)

        return None


if __name__ == "__main__":
    # Test the scanner
    import os
    from dotenv import load_dotenv

    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    scanner = DailyBreakoutScanner(api_key, secret_key)

    # Test on a recent date
    test_date = datetime(2025, 10, 15)
    candidates = scanner.scan(test_date)

    print(f"\n{'='*80}")
    print(f"SCAN RESULTS - {test_date.strftime('%Y-%m-%d')}")
    print(f"{'='*80}\n")

    if candidates:
        print(f"Found {len(candidates)} breakout candidates:\n")
        for i, c in enumerate(candidates, 1):
            print(f"{i}. {c.symbol}:")
            print(f"   Price: ${c.close:.2f} (20-day MA: ${c.sma_20:.2f})")
            print(f"   Volume: {c.breakout_volume_ratio:.1f}x average")
            print(f"   Base: {c.consolidation_days} days, {c.base_tightness*100:.1f}% volatility")
            print(f"   Distance from 52w high: {c.distance_from_52w_high:.1f}%")
            print(f"   Score: {c.score():.1f}/10")
            print()
    else:
        print("No breakouts found.")
