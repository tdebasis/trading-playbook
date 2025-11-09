"""
Composable Backtest Engine

Generic backtest orchestration that accepts scanner and exit strategy via protocols.
Eliminates code duplication across backtest implementations.

Author: Claude AI + Tanam Bam Sinha
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass
import logging
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from interfaces import Position, ExitSignal, BacktestResults
from interfaces import ScannerProtocol, ExitStrategyProtocol
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Composable backtest engine that orchestrates scanner + exit strategy.

    This engine extracts the duplicated backtest loop logic and allows
    mixing and matching any scanner with any exit strategy.

    Example:
        scanner = get_scanner('daily_breakout', api_key, secret_key)
        exit_strategy = get_exit_strategy('smart_exits')

        engine = BacktestEngine(
            scanner=scanner,
            exit_strategy=exit_strategy,
            data_client=data_client,
            starting_capital=100000
        )

        results = engine.run(start_date, end_date)
    """

    def __init__(
        self,
        scanner: ScannerProtocol,
        exit_strategy: ExitStrategyProtocol,
        data_client: StockHistoricalDataClient,
        starting_capital: float = 100000,
        max_positions: int = 3,
        position_size_percent: float = 0.0667
    ):
        """
        Initialize backtest engine.

        Args:
            scanner: Scanner implementing ScannerProtocol
            exit_strategy: Exit strategy implementing ExitStrategyProtocol
            data_client: Alpaca data client (can be CachedDataClient)
            starting_capital: Starting capital in dollars
            max_positions: Maximum concurrent positions
            position_size_percent: Position size as fraction of capital (e.g., 0.0667 = 6.67%)
                                   Default ensures max 20% total exposure (3 positions × 6.67%)
        """
        self._scanner = scanner
        self._exit_strategy = exit_strategy
        self.data_client = data_client

        self.starting_capital = starting_capital
        self.capital = starting_capital

        self.max_positions = max_positions
        self.position_size_percent = position_size_percent

        # Tracking
        self.positions: List[Position] = []
        self.closed_trades: List[Position] = []
        self.equity_curve = [starting_capital]
        self.peak_capital = starting_capital

    def run(self, start_date: datetime, end_date: datetime) -> BacktestResults:
        """
        Run backtest from start_date to end_date.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            BacktestResults with comprehensive metrics
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"COMPOSABLE BACKTEST ENGINE")
        logger.info(f"{'='*80}")
        logger.info(f"Scanner: {self._scanner.strategy_name}")
        logger.info(f"Exit Strategy: {self._exit_strategy.strategy_name}")
        logger.info(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"Starting Capital: ${self.starting_capital:,.2f}")
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

        return self._calculate_results(start_date, end_date)

    def _process_trading_day(self, date: datetime):
        """Process a single trading day."""
        logger.info(f"\n{'='*80}")
        logger.info(f"DAY: {date.strftime('%Y-%m-%d (%A)')}")
        logger.info(f"Capital: ${self.capital:,.2f} | Positions: {len(self.positions)}")
        logger.info(f"{'='*80}")

        # 1. Check exits for existing positions
        self._check_exits(date)

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
                    logger.info(f"  {pos.symbol}: ${current_price:.2f} ({unrealized:+,.2f})")

    def _check_exits(self, date: datetime):
        """Check all positions for exit signals."""
        for position in list(self.positions):
            # Get recent bars for exit strategy
            bars = self._get_recent_bars(position.symbol, date, lookback=20)
            if not bars or len(bars) < 5:
                logger.warning(f"  {position.symbol}: Insufficient data for exit check")
                continue

            current_price = float(bars[-1].close)

            # Update MFE/MAE tracking
            position.update_mfe_mae(current_price)

            # Check exit strategy
            signal = self._exit_strategy.check_exit(
                position, current_price, date, bars
            )

            if signal.should_exit:
                if signal.partial_exit:
                    self._partial_exit(position, date, signal)
                else:
                    self._close_position(position, date, signal.reason, signal.exit_price)

    def _scan_and_enter(self, date: datetime):
        """Scan for new entry candidates and enter positions."""
        logger.info(f"\n🔍 Scanning for entries...")

        try:
            # Use scanner's scan_standardized method if available, otherwise scan
            if hasattr(self._scanner, 'scan_standardized'):
                candidates = self._scanner.scan_standardized(date)
            else:
                candidates = self._scanner.scan(date)
        except Exception as e:
            logger.error(f"  Scanner error: {e}")
            return

        if not candidates:
            logger.info(f"  No candidates found")
            return

        logger.info(f"  Found {len(candidates)} candidates")

        # Filter out already held symbols
        held_symbols = {pos.symbol for pos in self.positions}
        candidates = [c for c in candidates if c.symbol not in held_symbols]

        if not candidates:
            logger.info(f"  All candidates already held")
            return

        # Enter positions (fill available slots)
        slots = self.max_positions - len(self.positions)
        for candidate in candidates[:slots]:
            entry_price = candidate.entry_price

            # TODO: REPLACE WITH PROFESSIONAL POSITION SIZING
            #
            # Current approach (NAIVE):
            # - Fixed 6.67% of capital per position
            # - No risk-based sizing (ignores stop loss distance)
            # - Total exposure capped at 20% (3 positions × 6.67%)
            # - No portfolio heat management
            #
            # Professional approach (FUTURE):
            # 1. RISK-BASED SIZING:
            #    Position size = (Account Risk % × Capital) / (Entry - Stop)
            #    Example: (2% × $100K) / ($100 - $92) = $2,000 risk / $8 = 250 shares
            #
            # 2. EXPONENTIAL QUALITY-BASED RISK:
            #    Grade A (9-10): 8% account risk (rare, highest conviction)
            #    Grade B (7-8):  5% account risk (strong setup)
            #    Grade C (5-6):  2% account risk (marginal, selective)
            #    Grade D (<5):   Skip entirely
            #
            # 3. TOTAL EXPOSURE CONTROLS:
            #    - Max 20% total capital deployed at once (professional standard)
            #    - Max 15% total account risk (sum of all position risks)
            #    - Exponential aspect: 80% of profits from 20% of trades (Grade A)
            #
            # 4. PORTFOLIO HEAT MANAGEMENT:
            #    - Track cumulative risk across all open positions
            #    - Reduce position size when heat is high
            #    - Increase size when heat is low and Grade A setup appears
            #
            # Implementation:
            # - Use PositionSizerProtocol (already defined in interfaces/position_sizer.py)
            # - Replace this inline calculation with: position_sizer.calculate_size(...)
            # - Scanner should provide quality score (0-10) for risk allocation
            # - Kelly Criterion could optimize exact risk ratios
            #
            # Current: Fixed 0.53% risk per position (6.67% position, -8% stop)
            # Max total risk: 1.6% with 3 positions (well below professional 15% max)
            position_value = self.capital * self.position_size_percent
            shares = int(position_value / entry_price)

            if shares == 0:
                logger.warning(f"  {candidate.symbol}: Insufficient capital for entry")
                continue

            # Get initial stop from exit strategy
            stop_price = self._exit_strategy.get_initial_stop(entry_price)

            # Create standardized Position
            position = Position(
                symbol=candidate.symbol,
                entry_date=date,
                entry_price=entry_price,
                shares=shares,
                stop_price=stop_price
            )

            # Store candidate data in position for reference
            if hasattr(candidate, 'strategy_data'):
                position.strategy_state['candidate_data'] = candidate.strategy_data

            self.positions.append(position)
            self.capital -= shares * entry_price

            risk_dollars = shares * (entry_price - stop_price)
            logger.info(f"  ✅ ENTER {candidate.symbol}: {shares} shares @ ${entry_price:.2f}")
            logger.info(f"     Stop: ${stop_price:.2f} | Risk: ${risk_dollars:,.2f}")

    def _partial_exit(self, position: Position, date: datetime, signal: ExitSignal):
        """Handle partial exit of position."""
        shares_to_exit = int(position.shares * signal.exit_percent)

        if shares_to_exit == 0:
            return

        # Add partial exit to position tracking
        position.add_partial_exit(
            exit_date=date,
            shares=shares_to_exit,
            price=signal.exit_price,
            reason=signal.reason
        )

        # Return capital
        self.capital += shares_to_exit * signal.exit_price

        pnl = (signal.exit_price - position.entry_price) * shares_to_exit
        logger.info(f"  📤 PARTIAL EXIT {position.symbol}: {shares_to_exit} shares @ ${signal.exit_price:.2f}")
        logger.info(f"     Reason: {signal.reason} | P&L: ${pnl:+,.2f}")
        logger.info(f"     Remaining: {position.shares} shares")

    def _close_position(self, position: Position, date: datetime, reason: str, price: Optional[float] = None):
        """Close position completely."""
        exit_price = price or self._get_current_price(position.symbol, date)

        if exit_price is None:
            logger.warning(f"  Cannot close {position.symbol}: No price data")
            return

        position.exit_date = date
        position.exit_price = exit_price
        position.exit_reason = reason

        # Return capital
        self.capital += position.shares * exit_price

        # Move to closed trades
        self.positions.remove(position)
        self.closed_trades.append(position)

        pnl = position.realized_pnl()
        pnl_pct = position.realized_pnl_percent()
        hold_days = position.hold_days()

        logger.info(f"  ❌ EXIT {position.symbol}: {position.shares} shares @ ${exit_price:.2f}")
        logger.info(f"     Reason: {reason}")
        logger.info(f"     P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%) | Hold: {hold_days} days")

    def _calculate_current_equity(self, date: datetime) -> float:
        """Calculate current total equity (cash + position value)."""
        equity = self.capital

        for pos in self.positions:
            current_price = self._get_current_price(pos.symbol, date)
            if current_price:
                equity += pos.shares * current_price

        return equity

    def _get_current_price(self, symbol: str, date: datetime) -> Optional[float]:
        """Get closing price for symbol on date."""
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=date,
                end=date + timedelta(days=1)
            )
            bars = self.data_client.get_stock_bars(request)

            # Access bars directly (BarSet supports indexing but not 'in' operator)
            symbol_bars = bars[symbol] if hasattr(bars, '__getitem__') else bars.data.get(symbol, [])
            if symbol_bars and len(symbol_bars) > 0:
                return float(symbol_bars[0].close)
        except Exception as e:
            logger.warning(f"Error fetching price for {symbol}: {e}")

        return None

    def _get_recent_bars(self, symbol: str, date: datetime, lookback: int = 20):
        """Get recent daily bars for symbol."""
        try:
            start = date - timedelta(days=lookback * 2)  # Extra buffer for weekends
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start,
                end=date + timedelta(days=1)
            )
            bars = self.data_client.get_stock_bars(request)

            # Access bars directly (BarSet supports indexing but not 'in' operator)
            symbol_bars = bars[symbol] if hasattr(bars, '__getitem__') else bars.data.get(symbol, [])
            if symbol_bars:
                return list(symbol_bars)[-lookback:]
        except Exception as e:
            logger.warning(f"Error fetching bars for {symbol}: {e}")

        return []

    def _get_trading_days(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Get list of trading days between start and end dates."""
        try:
            request = StockBarsRequest(
                symbol_or_symbols='SPY',
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date
            )
            bars = self.data_client.get_stock_bars(request)

            # Access bars directly (BarSet supports indexing but not 'in' operator)
            spy_bars = bars['SPY'] if hasattr(bars, '__getitem__') else bars.data.get('SPY', [])
            if spy_bars:
                return [bar.timestamp.replace(tzinfo=None) for bar in spy_bars]
        except Exception as e:
            logger.error(f"Error fetching trading days: {e}")

        return []

    def _calculate_results(self, start_date: datetime, end_date: datetime) -> BacktestResults:
        """Calculate final backtest results."""
        from .metrics import calculate_backtest_metrics

        return calculate_backtest_metrics(
            trades=self.closed_trades,
            equity_curve=self.equity_curve,
            starting_capital=self.starting_capital,
            start_date=start_date,
            end_date=end_date,
            scanner_name=self._scanner.strategy_name,
            exit_strategy_name=self._exit_strategy.strategy_name
        )

    # Properties for protocol compliance (if needed)
    @property
    def scanner(self) -> ScannerProtocol:
        return self._scanner

    @property
    def exit_strategy(self) -> ExitStrategyProtocol:
        return self._exit_strategy
