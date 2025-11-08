"""
Backtest interface and results for trading strategies.

Standardizes backtest execution and results reporting.
"""

from __future__ import annotations

from typing import Protocol, Optional, List, runtime_checkable, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .scanner import ScannerProtocol
    from .exit_strategy import ExitStrategyProtocol


@dataclass
class BacktestResults:
    """
    Standardized backtest results across all strategies.

    This format enables:
    - Easy comparison between different strategies
    - Consistent reporting and visualization
    - Database storage with uniform schema
    - API responses with predictable structure
    """

    # Capital tracking
    starting_capital: float
    ending_capital: float
    total_return: float  # Dollar amount
    total_return_percent: float  # Percentage

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float  # 0-100 (e.g., 55.5 for 55.5%)

    # Performance metrics
    avg_win: float  # Average winning trade ($)
    avg_loss: float  # Average losing trade ($)
    profit_factor: float  # Gross profit / Gross loss
    max_drawdown_percent: float  # Maximum peak-to-trough decline (%)

    # Risk-adjusted metrics
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    calmar_ratio: float | None = None

    # Time-based metrics
    avg_hold_days: float = 0.0
    max_hold_days: int = 0
    avg_bars_to_profit: float | None = None

    # Position metrics
    max_concurrent_positions: int = 0
    avg_position_size_percent: float = 0.0

    # Detailed tracking
    trades: List[dict] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)

    # Strategy identification
    strategy_name: str = ""
    scanner_name: str = ""
    exit_strategy_name: str = ""
    timeframe: str = ""

    # Backtest metadata
    start_date: datetime | None = None
    end_date: datetime | None = None
    trading_days: int = 0

    def __post_init__(self):
        """Calculate derived metrics if trades are provided."""
        if self.trades and self.total_trades == 0:
            self.total_trades = len(self.trades)
            self._calculate_from_trades()

    def _calculate_from_trades(self) -> None:
        """Calculate statistics from trades list."""
        if not self.trades:
            return

        winners = [t for t in self.trades if t.get('pnl', 0) > 0]
        losers = [t for t in self.trades if t.get('pnl', 0) < 0]

        self.winning_trades = len(winners)
        self.losing_trades = len(losers)
        self.win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        self.avg_win = sum(t['pnl'] for t in winners) / len(winners) if winners else 0
        self.avg_loss = sum(t['pnl'] for t in losers) / len(losers) if losers else 0

        gross_profit = sum(t['pnl'] for t in winners)
        gross_loss = abs(sum(t['pnl'] for t in losers))
        self.profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        hold_days = [t.get('hold_days', 0) for t in self.trades]
        self.avg_hold_days = sum(hold_days) / len(hold_days) if hold_days else 0
        self.max_hold_days = max(hold_days) if hold_days else 0

    @property
    def expectancy(self) -> float:
        """
        Calculate expectancy per trade.

        Expectancy = (Win% × Avg Win) - (Loss% × Avg Loss)

        Positive expectancy means the strategy has an edge.

        Returns:
            Expected profit/loss per trade in dollars
        """
        if self.total_trades == 0:
            return 0.0

        win_pct = self.winning_trades / self.total_trades
        loss_pct = self.losing_trades / self.total_trades

        return (win_pct * self.avg_win) - (loss_pct * abs(self.avg_loss))

    @property
    def avg_r_multiple(self) -> float:
        """
        Calculate average R-multiple across all trades.

        R-multiple is risk-adjusted return:
        - Positive = winning strategy
        - > 1.0 = profitable after considering risk
        - 2.0 = average trade makes 2x initial risk

        Returns:
            Average R-multiple, or 0.0 if not calculable
        """
        r_multiples = [t.get('r_multiple') for t in self.trades if t.get('r_multiple') is not None]
        return sum(r_multiples) / len(r_multiples) if r_multiples else 0.0

    @property
    def kelly_criterion(self) -> float:
        """
        Calculate Kelly Criterion for optimal position sizing.

        Kelly% = W - [(1 - W) / R]
        Where:
        - W = Win rate (as decimal)
        - R = Win/Loss ratio

        Returns:
            Optimal position size as decimal (e.g., 0.25 = 25%)
            Returns 0 if formula produces negative result
        """
        if self.total_trades == 0 or self.avg_loss == 0:
            return 0.0

        win_rate_decimal = self.win_rate / 100
        win_loss_ratio = abs(self.avg_win / self.avg_loss)

        kelly = win_rate_decimal - ((1 - win_rate_decimal) / win_loss_ratio)
        return max(0.0, kelly)  # Don't return negative Kelly

    def to_dict(self) -> dict:
        """
        Serialize for storage/API response.

        Returns:
            Dictionary with all metrics and metadata
        """
        return {
            # Capital
            'starting_capital': self.starting_capital,
            'ending_capital': self.ending_capital,
            'total_return': self.total_return,
            'total_return_percent': self.total_return_percent,

            # Trade stats
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,

            # Performance
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'max_drawdown_percent': self.max_drawdown_percent,
            'expectancy': self.expectancy,
            'avg_r_multiple': self.avg_r_multiple,

            # Risk-adjusted
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'calmar_ratio': self.calmar_ratio,

            # Time-based
            'avg_hold_days': self.avg_hold_days,
            'max_hold_days': self.max_hold_days,

            # Position metrics
            'max_concurrent_positions': self.max_concurrent_positions,
            'avg_position_size_percent': self.avg_position_size_percent,

            # Strategy info
            'strategy_name': self.strategy_name,
            'scanner_name': self.scanner_name,
            'exit_strategy_name': self.exit_strategy_name,
            'timeframe': self.timeframe,

            # Metadata
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'trading_days': self.trading_days,

            # Detailed data
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'drawdown_curve': self.drawdown_curve,

            # Derived metrics
            'kelly_criterion': self.kelly_criterion
        }

    def summary(self) -> str:
        """
        Generate human-readable summary.

        Returns:
            Multi-line string with key metrics
        """
        return f"""
Backtest Results: {self.strategy_name}
{'=' * 50}
Period: {self.start_date.date() if self.start_date else 'N/A'} to {self.end_date.date() if self.end_date else 'N/A'}
Trading Days: {self.trading_days}

Capital:
  Starting: ${self.starting_capital:,.2f}
  Ending: ${self.ending_capital:,.2f}
  Return: ${self.total_return:,.2f} ({self.total_return_percent:+.2f}%)

Performance:
  Total Trades: {self.total_trades}
  Win Rate: {self.win_rate:.1f}% ({self.winning_trades}W / {self.losing_trades}L)
  Profit Factor: {self.profit_factor:.2f}x
  Expectancy: ${self.expectancy:,.2f} per trade
  Avg R-Multiple: {self.avg_r_multiple:.2f}R

Risk:
  Max Drawdown: {self.max_drawdown_percent:.2f}%
  Avg Win: ${self.avg_win:,.2f}
  Avg Loss: ${self.avg_loss:,.2f}
  Kelly%: {self.kelly_criterion*100:.1f}%

Position Management:
  Avg Hold: {self.avg_hold_days:.1f} days
  Max Hold: {self.max_hold_days} days
  Max Concurrent: {self.max_concurrent_positions} positions
""".strip()


