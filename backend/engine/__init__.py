"""
Composable Backtest Engine

Provides a generic backtest engine that accepts scanners and exit strategies
via the standardized interfaces, enabling mix-and-match strategy composition.

Key Components:
- BacktestEngine: Main orchestration engine
- Metrics: Performance calculation utilities
- Comparison: Strategy comparison tools

Example Usage:
    from engine import BacktestEngine
    from strategies import get_scanner, get_exit_strategy

    scanner = get_scanner('daily_breakout', api_key, secret_key)
    exit_strategy = get_exit_strategy('smart_exits')

    engine = BacktestEngine(
        scanner=scanner,
        exit_strategy=exit_strategy,
        data_client=data_client,
        starting_capital=100000
    )

    results = engine.run(start_date, end_date)
    print(results.summary())
"""

from .backtest_engine import BacktestEngine
from .metrics import calculate_backtest_metrics, calculate_max_drawdown
from .comparison import compare_strategies, run_strategy_comparison

__all__ = [
    'BacktestEngine',
    'calculate_backtest_metrics',
    'calculate_max_drawdown',
    'compare_strategies',
    'run_strategy_comparison'
]
