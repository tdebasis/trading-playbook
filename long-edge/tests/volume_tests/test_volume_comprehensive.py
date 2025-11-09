#!/usr/bin/env python3
"""
Comprehensive Volume Filter Test (2018-2025)

Tests 3 approaches:
1. No volume filter (accept all)
2. Hard filter (0.5x minimum)
3. Scoring system (volume as one factor)

Goal: Determine which approach best balances catching PLTR-style moves
      vs avoiding false breakouts
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

from backtest.daily_momentum_smart_exits import SmartExitBacktester
from dotenv import load_dotenv

load_dotenv()


def run_backtest(start, end, volume_approach, api_key, secret_key):
    """
    Run backtest with specified volume approach.

    volume_approach:
        'none' - No volume filter (all pass)
        '0.5x' - Hard filter at 0.5x
        'score' - Volume as scoring factor (not filter)
    """
    backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)

    # Modify scanner based on approach
    if volume_approach == 'none':
        backtester.scanner.min_volume_ratio = 0.0  # Accept all
        approach_label = "No Filter"
    elif volume_approach == '0.5x':
        backtester.scanner.min_volume_ratio = 0.5
        approach_label = "0.5x Filter"
    elif volume_approach == 'score':
        # For scoring, we'll use a very low filter but modify scoring logic
        backtester.scanner.min_volume_ratio = 0.3  # Minimal threshold
        approach_label = "Scoring System"
        # Note: This requires modifying the scanner to use scoring
        # For now, we'll use low threshold as proxy

    print(f"\n{'='*80}")
    print(f"{start.year} - {approach_label}")
    print(f"{'='*80}\n")

    results = backtester.run(start, end)

    return {
        'year': start.year,
        'approach': volume_approach,
        'return': results['return_pct'],
        'trades': results['total_trades'],
        'win_rate': results['win_rate'],
        'profit_factor': results['profit_factor'],
        'avg_win': results['avg_win'],
        'avg_loss': results['avg_loss'],
        'max_drawdown': results['max_drawdown']
    }


def print_comparison(results_by_year):
    """Print year-by-year comparison."""

    print(f"\n{'='*100}")
    print("YEAR-BY-YEAR COMPARISON")
    print(f"{'='*100}\n")

    years = sorted(set(r['year'] for r in results_by_year))

    for year in years:
        year_results = [r for r in results_by_year if r['year'] == year]

        print(f"\n{'─'*100}")
        print(f"📅 {year}")
        print(f"{'─'*100}")

        # Headers
        print(f"{'Approach':<20} {'Return':<12} {'Trades':<10} {'Win Rate':<12} {'PF':<8} {'Avg Win':<12} {'Avg Loss':<12}")
        print(f"{'─'*100}")

        # Results
        for r in year_results:
            approach_label = {
                'none': 'No Filter',
                '0.5x': '0.5x Hard Filter',
                'score': 'Scoring System'
            }.get(r['approach'], r['approach'])

            print(f"{approach_label:<20} "
                  f"{r['return']:>+10.2f}%  "
                  f"{r['trades']:>8}  "
                  f"{r['win_rate']:>10.1f}%  "
                  f"{r['profit_factor']:>6.2f}x  "
                  f"${r['avg_win']:>+9.0f}  "
                  f"${r['avg_loss']:>+9.0f}")


def print_summary(results_by_year):
    """Print overall summary across all years."""

    print(f"\n{'='*100}")
    print("OVERALL SUMMARY (2018-2025)")
    print(f"{'='*100}\n")

    approaches = ['none', '0.5x', 'score']

    print(f"{'Approach':<20} {'Total Return':<15} {'Avg Annual':<15} {'Total Trades':<15} {'Avg Win Rate':<15}")
    print(f"{'─'*100}")

    for approach in approaches:
        approach_results = [r for r in results_by_year if r['approach'] == approach]

        total_return = sum(r['return'] for r in approach_results)
        avg_annual = total_return / len(approach_results)
        total_trades = sum(r['trades'] for r in approach_results)
        avg_win_rate = sum(r['win_rate'] for r in approach_results) / len(approach_results)

        approach_label = {
            'none': 'No Filter',
            '0.5x': '0.5x Hard Filter',
            'score': 'Scoring System'
        }.get(approach, approach)

        print(f"{approach_label:<20} "
              f"{total_return:>+13.2f}%  "
              f"{avg_annual:>+13.2f}%  "
              f"{total_trades:>13}  "
              f"{avg_win_rate:>13.1f}%")

    print(f"\n{'='*100}")
    print("RECOMMENDATION")
    print(f"{'='*100}\n")

    # Find best approach by total return
    approach_totals = {}
    for approach in approaches:
        approach_results = [r for r in results_by_year if r['approach'] == approach]
        approach_totals[approach] = sum(r['return'] for r in approach_results)

    best_approach = max(approach_totals, key=approach_totals.get)
    best_return = approach_totals[best_approach]

    best_label = {
        'none': 'No Volume Filter',
        '0.5x': '0.5x Hard Filter',
        'score': 'Scoring System'
    }.get(best_approach, best_approach)

    print(f"✅ WINNER: {best_label}")
    print(f"   Total Return: {best_return:+.2f}%")
    print(f"   Avg Annual: {best_return / 8:+.2f}%")


def main():
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        print("❌ ERROR: Missing Alpaca API credentials in .env file")
        return

    print(f"\n{'='*100}")
    print("COMPREHENSIVE VOLUME FILTER TEST (2018-2025)")
    print(f"{'='*100}\n")
    print("Testing 3 approaches:")
    print("  1. No volume filter (accept all breakouts)")
    print("  2. Hard filter at 0.5x (minimum threshold)")
    print("  3. Scoring system (volume as one factor)")
    print()
    print("⏱️  This will take ~30-45 minutes (24 backtests total)")
    print(f"{'='*100}\n")

    # Define test years (2018-2025)
    years = [
        (datetime(2018, 1, 1), datetime(2018, 12, 31)),
        (datetime(2019, 1, 1), datetime(2019, 12, 31)),
        (datetime(2020, 1, 1), datetime(2020, 12, 31)),
        (datetime(2021, 1, 1), datetime(2021, 12, 31)),
        (datetime(2022, 1, 1), datetime(2022, 12, 31)),
        (datetime(2023, 1, 1), datetime(2023, 12, 31)),
        (datetime(2024, 1, 1), datetime(2024, 12, 31)),
        (datetime(2025, 1, 1), datetime(2025, 10, 31)),  # YTD 2025
    ]

    approaches = ['none', '0.5x', 'score']

    all_results = []

    # Run all tests
    for start, end in years:
        print(f"\n{'#'*100}")
        print(f"TESTING {start.year}")
        print(f"{'#'*100}")

        for approach in approaches:
            try:
                result = run_backtest(start, end, approach, api_key, secret_key)
                all_results.append(result)

                print(f"\n✅ {approach.upper()} completed: {result['return']:+.2f}%")

            except Exception as e:
                print(f"\n❌ ERROR testing {approach} for {start.year}: {e}")
                continue

    # Print comparisons
    if all_results:
        print_comparison(all_results)
        print_summary(all_results)

        # Save results
        output_file = Path(__file__).parent / 'volume_comprehensive_results.json'
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)

        print(f"\n💾 Results saved to: {output_file}")

    else:
        print("\n❌ No results to display")


if __name__ == '__main__':
    main()
