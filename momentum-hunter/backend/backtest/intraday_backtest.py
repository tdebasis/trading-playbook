"""
Intraday Backtester - Tests momentum strategy with 2-minute bars.

This replays historical intraday data (2-min candles) to simulate real-time trading.
It scans for momentum breakouts as they happen during market hours.

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime, timedelta, time as dt_time
from typing import Dict, List, Optional
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

from scanner.market_scanner import MomentumScanner, MomentumCandidate
from scanner.news_aggregator import NewsAggregator
from brain.claude_engine import ClaudeTrader, TradeDecision

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class IntradayTrade:
    """A single intraday trade."""
    symbol: str
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    shares: int = 0
    stop_loss: float = 0.0
    profit_target: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    reason_entered: str = ""
    reason_exited: str = ""


class IntradayBacktester:
    """
    Backtests momentum strategy using 2-minute intraday bars.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        anthropic_key: str,
        starting_capital: float = 100000
    ):
        """
        Initialize intraday backtester.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            anthropic_key: Anthropic API key for Claude
            starting_capital: Starting account value
        """
        self.data_client = StockHistoricalDataClient(api_key, secret_key)
        self.scanner = MomentumScanner(api_key, secret_key)
        self.news = NewsAggregator(api_key, secret_key)
        self.claude = ClaudeTrader(anthropic_key, starting_capital)

        self.starting_capital = starting_capital
        self.capital = starting_capital
        self.positions: Dict[str, IntradayTrade] = {}
        self.closed_trades: List[IntradayTrade] = []

        # Risk management
        self.max_positions = 3
        self.max_position_size_percent = 0.25  # 25% of account per position

        logger.info(f"Intraday Backtester initialized (${starting_capital:,.0f})")

    def get_intraday_bars(
        self,
        symbols: List[str],
        start: datetime,
        end: datetime
    ) -> Dict[str, List]:
        """
        Fetch 2-minute bars for symbols over a date range.

        Args:
            symbols: List of stock symbols
            start: Start datetime
            end: End datetime

        Returns:
            Dict mapping symbol -> list of 2-min bars
        """
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=TimeFrame.Minute,  # 1-minute bars
                start=start,
                end=end
            )

            bars = self.data_client.get_stock_bars(request)

            # Group into 2-minute bars (aggregate every 2 candles)
            result = {}
            for symbol in symbols:
                if symbol in bars.data:
                    raw_bars = bars.data[symbol]
                    # For now, use 1-min bars directly (can aggregate to 2-min later)
                    result[symbol] = raw_bars

            return result

        except Exception as e:
            logger.error(f"Error fetching intraday bars: {e}")
            return {}

    def scan_for_breakouts(
        self,
        current_time: datetime,
        bars_cache: Dict[str, List]
    ) -> tuple[List[MomentumCandidate], Dict[str, float]]:
        """
        Scan for momentum breakouts at current time using ONLY completed bars.
        Returns candidates and their NEXT bar open prices for realistic entry.

        Args:
            current_time: Current simulation time (a bar just closed)
            bars_cache: Pre-fetched intraday bars

        Returns:
            Tuple of (candidates, next_bar_prices) where next_bar_prices has entry prices
        """
        candidates = []
        next_bar_prices = {}

        # For each symbol, check if it's breaking out
        for symbol, bars in bars_cache.items():
            # Get ONLY completed bars (bars that closed BEFORE current_time)
            # We cannot see the current bar's close yet!
            completed_bars = [b for b in bars if b.timestamp < current_time]
            if len(completed_bars) < 20:  # Need history for volume comparison
                continue

            # The most recent COMPLETED bar (this just closed)
            last_completed_bar = completed_bars[-1]
            recent_bars = completed_bars[-20:]

            # Find the NEXT bar (the one forming now) - this is where we'd actually enter
            next_bars = [b for b in bars if b.timestamp >= current_time]
            if not next_bars:
                continue
            next_bar = next_bars[0]  # The bar that's starting now
            entry_price = float(next_bar.open)  # We enter at next bar's OPEN

            # Calculate average volume from completed bars
            avg_volume = sum(b.volume for b in recent_bars[:-1]) / (len(recent_bars) - 1)

            # Check for volume spike in the LAST COMPLETED bar
            relative_volume = last_completed_bar.volume / avg_volume if avg_volume > 0 else 0

            if relative_volume < 2.0:  # Need 2x volume minimum
                continue

            # Calculate price change from session open to last completed bar close
            session_open = completed_bars[0].open if completed_bars else last_completed_bar.open
            percent_change = ((last_completed_bar.close - session_open) / session_open) * 100

            if abs(percent_change) < 3.0:  # Need 3% move minimum
                continue

            # This is a candidate! Use the last completed bar's close as "current price"
            candidate = MomentumCandidate(
                symbol=symbol,
                current_price=float(last_completed_bar.close),  # Last known price
                volume=int(last_completed_bar.volume),
                relative_volume=relative_volume,
                percent_change=percent_change,
                gap_percent=0.0,  # Calculate from previous day close if needed
                float_shares=None,
                market_cap=None,
                detected_at=current_time,
                price_vs_vwap=0.0,  # Can calculate if needed
                volume_spike_magnitude=int(relative_volume)
            )

            candidates.append(candidate)
            next_bar_prices[symbol] = entry_price  # Where we'd actually enter

            logger.info(f"🔥 Breakout detected: {symbol} @ ${last_completed_bar.close:.2f}")
            logger.info(f"   Entry would be next bar open: ${entry_price:.2f}")

        return candidates, next_bar_prices

    def run(
        self,
        start_date: datetime,
        end_date: datetime,
        test_symbols: List[str] = None
    ) -> Dict:
        """
        Run intraday backtest.

        Args:
            start_date: Start date
            end_date: End date
            test_symbols: List of symbols to test (if None, use scanner universe)

        Returns:
            Backtest results dictionary
        """
        logger.info("=" * 80)
        logger.info("STARTING INTRADAY BACKTEST (2-MIN BARS)")
        logger.info("=" * 80)
        logger.info(f"Period: {start_date.date()} to {end_date.date()}")
        logger.info(f"Starting Capital: ${self.starting_capital:,.0f}")
        logger.info("=" * 80)
        logger.info("")

        # Use smaller universe for testing
        if test_symbols is None:
            test_symbols = ['NVDA', 'TSLA', 'NVAX', 'SNAP', 'PTON']  # High-volume movers

        # For MVP: Test just ONE DAY first
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/New_York")
        test_start = datetime(2025, 8, 6, 9, 30, tzinfo=tz)  # Aug 6, market open
        test_end = datetime(2025, 8, 6, 16, 0, tzinfo=tz)   # Aug 6, market close

        logger.info(f"Testing 1 day: {test_start.date()}")
        logger.info(f"Symbols: {', '.join(test_symbols)}")
        logger.info("")

        # Fetch all intraday bars for the day
        logger.info("Fetching intraday bars...")
        bars_cache = self.get_intraday_bars(test_symbols, test_start, test_end)
        logger.info(f"Fetched bars for {len(bars_cache)} symbols")
        logger.info("")

        # Replay minute-by-minute
        current_time = test_start
        scan_interval = timedelta(minutes=2)  # Scan every 2 minutes
        decision_count = 0  # DEBUG: Count Claude decisions

        while current_time <= test_end:
            # Scan for breakouts (only on completed bars)
            candidates, next_bar_prices = self.scan_for_breakouts(current_time, bars_cache)

            if candidates:
                logger.info(f"\n⏰ {current_time.strftime('%H:%M')} - Found {len(candidates)} breakout(s)")

                # Get news for candidates
                catalysts = {}
                for candidate in candidates:
                    catalyst = self.news.analyze_catalyst(candidate.symbol)
                    if catalyst:
                        catalysts[candidate.symbol] = catalyst

                # Ask Claude to decide
                decision = self.claude.make_decision(candidates, catalysts)
                decision_count += 1

                # DEBUG: Stop after 3 decisions to see reasoning
                if decision_count >= 3:
                    logger.info("\\n⚠️  DEBUG MODE: Stopping after 3 decisions to review Claude's reasoning")
                    break

                if decision.action == "BUY" and decision.symbol:
                    # Use the realistic entry price (next bar open)
                    realistic_entry = next_bar_prices.get(decision.symbol, decision.entry_price)

                    logger.info(f"🎯 Claude wants to BUY {decision.symbol}!")
                    logger.info(f"   Detection price: ${decision.entry_price:.2f}")
                    logger.info(f"   Actual entry (next bar open): ${realistic_entry:.2f}")
                    logger.info(f"   Slippage: ${realistic_entry - decision.entry_price:+.2f}")
                    logger.info(f"   Stop: ${decision.stop_loss:.2f}, Target: ${decision.profit_target:.2f}")
                    logger.info(f"   Reasoning: {decision.reasoning[:100]}...")

                    # Calculate position size
                    if len(self.positions) < self.max_positions:
                        risk_per_trade = self.capital * 0.02  # 2% risk
                        stop_distance = abs(realistic_entry - decision.stop_loss)
                        shares = int(risk_per_trade / stop_distance) if stop_distance > 0 else 0

                        max_shares = int((self.capital * self.max_position_size_percent) / realistic_entry)
                        shares = min(shares, max_shares)

                        if shares > 0:
                            # Open position
                            trade = IntradayTrade(
                                symbol=decision.symbol,
                                entry_time=current_time,
                                entry_price=realistic_entry,
                                shares=shares,
                                stop_loss=decision.stop_loss,
                                profit_target=decision.profit_target,
                                reason_entered=decision.reasoning[:200]
                            )
                            self.positions[decision.symbol] = trade
                            self.capital -= shares * realistic_entry

                            logger.info(f"✅ Entered {shares} shares @ ${realistic_entry:.2f}")
                            logger.info(f"   Position value: ${shares * realistic_entry:,.2f}")
                            logger.info(f"   Remaining capital: ${self.capital:,.2f}")

            # Check existing positions for exits
            for symbol in list(self.positions.keys()):
                trade = self.positions[symbol]

                # Get current bar for this symbol
                symbol_bars = [b for b in bars_cache.get(symbol, []) if b.timestamp == current_time]
                if not symbol_bars:
                    continue

                current_bar = symbol_bars[0]
                current_price = float(current_bar.close)

                # Check stop loss
                if current_price <= trade.stop_loss:
                    # Stopped out
                    trade.exit_time = current_time
                    trade.exit_price = trade.stop_loss  # Assume we got stopped at stop price
                    trade.pnl = (trade.exit_price - trade.entry_price) * trade.shares
                    trade.pnl_percent = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
                    trade.reason_exited = "Stop loss hit"

                    self.capital += trade.shares * trade.exit_price
                    self.closed_trades.append(trade)
                    del self.positions[symbol]

                    logger.info(f"🛑 Stopped out: {symbol} @ ${trade.exit_price:.2f}")
                    logger.info(f"   P&L: ${trade.pnl:+,.2f} ({trade.pnl_percent:+.1f}%)")

                # Check profit target
                elif current_price >= trade.profit_target:
                    # Target hit
                    trade.exit_time = current_time
                    trade.exit_price = trade.profit_target
                    trade.pnl = (trade.exit_price - trade.entry_price) * trade.shares
                    trade.pnl_percent = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
                    trade.reason_exited = "Profit target hit"

                    self.capital += trade.shares * trade.exit_price
                    self.closed_trades.append(trade)
                    del self.positions[symbol]

                    logger.info(f"🎯 Target hit: {symbol} @ ${trade.exit_price:.2f}")
                    logger.info(f"   P&L: ${trade.pnl:+,.2f} ({trade.pnl_percent:+.1f}%)")

            # Advance time
            current_time += scan_interval

        # Close any remaining positions at end of day
        for symbol in list(self.positions.keys()):
            trade = self.positions[symbol]
            # Get final bar
            symbol_bars = bars_cache.get(symbol, [])
            if symbol_bars:
                final_bar = symbol_bars[-1]
                exit_price = float(final_bar.close)

                trade.exit_time = test_end
                trade.exit_price = exit_price
                trade.pnl = (exit_price - trade.entry_price) * trade.shares
                trade.pnl_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100
                trade.reason_exited = "End of day - position closed"

                self.capital += trade.shares * exit_price
                self.closed_trades.append(trade)

                logger.info(f"⏰ EOD close: {symbol} @ ${exit_price:.2f}")
                logger.info(f"   P&L: ${trade.pnl:+,.2f} ({trade.pnl_percent:+.1f}%)")

        self.positions.clear()

        logger.info("\n" + "=" * 80)
        logger.info("INTRADAY BACKTEST COMPLETE")
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

        # Calculate results
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
    """Test the intraday backtester."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    backtester = IntradayBacktester(api_key, secret_key, anthropic_key)

    # Test 1 day first
    start = datetime(2025, 8, 6)
    end = datetime(2025, 8, 6)

    results = backtester.run(start, end)

    print("\n📊 Results:")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
