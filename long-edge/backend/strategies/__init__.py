"""
Trading strategy implementations and registry.

This package contains:
- Strategy registry (registration and factory pattern)
- Scanner implementations (entry signals)
- Exit strategy implementations (exit signals)
- Position sizer implementations (risk management)
- Backtest implementations (simulation engines)

Usage:
    >>> from strategies import get_scanner, get_exit_strategy, get_position_sizer
    >>>
    >>> # Get strategy by name (configured externally)
    >>> scanner = get_scanner('daily_breakout', api_key, secret)
    >>> exit_strategy = get_exit_strategy('smart_exits')
    >>> sizer = get_position_sizer('fixed_risk', risk_percent=1.0)
    >>>
    >>> # Use strategies
    >>> candidates = scanner.scan()
    >>> for candidate in candidates:
    >>>     size = sizer.calculate_size(account, candidate.entry_price, candidate.suggested_stop, candidate)
    >>>     # ... execute trade
"""

# Import registry functions
from .registry import (
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

# Auto-import all strategy modules to trigger registration
# This ensures all strategies are registered when package is imported
import os
import importlib
from pathlib import Path

def _auto_register_strategies():
    """Automatically import all strategy modules to trigger @register decorators."""
    strategies_dir = Path(__file__).parent

    # Import all scanner implementations
    scanners_dir = strategies_dir / 'scanners'
    if scanners_dir.exists():
        for file in scanners_dir.glob('*.py'):
            if file.stem != '__init__' and not file.stem.startswith('_'):
                try:
                    importlib.import_module(f'strategies.scanners.{file.stem}')
                except Exception as e:
                    print(f"Warning: Could not import scanner {file.stem}: {e}")

    # Import all exit strategy implementations
    exits_dir = strategies_dir / 'exits'
    if exits_dir.exists():
        for file in exits_dir.glob('*.py'):
            if file.stem != '__init__' and not file.stem.startswith('_'):
                try:
                    importlib.import_module(f'strategies.exits.{file.stem}')
                except Exception as e:
                    print(f"Warning: Could not import exit strategy {file.stem}: {e}")

    # Import all position sizer implementations
    position_sizers_dir = strategies_dir / 'position_sizers'
    if position_sizers_dir.exists():
        for file in position_sizers_dir.glob('*.py'):
            if file.stem != '__init__' and not file.stem.startswith('_'):
                try:
                    importlib.import_module(f'strategies.position_sizers.{file.stem}')
                except Exception as e:
                    print(f"Warning: Could not import position sizer {file.stem}: {e}")

# Run auto-registration when package is imported
_auto_register_strategies()

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
