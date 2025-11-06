"""
Historical Backtester - Test Claude's decision-making on past data.

This replays historical market conditions and simulates what Claude would have
decided on each trading day. It's different from traditional backtesting because
it tests the AI's reasoning, not just rule-based signals.

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime, timedelta, time as dt_time
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass
import json
from pathlib import Path

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient

# Allow standalone testing
try:
    from scanner.market_scanner import MomentumScanner, MomentumCandidate
    from scanner.news_aggregator import NewsAggregator, CatalystAnalysis
    from brain.claude_engine import ClaudeTrader, TradeDecision
    from data.database import TradingDatabase
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scanner.market_scanner import MomentumScanner, MomentumCandidate
    from scanner.news_aggregator import NewsAggregator, CatalystAnalysis
    from brain.claude_engine import ClaudeTrader, TradeDecision
    from data.database import TradingDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """A simulated trade from backtesting."""
    symbol: str
    entry_date: datetime
    entry_price: float
    exit_date: Optional[datetime]
    exit_price: Optional[float]
    exit_reason: Optional[str]
    shares: int
    stop_loss: float
    profit_target: float
    pnl: Optional[float]
    pnl_percent: Optional[float]
    claude_reasoning: str
    catalyst_type: Optional[str]
    catalyst_strength: Optional[float]


@dataclass
class BacktestResult:
    """Results from a historical backtest."""
    start_date: datetime
    end_date: datetime
    starting_capital: float
    ending_capital: float
    total_return: float
    total_return_percent: float

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    total_profit: float
    total_loss: float
    profit_factor: float

    avg_win: float
    avg_loss: float
    avg_trade: float

    best_trade: float
    worst_trade: float

    max_drawdown: float
    max_drawdown_percent: float

    trades: List[BacktestTrade]
    daily_equity: Dict[str, float]

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'starting_capital': self.starting_capital,
            'ending_capital': self.ending_capital,
            'total_return': self.total_return,
            'total_return_percent': self.total_return_percent,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'profit_factor': self.profit_factor,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'avg_trade': self.avg_trade,
            'best_trade': self.best_trade,
            'worst_trade': self.worst_trade,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_percent': self.max_drawdown_percent,
            'trades': [
                {
                    'symbol': t.symbol,
                    'entry_date': t.entry_date.isoformat(),
                    'entry_price': t.entry_price,
                    'exit_date': t.exit_date.isoformat() if t.exit_date else None,
                    'exit_price': t.exit_price,
                    'exit_reason': t.exit_reason,
                    'shares': t.shares,
                    'stop_loss': t.stop_loss,
                    'profit_target': t.profit_target,
                    'pnl': t.pnl,
                    'pnl_percent': t.pnl_percent,
                    'claude_reasoning': t.claude_reasoning,
                    'catalyst_type': t.catalyst_type,
                    'catalyst_strength': t.catalyst_strength
                }
                for t in self.trades
            ],
            'daily_equity': {k.isoformat(): v for k, v in self.daily_equity.items()}
        }


class HistoricalBacktester:
    """
    Backtests Claude's trading decisions on historical data.

    This is different from traditional backtesting:
    - Tests Claude's actual decision-making process
    - Includes news/catalyst analysis
    - Simulates real-time decision context
    - Validates AI reasoning, not just rules
    """

    def __init__(
        self,
        alpaca_api_key: str,
        alpaca_secret_key: str,
        anthropic_api_key: str,
        starting_capital: float = 100000
    ):
        """
        Initialize backtester.

        Args:
            alpaca_api_key: Alpaca API key
            alpaca_secret_key: Alpaca secret key
            anthropic_api_key: Anthropic Claude API key
            starting_capital: Starting capital for backtest
        """
        self.data_client = StockHistoricalDataClient(alpaca_api_key, alpaca_secret_key)
        self.scanner = MomentumScanner(alpaca_api_key, alpaca_secret_key)
        self.news = NewsAggregator(alpaca_api_key, alpaca_secret_key)
        self.claude = ClaudeTrader(anthropic_api_key, account_size=starting_capital)

        self.starting_capital = starting_capital
        self.current_capital = starting_capital

        # State
        self.open_positions: List[BacktestTrade] = []
        self.closed_trades: List[BacktestTrade] = []
        self.daily_equity: Dict[datetime, float] = {}

        logger.info(f"Historical Backtester initialized (${starting_capital:,.0f})")

    def get_historical_candidates(
        self,
        date: datetime
    ) -> List[MomentumCandidate]:
        """
        Get momentum candidates as they would have appeared on a specific date.

        Args:
            date: The trading date to scan

        Returns:
            List of momentum candidates for that day
        """
        logger.info(f"Scanning for candidates on {date.date()}")

        # Use scanner's historical mode
        candidates = self.scanner.scan(historical_date=date)

        return candidates

    def simulate_trade_execution(
        self,
        decision: TradeDecision,
        entry_date: datetime,
        catalyst: Optional[CatalystAnalysis] = None
    ) -> BacktestTrade:
        """
        Simulate executing a trade and track it.

        Args:
            decision: Claude's trade decision
            entry_date: Date of entry
            catalyst: Detected catalyst if any

        Returns:
            BacktestTrade object
        """
        # Calculate position size (same logic as live trading)
        risk_per_trade = self.current_capital * 0.02  # 2% risk
        stop_distance = decision.entry_price - decision.stop_loss
        shares = int(risk_per_trade / stop_distance)

        # Create trade
        trade = BacktestTrade(
            symbol=decision.symbol,
            entry_date=entry_date,
            entry_price=decision.entry_price,
            exit_date=None,
            exit_price=None,
            exit_reason=None,
            shares=shares,
            stop_loss=decision.stop_loss,
            profit_target=decision.profit_target,
            pnl=None,
            pnl_percent=None,
            claude_reasoning=decision.reasoning,
            catalyst_type=catalyst.catalyst_type if catalyst else None,
            catalyst_strength=catalyst.catalyst_strength if catalyst else None
        )

        self.open_positions.append(trade)

        # Reduce capital by position cost
        position_cost = decision.entry_price * shares
        self.current_capital -= position_cost

        logger.info(f"  📈 Simulated BUY: {decision.symbol} x {shares} @ ${decision.entry_price:.2f}")
        logger.info(f"     Stop: ${decision.stop_loss:.2f}, Target: ${decision.profit_target:.2f}")

        return trade

    def update_positions(self, current_date: datetime):
        """
        Update open positions and check for exits.

        Args:
            current_date: Current simulation date
        """
        for trade in list(self.open_positions):
            # Fetch price data for this day
            try:
                # Get intraday bars for the symbol
                request = StockBarsRequest(
                    symbol_or_symbols=trade.symbol,
                    timeframe=TimeFrame.Minute,
                    start=current_date,
                    end=current_date + timedelta(days=1)
                )

                bars = self.data_client.get_stock_bars(request)

                if trade.symbol not in bars:
                    continue

                symbol_bars = bars[trade.symbol]

                # Check each bar for stop/target hits
                for bar in symbol_bars:
                    low = float(bar.low)
                    high = float(bar.high)
                    close = float(bar.close)

                    # Check stop loss
                    if low <= trade.stop_loss:
                        self.close_position(
                            trade,
                            trade.stop_loss,
                            bar.timestamp,
                            "stop_loss"
                        )
                        break

                    # Check profit target
                    elif high >= trade.profit_target:
                        self.close_position(
                            trade,
                            trade.profit_target,
                            bar.timestamp,
                            "profit_target"
                        )
                        break

            except Exception as e:
                logger.warning(f"Could not update {trade.symbol}: {e}")
                continue

    def close_position(
        self,
        trade: BacktestTrade,
        exit_price: float,
        exit_date: datetime,
        reason: str
    ):
        """
        Close a position and record results.

        Args:
            trade: Trade to close
            exit_price: Exit price
            exit_date: Exit date/time
            reason: Exit reason
        """
        # Calculate P&L
        pnl = (exit_price - trade.entry_price) * trade.shares
        pnl_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100

        # Update trade
        trade.exit_date = exit_date
        trade.exit_price = exit_price
        trade.exit_reason = reason
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent

        # Return capital
        self.current_capital += exit_price * trade.shares

        # Move to closed trades
        self.open_positions.remove(trade)
        self.closed_trades.append(trade)

        result = "✅" if pnl > 0 else "❌"
        logger.info(f"  {result} CLOSED: {trade.symbol} @ ${exit_price:.2f} ({reason})")
        logger.info(f"     P&L: ${pnl:+,.2f} ({pnl_percent:+.1f}%)")

    def close_all_eod(self, date: datetime):
        """
        Close all positions at end of day.

        Args:
            date: Trading date
        """
        for trade in list(self.open_positions):
            try:
                # Get closing price
                request = StockBarsRequest(
                    symbol_or_symbols=trade.symbol,
                    timeframe=TimeFrame.Day,
                    start=date,
                    end=date + timedelta(days=1)
                )

                bars = self.data_client.get_stock_bars(request)

                if trade.symbol in bars:
                    close_price = float(bars[trade.symbol][0].close)
                    self.close_position(trade, close_price, date, "end_of_day")

            except Exception as e:
                logger.warning(f"Could not close {trade.symbol} at EOD: {e}")

    def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        max_positions: int = 3
    ) -> BacktestResult:
        """
        Run backtest over a date range.

        Args:
            start_date: Start date for backtest
            end_date: End date for backtest
            max_positions: Maximum concurrent positions

        Returns:
            BacktestResult with performance metrics
        """
        logger.info("=" * 80)
        logger.info("STARTING HISTORICAL BACKTEST")
        logger.info("=" * 80)
        logger.info(f"Period: {start_date.date()} to {end_date.date()}")
        logger.info(f"Starting Capital: ${self.starting_capital:,.0f}")
        logger.info(f"Max Positions: {max_positions}")
        logger.info("=" * 80 + "\n")

        current_date = start_date

        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            logger.info(f"\n📅 {current_date.date()}")
            logger.info("-" * 80)

            # Morning: Scan and decide (simulating 9:35 AM scan)
            trading_window_start = dt_time(9, 30)
            trading_window_end = dt_time(11, 30)

            if len(self.open_positions) < max_positions:
                # Get candidates as they would have appeared
                candidates = self.get_historical_candidates(current_date)

                if candidates:
                    logger.info(f"Found {len(candidates)} candidates")

                    # Analyze catalysts
                    catalysts = {}
                    for candidate in candidates[:5]:
                        catalyst = self.news.analyze_catalyst(candidate.symbol)
                        if catalyst:
                            catalysts[candidate.symbol] = catalyst

                    # Ask Claude to decide
                    decision = self.claude.make_decision(candidates, catalysts)

                    if decision.action == "BUY":
                        logger.info(f"🤖 Claude Decision: BUY {decision.symbol}")
                        logger.info(f"   Confidence: {decision.confidence}/10")
                        logger.info(f"   Reasoning: {decision.reasoning[:100]}...")

                        # Validate
                        is_valid, reason = self.claude.validate_decision(decision)

                        if is_valid:
                            # Execute trade
                            catalyst = catalysts.get(decision.symbol)
                            self.simulate_trade_execution(decision, current_date, catalyst)
                        else:
                            logger.info(f"   ❌ Validation failed: {reason}")
                    else:
                        logger.info(f"🤖 Claude Decision: {decision.action}")
                        logger.info(f"   Reasoning: {decision.reasoning[:100]}...")
                else:
                    logger.info("No candidates found")

            # Throughout day: Monitor positions
            self.update_positions(current_date)

            # End of day: Close all positions
            self.close_all_eod(current_date)

            # Record daily equity
            total_equity = self.current_capital
            for trade in self.open_positions:
                total_equity += trade.entry_price * trade.shares

            self.daily_equity[current_date] = total_equity

            logger.info(f"📊 EOD Equity: ${total_equity:,.0f}")

            # Move to next day
            current_date += timedelta(days=1)

        # Calculate final results
        return self.calculate_results(start_date, end_date)

    def calculate_results(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """
        Calculate backtest performance metrics.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            BacktestResult with all metrics
        """
        logger.info("\n" + "=" * 80)
        logger.info("BACKTEST COMPLETE - CALCULATING RESULTS")
        logger.info("=" * 80)

        # Basic metrics
        ending_capital = self.current_capital
        total_return = ending_capital - self.starting_capital
        total_return_percent = (total_return / self.starting_capital) * 100

        # Trade metrics
        total_trades = len(self.closed_trades)
        winning_trades = len([t for t in self.closed_trades if t.pnl > 0])
        losing_trades = len([t for t in self.closed_trades if t.pnl < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # P&L metrics
        total_profit = sum(t.pnl for t in self.closed_trades if t.pnl > 0)
        total_loss = abs(sum(t.pnl for t in self.closed_trades if t.pnl < 0))
        profit_factor = (total_profit / total_loss) if total_loss > 0 else float('inf')

        avg_win = (total_profit / winning_trades) if winning_trades > 0 else 0
        avg_loss = (total_loss / losing_trades) if losing_trades > 0 else 0
        avg_trade = (total_return / total_trades) if total_trades > 0 else 0

        best_trade = max((t.pnl for t in self.closed_trades), default=0)
        worst_trade = min((t.pnl for t in self.closed_trades), default=0)

        # Drawdown calculation
        peak_equity = self.starting_capital
        max_drawdown = 0
        max_drawdown_percent = 0

        for equity in self.daily_equity.values():
            if equity > peak_equity:
                peak_equity = equity

            drawdown = peak_equity - equity
            drawdown_percent = (drawdown / peak_equity) * 100

            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_percent = drawdown_percent

        result = BacktestResult(
            start_date=start_date,
            end_date=end_date,
            starting_capital=self.starting_capital,
            ending_capital=ending_capital,
            total_return=total_return,
            total_return_percent=total_return_percent,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_profit=total_profit,
            total_loss=total_loss,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_trade=avg_trade,
            best_trade=best_trade,
            worst_trade=worst_trade,
            max_drawdown=max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            trades=self.closed_trades,
            daily_equity=self.daily_equity
        )

        # Print summary
        self.print_results(result)

        return result

    def print_results(self, result: BacktestResult):
        """Print backtest results to console."""
        print("\n" + "=" * 80)
        print("BACKTEST RESULTS")
        print("=" * 80)
        print(f"\nPeriod: {result.start_date.date()} to {result.end_date.date()}")
        print(f"Starting Capital: ${result.starting_capital:,.2f}")
        print(f"Ending Capital:   ${result.ending_capital:,.2f}")
        print(f"Total Return:     ${result.total_return:+,.2f} ({result.total_return_percent:+.2f}%)")

        print(f"\n📊 TRADE STATISTICS")
        print("-" * 80)
        print(f"Total Trades:     {result.total_trades}")
        print(f"Winning Trades:   {result.winning_trades}")
        print(f"Losing Trades:    {result.losing_trades}")
        print(f"Win Rate:         {result.win_rate:.1f}%")

        print(f"\n💰 P&L BREAKDOWN")
        print("-" * 80)
        print(f"Total Profit:     ${result.total_profit:,.2f}")
        print(f"Total Loss:       ${result.total_loss:,.2f}")
        print(f"Profit Factor:    {result.profit_factor:.2f}" if result.profit_factor != float('inf') else "Profit Factor:    ∞")
        print(f"Average Win:      ${result.avg_win:,.2f}")
        print(f"Average Loss:     ${result.avg_loss:,.2f}")
        print(f"Average Trade:    ${result.avg_trade:+,.2f}")

        print(f"\n📈 BEST/WORST")
        print("-" * 80)
        print(f"Best Trade:       ${result.best_trade:+,.2f}")
        print(f"Worst Trade:      ${result.worst_trade:+,.2f}")
        print(f"Max Drawdown:     ${result.max_drawdown:,.2f} ({result.max_drawdown_percent:.2f}%)")

        print("\n" + "=" * 80)

        # Assessment
        if result.total_trades >= 30:
            if result.win_rate >= 55 and result.profit_factor >= 1.5 and result.total_return > 0:
                print("✅ ASSESSMENT: System shows promise for live trading")
                print("   Consider paper trading to validate further.")
            else:
                print("⚠️  ASSESSMENT: Results below target metrics")
                print("   Refine strategy before considering live trading.")
        else:
            print("ℹ️  ASSESSMENT: Insufficient trades for conclusive analysis")
            print(f"   Run backtest for longer period (need 30+ trades, got {result.total_trades})")

        print("=" * 80 + "\n")

    def save_results(self, result: BacktestResult, filename: str):
        """
        Save backtest results to JSON file.

        Args:
            result: BacktestResult to save
            filename: Output filename
        """
        output_path = Path(filename)

        with open(output_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        logger.info(f"Results saved to {output_path}")


def main():
    """Run a sample backtest."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    print("\n" + "=" * 80)
    print("MOMENTUM HUNTER - Historical Backtest")
    print("=" * 80 + "\n")

    # Create backtester
    backtester = HistoricalBacktester(
        alpaca_api_key=api_key,
        alpaca_secret_key=secret_key,
        anthropic_api_key=anthropic_key,
        starting_capital=100000
    )

    # Run backtest for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    result = backtester.run_backtest(
        start_date=start_date,
        end_date=end_date,
        max_positions=3
    )

    # Save results
    backtester.save_results(result, "backtest_results.json")


if __name__ == "__main__":
    main()
