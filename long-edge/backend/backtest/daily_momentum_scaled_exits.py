"""
Daily Momentum Backtester - SCALED EXITS (Take Profits + Trail)

Exit strategy:
1. Scale out 25% at +8% (take first profit)
2. Scale out 25% at +15% (lock in more)
3. Scale out 25% at +25% (secure big gain)
4. Final 25%: Trail with smart exit logic

This approach:
- Secures profits incrementally
- Reduces position risk as it moves up
- Lets final piece run for home runs
- Psychological benefit: always banking some wins

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

from scanner.daily_breakout_scanner import DailyBreakoutScanner
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from data.cache import CachedDataClient

logger = logging.getLogger(__name__)


@dataclass
class ScaledPosition:
    """Position with scaled exit tracking."""
    symbol: str
    entry_date: datetime
    entry_price: float
    initial_shares: int
    current_shares: int  # Decreases as we scale out
    hard_stop: float

    # Scaling tracking
    scaled_25_pct: bool = False  # Hit +8%
    scaled_50_pct: bool = False  # Hit +15%
    scaled_75_pct: bool = False  # Hit +25%

    # Partial exit tracking
    partial_exits: List[Dict] = field(default_factory=list)

    # Smart exit tracking (for final 25%)
    highest_high: float = 0.0
    trailing_stop: float = 0.0
    prev_high: float = 0.0

    # Final exit info
    final_exit_date: Optional[datetime] = None
    final_exit_price: Optional[float] = None
    final_exit_reason: Optional[str] = None

    def position_value(self, current_price: float) -> float:
        return self.current_shares * current_price

    def unrealized_pnl(self, current_price: float) -> float:
        """Unrealized P&L on remaining shares."""
        return (current_price - self.entry_price) * self.current_shares

    def realized_pnl(self) -> float:
        """Total realized P&L from all exits."""
        total = 0.0
        for exit_info in self.partial_exits:
            total += (exit_info['price'] - self.entry_price) * exit_info['shares']

        # Add final exit if closed
        if self.final_exit_price and self.current_shares == 0:
            # Already included in partial_exits
            pass

        return total

    def total_pnl(self, current_price: float) -> float:
        """Total P&L (realized + unrealized)."""
        return self.realized_pnl() + self.unrealized_pnl(current_price)

    def hold_days(self, current_date: datetime) -> int:
        end_date = self.final_exit_date or current_date
        return (end_date - self.entry_date).days

    def profit_pct(self, current_price: float) -> float:
        """Current profit % from entry."""
        return ((current_price - self.entry_price) / self.entry_price) * 100


class ScaledExitBacktester:
    """
    Backtester with scaled exits + trailing runner.

    Scale Out Levels:
    - 25% at +8% profit
    - 25% at +15% profit
    - 25% at +25% profit
    - Final 25%: Trail with stops

    Stops (on remaining shares):
    - Hard stop: -8%
    - Trailing stop: Dynamic (2x ATR → 1x ATR → 5%)
    - MA break: Below 5-day MA
    - Time stop: 20 days (longer than before since we scaled out)
    """

    def __init__(self, api_key: str, secret_key: str, starting_capital: float = 100000, use_cache: bool = True, cache_dir: str = './cache_scaled_exits'):
        self.scanner = DailyBreakoutScanner(api_key, secret_key)

        # Use cached client for fast iteration
        if use_cache:
            self.data_client = CachedDataClient(api_key, secret_key, cache_dir=cache_dir)
            logger.info(f"🚀 Using CACHED data client: {cache_dir}")
        else:
            self.data_client = StockHistoricalDataClient(api_key, secret_key)
            logger.info("📥 Using live data client (no cache)")

        self.starting_capital = starting_capital
        self.capital = starting_capital

        # Risk management
        self.stop_loss_percent = 0.08  # 8% hard stop
        self.max_positions = 3
        self.position_size_percent = 0.30

        # Scaling levels
        self.scale_1_pct = 8.0   # First 25% out at +8%
        self.scale_2_pct = 15.0  # Second 25% out at +15%
        self.scale_3_pct = 25.0  # Third 25% out at +25%

        # Tracking
        self.positions: List[ScaledPosition] = []
        self.closed_trades: List[ScaledPosition] = []
        self.equity_curve = [starting_capital]
        self.peak_capital = starting_capital

    def run(self, start_date: datetime, end_date: datetime):
        """Run backtest with scaled exits."""
        logger.info(f"Starting scaled exit backtest: {start_date.date()} to {end_date.date()}")
        logger.info(f"Scale out: 25% @ +{self.scale_1_pct}%, 25% @ +{self.scale_2_pct}%, 25% @ +{self.scale_3_pct}%, trail final 25%")

        current_date = start_date

        while current_date <= end_date:
            # Check for new signals
            candidates = self.scanner.scan(current_date)

            # Enter new positions
            for candidate in candidates:
                if len(self.positions) < self.max_positions:
                    self._enter_position(candidate, current_date)

            # Check scaled exits on existing positions
            self._check_scaled_exits(current_date)

            # Update equity
            equity = self._calculate_equity(current_date)
            self.equity_curve.append(equity)

            # Move to next day
            current_date += timedelta(days=1)

        # Close any remaining positions at end (use last valid trading date)
        last_valid_date = current_date - timedelta(days=1)
        for pos in list(self.positions):
            final_price = self._get_current_price(pos.symbol, last_valid_date)
            if final_price == 0.0:
                # Fallback: try to get the last known price from recent bars
                bars = self._get_recent_bars(pos.symbol, last_valid_date, lookback=5)
                if bars:
                    final_price = float(bars[-1].close)
            self._close_final_position(pos, last_valid_date, "END_OF_BACKTEST", final_price)

        return self._generate_results()

    def _enter_position(self, candidate, date: datetime):
        """Enter a new position."""
        position_value = self.capital * self.position_size_percent
        shares = int(position_value / candidate.close)

        if shares == 0:
            return

        # Calculate hard stop
        hard_stop = candidate.close * (1 - self.stop_loss_percent)

        position = ScaledPosition(
            symbol=candidate.symbol,
            entry_date=date,
            entry_price=candidate.close,
            initial_shares=shares,
            current_shares=shares,
            hard_stop=hard_stop,
            highest_high=candidate.close
        )

        self.positions.append(position)
        self.capital -= (shares * candidate.close)

        logger.info(f"  🟢 ENTER {candidate.symbol}: {shares} shares @ ${candidate.close:.2f} (stop: ${hard_stop:.2f})")

    def _check_scaled_exits(self, date: datetime):
        """Check for scaled exits and smart exits on remaining shares."""

        for position in list(self.positions):
            # Get price data
            bars = self._get_recent_bars(position.symbol, date, lookback=10)
            if not bars or len(bars) == 0:
                continue

            current_bar = bars[-1]
            current_price = float(current_bar.close)
            current_high = float(current_bar.high)
            current_low = float(current_bar.low)

            profit_pct = position.profit_pct(current_price)

            # SCALED EXITS (take profits incrementally)

            # 1. First 25% at +8%
            if not position.scaled_25_pct and profit_pct >= self.scale_1_pct:
                shares_to_sell = position.initial_shares // 4
                self._partial_exit(position, date, current_price, shares_to_sell, f"SCALE_1 (+{profit_pct:.1f}%)")
                position.scaled_25_pct = True

            # 2. Second 25% at +15%
            if position.scaled_25_pct and not position.scaled_50_pct and profit_pct >= self.scale_2_pct:
                shares_to_sell = position.initial_shares // 4
                self._partial_exit(position, date, current_price, shares_to_sell, f"SCALE_2 (+{profit_pct:.1f}%)")
                position.scaled_50_pct = True

            # 3. Third 25% at +25%
            if position.scaled_50_pct and not position.scaled_75_pct and profit_pct >= self.scale_3_pct:
                shares_to_sell = position.initial_shares // 4
                self._partial_exit(position, date, current_price, shares_to_sell, f"SCALE_3 (+{profit_pct:.1f}%)")
                position.scaled_75_pct = True

            # If no shares left (shouldn't happen but defensive)
            if position.current_shares == 0:
                self._close_final_position(position, date, "FULLY_SCALED", current_price)
                continue

            # SMART EXITS on remaining shares

            # Calculate ATR for trailing stop
            atr = self._calculate_atr(bars, period=10)

            # Update highest high
            if current_high > position.highest_high:
                position.highest_high = current_high

                # Hybrid trailing (tighter as profit grows)
                if profit_pct >= 30:
                    position.trailing_stop = position.highest_high * 0.95  # 5% trail
                elif profit_pct >= 20:
                    position.trailing_stop = current_high - (atr * 1.0)  # 1x ATR
                else:
                    position.trailing_stop = current_high - (atr * 2.0)  # 2x ATR

            # Calculate 5-day MA
            if len(bars) >= 5:
                sma_5 = sum(float(b.close) for b in bars[-5:]) / 5
            else:
                sma_5 = current_price

            # EXIT LOGIC (on remaining shares)

            # 1. HARD STOP
            if current_low <= position.hard_stop:
                logger.info(f"  🛑 {position.symbol}: Hard stop hit")
                self._close_final_position(position, date, "HARD_STOP", position.hard_stop)
                continue

            # 2. TRAILING STOP (after scaling out at least once)
            if position.scaled_25_pct and position.highest_high > position.entry_price * 1.08:
                if current_low <= position.trailing_stop:
                    logger.info(f"  📉 {position.symbol}: Trailing stop at ${current_low:.2f}")
                    self._close_final_position(position, date, "TRAILING_STOP", position.trailing_stop)
                    continue

            # 3. TREND BREAK (close below 5-day MA after scaling)
            if position.scaled_25_pct and current_price < sma_5:
                logger.info(f"  📊 {position.symbol}: MA break at ${current_price:.2f}")
                self._close_final_position(position, date, "MA_BREAK", current_price)
                continue

            # 4. TIME STOP (20 days - longer since we scaled out)
            if position.hold_days(date) >= 20:
                logger.info(f"  ⏰ {position.symbol}: Time stop (20 days)")
                self._close_final_position(position, date, "TIME", current_price)
                continue

            # Update for next day
            position.prev_high = current_high

    def _partial_exit(self, position: ScaledPosition, date: datetime, price: float, shares: int, reason: str):
        """Partially exit position (scale out)."""
        if shares > position.current_shares:
            shares = position.current_shares  # Don't sell more than we have

        exit_value = shares * price
        self.capital += exit_value

        profit = (price - position.entry_price) * shares
        profit_pct = ((price - position.entry_price) / position.entry_price) * 100

        position.partial_exits.append({
            'date': date,
            'price': price,
            'shares': shares,
            'profit': profit,
            'reason': reason
        })

        position.current_shares -= shares

        logger.info(f"    💰 {position.symbol}: Sold {shares} shares @ ${price:.2f} ({reason}, +${profit:,.0f})")

    def _close_final_position(self, position: ScaledPosition, date: datetime, reason: str, price: float):
        """Close remaining shares."""
        if position.current_shares > 0:
            self._partial_exit(position, date, price, position.current_shares, reason)

        position.final_exit_date = date
        position.final_exit_price = price
        position.final_exit_reason = reason

        total_profit = position.realized_pnl()
        total_pct = (total_profit / (position.entry_price * position.initial_shares)) * 100

        self.positions.remove(position)
        self.closed_trades.append(position)

        logger.info(f"  🔴 CLOSE {position.symbol}: Total P&L: +${total_profit:,.0f} ({total_pct:+.1f}%) over {position.hold_days(date)} days")
        logger.info(f"      Exits: {len(position.partial_exits)} ({', '.join([e['reason'] for e in position.partial_exits])})")

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
        """Fetch recent bars for a symbol."""
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=date - timedelta(days=lookback + 5),
                end=date
            )
            bars_dict = self.data_client.get_stock_bars(request)
            # Handle both regular and cached client responses
            if hasattr(bars_dict, 'data'):
                return list(bars_dict.data[symbol]) if symbol in bars_dict.data else []
            else:
                return list(bars_dict[symbol]) if symbol in bars_dict else []
        except Exception as e:
            logger.warning(f"Error fetching bars for {symbol}: {e}")
            return []

    def _get_current_price(self, symbol: str, date: datetime) -> float:
        """Get current closing price."""
        bars = self._get_recent_bars(symbol, date, lookback=1)
        return float(bars[-1].close) if bars else 0.0

    def _calculate_equity(self, date: datetime) -> float:
        """Calculate current equity (cash + positions)."""
        equity = self.capital
        for pos in self.positions:
            current_price = self._get_current_price(pos.symbol, date)
            if current_price:
                equity += pos.position_value(current_price)
        return equity

    def _generate_results(self):
        """Generate backtest results."""
        from collections import namedtuple

        total_trades = len(self.closed_trades)
        winning_trades = [t for t in self.closed_trades if t.realized_pnl() > 0]
        losing_trades = [t for t in self.closed_trades if t.realized_pnl() < 0]

        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0

        total_wins = sum(t.realized_pnl() for t in winning_trades) if winning_trades else 0
        total_losses = sum(abs(t.realized_pnl()) for t in losing_trades) if losing_trades else 1
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        avg_win = total_wins / len(winning_trades) if winning_trades else 0
        avg_loss = -sum(t.realized_pnl() for t in losing_trades) / len(losing_trades) if losing_trades else 0

        final_capital = self.equity_curve[-1] if self.equity_curve else self.starting_capital
        total_return = final_capital - self.starting_capital
        total_return_pct = (total_return / self.starting_capital) * 100

        # Max drawdown
        peak = self.starting_capital
        max_dd = 0
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100
            max_dd = max(max_dd, dd)

        Results = namedtuple('Results', [
            'total_return', 'total_return_percent', 'total_trades',
            'win_rate', 'profit_factor', 'avg_win', 'avg_loss',
            'max_drawdown_percent', 'final_capital'
        ])

        return Results(
            total_return=total_return,
            total_return_percent=total_return_pct,
            total_trades=total_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            max_drawdown_percent=max_dd,
            final_capital=final_capital
        )
