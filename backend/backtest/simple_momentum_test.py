"""
Simple Momentum Backtester - Tests pure momentum signals without AI decision layer.

This uses SIMPLE RULES to test if momentum breakouts are profitable:
- If scanner detects breakout (2x+ volume, 3%+ move) → BUY
- Stop loss: 2% below entry
- Profit target: 4% above entry (2:1 R/R)
- Max 3 positions, 25% position size each

No Claude, no news filtering - just pure momentum signals.

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime, timedelta
from typing import Dict, List
import logging
from dataclasses import dataclass, asdict
import json
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from scanner.long.market_scanner import MomentumScanner, MomentumCandidate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SimpleTrade:
    """A simple momentum trade."""
    symbol: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime = None
    exit_price: float = None
    shares: int = 0
    stop_loss: float = 0.0
    profit_target: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    reason_exited: str = ""
    scanner_score: float = 0.0
    relative_volume: float = 0.0
    percent_change: float = 0.0


class SimpleMomentumBacktester:
    """
    Simple rule-based momentum backtester.
    No AI, no news - just pure momentum signals.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        starting_capital: float = 100000
    ):
        """
        Initialize simple momentum backtester.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            starting_capital: Starting account value
        """
        self.data_client = StockHistoricalDataClient(api_key, secret_key)
        self.scanner = MomentumScanner(api_key, secret_key)

        self.starting_capital = starting_capital
        self.capital = starting_capital
        self.positions: Dict[str, SimpleTrade] = {}
        self.closed_trades: List[SimpleTrade] = []

        # Simple risk management
        self.max_positions = 3
        self.max_position_size_percent = 0.25  # 25% per position
        self.stop_loss_percent = 0.02  # 2% stop
        self.profit_target_percent = 0.04  # 4% target (2:1 R/R)

        # Entry criteria (SIMPLE RULES)
        self.min_scanner_score = 2.0  # Accept scanner score 2+
        self.min_relative_volume = 2.0  # Accept 2x+ volume

        logger.info(f"Simple Momentum Backtester initialized (${starting_capital:,.0f})")
        logger.info(f"Rules: Score {self.min_scanner_score}+, Volume {self.min_relative_volume}x+")

    def get_intraday_bars(
        self,
        symbols: List[str],
        start: datetime,
        end: datetime
    ) -> Dict[str, List]:
        """Fetch 2-minute bars for symbols."""
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=TimeFrame.Minute,
                start=start,
                end=end
            )

            bars = self.data_client.get_stock_bars(request)

            result = {}
            for symbol in symbols:
                if symbol in bars.data:
                    result[symbol] = bars.data[symbol]

            return result

        except Exception as e:
            logger.error(f"Error fetching intraday bars: {e}")
            return {}

    def scan_for_breakouts(
        self,
        current_time: datetime,
        bars_cache: Dict[str, List]
    ) -> tuple[List[MomentumCandidate], Dict[str, float]]:
        """Scan for momentum breakouts using completed bars only."""
        candidates = []
        next_bar_prices = {}

        for symbol, bars in bars_cache.items():
            # Only use completed bars
            completed_bars = [b for b in bars if b.timestamp < current_time]
            if len(completed_bars) < 20:
                continue

            last_completed_bar = completed_bars[-1]
            recent_bars = completed_bars[-20:]

            # Find next bar for entry
            next_bars = [b for b in bars if b.timestamp >= current_time]
            if not next_bars:
                continue
            next_bar = next_bars[0]
            entry_price = float(next_bar.open)

            # Calculate metrics
            avg_volume = sum(b.volume for b in recent_bars[:-1]) / (len(recent_bars) - 1)
            relative_volume = last_completed_bar.volume / avg_volume if avg_volume > 0 else 0

            if relative_volume < 2.0:
                continue

            session_open = completed_bars[0].open if completed_bars else last_completed_bar.open
            percent_change = ((last_completed_bar.close - session_open) / session_open) * 100

            if abs(percent_change) < 3.0:
                continue

            # Create candidate
            candidate = MomentumCandidate(
                symbol=symbol,
                current_price=float(last_completed_bar.close),
                volume=int(last_completed_bar.volume),
                relative_volume=relative_volume,
                percent_change=percent_change,
                gap_percent=0.0,
                float_shares=None,
                market_cap=None,
                detected_at=current_time,
                price_vs_vwap=0.0,
                volume_spike_magnitude=int(relative_volume)
            )

            candidates.append(candidate)
            next_bar_prices[symbol] = entry_price

            logger.info(f"🔥 Breakout: {symbol} @ ${last_completed_bar.close:.2f}")
            logger.info(f"   Score: {candidate.score():.1f}, Vol: {relative_volume:.1f}x, Change: {percent_change:+.1f}%")

        return candidates, next_bar_prices

    def should_enter_trade(self, candidate: MomentumCandidate) -> bool:
        """
        Simple rule-based entry decision.
        No AI, no news - just scanner metrics.
        """
        # Rule 1: Scanner score must be decent
        if candidate.score() < self.min_scanner_score:
            logger.info(f"   ❌ Skip {candidate.symbol}: Score {candidate.score():.1f} < {self.min_scanner_score}")
            return False

        # Rule 2: Volume must be strong
        if candidate.relative_volume < self.min_relative_volume:
            logger.info(f"   ❌ Skip {candidate.symbol}: Volume {candidate.relative_volume:.1f}x < {self.min_relative_volume}x")
            return False

        # Rule 3: Not already at max positions
        if len(self.positions) >= self.max_positions:
            logger.info(f"   ❌ Skip {candidate.symbol}: Already at max positions ({self.max_positions})")
            return False

        # Rule 4: Don't already have this position
        if candidate.symbol in self.positions:
            logger.info(f"   ❌ Skip {candidate.symbol}: Already in position")
            return False

        # All rules passed!
        return True

    def run(
        self,
        start_date: datetime,
        end_date: datetime,
        test_symbols: List[str] = None
    ) -> Dict:
        """Run simple momentum backtest."""
        logger.info("=" * 80)
        logger.info("SIMPLE MOMENTUM BACKTEST (NO AI, NO NEWS)")
        logger.info("=" * 80)
        logger.info(f"Period: {start_date.date()} to {end_date.date()}")
        logger.info(f"Starting Capital: ${self.starting_capital:,.0f}")
        logger.info("=" * 80)
        logger.info("")

        # Use smaller universe for testing
        if test_symbols is None:
            test_symbols = ['NVDA', 'TSLA', 'NVAX', 'SNAP', 'PTON']

        # Test one day first
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/New_York")
        test_start = datetime(2025, 8, 6, 9, 30, tzinfo=tz)
        test_end = datetime(2025, 8, 6, 16, 0, tzinfo=tz)

        logger.info(f"Testing 1 day: {test_start.date()}")
        logger.info(f"Symbols: {', '.join(test_symbols)}")
        logger.info("")

        # Fetch intraday bars
        logger.info("Fetching intraday bars...")
        bars_cache = self.get_intraday_bars(test_symbols, test_start, test_end)
        logger.info(f"Fetched bars for {len(bars_cache)} symbols")
        logger.info("")

        # Replay minute-by-minute
        current_time = test_start
        scan_interval = timedelta(minutes=2)

        while current_time <= test_end:
            # Scan for breakouts
            candidates, next_bar_prices = self.scan_for_breakouts(current_time, bars_cache)

            if candidates:
                logger.info(f"\n⏰ {current_time.strftime('%H:%M')} - Found {len(candidates)} breakout(s)")

                # Apply simple rules to decide
                for candidate in candidates:
                    if self.should_enter_trade(candidate):
                        # ENTER TRADE (simple rules say YES)
                        entry_price = next_bar_prices[candidate.symbol]
                        stop_loss = entry_price * (1 - self.stop_loss_percent)
                        profit_target = entry_price * (1 + self.profit_target_percent)

                        # Position sizing: 25% of account
                        position_value = self.capital * self.max_position_size_percent
                        shares = int(position_value / entry_price)

                        if shares > 0:
                            trade = SimpleTrade(
                                symbol=candidate.symbol,
                                entry_time=current_time,
                                entry_price=entry_price,
                                shares=shares,
                                stop_loss=stop_loss,
                                profit_target=profit_target,
                                scanner_score=candidate.score(),
                                relative_volume=candidate.relative_volume,
                                percent_change=candidate.percent_change
                            )
                            self.positions[candidate.symbol] = trade
                            self.capital -= shares * entry_price

                            logger.info(f"✅ ENTER {candidate.symbol}: {shares} shares @ ${entry_price:.2f}")
                            logger.info(f"   Stop: ${stop_loss:.2f}, Target: ${profit_target:.2f}")
                            logger.info(f"   Position value: ${shares * entry_price:,.2f}")
                            logger.info(f"   Remaining capital: ${self.capital:,.2f}")

            # Check existing positions for exits
            for symbol in list(self.positions.keys()):
                trade = self.positions[symbol]

                # Get current bar
                symbol_bars = [b for b in bars_cache.get(symbol, []) if b.timestamp == current_time]
                if not symbol_bars:
                    continue

                current_bar = symbol_bars[0]
                current_price = float(current_bar.close)

                # Check stop loss
                if current_price <= trade.stop_loss:
                    trade.exit_time = current_time
                    trade.exit_price = trade.stop_loss
                    trade.pnl = (trade.exit_price - trade.entry_price) * trade.shares
                    trade.pnl_percent = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
                    trade.reason_exited = "Stop loss hit"

                    self.capital += trade.shares * trade.exit_price
                    self.closed_trades.append(trade)
                    del self.positions[symbol]

                    logger.info(f"🛑 STOP OUT: {symbol} @ ${trade.exit_price:.2f}")
                    logger.info(f"   P&L: ${trade.pnl:+,.2f} ({trade.pnl_percent:+.1f}%)")

                # Check profit target
                elif current_price >= trade.profit_target:
                    trade.exit_time = current_time
                    trade.exit_price = trade.profit_target
                    trade.pnl = (trade.exit_price - trade.entry_price) * trade.shares
                    trade.pnl_percent = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
                    trade.reason_exited = "Profit target hit"

                    self.capital += trade.shares * trade.exit_price
                    self.closed_trades.append(trade)
                    del self.positions[symbol]

                    logger.info(f"🎯 TARGET HIT: {symbol} @ ${trade.exit_price:.2f}")
                    logger.info(f"   P&L: ${trade.pnl:+,.2f} ({trade.pnl_percent:+.1f}%)")

            # Advance time
            current_time += scan_interval

        # Close remaining positions at EOD
        for symbol in list(self.positions.keys()):
            trade = self.positions[symbol]
            symbol_bars = bars_cache.get(symbol, [])
            if symbol_bars:
                final_bar = symbol_bars[-1]
                exit_price = float(final_bar.close)

                trade.exit_time = test_end
                trade.exit_price = exit_price
                trade.pnl = (exit_price - trade.entry_price) * trade.shares
                trade.pnl_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100
                trade.reason_exited = "End of day"

                self.capital += trade.shares * exit_price
                self.closed_trades.append(trade)

                logger.info(f"⏰ EOD CLOSE: {symbol} @ ${exit_price:.2f}")
                logger.info(f"   P&L: ${trade.pnl:+,.2f} ({trade.pnl_percent:+.1f}%)")

        self.positions.clear()

        logger.info("\n" + "=" * 80)
        logger.info("SIMPLE MOMENTUM BACKTEST COMPLETE")
        logger.info("=" * 80)

        # Calculate statistics
        total_pnl = sum(t.pnl for t in self.closed_trades)
        winning_trades = [t for t in self.closed_trades if t.pnl > 0]
        losing_trades = [t for t in self.closed_trades if t.pnl < 0]

        win_rate = (len(winning_trades) / len(self.closed_trades) * 100) if self.closed_trades else 0
        avg_win = (sum(t.pnl for t in winning_trades) / len(winning_trades)) if winning_trades else 0
        avg_loss = (sum(t.pnl for t in losing_trades) / len(losing_trades)) if losing_trades else 0

        logger.info(f"\nTotal Trades: {len(self.closed_trades)}")
        logger.info(f"Winners: {len(winning_trades)}, Losers: {len(losing_trades)}")
        logger.info(f"Win Rate: {win_rate:.1f}%")
        logger.info(f"Total P&L: ${total_pnl:+,.2f}")
        logger.info(f"Avg Win: ${avg_win:+,.2f}, Avg Loss: ${avg_loss:+,.2f}")
        logger.info(f"Final Capital: ${self.capital:,.2f}")
        logger.info(f"Return: {(total_pnl / self.starting_capital * 100):+.2f}%")

        # Show all trades
        if self.closed_trades:
            logger.info("\n📊 ALL TRADES:")
            for i, trade in enumerate(self.closed_trades, 1):
                logger.info(f"{i}. {trade.symbol}: ${trade.pnl:+,.2f} ({trade.pnl_percent:+.1f}%) - {trade.reason_exited}")
                logger.info(f"   Entry: {trade.entry_time.strftime('%H:%M')} @ ${trade.entry_price:.2f}")
                logger.info(f"   Exit:  {trade.exit_time.strftime('%H:%M')} @ ${trade.exit_price:.2f}")
                logger.info(f"   Score: {trade.scanner_score:.1f}, Vol: {trade.relative_volume:.1f}x")

        # Return results
        results = {
            "start_time": test_start.isoformat(),
            "end_time": test_end.isoformat(),
            "starting_capital": self.starting_capital,
            "ending_capital": self.capital,
            "total_return": total_pnl,
            "total_return_percent": (total_pnl / self.starting_capital) * 100,
            "total_trades": len(self.closed_trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "trades": [asdict(t) for t in self.closed_trades]
        }

        return results


def main():
    """Test simple momentum strategy."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    backtester = SimpleMomentumBacktester(api_key, secret_key)

    # Test 1 day
    start = datetime(2025, 8, 6)
    end = datetime(2025, 8, 6)

    results = backtester.run(start, end)

    print("\n📊 Results:")
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
