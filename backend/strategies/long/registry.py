"""
Strategy registry and factory pattern.

Provides centralized registration and retrieval of trading strategies,
enabling configuration-based strategy selection without code changes.
"""

from typing import Dict, Type, Callable, Any
import logging

# Import interfaces using absolute import from backend
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from backend.interfaces import (
    ScannerProtocol,
    ExitStrategyProtocol,
    PositionSizerProtocol,
    BacktestProtocol
)

logger = logging.getLogger(__name__)

# Registry storage
_SCANNERS: Dict[str, Type[ScannerProtocol]] = {}
_EXIT_STRATEGIES: Dict[str, Type[ExitStrategyProtocol]] = {}
_POSITION_SIZERS: Dict[str, Type[PositionSizerProtocol]] = {}
_BACKTESTS: Dict[str, Type[BacktestProtocol]] = {}


# ============================================================================
# Registration Decorators
# ============================================================================

def register_scanner(name: str) -> Callable:
    """
    Decorator to register a scanner implementation.

    Usage:
        >>> from strategies.registry import register_scanner
        >>> from interfaces import ScannerProtocol, Candidate
        >>>
        >>> @register_scanner('daily_breakout')
        >>> class DailyBreakoutScanner:
        >>>     def scan(self, scan_date=None) -> List[Candidate]:
        >>>         ...
        >>>     @property
        >>>     def strategy_name(self) -> str:
        >>>         return 'daily_breakout'
        >>>     ...

    Args:
        name: Unique identifier for this scanner (e.g., 'daily_breakout')

    Returns:
        Decorator function
    """
    def decorator(cls: Type[ScannerProtocol]) -> Type[ScannerProtocol]:
        if name in _SCANNERS:
            logger.warning(f"Scanner '{name}' is already registered. Overwriting.")

        _SCANNERS[name] = cls
        logger.info(f"Registered scanner: '{name}' -> {cls.__name__}")
        return cls

    return decorator


def register_exit_strategy(name: str) -> Callable:
    """
    Decorator to register an exit strategy implementation.

    Usage:
        >>> from strategies.registry import register_exit_strategy
        >>> from interfaces import ExitStrategyProtocol, ExitSignal
        >>>
        >>> @register_exit_strategy('smart_exits')
        >>> class SmartExits:
        >>>     def check_exit(self, position, current_price, current_date, bars) -> ExitSignal:
        >>>         ...
        >>>     @property
        >>>     def strategy_name(self) -> str:
        >>>         return 'smart_exits'
        >>>     ...

    Args:
        name: Unique identifier for this exit strategy (e.g., 'smart_exits')

    Returns:
        Decorator function
    """
    def decorator(cls: Type[ExitStrategyProtocol]) -> Type[ExitStrategyProtocol]:
        if name in _EXIT_STRATEGIES:
            logger.warning(f"Exit strategy '{name}' is already registered. Overwriting.")

        _EXIT_STRATEGIES[name] = cls
        logger.info(f"Registered exit strategy: '{name}' -> {cls.__name__}")
        return cls

    return decorator


def register_position_sizer(name: str) -> Callable:
    """
    Decorator to register a position sizer implementation.

    Usage:
        >>> from strategies.registry import register_position_sizer
        >>> from interfaces import PositionSizerProtocol, PositionSize
        >>>
        >>> @register_position_sizer('fixed_risk')
        >>> class FixedRiskSizer:
        >>>     def calculate_size(self, account_equity, entry_price, stop_price, candidate) -> PositionSize:
        >>>         ...
        >>>     @property
        >>>     def strategy_name(self) -> str:
        >>>         return 'fixed_risk'
        >>>     ...

    Args:
        name: Unique identifier for this position sizer (e.g., 'fixed_risk')

    Returns:
        Decorator function
    """
    def decorator(cls: Type[PositionSizerProtocol]) -> Type[PositionSizerProtocol]:
        if name in _POSITION_SIZERS:
            logger.warning(f"Position sizer '{name}' is already registered. Overwriting.")

        _POSITION_SIZERS[name] = cls
        logger.info(f"Registered position sizer: '{name}' -> {cls.__name__}")
        return cls

    return decorator


def register_backtest(name: str) -> Callable:
    """
    Decorator to register a backtest implementation.

    Usage:
        >>> from strategies.registry import register_backtest
        >>> from interfaces import BacktestProtocol, BacktestResults
        >>>
        >>> @register_backtest('momentum_backtest')
        >>> class MomentumBacktest:
        >>>     def run(self, start_date, end_date) -> BacktestResults:
        >>>         ...

    Args:
        name: Unique identifier for this backtest (e.g., 'momentum_backtest')

    Returns:
        Decorator function
    """
    def decorator(cls: Type[BacktestProtocol]) -> Type[BacktestProtocol]:
        if name in _BACKTESTS:
            logger.warning(f"Backtest '{name}' is already registered. Overwriting.")

        _BACKTESTS[name] = cls
        logger.info(f"Registered backtest: '{name}' -> {cls.__name__}")
        return cls

    return decorator


# ============================================================================
# Factory Functions
# ============================================================================

