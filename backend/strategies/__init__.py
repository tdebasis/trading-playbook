"""
Trading strategies - top-level module.

This module re-exports the registry functions from strategies.long,
making them available as `from strategies import get_exit_strategy`.

The long/short structure is organizational but transparent to users.
"""

# Re-export all registry functions from strategies.long
from .long import (
    # Registration decorators
    register_scanner,
    register_exit_strategy,
    register_position_sizer,
    register_backtest,

    # Factory functions
    get_scanner,
    get_exit_strategy,
    get_position_sizer,
    get_backtest,

    # Registry inspection
    list_scanners,
    list_exit_strategies,
    list_position_sizers,
    list_backtests,
    list_all_strategies,
    print_registry
)

__all__ = [
    # Registration
    'register_scanner',
    'register_exit_strategy',
    'register_position_sizer',
    'register_backtest',

    # Factory
    'get_scanner',
    'get_exit_strategy',
    'get_position_sizer',
    'get_backtest',

    # Inspection
    'list_scanners',
    'list_exit_strategies',
    'list_position_sizers',
    'list_backtests',
    'list_all_strategies',
    'print_registry',
]
