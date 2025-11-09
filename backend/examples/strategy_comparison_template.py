#!/usr/bin/env python3
"""
Strategy Comparison Template

This template demonstrates how to compare different strategies, scanners,
or exit configurations. Use this as a starting point for your own analysis.

Usage:
    1. Copy this file to your working directory (e.g., tmp-scripts/)
    2. Modify the configuration section below
    3. Run the comparison
    4. Results will be saved to docs/backtest-reports/

Author: Trading Playbook
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
import os

# ============================================================================
# CONFIGURATION - Modify this section for your comparison
# ============================================================================

# Date range
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 12, 31)

# Capital and position sizing
STARTING_CAPITAL = 100_000
MAX_POSITIONS = 3
POSITION_SIZE_PERCENT = 0.0667  # 6.67% per position

# Strategies to compare (add your own combinations)
STRATEGIES = [
    {
        'name': 'moderate_smart',
        'scanner': 'daily_breakout_moderate',
        'exit': 'smart_exits',
        'description': 'Moderate scanner with Smart Exits'
    },
    {
        'name': 'moderate_scaled',
        'scanner': 'daily_breakout_moderate',
        'exit': 'scaled_exits',
        'description': 'Moderate scanner with Scaled Exits'
    },
    # Add more strategy combinations here
]

# Report configuration
REPORT_FILENAME = f'strategy-comparison-{datetime.now().strftime("%Y-%m-%d")}.md'
REPORT_DIR = Path(__file__).parent.parent.parent / 'docs' / 'backtest-reports'

# ============================================================================
# IMPLEMENTATION - Generally no need to modify below
# ============================================================================

print("=" * 80)
print("STRATEGY COMPARISON")
print("=" * 80)
print(f"\nDate Range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
print(f"Capital: ${STARTING_CAPITAL:,}")
print(f"Max Positions: {MAX_POSITIONS}")
print(f"Position Size: {POSITION_SIZE_PERCENT * 100:.2f}%")
print(f"\nComparing {len(STRATEGIES)} strategies...\n")

# Load credentials
load_dotenv()
api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

if not api_key or not secret_key:
    print("❌ ERROR: Missing Alpaca API credentials in .env file")
    sys.exit(1)

# Import required modules
from scanner.long.daily_breakout_moderate import DailyBreakoutScannerModerate
from scanner.long.daily_breakout_relaxed import DailyBreakoutRelaxed
# Add more scanner imports as needed

from strategies import get_exit_strategy
from engine.backtest_engine import BacktestEngine
from alpaca.data.historical import StockHistoricalDataClient

# Initialize data client (shared across all backtests)
data_client = StockHistoricalDataClient(api_key, secret_key)

# Run comparisons
results = []

for idx, strategy in enumerate(STRATEGIES, 1):
    print(f"\n[{idx}/{len(STRATEGIES)}] Running: {strategy['name']}")
    print(f"    Scanner: {strategy['scanner']}")
    print(f"    Exit: {strategy['exit']}")

    # Initialize scanner (add your scanner logic here)
    if strategy['scanner'] == 'daily_breakout_moderate':
        scanner = DailyBreakoutScannerModerate(api_key, secret_key, universe='default')
    elif strategy['scanner'] == 'daily_breakout_relaxed':
        scanner = DailyBreakoutRelaxed(api_key, secret_key, universe='default')
    # Add more scanner types as needed
    else:
        print(f"    ⚠️  Unknown scanner: {strategy['scanner']}, skipping...")
        continue

    # Initialize exit strategy
    exit_strategy = get_exit_strategy(strategy['exit'])

    # Create backtest engine
    engine = BacktestEngine(
        scanner=scanner,
        exit_strategy=exit_strategy,
        data_client=data_client,
        starting_capital=STARTING_CAPITAL,
        max_positions=MAX_POSITIONS,
        position_size_percent=POSITION_SIZE_PERCENT
    )

    # Run backtest
    try:
        result = engine.run(START_DATE, END_DATE)
        results.append({
            'strategy': strategy,
            'result': result
        })

        # Print summary
        print(f"    ✓ Complete: {result.total_return_percent:+.2f}% return, {result.total_trades} trades")

    except Exception as e:
        print(f"    ❌ Error: {e}")
        continue

# ============================================================================
# RESULTS SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("COMPARISON RESULTS")
print("=" * 80 + "\n")

# Sort by return
results_sorted = sorted(results, key=lambda x: x['result'].total_return_percent, reverse=True)

print(f"{'Rank':<6} {'Strategy':<25} {'Return':<12} {'Trades':<8} {'Win Rate':<10} {'Max DD':<10}")
print("-" * 80)

for idx, item in enumerate(results_sorted, 1):
    strategy = item['strategy']
    result = item['result']

    print(f"{idx:<6} {strategy['name']:<25} "
          f"{result.total_return_percent:>+10.2f}% "
          f"{result.total_trades:>6}   "
          f"{result.win_rate:>8.1f}% "
          f"{result.max_drawdown_percent:>8.2f}%")

# ============================================================================
# GENERATE REPORT (Optional)
# ============================================================================

print(f"\n\n{'=' * 80}")
print("GENERATE DETAILED REPORT?")
print(f"{'=' * 80}")
print(f"\nReport will be saved to: {REPORT_DIR / REPORT_FILENAME}")
print("\nUncomment the report generation code below to create a markdown report.")

# UNCOMMENT THE FOLLOWING TO GENERATE A DETAILED REPORT:
#
# REPORT_DIR.mkdir(parents=True, exist_ok=True)
#
# with open(REPORT_DIR / REPORT_FILENAME, 'w') as f:
#     f.write(f"# Strategy Comparison Report\n\n")
#     f.write(f"**Date Range:** {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}\n")
#     f.write(f"**Capital:** ${STARTING_CAPITAL:,}\n")
#     f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
#
#     f.write("## Results Summary\n\n")
#     f.write("| Rank | Strategy | Return | Trades | Win Rate | Max DD |\n")
#     f.write("|------|----------|--------|--------|----------|--------|\n")
#
#     for idx, item in enumerate(results_sorted, 1):
#         strategy = item['strategy']
#         result = item['result']
#         f.write(f"| {idx} | {strategy['name']} | {result.total_return_percent:+.2f}% | "
#                f"{result.total_trades} | {result.win_rate:.1f}% | {result.max_drawdown_percent:.2f}% |\n")
#
#     # Add more detailed analysis sections as needed
#
# print(f"\n✓ Report saved to: {REPORT_DIR / REPORT_FILENAME}")

print("\n" + "=" * 80)
print("COMPARISON COMPLETE")
print("=" * 80 + "\n")
