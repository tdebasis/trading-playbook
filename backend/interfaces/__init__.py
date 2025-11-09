"""
Trading strategy interfaces using Python Protocols (PEP 544).

This module provides standardized interfaces for all trading strategy components,
enabling plug-and-play architecture between research, backtesting, and production.

Key Interfaces:
    - ScannerProtocol: Entry signal generation
    - ExitStrategyProtocol: Exit signal generation
    - BacktestProtocol: Backtest execution
    - PositionSizerProtocol: Position sizing/risk management

Key Data Models:
    - Candidate: Scanner output (entry signals)
    - Position: Position tracking
    - ExitSignal: Exit strategy output
    - PositionSize: Position sizer output
    - BacktestResults: Backtest performance metrics

Example Usage:
    >>> from interfaces import ScannerProtocol, Candidate
    >>> from strategies import get_scanner
    >>>
    >>> # Get any scanner that implements the interface
    >>> scanner: ScannerProtocol = get_scanner('daily_breakout', api_key, secret)
    >>>
    >>> # Scan for opportunities
    >>> candidates: List[Candidate] = scanner.scan()
    >>>
    >>> # Work with standardized output
    >>> for candidate in candidates:
    >>>     if candidate.score >= 8.0:
    >>>         print(f"{candidate.symbol}: {candidate.entry_price} (risk: {candidate.risk_percent():.1f}%)")

Benefits:
    - Type safety with static type checking (mypy)
    - Interchangeable implementations (swap strategies without code changes)
    - Consistent data formats across all strategies
    - Easy testing with mock implementations
    - Clear contracts for strategy developers
"""

# Scanner interface
from .scanner import (
    ScannerProtocol,
    Candidate
)

# Exit strategy interface
from .exit_strategy import (
    ExitStrategyProtocol,
    ExitSignal
)

# Position model
from .position import (
    Position
)

# Backtest interface
from .backtest import (
    BacktestProtocol,
    BacktestResults
)

# Position sizer interface
from .position_sizer import (
    PositionSizerProtocol,
    PositionSize
)

__all__ = [
    # Protocols (interfaces)
    'ScannerProtocol',
    'ExitStrategyProtocol',
    'BacktestProtocol',
    'PositionSizerProtocol',

    # Data models
    'Candidate',
    'Position',
    'ExitSignal',
    'PositionSize',
    'BacktestResults',
]

# Version info
__version__ = '1.0.0'
__author__ = 'LongEdge Trading Systems'
__description__ = 'Standardized interfaces for trading strategies'
