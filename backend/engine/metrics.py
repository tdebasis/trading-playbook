"""
Backtest Metrics Calculation

Reusable performance calculation utilities extracted from duplicated backtest code.

Author: Claude AI + Tanam Bam Sinha
"""

from __future__ import annotations
from typing import List, Dict
from datetime import datetime
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from interfaces import BacktestResults, Position


def calculate_backtest_metrics(
    trades: List[Position],
    equity_curve: List[float],
    starting_capital: float,
    start_date: datetime,
    end_date: datetime,
    scanner_name: str = "",
    exit_strategy_name: str = ""
) -> BacktestResults:
    """
    Calculate comprehensive backtest metrics from trades and equity curve.

    This function extracts all the metrics calculation logic that's
    currently duplicated across backtest implementations.

    Args:
        trades: List of closed Position objects
        equity_curve: List of equity values over time
        starting_capital: Starting capital amount
        start_date: Backtest start date
        end_date: Backtest end date
        scanner_name: Name of scanner used
        exit_strategy_name: Name of exit strategy used

    Returns:
        BacktestResults dataclass with all metrics
    """
    # Trade statistics
    total_trades = len(trades)

    if total_trades == 0:
        # No trades - return empty results
        return BacktestResults(
            starting_capital=starting_capital,
            ending_capital=starting_capital,
            total_return=0.0,
            total_return_percent=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            profit_factor=0.0,
            max_drawdown_percent=0.0,
            avg_hold_days=0.0,
            max_hold_days=0,
            trades=[],
            equity_curve=equity_curve,
            scanner_name=scanner_name,
            exit_strategy_name=exit_strategy_name,
            start_date=start_date,
            end_date=end_date
        )

    # Separate winners and losers
    winners = [t for t in trades if t.realized_pnl() > 0]
    losers = [t for t in trades if t.realized_pnl() < 0]
    breakeven = [t for t in trades if t.realized_pnl() == 0]

    winning_trades = len(winners)
    losing_trades = len(losers)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    # P&L metrics
    avg_win = sum(t.realized_pnl() for t in winners) / len(winners) if winners else 0
    avg_loss = sum(t.realized_pnl() for t in losers) / len(losers) if losers else 0

    total_wins = sum(t.realized_pnl() for t in winners)
    total_losses = abs(sum(t.realized_pnl() for t in losers))
    profit_factor = total_wins / total_losses if total_losses > 0 else float('inf') if total_wins > 0 else 0

    # Capital tracking
    ending_capital = equity_curve[-1] if equity_curve else starting_capital
    total_return = ending_capital - starting_capital
    total_return_pct = (total_return / starting_capital) * 100

    # Drawdown
    max_dd_pct = calculate_max_drawdown(equity_curve)

    # Time metrics
    hold_days_list = [t.hold_days() for t in trades if t.exit_date]
    avg_hold_days = sum(hold_days_list) / len(hold_days_list) if hold_days_list else 0
    max_hold_days = max(hold_days_list) if hold_days_list else 0
    min_hold_days = min(hold_days_list) if hold_days_list else 0

    # R-multiple metrics
    r_multiples = [t.r_multiple() for t in trades if t.r_multiple() is not None]
    avg_r = sum(r_multiples) / len(r_multiples) if r_multiples else 0
    max_r = max(r_multiples) if r_multiples else 0
    min_r = min(r_multiples) if r_multiples else 0

    # Expectancy (average P&L per trade)
    expectancy = sum(t.realized_pnl() for t in trades) / len(trades) if trades else 0

    # Best and worst trades
    best_trade_pnl = max((t.realized_pnl() for t in trades), default=0)
    worst_trade_pnl = min((t.realized_pnl() for t in trades), default=0)
    best_trade_pct = max((t.realized_pnl_percent() for t in trades), default=0)
    worst_trade_pct = min((t.realized_pnl_percent() for t in trades), default=0)

    # MFE/MAE metrics
    avg_mfe = sum(t.max_favorable_excursion for t in trades) / len(trades) if trades else 0
    avg_mae = sum(t.max_adverse_excursion for t in trades) / len(trades) if trades else 0

    # Convert positions to trade dicts
    trade_dicts = [position_to_trade_dict(t) for t in trades]

    return BacktestResults(
        starting_capital=starting_capital,
        ending_capital=ending_capital,
        total_return=total_return,
        total_return_percent=total_return_pct,
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        max_drawdown_percent=max_dd_pct,
        avg_hold_days=avg_hold_days,
        max_hold_days=max_hold_days,
        trades=trade_dicts,
        equity_curve=equity_curve,
        scanner_name=scanner_name,
        exit_strategy_name=exit_strategy_name,
        start_date=start_date,
        end_date=end_date
        # Note: expectancy, avg_r_multiple, best_trade, worst_trade are calculated
        # as @property methods on BacktestResults, not init parameters
    )


