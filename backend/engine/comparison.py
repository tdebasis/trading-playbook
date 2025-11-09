"""
Strategy Comparison Tools

Utilities for comparing multiple backtest results side-by-side.

Author: Claude AI + Tanam Bam Sinha
"""

from __future__ import annotations
from typing import List, Dict
from datetime import datetime
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from interfaces import BacktestResults, ScannerProtocol, ExitStrategyProtocol


def compare_strategies(results: List[BacktestResults]) -> str:
    """
    Compare multiple backtest results side-by-side.

    Args:
        results: List of BacktestResults to compare

    Returns:
        Formatted comparison table as string
    """
    if not results:
        return "No results to compare"

    # Build comparison table
    lines = []
    lines.append("\n" + "="*100)
    lines.append("STRATEGY COMPARISON")
    lines.append("="*100 + "\n")

    # Header
    header = f"{'Strategy':<40} {'Return':>12} {'Trades':>8} {'Win%':>8} {'PF':>8} {'MaxDD':>10} {'Avg R':>10}"
    lines.append(header)
    lines.append("-"*100)

    # Data rows
    for result in results:
        strategy_name = f"{result.scanner_name} + {result.exit_strategy_name}"
        if len(strategy_name) > 38:
            strategy_name = strategy_name[:35] + "..."

        row = (
            f"{strategy_name:<40} "
            f"{result.total_return_percent:>11.2f}% "
            f"{result.total_trades:>8} "
            f"{result.win_rate:>7.1f}% "
            f"{result.profit_factor:>7.2f}x "
            f"{result.max_drawdown_percent:>9.2f}% "
            f"{result.avg_r_multiple:>9.2f}R"
        )
        lines.append(row)

    lines.append("-"*100)

    # Detailed metrics section
    lines.append("\nDETAILED METRICS:")
    lines.append("="*100 + "\n")

    for i, result in enumerate(results, 1):
        lines.append(f"{i}. {result.scanner_name} + {result.exit_strategy_name}")
        lines.append(f"   Capital: ${result.starting_capital:,.0f} → ${result.ending_capital:,.0f} ({result.total_return_percent:+.2f}%)")
        lines.append(f"   Trades: {result.total_trades} ({result.winning_trades}W / {result.losing_trades}L / {result.total_trades - result.winning_trades - result.losing_trades}BE)")
        lines.append(f"   Win Rate: {result.win_rate:.1f}%")
        lines.append(f"   Profit Factor: {result.profit_factor:.2f}x")
        lines.append(f"   Avg Win: ${result.avg_win:,.0f} | Avg Loss: ${result.avg_loss:,.0f}")
        lines.append(f"   Expectancy: ${result.expectancy:,.0f} per trade")
        lines.append(f"   R-Multiple: Avg {result.avg_r_multiple:.2f}R | Best {result.best_trade:,.0f} | Worst {result.worst_trade:,.0f}")
        lines.append(f"   Max Drawdown: {result.max_drawdown_percent:.2f}%")
        lines.append(f"   Hold Days: Avg {result.avg_hold_days:.1f} | Max {result.max_hold_days}")
        lines.append("")

    lines.append("="*100)

    return "\n".join(lines)


def run_strategy_comparison(
    scanner: ScannerProtocol,
    exit_strategies: List[ExitStrategyProtocol],
    data_client,
    start_date: datetime,
    end_date: datetime,
    capital: float = 100000
) -> Dict[str, BacktestResults]:
    """
    Run same scanner with multiple exit strategies for comparison.

    Args:
        scanner: Scanner to use for all backtests
        exit_strategies: List of exit strategies to compare
        data_client: Data client for market data
        start_date: Backtest start date
        end_date: Backtest end date
        capital: Starting capital

    Returns:
        Dictionary mapping strategy name to BacktestResults
    """
    from .backtest_engine import BacktestEngine

    results = {}

    for exit_strategy in exit_strategies:
        print(f"\nRunning backtest: {scanner.strategy_name} + {exit_strategy.strategy_name}...")

        engine = BacktestEngine(
            scanner=scanner,
            exit_strategy=exit_strategy,
            data_client=data_client,
            starting_capital=capital
        )

        result = engine.run(start_date, end_date)
        results[exit_strategy.strategy_name] = result

    return results


