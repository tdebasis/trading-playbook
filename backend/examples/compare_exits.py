"""
Compare Exit Strategies Example

Demonstrates strategy comparison by running the same scanner with different exit strategies.

This shows the power of the composable engine - we can easily A/B test different exits.

Usage:
    python3 compare_exits.py

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
from engine.comparison import compare_strategies, generate_comparison_csv
from strategies import get_scanner, get_exit_strategy
from data.cache import CachedDataClient

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise for comparison
    format='%(message)s'
)

def main():
    """Compare smart_exits vs scaled_exits on same period."""

    # Get API keys from environment
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        print("ERROR: Please set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables")
        sys.exit(1)

    print("\n" + "="*80)
    print("EXIT STRATEGY COMPARISON")
    print("="*80)
    print("\nComparing two exit strategies:")
    print("  1. Smart Exits - All-or-nothing with trailing stops")
    print("  2. Scaled Exits - Partial profit taking (25% at +8%, +15%, +25%)")
    print("\nSame scanner, same period, different exits.")
    print("="*80 + "\n")

    # Configure scanner (same for both)
    scanner = get_scanner('daily_breakout', api_key, secret_key)
    data_client = CachedDataClient(api_key, secret_key, cache_dir='./cache_comparison')

    # Test period
    start_date = datetime(2024, 4, 1)
    end_date = datetime(2024, 6, 30)

    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n")

    # Run backtests with different exit strategies
    results = []

    for exit_name in ['smart_exits', 'scaled_exits']:
        print(f"\nRunning: {scanner.strategy_name} + {exit_name}...")

        exit_strategy = get_exit_strategy(exit_name)

        engine = BacktestEngine(
            scanner=scanner,
            exit_strategy=exit_strategy,
            data_client=data_client,
            starting_capital=100000
        )

        result = engine.run(start_date, end_date)
        results.append(result)

        print(f"  Complete - Return: {result.total_return_percent:+.2f}% ({result.total_trades} trades)")

    # Print comparison
    comparison = compare_strategies(results)
    print(comparison)

    # Save to files
    os.makedirs('./output', exist_ok=True)

    # Save comparison text
    with open('./output/exit_comparison.txt', 'w') as f:
        f.write(comparison)

    # Save comparison CSV
    generate_comparison_csv(results, './output/exit_comparison.csv')

    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)

    smart_result = results[0]
    scaled_result = results[1]

    print(f"\nSmart Exits (all-or-nothing):")
    print(f"  • Captures full moves when right")
    print(f"  • Higher average win: ${smart_result.avg_win:,.0f}")
    print(f"  • Win rate: {smart_result.win_rate:.1f}%")
    print(f"  • Total return: {smart_result.total_return_percent:+.2f}%")

    print(f"\nScaled Exits (profit taking):")
    print(f"  • Banks profits incrementally")
    print(f"  • More trades (partial exits): {scaled_result.total_trades}")
    print(f"  • Win rate: {scaled_result.win_rate:.1f}%")
    print(f"  • Total return: {scaled_result.total_return_percent:+.2f}%")

    # Determine winner
    if smart_result.total_return_percent > scaled_result.total_return_percent:
        winner = "Smart Exits"
        diff = smart_result.total_return_percent - scaled_result.total_return_percent
    else:
        winner = "Scaled Exits"
        diff = scaled_result.total_return_percent - smart_result.total_return_percent

    print(f"\n🏆 Winner: {winner} (+{diff:.2f}% advantage)")

    print("\n" + "="*80)
    print("\nComparison files saved:")
    print("  • ./output/exit_comparison.txt")
    print("  • ./output/exit_comparison.csv")
    print()

if __name__ == '__main__':
    main()