def calculate_max_drawdown(equity_curve: List[float]) -> float:
    """
    Calculate maximum drawdown percentage from equity curve.

    Args:
        equity_curve: List of equity values over time

    Returns:
        Maximum drawdown as percentage (e.g., 15.5 for 15.5% drawdown)
    """
    if not equity_curve or len(equity_curve) < 2:
        return 0.0

    peak = equity_curve[0]
    max_dd = 0.0

    for equity in equity_curve:
        if equity > peak:
            peak = equity

        dd = ((peak - equity) / peak) * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd

    return max_dd


def position_to_trade_dict(position: Position) -> Dict:
    """
    Convert Position object to trade dictionary for BacktestResults.

    Args:
        position: Closed Position object

    Returns:
        Dictionary with trade information
    """
    trade_dict = {
        'symbol': position.symbol,
        'entry_date': position.entry_date.strftime('%Y-%m-%d'),
        'exit_date': position.exit_date.strftime('%Y-%m-%d') if position.exit_date else None,
        'entry_price': float(position.entry_price),
        'exit_price': float(position.exit_price) if position.exit_price else None,
        'shares': position.shares,
        'stop_price': float(position.stop_price),
        'pnl': float(position.realized_pnl()),
        'pnl_pct': float(position.realized_pnl_percent()),
        'hold_days': position.hold_days(),
        'exit_reason': position.exit_reason,
        'r_multiple': position.r_multiple(),
        'mfe': position.max_favorable_excursion,
        'mae': position.max_adverse_excursion
    }

    # Add partial exits if any
    if position.partial_exits:
        trade_dict['partial_exits'] = position.partial_exits
        trade_dict['original_shares'] = position.original_shares

    return trade_dict


def calculate_sharpe_ratio(equity_curve: List[float], risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio from equity curve.

    Args:
        equity_curve: List of equity values
        risk_free_rate: Annual risk-free rate (default 2%)

    Returns:
        Sharpe ratio (annualized)
    """
    if not equity_curve or len(equity_curve) < 2:
        return 0.0

    # Calculate daily returns
    returns = []
    for i in range(1, len(equity_curve)):
        ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1] if equity_curve[i-1] > 0 else 0
        returns.append(ret)

    if not returns:
        return 0.0

    # Calculate average return and std dev
    avg_return = sum(returns) / len(returns)
    variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
    std_dev = variance ** 0.5

    if std_dev == 0:
        return 0.0

    # Annualize (assuming ~252 trading days)
    daily_risk_free = (1 + risk_free_rate) ** (1/252) - 1
    sharpe = (avg_return - daily_risk_free) / std_dev * (252 ** 0.5)

    return sharpe


def calculate_sortino_ratio(equity_curve: List[float], risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sortino ratio (like Sharpe but only penalizes downside volatility).

    Args:
        equity_curve: List of equity values
        risk_free_rate: Annual risk-free rate (default 2%)

    Returns:
        Sortino ratio (annualized)
    """
    if not equity_curve or len(equity_curve) < 2:
        return 0.0

    # Calculate daily returns
    returns = []
    for i in range(1, len(equity_curve)):
        ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1] if equity_curve[i-1] > 0 else 0
        returns.append(ret)

    if not returns:
        return 0.0

    # Calculate average return
    avg_return = sum(returns) / len(returns)

    # Calculate downside deviation (only negative returns)
    downside_returns = [r for r in returns if r < 0]
    if not downside_returns:
        return float('inf') if avg_return > 0 else 0.0

    downside_variance = sum(r ** 2 for r in downside_returns) / len(downside_returns)
    downside_dev = downside_variance ** 0.5

    if downside_dev == 0:
        return float('inf') if avg_return > 0 else 0.0

    # Annualize
    daily_risk_free = (1 + risk_free_rate) ** (1/252) - 1
    sortino = (avg_return - daily_risk_free) / downside_dev * (252 ** 0.5)

    return sortino


def calculate_win_loss_ratio(trades: List[Position]) -> float:
    """
    Calculate ratio of average win to average loss.

    Args:
        trades: List of closed positions

    Returns:
        Win/loss ratio (e.g., 2.0 means avg win is 2x avg loss)
    """
    winners = [t.realized_pnl() for t in trades if t.realized_pnl() > 0]
    losers = [abs(t.realized_pnl()) for t in trades if t.realized_pnl() < 0]

    if not losers:
        return float('inf') if winners else 0.0

    avg_win = sum(winners) / len(winners) if winners else 0
    avg_loss = sum(losers) / len(losers) if losers else 0

    return avg_win / avg_loss if avg_loss > 0 else float('inf')
