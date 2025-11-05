"""
Market Scanner - Identifies high-probability momentum trading opportunities.

This scanner runs continuously during market hours and identifies stocks with:
- Unusual volume (relative volume > 2x)
- Significant price movement (gaps, breakouts)
- Appropriate price range ($3-$30)
- Low float (< 100M shares for faster movement)

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime, timedelta, time as dt_time
from typing import List, Dict, Optional
import pandas as pd
from dataclasses import dataclass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest, StockSnapshotRequest
from alpaca.data.timeframe import TimeFrame
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MomentumCandidate:
    """A stock that meets our momentum criteria."""
    symbol: str
    current_price: float
    volume: int
    relative_volume: float  # Current volume / average volume
    percent_change: float
    gap_percent: float  # Gap from previous close
    float_shares: Optional[float]  # Outstanding shares
    market_cap: Optional[float]
    detected_at: datetime

    # Technical indicators
    price_vs_vwap: float
    volume_spike_magnitude: int  # 2x, 5x, 10x

    # Catalyst hints (we'll enrich this with news later)
    catalyst_detected: bool = False
    catalyst_type: Optional[str] = None

    def __str__(self):
        return (
            f"{self.symbol}: ${self.current_price:.2f} "
            f"({self.percent_change:+.1f}%), "
            f"Vol {self.volume:,} ({self.relative_volume:.1f}x avg)"
        )

    def score(self) -> float:
        """
        Calculate opportunity score (0-10).
        Higher score = better setup.
        """
        score = 0.0

        # Volume is king (0-4 points)
        if self.relative_volume >= 10:
            score += 4
        elif self.relative_volume >= 5:
            score += 3
        elif self.relative_volume >= 3:
            score += 2
        elif self.relative_volume >= 2:
            score += 1

        # Price movement (0-3 points)
        abs_change = abs(self.percent_change)
        if abs_change >= 20:
            score += 3
        elif abs_change >= 10:
            score += 2
        elif abs_change >= 5:
            score += 1

        # Gap (0-2 points)
        abs_gap = abs(self.gap_percent)
        if abs_gap >= 10:
            score += 2
        elif abs_gap >= 5:
            score += 1

        # Catalyst bonus (0-1 point)
        if self.catalyst_detected:
            score += 1

        return min(score, 10.0)


class MomentumScanner:
    """
    Scans the market for momentum trading opportunities.
    """

    def __init__(self, api_key: str, secret_key: str):
        """
        Initialize scanner with Alpaca credentials.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
        """
        self.data_client = StockHistoricalDataClient(api_key, secret_key)
        self.api_key = api_key
        self.secret_key = secret_key

        # Scanner configuration
        self.config = {
            'min_price': 3.0,
            'max_price': 30.0,
            'min_relative_volume': 2.0,
            'min_percent_change': 4.0,
            'max_float': 100_000_000,  # 100M shares
            'lookback_days': 20,  # For average volume calculation
        }

        logger.info("Market Scanner initialized")

    def is_market_open(self, check_date: Optional[datetime] = None) -> bool:
        """
        Check if market is/was open on a given date.

        Args:
            check_date: Date to check (default: now)

        Returns:
            True if market is/was open on that date
        """
        check_datetime = check_date if check_date else datetime.now()

        # Check if weekday
        if check_datetime.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # For historical dates, assume market was open (we can't check holidays easily)
        # For current/recent dates, check time
        if check_date:
            # Historical check - just verify it's a weekday
            return True
        else:
            # Current time check
            market_open = dt_time(9, 30)
            market_close = dt_time(16, 0)
            current_time = check_datetime.time()
            return market_open <= current_time <= market_close

    def get_universe(self) -> List[str]:
        """
        Get list of stocks to scan.

        For now, we'll use a curated list of liquid stocks.
        In production, this would pull from a larger universe.

        Returns:
            List of stock symbols to scan
        """
        # For MVP, we'll scan popular stocks + recent movers
        # In production, we'd scan ALL stocks or use a screener API

        universe = [
            # Mega caps (for reference)
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',

            # High beta tech
            'PLTR', 'SNOW', 'CRWD', 'NET', 'DDOG', 'ZS',

            # Biotech (catalyst rich)
            'MRNA', 'BNTX', 'NVAX', 'VRTX', 'REGN', 'GILD',
            'SGEN', 'BMRN', 'ALNY', 'IONS',

            # EV / Clean Energy
            'RIVN', 'LCID', 'NIO', 'XPEV', 'ENPH', 'SEDG',

            # Meme stocks (high retail interest)
            'GME', 'AMC', 'BBBY', 'PTON',

            # Fintech
            'SQ', 'PYPL', 'COIN', 'HOOD', 'SOFI',

            # Retail
            'SHOP', 'ETSY', 'W', 'CHWY',

            # Other volatile names
            'ROKU', 'SNAP', 'UBER', 'LYFT', 'ABNB', 'DASH',
            'ZM', 'DOCU', 'PTON', 'AFRM'
        ]

        return universe

    def calculate_average_volume(self, symbol: str, days: int = 20) -> Optional[float]:
        """
        Calculate average daily volume over past N days.

        Args:
            symbol: Stock symbol
            days: Number of days to average

        Returns:
            Average volume or None if data unavailable
        """
        try:
            end = datetime.now()
            start = end - timedelta(days=days + 5)  # Extra buffer for weekends

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start,
                end=end
            )

            bars = self.data_client.get_stock_bars(request)

            if symbol not in bars.data:
                return None

            volumes = [bar.volume for bar in bars.data[symbol][-days:]]

            if not volumes:
                return None

            return sum(volumes) / len(volumes)

        except Exception as e:
            logger.warning(f"Could not calculate avg volume for {symbol}: {e}")
            return None

    def scan_symbol(self, symbol: str, historical_date: Optional[datetime] = None) -> Optional[MomentumCandidate]:
        """
        Scan a single symbol for momentum setup.

        Args:
            symbol: Stock ticker to analyze
            historical_date: Optional date for historical data (for backtesting)

        Returns:
            MomentumCandidate if criteria met, None otherwise
        """
        try:
            if historical_date:
                # Historical mode - use bar data for that specific date
                return self._scan_symbol_historical(symbol, historical_date)
            else:
                # Live mode - use current snapshot
                return self._scan_symbol_live(symbol)

        except Exception as e:
            logger.debug(f"Error scanning {symbol}: {e}")
            return None

    def _scan_symbol_live(self, symbol: str) -> Optional[MomentumCandidate]:
        """Scan symbol using live/current data."""
        try:
            # Get current snapshot
            snapshot_request = StockSnapshotRequest(symbol_or_symbols=symbol)
            snapshot = self.data_client.get_stock_snapshot(snapshot_request)

            if symbol not in snapshot:
                return None

            snap = snapshot[symbol]
            latest_quote = snap.latest_quote
            latest_trade = snap.latest_trade
            daily_bar = snap.daily_bar
            prev_daily = snap.previous_daily_bar

            # Current stats
            current_price = latest_trade.price
            current_volume = daily_bar.volume

            # Filter by price range
            if not (self.config['min_price'] <= current_price <= self.config['max_price']):
                return None

            # Calculate metrics
            avg_volume = self.calculate_average_volume(symbol)
            if not avg_volume or avg_volume == 0:
                return None

            relative_volume = current_volume / avg_volume

            # Filter by relative volume
            if relative_volume < self.config['min_relative_volume']:
                return None

            # Calculate percent change
            if prev_daily and prev_daily.close > 0:
                percent_change = ((current_price - prev_daily.close) / prev_daily.close) * 100
                gap_percent = ((daily_bar.open - prev_daily.close) / prev_daily.close) * 100
            else:
                percent_change = 0
                gap_percent = 0

            # Filter by percent change
            if abs(percent_change) < self.config['min_percent_change']:
                return None

            # Calculate price vs VWAP
            vwap = daily_bar.vwap if daily_bar.vwap else current_price
            price_vs_vwap = ((current_price - vwap) / vwap) * 100

            # Volume spike magnitude
            volume_spike_magnitude = int(relative_volume)

            candidate = MomentumCandidate(
                symbol=symbol,
                current_price=current_price,
                volume=current_volume,
                relative_volume=relative_volume,
                percent_change=percent_change,
                gap_percent=gap_percent,
                float_shares=None,  # Would need separate API for this
                market_cap=None,
                detected_at=datetime.now(),
                price_vs_vwap=price_vs_vwap,
                volume_spike_magnitude=volume_spike_magnitude
            )

            logger.info(f"✓ Found candidate: {candidate}")
            return candidate

        except Exception as e:
            logger.debug(f"Error scanning {symbol}: {e}")
            return None

    def _scan_symbol_historical(self, symbol: str, target_date: datetime) -> Optional[MomentumCandidate]:
        """
        Scan symbol using historical data for a specific date.

        Args:
            symbol: Stock ticker
            target_date: The historical date to scan

        Returns:
            MomentumCandidate if criteria met on that date
        """
        try:
            # Get bars for the target date + a few days prior for comparison
            start_date = target_date - timedelta(days=5)
            end_date = target_date + timedelta(days=1)

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date
            )

            bars = self.data_client.get_stock_bars(request)

            if symbol not in bars.data or not bars.data[symbol]:
                return None

            symbol_bars = list(bars.data[symbol])

            # Find the bar for our target date
            target_bar = None
            prev_bar = None

            for i, bar in enumerate(symbol_bars):
                bar_date = bar.timestamp.date()
                if bar_date == target_date.date():
                    target_bar = bar
                    if i > 0:
                        prev_bar = symbol_bars[i - 1]
                    break

            if not target_bar:
                return None

            # Current stats from that day
            current_price = float(target_bar.close)
            current_volume = int(target_bar.volume)

            # Filter by price range
            if not (self.config['min_price'] <= current_price <= self.config['max_price']):
                return None

            # Calculate average volume (20 days prior to target date)
            avg_volume_start = target_date - timedelta(days=25)
            avg_volume_end = target_date - timedelta(days=1)

            avg_request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=avg_volume_start,
                end=avg_volume_end
            )

            avg_bars = self.data_client.get_stock_bars(avg_request)

            if symbol in avg_bars.data and avg_bars.data[symbol]:
                volumes = [float(bar.volume) for bar in list(avg_bars.data[symbol])[-20:]]
                if volumes:
                    avg_volume = sum(volumes) / len(volumes)
                else:
                    return None
            else:
                return None

            relative_volume = current_volume / avg_volume if avg_volume > 0 else 0

            # Filter by relative volume
            if relative_volume < self.config['min_relative_volume']:
                return None

            # Calculate percent change
            if prev_bar and prev_bar.close > 0:
                percent_change = ((current_price - float(prev_bar.close)) / float(prev_bar.close)) * 100
                gap_percent = ((float(target_bar.open) - float(prev_bar.close)) / float(prev_bar.close)) * 100
            else:
                percent_change = 0
                gap_percent = 0

            # Filter by percent change
            if abs(percent_change) < self.config['min_percent_change']:
                return None

            # Calculate price vs VWAP
            vwap = float(target_bar.vwap) if target_bar.vwap else current_price
            price_vs_vwap = ((current_price - vwap) / vwap) * 100 if vwap > 0 else 0

            # Volume spike magnitude
            volume_spike_magnitude = int(relative_volume)

            candidate = MomentumCandidate(
                symbol=symbol,
                current_price=current_price,
                volume=current_volume,
                relative_volume=relative_volume,
                percent_change=percent_change,
                gap_percent=gap_percent,
                float_shares=None,
                market_cap=None,
                detected_at=target_date,
                price_vs_vwap=price_vs_vwap,
                volume_spike_magnitude=volume_spike_magnitude
            )

            logger.info(f"✓ Historical candidate on {target_date.date()}: {candidate}")
            return candidate

        except Exception as e:
            logger.debug(f"Error scanning {symbol} on {target_date.date()}: {e}")
            return None

    def scan(self, historical_date: Optional[datetime] = None) -> List[MomentumCandidate]:
        """
        Scan entire universe for momentum candidates.

        Args:
            historical_date: Optional date for historical scanning (for backtesting)

        Returns:
            List of MomentumCandidates sorted by score (best first)
        """
        logger.info("Starting market scan...")

        if not self.is_market_open(historical_date):
            logger.warning("Market is closed. Scan aborted.")
            return []

        universe = self.get_universe()
        candidates = []

        for symbol in universe:
            candidate = self.scan_symbol(symbol, historical_date=historical_date)
            if candidate:
                candidates.append(candidate)

        # Sort by score (highest first)
        candidates.sort(key=lambda c: c.score(), reverse=True)

        logger.info(f"Scan complete. Found {len(candidates)} candidates.")

        # Show top 5
        for i, candidate in enumerate(candidates[:5], 1):
            logger.info(f"  #{i} {candidate} (score: {candidate.score():.1f}/10)")

        return candidates


def main():
    """Test the scanner."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    scanner = MomentumScanner(api_key, secret_key)

    print("\n" + "="*80)
    print("MOMENTUM HUNTER - Market Scanner Test")
    print("="*80 + "\n")

    candidates = scanner.scan()

    if candidates:
        print(f"\n🎯 Top Momentum Candidates:\n")
        for i, candidate in enumerate(candidates[:10], 1):
            print(f"{i:2}. {candidate}")
            print(f"     Score: {candidate.score():.1f}/10")
            print(f"     Gap: {candidate.gap_percent:+.1f}%, VWAP: {candidate.price_vs_vwap:+.1f}%")
            print()
    else:
        print("No candidates found matching criteria.")


if __name__ == "__main__":
    main()
