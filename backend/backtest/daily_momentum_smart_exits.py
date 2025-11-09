"""
Daily Momentum Backtester - SMART EXITS (Price Action Based)

Instead of fixed 20% target, exits based on:
1. Trailing stop (2x ATR below highest high)
2. Close below 5-day MA (trend broken)
3. Lower high pattern (momentum weakening)
4. Hard stop at -8% (risk management)

This is how professionals actually exit trades.

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import logging
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from scanner.long.daily_breakout_scanner import DailyBreakoutScanner
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

logger = logging.getLogger(__name__)


@dataclass
class SmartPosition:
    """Position with smart exit tracking."""
    symbol: str
    entry_date: datetime
    entry_price: float
    shares: int
    hard_stop: float  # 8% hard stop

    # Smart exit tracking (close-based, no lookahead bias)
    highest_close: float = 0.0  # Track highest CLOSE, not intraday high
    trailing_stop: float = 0.0
    prev_close: float = 0.0  # For momentum detection
    sma_5: List[float] = field(default_factory=list)

    # Exit info
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None

    def position_value(self, current_price: float) -> float:
        return self.shares * current_price

    def unrealized_pnl(self, current_price: float) -> float:
        return (current_price - self.entry_price) * self.shares

    def realized_pnl(self) -> float:
        if self.exit_price is None:
            return 0.0
        return (self.exit_price - self.entry_price) * self.shares

    def hold_days(self, current_date: datetime) -> int:
        end_date = self.exit_date or current_date
        return (end_date - self.entry_date).days


class SmartExitBacktester:
    """
    Backtester with smart exits based on price action.

    Exit Triggers:
    1. Trailing stop (2x ATR below highest high) - locks in profits
    2. Close below 5-day MA - trend broken
    3. Lower high (after hitting +5%) - momentum weakening
    4. Hard stop at -8% - risk management
    """

    def __init__(self, api_key: str, secret_key: str, starting_capital: float = 100000):
        self.scanner = DailyBreakoutScanner(api_key, secret_key)
        self.data_client = StockHistoricalDataClient(api_key, secret_key)

        self.starting_capital = starting_capital
        self.capital = starting_capital

        # Risk management
        self.stop_loss_percent = 0.08  # 8% hard stop
        self.trailing_atr_multiplier = 2.0  # Trail 2x ATR below high
        self.max_positions = 3
        self.position_size_percent = 0.30

        # Tracking
        self.positions: List[SmartPosition] = []
        self.closed_trades: List[SmartPosition] = []
        self.equity_curve = [starting_capital]
        self.peak_capital = starting_capital

    def run(self, start_date: datetime, end_date: datetime):
        """Run backtest with smart exits."""

        logger.info(f"\n{'='*80}")
        logger.info(f"DAILY MOMENTUM BACKTEST - SMART EXITS")
        logger.info(f"{'='*80}")
        logger.info(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"Starting Capital: ${self.starting_capital:,.2f}")
        logger.info(f"Exit Strategy: Price action based (trailing stops, MA breaks, momentum)")
        logger.info(f"{'='*80}\n")

        trading_days = self._get_trading_days(start_date, end_date)
        logger.info(f"Found {len(trading_days)} trading days to test\n")

        for current_date in trading_days:
            self._process_trading_day(current_date)

        # Close remaining positions
        if self.positions:
            logger.info(f"\nClosing {len(self.positions)} remaining positions...")
            for pos in list(self.positions):
                self._close_position(pos, end_date, "END_OF_TEST")

        return self._calculate_results()

    def _process_trading_day(self, date: datetime):
        """Process a single trading day with smart exits."""
        logger.info(f"\n{'='*80}")
        logger.info(f"DAY: {date.strftime('%Y-%m-%d (%A)')}")
        logger.info(f"Capital: ${self.capital:,.2f} | Positions: {len(self.positions)}")
        logger.info(f"{'='*80}")

        # 1. Check exits for existing positions (SMART LOGIC)
        self._check_smart_exits(date)

        # 2. Scan for new entries
        if len(self.positions) < self.max_positions:
            self._scan_and_enter(date)

        # 3. Update equity curve
        current_equity = self._calculate_current_equity(date)
        self.equity_curve.append(current_equity)

        # 4. Log summary
        day_pnl = current_equity - self.equity_curve[-2] if len(self.equity_curve) > 1 else 0
        logger.info(f"\nDay Summary:")
        logger.info(f"  Equity: ${current_equity:,.2f} ({day_pnl:+,.2f})")
        logger.info(f"  Positions: {len(self.positions)}")

        if self.positions:
            for pos in self.positions:
                current_price = self._get_current_price(pos.symbol, date)
                if current_price:
                    unrealized = pos.unrealized_pnl(current_price)
                    pct = (unrealized / (pos.entry_price * pos.shares)) * 100
                    logger.info(f"    {pos.symbol}: ${pos.entry_price:.2f} → ${current_price:.2f} ({pct:+.1f}%, {pos.hold_days(date)} days)")

    def _check_smart_exits(self, date: datetime):
        """Check all positions for smart exit signals."""

        for position in list(self.positions):
            # Get price data
            bars = self._get_recent_bars(position.symbol, date, lookback=10)
            if not bars or len(bars) == 0:
                continue

            current_bar = bars[-1]
            current_close = float(current_bar.close)
            current_low = float(current_bar.low)  # Still use for hard stop check

            # Calculate ATR (Average True Range) for trailing stop
            atr = self._calculate_atr(bars, period=10)

            # Update highest CLOSE (not high - no lookahead bias)
            if current_close > position.highest_close:
                position.highest_close = current_close

                # HYBRID TRAILING: Tighten stop as profit increases
                profit_pct = ((position.highest_close - position.entry_price) / position.entry_price) * 100

                if profit_pct >= 15:
                    # +15%+: Very tight trail (5% from peak close)
                    position.trailing_stop = position.highest_close * 0.95
                elif profit_pct >= 10:
                    # +10-15%: Tighter trail (1x ATR)
                    position.trailing_stop = position.highest_close - (atr * 1.0)
                else:
                    # 0-10%: Normal trail (2x ATR)
                    position.trailing_stop = position.highest_close - (atr * 2.0)

            # Calculate 5-day MA
            if len(bars) >= 5:
                sma_5 = sum(float(b.close) for b in bars[-5:]) / 5
            else:
                sma_5 = current_close

            # EXIT LOGIC (in priority order)

            # 1. HARD STOP (always active) - use intraday low for hard stops
            if current_low <= position.hard_stop:
                logger.info(f"  🛑 {position.symbol}: Hard stop at ${current_low:.2f} (stop: ${position.hard_stop:.2f})")
                self._close_position(position, date, "HARD_STOP", position.hard_stop)
                continue

            # 2. TRAILING STOP (after we've established profit) - use CLOSE not low
            if position.highest_close > position.entry_price * 1.05:  # At least 5% up
                if current_close < position.trailing_stop:  # Close breaks trail, not intraday low
                    logger.info(f"  📉 {position.symbol}: Trailing stop - close ${current_close:.2f} < trail ${position.trailing_stop:.2f}")
                    self._close_position(position, date, "TRAILING_STOP", current_close)  # Exit at close
                    continue

            # 3. TREND BREAK (close below 5-day MA - but only if current profit < 3%)
            # Logic: If we're up 3%+ NOW, let trailing stop handle it
            # Only use MA break to cut small losses/gains before they become bigger losses
            current_profit_pct = ((current_close - position.entry_price) / position.entry_price) * 100
            if current_profit_pct < 3.0:  # Less than +3% profit right now
                if current_close < sma_5:
                    logger.info(f"  📊 {position.symbol}: Broke 5-day MA at ${current_close:.2f} (MA: ${sma_5:.2f}, +{current_profit_pct:.1f}%)")
                    self._close_position(position, date, "MA_BREAK", current_close)
                    continue

            # 4. LOWER CLOSE (momentum weakening after 5%+ gain)
            if position.highest_close > position.entry_price * 1.05:  # At least 5% up
                if position.prev_close > 0 and current_close < position.prev_close:
                    # Stock made a lower close - momentum fading
                    logger.info(f"  ⚠️  {position.symbol}: Lower close at ${current_close:.2f} (prev: ${position.prev_close:.2f})")
                    self._close_position(position, date, "LOWER_HIGH", current_close)
                    continue

            # 5. TIME STOP (backup, 17 days max)
            if position.hold_days(date) >= 17:
                logger.info(f"  ⏰ {position.symbol}: Time stop at ${current_close:.2f} (held 17 days)")
                self._close_position(position, date, "TIME", current_close)
                continue

            # Update for next day
            position.prev_close = current_close

    def _calculate_atr(self, bars: list, period: int = 10) -> float:
        """Calculate Average True Range."""
        if len(bars) < period + 1:
            return 0.0

        true_ranges = []
        for i in range(1, len(bars)):
            high = float(bars[i].high)
            low = float(bars[i].low)
            prev_close = float(bars[i-1].close)

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        return sum(true_ranges[-period:]) / period if true_ranges else 0.0

    def _get_recent_bars(self, symbol: str, date: datetime, lookback: int = 10):
        """Get recent bars for a symbol."""
        try:
            start = date - timedelta(days=lookback + 5)
            request = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Day,
                start=start,
                end=date
            )
            response = self.data_client.get_stock_bars(request)

            if symbol in response.data and response.data[symbol]:
                return list(response.data[symbol])
        except Exception as e:
            logger.warning(f"Error getting bars for {symbol}: {e}")

        return []

    def _scan_and_enter(self, date: datetime):
        """Scan and enter new positions."""
        candidates = self.scanner.scan(date)

        if not candidates:
            logger.info("  No breakout candidates found")
            return

        held_symbols = {pos.symbol for pos in self.positions}
        candidates = [c for c in candidates if c.symbol not in held_symbols]

        if not candidates:
            logger.info("  All candidates already held")
            return

        slots_available = self.max_positions - len(self.positions)
        for candidate in candidates[:slots_available]:
            entry_price = candidate.close
            position_value = self.capital * self.position_size_percent
            shares = int(position_value / entry_price)

            if shares == 0:
                logger.info(f"  ⚠️  {candidate.symbol}: Insufficient capital")
                continue

            position = SmartPosition(
                symbol=candidate.symbol,
                entry_date=date,
                entry_price=entry_price,
                shares=shares,
                hard_stop=entry_price * (1 - self.stop_loss_percent),
                highest_close=entry_price,  # Start with entry price as highest close
                trailing_stop=entry_price * (1 - self.stop_loss_percent),
                prev_close=entry_price
            )

            self.positions.append(position)
            self.capital -= shares * entry_price

            logger.info(f"  ✅ ENTER {candidate.symbol}: {shares} shares @ ${entry_price:.2f}")
            logger.info(f"     Hard Stop: ${position.hard_stop:.2f}")
            logger.info(f"     Score: {candidate.score():.1f}/10")

    def _close_position(self, position: SmartPosition, date: datetime, reason: str, price: Optional[float] = None):
        """Close a position."""
        exit_price = price or self._get_current_price(position.symbol, date)

        if exit_price is None:
            logger.warning(f"  ⚠️  Cannot close {position.symbol}: No price data")
            return

        position.exit_date = date
        position.exit_price = exit_price
        position.exit_reason = reason

        pnl = position.realized_pnl()
        pnl_pct = (pnl / (position.entry_price * position.shares)) * 100

        self.capital += position.shares * exit_price

        self.positions.remove(position)
        self.closed_trades.append(position)

        emoji = "✅" if pnl > 0 else "❌"
        logger.info(f"  {emoji} CLOSE {position.symbol}: ${exit_price:.2f} | P&L: {pnl:+,.0f} ({pnl_pct:+.1f}%) | {reason}")

    def _get_current_price(self, symbol: str, date: datetime) -> Optional[float]:
        """Get close price for symbol."""
        bars = self._get_recent_bars(symbol, date, lookback=3)
        if bars:
            return float(bars[-1].close)
        return None

    def _calculate_current_equity(self, date: datetime) -> float:
        """Calculate total equity."""
        equity = self.capital

        for position in self.positions:
            current_price = self._get_current_price(position.symbol, date)
            if current_price:
                equity += position.position_value(current_price)

        return equity

    def _get_trading_days(self, start: datetime, end: datetime) -> List[datetime]:
        """Get trading days."""
        days = []
        current = start

        while current <= end:
            if current.weekday() < 5:
                days.append(current)
            current += timedelta(days=1)

        return days

    def _calculate_results(self):
        """Calculate backtest results."""
        ending_capital = self.capital
        total_return = ending_capital - self.starting_capital
        total_return_pct = (total_return / self.starting_capital) * 100

        winners = [t for t in self.closed_trades if t.realized_pnl() > 0]
        losers = [t for t in self.closed_trades if t.realized_pnl() < 0]

        win_rate = (len(winners) / len(self.closed_trades) * 100) if self.closed_trades else 0
        avg_win = (sum(t.realized_pnl() for t in winners) / len(winners)) if winners else 0
        avg_loss = (sum(t.realized_pnl() for t in losers) / len(losers)) if losers else 0

        total_wins = sum(t.realized_pnl() for t in winners)
        total_losses = abs(sum(t.realized_pnl() for t in losers))
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0

        peak = self.starting_capital
        max_dd = 0
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = ((peak - equity) / peak) * 100
            if dd > max_dd:
                max_dd = dd

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

        from backtest.daily_momentum_backtest import DailyBacktestResults
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
