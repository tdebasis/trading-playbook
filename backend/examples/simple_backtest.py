"""
Simple Backtest Example

Demonstrates basic usage of the composable backtest engine.

Usage:
    python3 simple_backtest.py

Author: Claude AI + Tanam Bam Sinha
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import logging

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from engine import BacktestEngine
from strategies import get_scanner, get_exit_strategy
from data.cache import CachedDataClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def main():
    """Run a simple backtest using composable engine."""

    # Get API keys from environment
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        print("ERROR: Please set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables")
        sys.exit(1)

    print("\n" + "="*80)
    print("SIMPLE BACKTEST EXAMPLE")
    print("="*80)
    print("\nThis example demonstrates the composable backtest engine:")
    print("  • Uses daily_breakout scanner")
    print("  • Uses smart_exits exit strategy")
    print("  • Runs on Q2 2024 data")
    print("\n" + "="*80 + "\n")

    # Configure components
    scanner = get_scanner('daily_breakout', api_key, secret_key)
    exit_strategy = get_exit_strategy('smart_exits')
    data_client = CachedDataClient(api_key, secret_key, cache_dir='./cache_simple_backtest')

    # Create backtest engine
    engine = BacktestEngine(
        scanner=scanner,
        exit_strategy=exit_strategy,
        data_client=data_client,
        starting_capital=100000,
        max_positions=3,
        position_size_percent=0.30
    )

    # Run backtest
    start_date = datetime(2024, 4, 1)
    end_date = datetime(2024, 6, 30)

    results = engine.run(start_date, end_date)

    # Print results
    print("\n" + "="*80)
    print("BACKTEST RESULTS")
    print("="*80 + "\n")

    print(results.summary())

    # Save to file
    output_file = './output/simple_backtest_results.txt'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        f.write(results.summary())

    print(f"\nResults saved to: {output_file}")

if __name__ == '__main__':
    main()