@runtime_checkable
class BacktestProtocol(Protocol):
    """
    Interface for backtesting trading strategies.

    A backtest combines a scanner (entry signals), exit strategy (exit signals),
    and position sizer (risk management) to simulate historical trading.

    Example:
        >>> from interfaces import BacktestProtocol, BacktestResults
        >>> from strategies import get_backtest
        >>>
        >>> backtest: BacktestProtocol = get_backtest(
        >>>     scanner='daily_breakout',
        >>>     exit_strategy='smart_exits',
        >>>     capital=100_000
        >>> )
        >>>
        >>> results: BacktestResults = backtest.run(
        >>>     start_date=datetime(2024, 1, 1),
        >>>     end_date=datetime(2024, 12, 31)
        >>> )
        >>>
        >>> print(results.summary())
    """

    def run(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResults:
        """
        Run backtest over specified date range.

        Args:
            start_date: Start of backtest period
            end_date: End of backtest period (inclusive)

        Returns:
            BacktestResults with complete performance analysis

        Raises:
            ValueError: If date range is invalid
            ConnectionError: If market data unavailable
        """
        ...

    @property
    def scanner(self) -> "ScannerProtocol":
        """
        Get the scanner used by this backtest.

        Returns:
            Scanner protocol implementation
        """
        ...

    @property
    def exit_strategy(self) -> "ExitStrategyProtocol":
        """
        Get the exit strategy used by this backtest.

        Returns:
            Exit strategy protocol implementation
        """
        ...

    @property
    def starting_capital(self) -> float:
        """
        Get starting capital for backtest.

        Returns:
            Starting capital in dollars
        """
        ...
