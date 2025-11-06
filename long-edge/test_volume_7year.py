#!/usr/bin/env python3
"""
7-Year Volume Filter Test (2018-2025)

Tests 3 approaches on FULL 7-year period:
1. No volume filter (0.0x - accept all)
2. Soft filter (0.5x - PLTR would pass)
3. Current filter (1.2x - baseline)

Goal: See if PLTR-style quiet accumulation is worth catching
      or if volume really is a critical breakout signal
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


def run_year_test(year, volume_filter, api_key, secret_key):
    """Run full year backtest with specified volume filter."""

    if year == 2025:
        start = datetime(2025, 1, 1)
        end = datetime(2025, 10, 31)  # YTD
    else:
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31)

    backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)
    backtester.scanner.min_volume_ratio = volume_filter

    filter_label = {
        0.0: "No Filter (All)",
        0.5: "0.5x (Soft)",
        1.2: "1.2x (Current)"
    }.get(volume_filter, f"{volume_filter}x")

    print(f"\n{'─'*80}")
    print(f"📅 {year} - Volume Filter: {filter_label}")
    print(f"{'─'*80}")

    results = backtester.run(start, end)

    print(f"\n📊 RESULTS:")
    print(f"   Return: {results['return_pct']:+.2f}%")
    print(f"   Trades: {results['total_trades']}")
    print(f"   Win Rate: {results['win_rate']:.1f}%")
    print(f"   Profit Factor: {results['profit_factor']:.2f}x")
    print(f"   Avg Win: ${results['avg_win']:+,.0f}")
    print(f"   Avg Loss: ${results['avg_loss']:+,.0f}")
    print(f"   Max Drawdown: {results['max_drawdown']:.1f}%\n")

    return {
        'year': year,
        'filter': volume_filter,
        'return': results['return_pct'],
        'trades': results['total_trades'],
        'win_rate': results['win_rate'],
        'profit_factor': results['profit_factor'],
        'avg_win': results['avg_win'],
        'avg_loss': results['avg_loss'],
        'max_dd': results['max_drawdown']
    }


def print_year_comparison(year_results):
    """Print side-by-side comparison for one year."""

    year = year_results[0]['year']

    print(f"\n{'='*100}")
    print(f"{year} COMPARISON")
    print(f"{'='*100}\n")

    print(f"{'Filter':<20} {'Return':<12} {'Trades':<10} {'Win %':<10} {'PF':<8} {'Avg Win':<12} {'Avg Loss':<12}")
    print(f"{'─'*100}")

    for r in year_results:
        filter_label = {
            0.0: "No Filter",
            0.5: "0.5x Soft",
            1.2: "1.2x Current"
        }.get(r['filter'], f"{r['filter']}x")

        print(f"{filter_label:<20} "
              f"{r['return']:>+10.2f}%  "
              f"{r['trades']:>8}  "
              f"{r['win_rate']:>8.1f}%  "
              f"{r['profit_factor']:>6.2f}x  "
              f"${r['avg_win']:>+9.0f}  "
              f"${r['avg_loss']:>+9.0f}")

    # Highlight winner
    best = max(year_results, key=lambda x: x['return'])
    best_label = {0.0: "No Filter", 0.5: "0.5x", 1.2: "1.2x"}.get(best['filter'])

    print(f"\n✅ Winner: {best_label} ({best['return']:+.2f}%)")


def print_final_summary(all_results):
    """Print 7-year summary."""

    print(f"\n\n{'='*100}")
    print("7-YEAR SUMMARY (2018-2025)")
    print(f"{'='*100}\n")

    filters = [0.0, 0.5, 1.2]

    print(f"{'Filter':<20} {'Total Return':<15} {'Avg Annual':<15} {'Total Trades':<15} {'Avg Win %':<12}")
    print(f"{'─'*100}")

    for f in filters:
        filter_results = [r for r in all_results if r['filter'] == f]

        total_return = sum(r['return'] for r in filter_results)
        avg_annual = total_return / len(filter_results)
        total_trades = sum(r['trades'] for r in filter_results)
        avg_win_rate = sum(r['win_rate'] for r in filter_results) / len(filter_results)

        filter_label = {0.0: "No Filter", 0.5: "0.5x Soft", 1.2: "1.2x Current"}.get(f)

        print(f"{filter_label:<20} "
              f"{total_return:>+13.2f}%  "
              f"{avg_annual:>+13.2f}%  "
              f"{total_trades:>13}  "
              f"{avg_win_rate:>10.1f}%")

    # Determine winner
    print(f"\n{'='*100}")
    print("VERDICT")
    print(f"{'='*100}\n")

    filter_totals = {}
    for f in filters:
        filter_results = [r for r in all_results if r['filter'] == f]
        filter_totals[f] = sum(r['return'] for r in filter_results)

    best_filter = max(filter_totals, key=filter_totals.get)
    worst_filter = min(filter_totals, key=filter_totals.get)

    best_label = {0.0: "No Filter", 0.5: "0.5x Soft", 1.2: "1.2x Current"}.get(best_filter)
    worst_label = {0.0: "No Filter", 0.5: "0.5x Soft", 1.2: "1.2x Current"}.get(worst_filter)

    print(f"✅ WINNER: {best_label}")
    print(f"   Total 7-year return: {filter_totals[best_filter]:+.2f}%")
    print(f"   Average annual: {filter_totals[best_filter]/8:+.2f}%")
    print()
    print(f"❌ LOSER: {worst_label}")
    print(f"   Total 7-year return: {filter_totals[worst_filter]:+.2f}%")
    print(f"   Difference: {filter_totals[best_filter] - filter_totals[worst_filter]:+.2f}%")
    print()

    # Interpretation
    if best_filter == 1.2:
        print("💡 INTERPRETATION:")
        print("   Volume IS a critical signal. Low-volume breakouts are false signals.")
        print("   RECOMMENDATION: Keep 1.2x filter (or even increase it).")
    elif best_filter == 0.5:
        print("💡 INTERPRETATION:")
        print("   Quality stocks (like PLTR) accumulate quietly. Too strict filter misses them.")
        print("   RECOMMENDATION: Lower to 0.5x to catch PLTR-style moves.")
    else:  # 0.0
        print("💡 INTERPRETATION:")
        print("   Volume doesn't matter at all. Price action alone is sufficient.")
        print("   RECOMMENDATION: Remove volume filter entirely.")

    print(f"\n{'='*100}\n")


def main():
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        print("❌ ERROR: Missing Alpaca API credentials")
        return

    print(f"\n{'='*100}")
    print("7-YEAR VOLUME FILTER TEST (2018-2025)")
    print(f"{'='*100}\n")
    print("Testing 3 volume filters across 8 years:")
    print("  1. No filter (0.0x) - Accept all breakouts")
    print("  2. Soft filter (0.5x) - PLTR would pass")
    print("  3. Current filter (1.2x) - Current baseline")
    print()
    print("⏱️  Estimated time: 45-60 minutes (24 backtests)")
    print(f"{'='*100}\n")

    input("Press Enter to start...")

    years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    filters = [0.0, 0.5, 1.2]

    all_results = []

    for year in years:
        print(f"\n\n{'#'*100}")
        print(f"TESTING {year}")
        print(f"{'#'*100}")

        year_results = []

        for vol_filter in filters:
            try:
                result = run_year_test(year, vol_filter, api_key, secret_key)
                year_results.append(result)
                all_results.append(result)

            except Exception as e:
                print(f"\n❌ ERROR: {e}")
                continue

        # Print comparison for this year
        if year_results:
            print_year_comparison(year_results)

    # Print final summary
    if all_results:
        print_final_summary(all_results)

        # Save results
        output_file = Path(__file__).parent / 'volume_7year_results.json'
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)

        print(f"💾 Results saved to: {output_file}\n")

    else:
        print("\n❌ No results to display\n")


if __name__ == '__main__':
    main()