def get_scanner(name: str, *args, **kwargs) -> ScannerProtocol:
    """
    Factory to get scanner by name.

    Args:
        name: Scanner name (must be registered)
        *args: Positional arguments for scanner constructor
        **kwargs: Keyword arguments for scanner constructor

    Returns:
        Scanner instance implementing ScannerProtocol

    Raises:
        ValueError: If scanner name not found in registry

    Example:
        >>> scanner = get_scanner('daily_breakout', api_key='xxx', secret='yyy')
        >>> candidates = scanner.scan()
    """
    if name not in _SCANNERS:
        available = ', '.join(_SCANNERS.keys())
        raise ValueError(
            f"Scanner '{name}' not found in registry. "
            f"Available scanners: {available}"
        )

    scanner_class = _SCANNERS[name]
    return scanner_class(*args, **kwargs)


def get_exit_strategy(name: str, *args, **kwargs) -> ExitStrategyProtocol:
    """
    Factory to get exit strategy by name.

    Args:
        name: Exit strategy name (must be registered)
        *args: Positional arguments for exit strategy constructor
        **kwargs: Keyword arguments for exit strategy constructor

    Returns:
        Exit strategy instance implementing ExitStrategyProtocol

    Raises:
        ValueError: If exit strategy name not found in registry

    Example:
        >>> exit_strategy = get_exit_strategy('smart_exits')
        >>> signal = exit_strategy.check_exit(position, price, date, bars)
    """
    if name not in _EXIT_STRATEGIES:
        available = ', '.join(_EXIT_STRATEGIES.keys())
        raise ValueError(
            f"Exit strategy '{name}' not found in registry. "
            f"Available exit strategies: {available}"
        )

    exit_class = _EXIT_STRATEGIES[name]
    return exit_class(*args, **kwargs)


def get_position_sizer(name: str, *args, **kwargs) -> PositionSizerProtocol:
    """
    Factory to get position sizer by name.

    Args:
        name: Position sizer name (must be registered)
        *args: Positional arguments for position sizer constructor
        **kwargs: Keyword arguments for position sizer constructor

    Returns:
        Position sizer instance implementing PositionSizerProtocol

    Raises:
        ValueError: If position sizer name not found in registry

    Example:
        >>> sizer = get_position_sizer('fixed_risk', risk_percent=1.0)
        >>> size = sizer.calculate_size(100_000, 100.0, 92.0, candidate)
    """
    if name not in _POSITION_SIZERS:
        available = ', '.join(_POSITION_SIZERS.keys())
        raise ValueError(
            f"Position sizer '{name}' not found in registry. "
            f"Available position sizers: {available}"
        )

    sizer_class = _POSITION_SIZERS[name]
    return sizer_class(*args, **kwargs)


def get_backtest(name: str, *args, **kwargs) -> BacktestProtocol:
    """
    Factory to get backtest by name.

    Args:
        name: Backtest name (must be registered)
        *args: Positional arguments for backtest constructor
        **kwargs: Keyword arguments for backtest constructor

    Returns:
        Backtest instance implementing BacktestProtocol

    Raises:
        ValueError: If backtest name not found in registry

    Example:
        >>> backtest = get_backtest('momentum_backtest', scanner='daily_breakout', capital=100_000)
        >>> results = backtest.run(start_date, end_date)
    """
    if name not in _BACKTESTS:
        available = ', '.join(_BACKTESTS.keys())
        raise ValueError(
            f"Backtest '{name}' not found in registry. "
            f"Available backtests: {available}"
        )

    backtest_class = _BACKTESTS[name]
    return backtest_class(*args, **kwargs)


# ============================================================================
# Registry Inspection
# ============================================================================

def list_scanners() -> Dict[str, Type[ScannerProtocol]]:
    """Get all registered scanners."""
    return _SCANNERS.copy()


def list_exit_strategies() -> Dict[str, Type[ExitStrategyProtocol]]:
    """Get all registered exit strategies."""
    return _EXIT_STRATEGIES.copy()


def list_position_sizers() -> Dict[str, Type[PositionSizerProtocol]]:
    """Get all registered position sizers."""
    return _POSITION_SIZERS.copy()


def list_backtests() -> Dict[str, Type[BacktestProtocol]]:
    """Get all registered backtests."""
    return _BACKTESTS.copy()


def list_all_strategies() -> dict:
    """
    Get all registered strategies across all types.

    Returns:
        Dictionary with keys: scanners, exit_strategies, position_sizers, backtests
    """
    return {
        'scanners': list(_SCANNERS.keys()),
        'exit_strategies': list(_EXIT_STRATEGIES.keys()),
        'position_sizers': list(_POSITION_SIZERS.keys()),
        'backtests': list(_BACKTESTS.keys())
    }


def print_registry() -> None:
    """Print all registered strategies (useful for debugging)."""
    all_strategies = list_all_strategies()

    print("\n" + "=" * 60)
    print("STRATEGY REGISTRY")
    print("=" * 60)

    print(f"\nScanners ({len(all_strategies['scanners'])}):")
    for name in sorted(all_strategies['scanners']):
        print(f"  - {name}")

    print(f"\nExit Strategies ({len(all_strategies['exit_strategies'])}):")
    for name in sorted(all_strategies['exit_strategies']):
        print(f"  - {name}")

    print(f"\nPosition Sizers ({len(all_strategies['position_sizers'])}):")
    for name in sorted(all_strategies['position_sizers']):
        print(f"  - {name}")

    print(f"\nBacktests ({len(all_strategies['backtests'])}):")
    for name in sorted(all_strategies['backtests']):
        print(f"  - {name}")

    print("\n" + "=" * 60 + "\n")
