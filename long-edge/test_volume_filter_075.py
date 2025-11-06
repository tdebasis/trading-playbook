"""
Test 0.75x Volume Filter vs Current 1.2x Filter
Quarter-by-Quarter Comparison for 2025

Tests hypothesis: Lowering volume filter catches more quality moves (like PLTR quiet accumulation)
"""

from datetime import datetime
import json
import sys
from pathlib import Path
import logging

backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from backtest.daily_momentum_smart_exits import SmartExitBacktester
import os
from dotenv import load_dotenv

load_dotenv()

# Suppress scanner logs for cleaner output
logging.basicConfig(level=logging.WARNING)


def run_quarter_test(quarter_name, start, end, api_key, secret_key, volume_filter):
    """Test a single quarter with specified volume filter."""

    print(f"\n{'='*80}")
    print(f"{quarter_name} - Volume Filter: {volume_filter}x")
    print(f"{'='*80}")

    backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)

    # Override the scanner's volume filter
    backtester.scanner.min_volume_ratio = volume_filter

    results = backtester.run(start, end)

    print(f"\n📊 RESULTS:")
    print(f"   Return: {results.total_return_percent:+.2f}%")
    print(f"   Trades: {results.total_trades}")
    print(f"   Win Rate: {results.win_rate:.1f}%")
    print(f"   Profit Factor: {results.profit_factor:.2f}x")
    print(f"   Avg Win: ${results.avg_win:+,.0f}")
    print(f"   Avg Loss: ${results.avg_loss:+,.0f}")
    print(f"   Max Drawdown: {results.max_drawdown_percent:.1f}%")

    return {
        'quarter': quarter_name,
        'volume_filter': volume_filter,
        'return': results.total_return_percent,
        'trades': results.total_trades,
        'win_rate': results.win_rate,
        'profit_factor': results.profit_factor,
        'avg_win': results.avg_win,
        'avg_loss': results.avg_loss,
        'max_drawdown': results.max_drawdown_percent,
    }


