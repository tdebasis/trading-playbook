"""
Daily Momentum Backtester - Swing Trading Style

Tests daily breakout strategy with:
- Multi-day holds (not intraday)
- 8% stop loss, 20% profit target
- Max 3 positions at once
- Position sizing: 25-33% of capital per trade

This is the Minervini/O'Neil approach that actually works.

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import logging
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from scanner.long.daily_breakout_scanner import DailyBreakoutScanner, DailyBreakoutCandidate
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

logger = logging.getLogger(__name__)


@dataclass
class DailyPosition:
    """A swing trade position held for multiple days."""
    symbol: str
    entry_date: datetime
    entry_price: float
    shares: int
    stop_loss: float
    profit_target: float

    # Exit info (filled when position closes)
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None  # "STOP", "TARGET", "EOW" (end of week)

    def position_value(self, current_price: float) -> float:
        """Current value of position."""
        return self.shares * current_price

    def unrealized_pnl(self, current_price: float) -> float:
        """Unrealized P&L."""
        return (current_price - self.entry_price) * self.shares

    def realized_pnl(self) -> float:
        """Realized P&L (after exit)."""
        if self.exit_price is None:
            return 0.0
        return (self.exit_price - self.entry_price) * self.shares

    def hold_days(self, current_date: datetime) -> int:
        """Days held."""
        end_date = self.exit_date or current_date
        return (end_date - self.entry_date).days


@dataclass
class DailyBacktestResults:
    """Results from daily momentum backtest."""
    starting_capital: float
    ending_capital: float
    total_return: float
    total_return_percent: float

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown_percent: float

    trades: List[Dict] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    daily_pnl: List[Dict] = field(default_factory=list)


class DailyMomentumBacktester:
    """
    Backtester for daily breakout strategy.

    Strategy:
    - Scan for breakouts each day
    - Enter on close (or next day open with gap handling)
    - Hold for multiple days (not intraday exits)
    - Exit on: Stop loss (8%), Profit target (20%), or time stop (10 days max)
    - Max 3 positions at once
    """

    def __init__(self, api_key: str, secret_key: str, starting_capital: float = 100000):
        self.scanner = DailyBreakoutScanner(api_key, secret_key)
        self.data_client = StockHistoricalDataClient(api_key, secret_key)

        # Capital
        self.starting_capital = starting_capital
        self.capital = starting_capital

        # Risk management
        self.stop_loss_percent = 0.08  # 8% stop (wider than intraday)
        self.profit_target_percent = 0.20  # 20% target (2.5:1 R/R)
        self.max_hold_days = 10  # Max 10 days per trade
        self.max_positions = 3
        self.position_size_percent = 0.30  # 30% of capital per trade

        # Tracking
        self.positions: List[DailyPosition] = []
        self.closed_trades: List[DailyPosition] = []
        self.equity_curve = [starting_capital]
        self.peak_capital = starting_capital

    def run(self, start_date: datetime, end_date: datetime) -> DailyBacktestResults:
        """
        Run backtest over date range.

        Args:
            start_date: Start of backtest
            end_date: End of backtest

        Returns:
            DailyBacktestResults with all metrics
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"DAILY MOMENTUM BACKTEST")
        logger.info(f"{'='*80}")
        logger.info(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"Starting Capital: ${self.starting_capital:,.2f}")
        logger.info(f"Strategy: Daily breakouts, 8% stops, 20% targets")
        logger.info(f"{'='*80}\n")

        # Get all trading days
        trading_days = self._get_trading_days(start_date, end_date)

        logger.info(f"Found {len(trading_days)} trading days to test\n")

        # Run day by day
        for current_date in trading_days:
            self._process_trading_day(current_date)

        # Close all remaining positions at end
        if self.positions:
            logger.info(f"\nClosing {len(self.positions)} remaining positions at backtest end...")
            for pos in list(self.positions):
                self._close_position(pos, end_date, "END_OF_TEST")

        # Calculate results
        return self._calculate_results()

    def _process_trading_day(self, date: datetime):
        """Process a single trading day."""
        logger.info(f"\n{'='*80}")
        logger.info(f"DAY: {date.strftime('%Y-%m-%d (%A)')}")
        logger.info(f"Capital: ${self.capital:,.2f} | Positions: {len(self.positions)}")
        logger.info(f"{'='*80}")

        # 1. Check existing positions for exits
        self._check_exits(date)

        # 2. Scan for new opportunities
        if len(self.positions) < self.max_positions:
            self._scan_and_enter(date)

        # 3. Update equity curve
        current_equity = self._calculate_current_equity(date)
        self.equity_curve.append(current_equity)

        # Log daily summary
        day_pnl = current_equity - self.equity_curve[-2] if len(self.equity_curve) > 1 else 0
        logger.info(f"\nDay Summary:")
        logger.info(f"  Equity: ${current_equity:,.2f} ({day_pnl:+,.2f})")
        logger.info(f"  Positions: {len(self.positions)}")
        if self.positions:
            for pos in self.positions:
                unrealized = pos.unrealized_pnl(self._get_current_price(pos.symbol, date))
                logger.info(f"    {pos.symbol}: ${pos.entry_price:.2f} → {unrealized:+,.0f} ({pos.hold_days(date)} days)")

    def _check_exits(self, date: datetime):
        """Check if any positions should be closed."""
        for position in list(self.positions):
            # Get current price
            current_price = self._get_current_price(position.symbol, date)
            if current_price is None:
                continue

            # Check stop loss
            if current_price <= position.stop_loss:
                logger.info(f"  🛑 {position.symbol}: Stop hit at ${current_price:.2f} (stop: ${position.stop_loss:.2f})")
                self._close_position(position, date, "STOP", current_price)
                continue

            # Check profit target
            if current_price >= position.profit_target:
                logger.info(f"  🎯 {position.symbol}: Target hit at ${current_price:.2f} (target: ${position.profit_target:.2f})")
                self._close_position(position, date, "TARGET", current_price)
                continue

            # Check time stop
            if position.hold_days(date) >= self.max_hold_days:
                logger.info(f"  ⏰ {position.symbol}: Time stop at ${current_price:.2f} (held {self.max_hold_days} days)")
                self._close_position(position, date, "TIME", current_price)
                continue

    def _scan_and_enter(self, date: datetime):
        """Scan for breakouts and enter new positions."""
        # Scan for candidates
        candidates = self.scanner.scan(date)

        if not candidates:
            logger.info("  No breakout candidates found")
            return

        # Filter out symbols we're already holding
        held_symbols = {pos.symbol for pos in self.positions}
        candidates = [c for c in candidates if c.symbol not in held_symbols]

        if not candidates:
            logger.info("  All candidates already held")
            return

        # Take best candidates (sorted by score)
        slots_available = self.max_positions - len(self.positions)
        top_candidates = candidates[:slots_available]

        for candidate in top_candidates:
            # Enter position
            entry_price = candidate.close  # Buy at close (or next open)
            position_value = self.capital * self.position_size_percent
            shares = int(position_value / entry_price)

            if shares == 0:
                logger.info(f"  ⚠️  {candidate.symbol}: Insufficient capital for 1 share")
                continue

            # Create position
            position = DailyPosition(
                symbol=candidate.symbol,
                entry_date=date,
                entry_price=entry_price,
                shares=shares,
                stop_loss=entry_price * (1 - self.stop_loss_percent),
                profit_target=entry_price * (1 + self.profit_target_percent)
            )

            self.positions.append(position)

            # Reduce available capital
            self.capital -= shares * entry_price

            logger.info(f"  ✅ ENTER {candidate.symbol}: {shares} shares @ ${entry_price:.2f}")
            logger.info(f"     Stop: ${position.stop_loss:.2f} | Target: ${position.profit_target:.2f}")
            logger.info(f"     Score: {candidate.score():.1f}/10 | Risk: ${shares * entry_price * self.stop_loss_percent:,.0f}")

    def _close_position(self, position: DailyPosition, date: datetime, reason: str, price: Optional[float] = None):
        """Close a position."""
        exit_price = price or self._get_current_price(position.symbol, date)

        if exit_price is None:
            logger.warning(f"  ⚠️  Cannot close {position.symbol}: No price data")
            return

        position.exit_date = date
        position.exit_price = exit_price
        position.exit_reason = reason

        # Calculate P&L
        pnl = position.realized_pnl()
        pnl_pct = (pnl / (position.entry_price * position.shares)) * 100

        # Return capital
        self.capital += position.shares * exit_price

        # Move to closed trades
        self.positions.remove(position)
        self.closed_trades.append(position)

        emoji = "✅" if pnl > 0 else "❌"
        logger.info(f"  {emoji} CLOSE {position.symbol}: ${exit_price:.2f} | P&L: {pnl:+,.0f} ({pnl_pct:+.1f}%) | {reason}")

    def _get_current_price(self, symbol: str, date: datetime) -> Optional[float]:
        """Get close price for symbol on given date."""
        try:
            start = date - timedelta(days=5)  # Look back a few days in case of holidays
            request = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Day,
                start=start,
                end=date
            )
            bars_response = self.data_client.get_stock_bars(request)

            if symbol in bars_response.data and bars_response.data[symbol]:
                bars = list(bars_response.data[symbol])
                # Get most recent bar (should be scan_date)
                return float(bars[-1].close)
        except Exception as e:
            logger.warning(f"Error getting price for {symbol} on {date}: {e}")

        return None

    def _calculate_current_equity(self, date: datetime) -> float:
        """Calculate total equity (cash + positions)."""
        equity = self.capital

        for position in self.positions:
            current_price = self._get_current_price(position.symbol, date)
            if current_price:
                equity += position.position_value(current_price)

        return equity

    def _get_trading_days(self, start: datetime, end: datetime) -> List[datetime]:
        """Get list of trading days (weekdays, no holidays for now)."""
        days = []
        current = start

        while current <= end:
            if current.weekday() < 5:  # Monday-Friday
                days.append(current)
            current += timedelta(days=1)

        return days

    def _calculate_results(self) -> DailyBacktestResults:
        """Calculate final backtest results."""
        ending_capital = self.capital
        total_return = ending_capital - self.starting_capital
        total_return_pct = (total_return / self.starting_capital) * 100

        # Trade statistics
        winners = [t for t in self.closed_trades if t.realized_pnl() > 0]
        losers = [t for t in self.closed_trades if t.realized_pnl() < 0]

        win_rate = (len(winners) / len(self.closed_trades) * 100) if self.closed_trades else 0
        avg_win = (sum(t.realized_pnl() for t in winners) / len(winners)) if winners else 0
        avg_loss = (sum(t.realized_pnl() for t in losers) / len(losers)) if losers else 0

        # Profit factor
        total_wins = sum(t.realized_pnl() for t in winners)
        total_losses = abs(sum(t.realized_pnl() for t in losers))
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0

        # Max drawdown
        peak = self.starting_capital
        max_dd = 0
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = ((peak - equity) / peak) * 100
            if dd > max_dd:
                max_dd = dd

        # Trade list
        trades = []
        for t in self.closed_trades:
            trades.append({
                'symbol': t.symbol,
                'entry_date': t.entry_date.strftime('%Y-%m-%d'),
                'exit_date': t.exit_date.strftime('%Y-%m-%d') if t.exit_date else None,
                'entry_price': float(t.entry_price),
                'exit_price': float(t.exit_price) if t.exit_price else None,
                'shares': t.shares,
                'pnl': float(t.realized_pnl()),
                'pnl_pct': float((t.realized_pnl() / (t.entry_price * t.shares)) * 100),
                'hold_days': t.hold_days(t.exit_date) if t.exit_date else 0,
                'exit_reason': t.exit_reason
            })

        return DailyBacktestResults(
            starting_capital=self.starting_capital,
            ending_capital=ending_capital,
            total_return=total_return,
            total_return_percent=total_return_pct,
            total_trades=len(self.closed_trades),
            winning_trades=len(winners),
            losing_trades=len(losers),
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown_percent=max_dd,
            trades=trades,
            equity_curve=self.equity_curve
        )


if __name__ == "__main__":
    # Test the backtester
    import os
    from dotenv import load_dotenv

    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    backtester = DailyMomentumBacktester(api_key, secret_key, starting_capital=100000)

    # Test on 1 week first
    start = datetime(2025, 8, 1)
    end = datetime(2025, 8, 8)

    results = backtester.run(start, end)

    print(f"\n{'='*80}")
    print("BACKTEST RESULTS")
    print(f"{'='*80}\n")
    print(f"Starting Capital: ${results.starting_capital:,.2f}")
    print(f"Ending Capital: ${results.ending_capital:,.2f}")
    print(f"Total Return: ${results.total_return:+,.2f} ({results.total_return_percent:+.2f}%)")
    print(f"\nTrades: {results.total_trades}")
    print(f"Winners: {results.winning_trades} ({results.win_rate:.1f}%)")
    print(f"Losers: {results.losing_trades}")
    print(f"Avg Win: ${results.avg_win:+,.2f}")
    print(f"Avg Loss: ${results.avg_loss:+,.2f}")
    print(f"Profit Factor: {results.profit_factor:.2f}x")
    print(f"Max Drawdown: {results.max_drawdown_percent:.2f}%")