def compare_periods(
    scanner: ScannerProtocol,
    exit_strategy: ExitStrategyProtocol,
    data_client,
    periods: List[tuple],  # List of (start_date, end_date, label) tuples
    capital: float = 100000
) -> Dict[str, BacktestResults]:
    """
    Run same strategy across multiple time periods.

    Args:
        scanner: Scanner to use
        exit_strategy: Exit strategy to use
        data_client: Data client for market data
        periods: List of (start_date, end_date, label) tuples
        capital: Starting capital

    Returns:
        Dictionary mapping period label to BacktestResults
    """
    from .backtest_engine import BacktestEngine

    results = {}

    for start_date, end_date, label in periods:
        print(f"\nRunning backtest for {label}: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")

        engine = BacktestEngine(
            scanner=scanner,
            exit_strategy=exit_strategy,
            data_client=data_client,
            starting_capital=capital
        )

        result = engine.run(start_date, end_date)
        results[label] = result

    return results


def print_comparison_summary(results_dict: Dict[str, BacktestResults], title: str = "COMPARISON SUMMARY"):
    """
    Print formatted comparison of results dictionary.

    Args:
        results_dict: Dictionary mapping strategy/period name to results
        title: Title for the comparison table
    """
    lines = []
    lines.append("\n" + "="*100)
    lines.append(title)
    lines.append("="*100 + "\n")

    # Header
    header = f"{'Name':<30} {'Return':>12} {'Trades':>8} {'Win%':>8} {'PF':>8} {'MaxDD':>10} {'Avg R':>10}"
    lines.append(header)
    lines.append("-"*100)

    # Data rows
    for name, result in results_dict.items():
        name_display = name if len(name) <= 28 else name[:25] + "..."

        row = (
            f"{name_display:<30} "
            f"{result.total_return_percent:>11.2f}% "
            f"{result.total_trades:>8} "
            f"{result.win_rate:>7.1f}% "
            f"{result.profit_factor:>7.2f}x "
            f"{result.max_drawdown_percent:>9.2f}% "
            f"{result.avg_r_multiple:>9.2f}R"
        )
        lines.append(row)

    lines.append("-"*100)
    lines.append("")

    print("\n".join(lines))


def generate_comparison_csv(results: List[BacktestResults], output_file: str):
    """
    Generate CSV file with comparison data.

    Args:
        results: List of BacktestResults
        output_file: Path to output CSV file
    """
    import csv

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'Scanner', 'Exit Strategy', 'Starting Capital', 'Ending Capital',
            'Total Return $', 'Total Return %', 'Total Trades',
            'Winning Trades', 'Losing Trades', 'Win Rate %',
            'Avg Win $', 'Avg Loss $', 'Profit Factor',
            'Expectancy $', 'Avg R-Multiple', 'Max Drawdown %',
            'Avg Hold Days', 'Max Hold Days'
        ])

        # Data rows
        for result in results:
            writer.writerow([
                result.scanner_name,
                result.exit_strategy_name,
                result.starting_capital,
                result.ending_capital,
                result.total_return,
                result.total_return_percent,
                result.total_trades,
                result.winning_trades,
                result.losing_trades,
                result.win_rate,
                result.avg_win,
                result.avg_loss,
                result.profit_factor,
                result.expectancy,
                result.avg_r_multiple,
                result.max_drawdown_percent,
                result.avg_hold_days,
                result.max_hold_days
            ])

    print(f"\nComparison data saved to: {output_file}")


def find_best_strategy(results: List[BacktestResults], metric: str = 'total_return_percent') -> BacktestResults:
    """
    Find best performing strategy by specified metric.

    Args:
        results: List of BacktestResults
        metric: Metric to optimize ('total_return_percent', 'profit_factor', 'win_rate', etc.)

    Returns:
        Best performing BacktestResults
    """
    if not results:
        raise ValueError("No results provided")

    return max(results, key=lambda r: getattr(r, metric, 0))


def rank_strategies(results: List[BacktestResults], metric: str = 'total_return_percent') -> List[tuple]:
    """
    Rank strategies by specified metric.

    Args:
        results: List of BacktestResults
        metric: Metric to rank by

    Returns:
        List of (rank, strategy_name, metric_value, result) tuples
    """
    sorted_results = sorted(results, key=lambda r: getattr(r, metric, 0), reverse=True)

    rankings = []
    for rank, result in enumerate(sorted_results, 1):
        strategy_name = f"{result.scanner_name} + {result.exit_strategy_name}"
        metric_value = getattr(result, metric, 0)
        rankings.append((rank, strategy_name, metric_value, result))

    return rankings