def main():
    """Run quarter-by-quarter comparison for 2025."""

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    print("\n" + "="*80)
    print("VOLUME FILTER TEST: 0.75x vs 1.2x (Current)")
    print("="*80)
    print("\nTesting full year 2025 quarter-by-quarter")
    print("Hypothesis: 0.75x filter catches more quality moves (PLTR-style quiet accumulation)")
    print("\nBenchmark to beat (1.2x filter):")
    print("  Q1 2025: Not tested yet")
    print("  Q2 2025: -1.43%")
    print("  Q3 2025: +6.50%")
    print("="*80)

    # Define quarters for 2025
    quarters = [
        ("Q1 2025", datetime(2025, 1, 1), datetime(2025, 3, 31)),
        ("Q2 2025", datetime(2025, 4, 1), datetime(2025, 6, 30)),
        ("Q3 2025", datetime(2025, 7, 1), datetime(2025, 9, 30)),
    ]

    results_120 = []  # Current 1.2x filter
    results_075 = []  # New 0.75x filter

    # Test each quarter with both filters
    for quarter_name, start, end in quarters:

        print("\n\n" + "="*80)
        print(f"TESTING {quarter_name}")
        print("="*80)

        # Test with current 1.2x filter
        print(f"\n🔵 Test 1: Current Filter (1.2x volume)")
        result_120 = run_quarter_test(quarter_name, start, end, api_key, secret_key, 1.2)
        results_120.append(result_120)

        # Test with new 0.75x filter
        print(f"\n🟢 Test 2: New Filter (0.75x volume)")
        result_075 = run_quarter_test(quarter_name, start, end, api_key, secret_key, 0.75)
        results_075.append(result_075)

        # Quick comparison for this quarter
        print(f"\n{'='*80}")
        print(f"{quarter_name} COMPARISON")
        print(f"{'='*80}")

        return_diff = result_075['return'] - result_120['return']
        trades_diff = result_075['trades'] - result_120['trades']

        print(f"\n{'Metric':<20} {'1.2x Filter':<15} {'0.75x Filter':<15} {'Difference':<15}")
        print("-" * 80)
        print(f"{'Return':<20} {result_120['return']:>+12.2f}% {result_075['return']:>+13.2f}% {return_diff:>+13.2f}%")
        print(f"{'Trades':<20} {result_120['trades']:>12} {result_075['trades']:>13} {trades_diff:>+13}")
        print(f"{'Win Rate':<20} {result_120['win_rate']:>12.1f}% {result_075['win_rate']:>13.1f}% {result_075['win_rate']-result_120['win_rate']:>+13.1f}%")
        print(f"{'Profit Factor':<20} {result_120['profit_factor']:>12.2f}x {result_075['profit_factor']:>13.2f}x {result_075['profit_factor']-result_120['profit_factor']:>+13.2f}x")

        if return_diff > 0:
            print(f"\n✅ 0.75x filter OUTPERFORMED by {return_diff:+.2f}%")
        else:
            print(f"\n❌ 0.75x filter UNDERPERFORMED by {return_diff:+.2f}%")

    # Final Summary
    print("\n\n" + "="*80)
    print("FINAL SUMMARY - Full Year 2025")
    print("="*80)

    # Calculate yearly totals
    total_return_120 = sum(r['return'] for r in results_120)
    total_return_075 = sum(r['return'] for r in results_075)

    total_trades_120 = sum(r['trades'] for r in results_120)
    total_trades_075 = sum(r['trades'] for r in results_075)

    avg_win_rate_120 = sum(r['win_rate'] for r in results_120) / len(results_120)
    avg_win_rate_075 = sum(r['win_rate'] for r in results_075) / len(results_075)

    print(f"\n{'Metric':<25} {'1.2x Filter':<20} {'0.75x Filter':<20} {'Difference':<15}")
    print("-" * 90)
    print(f"{'Total Return (3Q)':<25} {total_return_120:>+17.2f}% {total_return_075:>+18.2f}% {total_return_075-total_return_120:>+13.2f}%")
    print(f"{'Total Trades':<25} {total_trades_120:>17} {total_trades_075:>18} {total_trades_075-total_trades_120:>+13}")
    print(f"{'Avg Win Rate':<25} {avg_win_rate_120:>17.1f}% {avg_win_rate_075:>18.1f}% {avg_win_rate_075-avg_win_rate_120:>+13.1f}%")

    print(f"\n{'Quarter-by-Quarter Breakdown:':<25}")
    print("-" * 90)

    for i, (r120, r075) in enumerate(zip(results_120, results_075)):
        diff = r075['return'] - r120['return']
        symbol = "✅" if diff > 0 else "❌"
        print(f"  {r120['quarter']:<15} 1.2x: {r120['return']:>+6.2f}%  |  0.75x: {r075['return']:>+6.2f}%  |  Diff: {diff:>+6.2f}% {symbol}")

    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)

    if total_return_075 > total_return_120:
        improvement = total_return_075 - total_return_120
        print(f"\n✅ SUCCESS: 0.75x filter OUTPERFORMED by {improvement:+.2f}%")
        print(f"\n   New filter caught {total_trades_075 - total_trades_120:+} more trades")
        print(f"   This confirms hypothesis: Lower volume filter catches quality moves")
        print(f"\n   💡 RECOMMENDATION: Switch to 0.75x volume filter")
    elif total_return_075 < total_return_120:
        decline = total_return_120 - total_return_075
        print(f"\n❌ FAILURE: 0.75x filter UNDERPERFORMED by {decline:.2f}%")
        print(f"\n   Lower filter caught {total_trades_075 - total_trades_120:+} trades")
        print(f"   But they were lower quality (more false breakouts)")
        print(f"\n   💡 RECOMMENDATION: Keep 1.2x filter OR test 1.0x as compromise")
    else:
        print(f"\n⚖️  NEUTRAL: Both filters performed the same")
        print(f"\n   💡 RECOMMENDATION: Keep simpler 1.2x filter")

    # Save results
    output = {
        'test_date': datetime.now().isoformat(),
        'test_description': 'Compare 0.75x vs 1.2x volume filter on 2025 quarters',
        'hypothesis': 'Lower volume catches PLTR-style quiet accumulation',
        'filter_120': {
            'total_return': total_return_120,
            'total_trades': total_trades_120,
            'avg_win_rate': avg_win_rate_120,
            'quarterly_results': results_120
        },
        'filter_075': {
            'total_return': total_return_075,
            'total_trades': total_trades_075,
            'avg_win_rate': avg_win_rate_075,
            'quarterly_results': results_075
        },
        'verdict': 'outperformed' if total_return_075 > total_return_120 else 'underperformed',
        'improvement': total_return_075 - total_return_120
    }

    output_file = Path(__file__).parent / "volume_filter_test_075_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n📊 Detailed results saved to: {output_file}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
