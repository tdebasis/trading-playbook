"""
Trade models for backtesting results.

These capture the complete lifecycle of a trade from entry to exit.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class ExitReason(Enum):
    """Why a trade was exited."""
    STOP_LOSS = "stop_loss"
    END_OF_DAY = "end_of_day"


@dataclass
class Trade:
    """
    Represents a completed trade with entry, exit, and P&L.

    This is the fundamental unit of backtest results.
    Each trade represents one complete round-trip (entry + exit).

    Attributes:
        symbol: Stock symbol
        entry_time: When we entered
        entry_price: Price we entered at
        exit_time: When we exited
        exit_price: Price we exited at
        exit_reason: Why we exited (stop or EOD)
        shares: Number of shares traded

        # Risk management
        stop_price: Stop loss price

        # Signal metadata
        signal_date: Date of the signal
        pullback_time: When pullback occurred
        reversal_time: When reversal occurred
        reversal_strength: Reversal candle body %

        # Performance
        pnl: Profit/Loss in dollars
        pnl_percent: Profit/Loss as percentage
        mae: Maximum Adverse Excursion (worst drawdown during trade)
        mfe: Maximum Favorable Excursion (best profit during trade)

    Example:
        >>> trade = Trade(
        ...     symbol="QQQ",
        ...     entry_time=datetime(2024, 11, 1, 10, 32),
        ...     entry_price=450.25,
        ...     exit_time=datetime(2024, 11, 1, 15, 55),
        ...     exit_price=451.80,
        ...     exit_reason=ExitReason.END_OF_DAY,
        ...     shares=100,
        ...     stop_price=447.80,
        ...     pnl=155.0,
        ...     pnl_percent=0.34
        ... )
    """
    symbol: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    exit_reason: ExitReason
    shares: int
    stop_price: float

    # Signal details
    signal_date: datetime
    pullback_time: Optional[datetime] = None
    reversal_time: Optional[datetime] = None
    reversal_strength: Optional[float] = None

    # Performance metrics
    pnl: float = 0.0
    pnl_percent: float = 0.0
    mae: float = 0.0  # Maximum Adverse Excursion
    mfe: float = 0.0  # Maximum Favorable Excursion

    def __post_init__(self):
        """Calculate P&L if not provided."""
        if self.pnl == 0.0:
            self.pnl = (self.exit_price - self.entry_price) * self.shares
            self.pnl_percent = ((self.exit_price - self.entry_price) / self.entry_price) * 100

    def is_winner(self) -> bool:
        """Check if trade was profitable."""
        return self.pnl > 0

    def __str__(self) -> str:
        """Human-readable string representation."""
        win_loss = "WIN" if self.is_winner() else "LOSS"
        return (
            f"Trade({self.signal_date.date()} {self.symbol}): "
            f"{win_loss} ${self.pnl:+.2f} ({self.pnl_percent:+.2f}%) "
            f"[{self.exit_reason.value}]"
        )


@dataclass
class BacktestResults:
    """
    Complete results from a backtest run.

    This aggregates all trades and calculates overall statistics.

    Attributes:
        trades: List of all completed trades
        start_date: Backtest start date
        end_date: Backtest end date
        symbol: Symbol tested

        # Summary statistics (calculated automatically)
        total_trades: Total number of trades
        winning_trades: Number of winning trades
        losing_trades: Number of losing trades
        win_rate: Percentage of winning trades

        total_pnl: Total profit/loss
        avg_win: Average winning trade
        avg_loss: Average losing trade
        largest_win: Biggest winning trade
        largest_loss: Biggest losing trade

        expectancy: Expected value per trade
        profit_factor: Gross profit / Gross loss

    Example:
        >>> results = BacktestResults(
        ...     trades=trade_list,
        ...     start_date=date(2024, 1, 1),
        ...     end_date=date(2024, 3, 31),
        ...     symbol="QQQ"
        ... )
        >>> print(f"Win rate: {results.win_rate:.1f}%")
    """
    trades: list
    start_date: datetime
    end_date: datetime
    symbol: str

    # Summary stats (calculated)
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0

    total_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0

    expectancy: float = 0.0
    profit_factor: float = 0.0

    def __post_init__(self):
        """Calculate all statistics from trades."""
        if not self.trades:
            return

        self.total_trades = len(self.trades)

        # Separate winners and losers
        winners = [t for t in self.trades if t.is_winner()]
        losers = [t for t in self.trades if not t.is_winner()]

        self.winning_trades = len(winners)
        self.losing_trades = len(losers)
        self.win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        # P&L statistics
        self.total_pnl = sum(t.pnl for t in self.trades)

        if winners:
            self.avg_win = sum(t.pnl for t in winners) / len(winners)
            self.largest_win = max(t.pnl for t in winners)

        if losers:
            self.avg_loss = sum(t.pnl for t in losers) / len(losers)
            self.largest_loss = min(t.pnl for t in losers)

        # Expectancy: average P&L per trade
        self.expectancy = self.total_pnl / self.total_trades if self.total_trades > 0 else 0

        # Profit factor: gross profit / gross loss
        gross_profit = sum(t.pnl for t in winners) if winners else 0
        gross_loss = abs(sum(t.pnl for t in losers)) if losers else 0
        self.profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

    def summary(self) -> str:
        """Generate human-readable summary."""
        return f"""
BACKTEST RESULTS: {self.symbol}
Period: {self.start_date.date()} to {self.end_date.date()}

TRADES:
  Total Trades:    {self.total_trades}
  Winners:         {self.winning_trades} ({self.win_rate:.1f}%)
  Losers:          {self.losing_trades}

PERFORMANCE:
  Total P&L:       ${self.total_pnl:,.2f}
  Avg Win:         ${self.avg_win:,.2f}
  Avg Loss:        ${self.avg_loss:,.2f}
  Largest Win:     ${self.largest_win:,.2f}
  Largest Loss:    ${self.largest_loss:,.2f}

METRICS:
  Expectancy:      ${self.expectancy:.2f} per trade
  Profit Factor:   {self.profit_factor:.2f}
"""
