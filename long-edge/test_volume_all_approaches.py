#!/usr/bin/env python3
"""
Complete Volume Filter Test (2018-2025)

Tests 4 approaches:
1. No volume filter (0.0x)
2. Soft filter (0.5x) - PLTR would pass
3. Current filter (1.2x) - Baseline
4. SCORING SYSTEM - Weak volume requires stronger price action

This is the definitive test to answer: "Is volume critical or not?"
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

from backtest.daily_momentum_smart_exits import SmartExitBacktester
from dotenv import load_dotenv

load_dotenv()


def run_hard_filter_test(year, volume_filter, api_key, secret_key):
    """Run test with hard volume filter."""

    if year == 2025:
        start = datetime(2025, 1, 1)
        end = datetime(2025, 10, 31)
    else:
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31)

    print(f"   📥 Creating backtester (volume filter: {volume_filter}x)...")
    backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)
    backtester.scanner.min_volume_ratio = volume_filter

    print(f"   🏃 Running {year} backtest...")
    results = backtester.run(start, end)
    print(f"   ✅ {year} complete: {results.total_return_percent:+.2f}% ({results.total_trades} trades)")

    return {
        'year': year,
        'approach': f'hard_{volume_filter}x',
        'filter': volume_filter,
        'return': results.total_return_percent,
        'trades': results.total_trades,
        'win_rate': results.win_rate,
        'profit_factor': results.profit_factor,
        'avg_win': results.avg_win,
        'avg_loss': results.avg_loss,
        'max_dd': results.max_drawdown_percent
    }


def run_scoring_test(year, api_key, secret_key):
    """Run test with SCORING SYSTEM."""

    if year == 2025:
        start = datetime(2025, 1, 1)
        end = datetime(2025, 10, 31)
    else:
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31)

    # Import the scoring scanner
    print(f"   📥 Loading scoring scanner...")
    from scanner.daily_breakout_scanner_scoring import DailyBreakoutScannerScoring

    # Create backtester with scoring scanner
    print(f"   📥 Creating backtester with scoring system...")
    backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)

    # Replace scanner with scoring version
    backtester.scanner = DailyBreakoutScannerScoring(api_key, secret_key)

    print(f"   🏃 Running {year} backtest (scoring may be slower)...")
    results = backtester.run(start, end)
    print(f"   ✅ {year} complete: {results.total_return_percent:+.2f}% ({results.total_trades} trades)")

    return {
        'year': year,
        'approach': 'scoring',
        'filter': 'scoring',
        'return': results.total_return_percent,
        'trades': results.total_trades,
        'win_rate': results.win_rate,
        'profit_factor': results.profit_factor,
        'avg_win': results.avg_win,
        'avg_loss': results.avg_loss,
        'max_dd': results.max_drawdown_percent
    }


def print_year_results(year, results):
    """Print results for one year."""

    print(f"\n{'='*110}")
    print(f"📅 {year} RESULTS")
    print(f"{'='*110}\n")

    print(f"{'Approach':<25} {'Return':<12} {'Trades':<10} {'Win %':<10} {'PF':<8} {'Avg Win':<12} {'Avg Loss':<12}")
    print(f"{'─'*110}")

    # Sort by return
    results_sorted = sorted(results, key=lambda x: x['return'], reverse=True)

    for r in results_sorted:
        if r['approach'] == 'scoring':
            label = "🎯 Scoring System"
        elif r['filter'] == 0.0:
            label = "No Filter (0.0x)"
        elif r['filter'] == 0.5:
            label = "Soft Filter (0.5x)"
        elif r['filter'] == 1.2:
            label = "Current (1.2x)"
        else:
            label = f"{r['filter']}x Filter"

        winner_mark = "✅ " if r == results_sorted[0] else "   "

        print(f"{winner_mark}{label:<22} "
              f"{r['return']:>+10.2f}%  "
              f"{r['trades']:>8}  "
              f"{r['win_rate']:>8.1f}%  "
              f"{r['profit_factor']:>6.2f}x  "
              f"${r['avg_win']:>+9.0f}  "
              f"${r['avg_loss']:>+9.0f}")

    best = results_sorted[0]
    worst = results_sorted[-1]
    spread = best['return'] - worst['return']

    print(f"\n💡 Best: {best['approach']:<15} Worst: {worst['approach']:<15} Spread: {spread:+.2f}%")


def print_final_summary(all_results):
    """Print 7-year summary."""

    print(f"\n\n{'='*110}")
    print("🏆 FINAL SUMMARY (2018-2025)")
    print(f"{'='*110}\n")

    approaches = ['hard_0.0x', 'hard_0.5x', 'hard_1.2x', 'scoring']

    print(f"{'Approach':<25} {'Total Return':<15} {'Avg Annual':<15} {'Total Trades':<15} {'Avg Win %':<12}")
    print(f"{'─'*110}")

    approach_data = {}

    for approach in approaches:
        approach_results = [r for r in all_results if r['approach'] == approach]

        if not approach_results:
            continue

        total_return = sum(r['return'] for r in approach_results)
        avg_annual = total_return / len(approach_results)
        total_trades = sum(r['trades'] for r in approach_results)
        avg_win_rate = sum(r['win_rate'] for r in approach_results) / len(approach_results)

        approach_data[approach] = {
            'total': total_return,
            'avg': avg_annual,
            'trades': total_trades,
            'win_rate': avg_win_rate
        }

        if approach == 'scoring':
            label = "🎯 Scoring System"
        elif approach == 'hard_0.0x':
            label = "No Filter"
        elif approach == 'hard_0.5x':
            label = "Soft Filter (0.5x)"
        elif approach == 'hard_1.2x':
            label = "Current (1.2x)"
        else:
            label = approach

        print(f"{label:<25} "
              f"{total_return:>+13.2f}%  "
              f"{avg_annual:>+13.2f}%  "
              f"{total_trades:>13}  "
              f"{avg_win_rate:>10.1f}%")

    # Determine winner
    print(f"\n{'='*110}")
    print("🎯 VERDICT")
    print(f"{'='*110}\n")

    best_approach = max(approach_data.keys(), key=lambda k: approach_data[k]['total'])
    worst_approach = min(approach_data.keys(), key=lambda k: approach_data[k]['total'])

    best_data = approach_data[best_approach]
    worst_data = approach_data[worst_approach]

    best_label = {
        'hard_0.0x': 'No Volume Filter',
        'hard_0.5x': 'Soft Filter (0.5x)',
        'hard_1.2x': 'Current Filter (1.2x)',
        'scoring': 'Scoring System'
    }.get(best_approach, best_approach)

    worst_label = {
        'hard_0.0x': 'No Volume Filter',
        'hard_0.5x': 'Soft Filter (0.5x)',
        'hard_1.2x': 'Current Filter (1.2x)',
        'scoring': 'Scoring System'
    }.get(worst_approach, worst_approach)

    print(f"✅ WINNER: {best_label}")
    print(f"   Total 7-year return: {best_data['total']:+.2f}%")
    print(f"   Average annual: {best_data['avg']:+.2f}%")
    print(f"   Total trades: {best_data['trades']}")
    print()
    print(f"❌ LOSER: {worst_label}")
    print(f"   Total 7-year return: {worst_data['total']:+.2f}%")
    print(f"   Performance gap: {best_data['total'] - worst_data['total']:+.2f}%")
    print()

    # Interpretation
    print("💡 INTERPRETATION:\n")

    if best_approach == 'hard_1.2x':
        print("   Volume IS critical. The 1.2x filter works best.")
        print("   Low-volume breakouts are false signals.")
        print("   📌 RECOMMENDATION: Keep 1.2x filter (or higher).\n")

    elif best_approach == 'hard_0.5x':
        print("   Quality stocks accumulate quietly (PLTR thesis correct).")
        print("   1.2x filter too strict, misses institutional accumulation.")
        print("   📌 RECOMMENDATION: Lower filter to 0.5x.\n")

    elif best_approach == 'hard_0.0x':
        print("   Volume doesn't matter - price action alone works.")
        print("   Filtering by volume hurts performance.")
        print("   📌 RECOMMENDATION: Remove volume filter entirely.\n")

    elif best_approach == 'scoring':
        print("   SCORING SYSTEM WINS!")
        print("   Low volume CAN work if compensated by strong price action.")
        print("   Binary filters are too rigid - nuanced scoring is better.")
        print("   📌 RECOMMENDATION: Implement scoring system in production.\n")

    # Show second best
    sorted_approaches = sorted(approach_data.keys(), key=lambda k: approach_data[k]['total'], reverse=True)
    second_best = sorted_approaches[1] if len(sorted_approaches) > 1 else None

    if second_best:
        second_label = {
            'hard_0.0x': 'No Filter',
            'hard_0.5x': '0.5x',
            'hard_1.2x': '1.2x',
            'scoring': 'Scoring'
        }.get(second_best)

        gap = approach_data[best_approach]['total'] - approach_data[second_best]['total']

        print(f"   Runner-up: {second_label} ({approach_data[second_best]['total']:+.2f}%)")
        print(f"   Gap to winner: {gap:+.2f}%")

        if abs(gap) < 5.0:
            print(f"   ⚠️  Close race! Difference is small (<5%). Consider testing more data.\n")

    print(f"{'='*110}\n")


def main():
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        print("❌ ERROR: Missing Alpaca API credentials")
        return

    print(f"\n{'='*110}")
    print("COMPREHENSIVE VOLUME TEST (2018-2025)")
    print(f"{'='*110}\n")
    print("Testing 4 approaches across 8 years:")
    print("  1. No filter (0.0x) - Accept all")
    print("  2. Soft filter (0.5x) - PLTR passes")
    print("  3. Current filter (1.2x) - Baseline")
    print("  4. 🎯 SCORING SYSTEM - Weak volume needs strong price")
    print()
    print("⏱️  Estimated time: 60-75 minutes (32 backtests)")
    print(f"{'='*110}\n")
    print("Starting test...\n")

    years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    filters = [0.0, 0.5, 1.2]

    all_results = []

    for year in years:
        print(f"\n\n{'#'*110}")
        print(f"TESTING {year}")
        print(f"{'#'*110}")

        year_results = []

        # Test hard filters
        for vol_filter in filters:
            print(f"\n🔵 Hard Filter: {vol_filter}x")
            try:
                result = run_hard_filter_test(year, vol_filter, api_key, secret_key)
                year_results.append(result)
                all_results.append(result)
                print(f"   ✅ Completed: {result['return']:+.2f}% ({result['trades']} trades)")
            except Exception as e:
                print(f"   ❌ ERROR: {e}")

        # Test scoring system
        print(f"\n🎯 Scoring System")
        try:
            result = run_scoring_test(year, api_key, secret_key)
            year_results.append(result)
            all_results.append(result)
            print(f"   ✅ Completed: {result['return']:+.2f}% ({result['trades']} trades)")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

        # Print year comparison
        if year_results:
            print_year_results(year, year_results)

    # Print final summary
    if all_results:
        print_final_summary(all_results)

        # Save results
        output_file = Path(__file__).parent / 'volume_all_approaches_results.json'
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)

        print(f"💾 Results saved to: {output_file}\n")

    else:
        print("\n❌ No results to display\n")


if __name__ == '__main__':
    main()
