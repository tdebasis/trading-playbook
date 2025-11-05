"""
FINAL VALIDATION: Test on UNSEEN periods

This is the critical test to avoid overfitting.

We optimized the strategy on:
- Q1 2024, Q2 2024, Q2 2025, Q3 2025

Now testing on COMPLETELY UNSEEN periods:
- Q3 2024 (Aug-Oct 2024)
- Q4 2024 (Nov 2024-Jan 2025)

If the strategy performs similarly on unseen data, we've validated
it's not overfit and should generalize to future periods.

Final Strategy Settings:
- Volume: 1.2x (industry standard)
- Base volatility: 12% (matches real growth stock patterns)
- Trend: SMA20 > SMA50 (EMA didn't help)
- 15-day time stop (removes false breakouts)
- Hybrid trailing stops (progressive tightening)
"""

from datetime import datetime
import json
import sys
from pathlib import Path
import logging

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from backtest.daily_momentum_smart_exits import SmartExitBacktester
import os
from dotenv import load_dotenv

load_dotenv()


def test_period(name, start, end, api_key, secret_key):
    """Test a single period."""
    print(f"\n{'='*80}")
    print(f"TESTING: {name}")
    print(f"{'='*80}\n")

    backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)
    results = backtester.run(start, end)

    print(f"\n📊 {name} RESULTS:")
    print(f"   Return: {results.total_return_percent:+.2f}%")
    print(f"   Win Rate: {results.win_rate:.1f}%")
    print(f"   Profit Factor: {results.profit_factor:.2f}x")
    print(f"   Trades: {results.total_trades}")
    print(f"   Avg Win: ${results.avg_win:+,.0f}")
    print(f"   Avg Loss: ${results.avg_loss:+,.0f}")
    print(f"   Max Drawdown: {results.max_drawdown_percent:.1f}%")

    return {
        'period': name,
        'return': results.total_return_percent,
        'win_rate': results.win_rate,
        'profit_factor': results.profit_factor,
        'trades': results.total_trades,
        'avg_win': results.avg_win,
        'avg_loss': results.avg_loss,
        'max_drawdown': results.max_drawdown_percent,
    }


def main():
    """Final validation on completely unseen periods."""

    logging.basicConfig(level=logging.WARNING)

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    print("\n" + "="*80)
    print("FINAL VALIDATION - UNSEEN PERIODS")
    print("="*80)
    print("\nFinal Strategy:")
    print("  • Volume: 1.2x (was 1.5x)")
    print("  • Base volatility: 12% (was 8%)")
    print("  • Trend: SMA20 > SMA50")
    print("  • Exit: Hybrid trailing stops + 15-day time stop")
    print("\nTesting on COMPLETELY UNSEEN periods:")
    print("  • Q3 2024 (Aug-Oct 2024)")
    print("  • Q4 2024 (Nov 2024-Jan 2025)")
    print("\nThese periods were NOT used in optimization!")
    print("="*80)

    # Test UNSEEN periods
    periods = [
        ("Q3 2024", datetime(2024, 8, 1), datetime(2024, 10, 31)),
        ("Q4 2024", datetime(2024, 11, 1), datetime(2025, 1, 31)),
    ]

    results = []
    for name, start, end in periods:
        result = test_period(name, start, end, api_key, secret_key)
        results.append(result)

    # Summary
    print("\n\n" + "="*80)
    print("VALIDATION RESULTS - UNSEEN vs SEEN PERIODS")
    print("="*80 + "\n")

    print(f"{'Period':<15} {'Type':<12} {'Return':<12} {'Win Rate':<12} {'Trades':<10}")
    print("-" * 80)

    # Previously seen periods (what we optimized on)
    seen_results = [
        ('Q1 2024', 'SEEN', +5.80, 56.2, 16),
        ('Q2 2024', 'SEEN', -0.71, 63.6, 11),
        ('Q2 2025', 'SEEN', -1.43, 50.0, 20),
        ('Q3 2025', 'SEEN', +6.50, 57.9, 19),
    ]

    for period, type_, ret, wr, trades in seen_results:
        print(f"{period:<15} {type_:<12} {ret:>+8.2f}% {wr:>9.1f}% {trades:>8}")

    print()

    # Unseen periods (validation)
    for r in results:
        print(f"{r['period']:<15} {'UNSEEN':<12} {r['return']:>+8.2f}% {r['win_rate']:>9.1f}% {r['trades']:>8}")

    print("-" * 80)

    # Calculate averages
    seen_avg_return = (5.80 - 0.71 - 1.43 + 6.50) / 4
    unseen_avg_return = sum(r['return'] for r in results) / len(results)

    seen_avg_wr = (56.2 + 63.6 + 50.0 + 57.9) / 4
    unseen_avg_wr = sum(r['win_rate'] for r in results) / len(results)

    print(f"{'SEEN AVG':<15} {'':<12} {seen_avg_return:>+8.2f}% {seen_avg_wr:>9.1f}%")
    print(f"{'UNSEEN AVG':<15} {'':<12} {unseen_avg_return:>+8.2f}% {unseen_avg_wr:>9.1f}%")

    print()

    # Verdict
    print("\n" + "="*80)
    print("FINAL VERDICT")
    print("="*80 + "\n")

    difference = unseen_avg_return - seen_avg_return

    if unseen_avg_return > 2.0:
        print(f"✅ VALIDATION PASSED - Strategy performs well on unseen data!")
        print(f"   Unseen periods: {unseen_avg_return:+.2f}% average return")
        print(f"   Seen periods: {seen_avg_return:+.2f}% average return")

        if abs(difference) < 2.0:
            print(f"\n🎯 EXCELLENT: Consistent performance across seen/unseen periods")
            print(f"   Difference: {difference:+.2f}% (within acceptable range)")
            print(f"\n   This indicates the strategy is NOT overfit!")
            print(f"   The changes we made (1.2x volume, 12% base) are generalizing well.")
        else:
            if difference > 0:
                print(f"\n⚠️  CAUTION: Unseen data performs BETTER than seen data")
                print(f"   Difference: {difference:+.2f}%")
                print(f"   This is unusual but acceptable. May indicate we got lucky")
                print(f"   with Q3-Q4 2024, or those periods favored momentum strategies.")
            else:
                print(f"\n⚠️  CAUTION: Unseen data performs WORSE than seen data")
                print(f"   Difference: {difference:+.2f}%")
                print(f"   Still acceptable if unseen > 2%, but watch for degradation.")

        print(f"\n📈 RECOMMENDATION: Strategy is ready for forward testing")
        print(f"   • Use 1.2x volume threshold")
        print(f"   • Use 12% base volatility")
        print(f"   • Keep SMA20 (not EMA20)")
        print(f"   • Keep 15-day time stop")

    elif unseen_avg_return > 0:
        print(f"⚠️  MARGINAL VALIDATION - Strategy barely profitable on unseen data")
        print(f"   Unseen periods: {unseen_avg_return:+.2f}% average return")
        print(f"   Seen periods: {seen_avg_return:+.2f}% average return")
        print(f"\n   This suggests the strategy may be overfit to training periods.")
        print(f"   Consider:")
        print(f"   1. Testing on more unseen periods")
        print(f"   2. Using more conservative position sizing")
        print(f"   3. Accepting that momentum strategies are inherently volatile")

    else:
        print(f"❌ VALIDATION FAILED - Strategy loses money on unseen data")
        print(f"   Unseen periods: {unseen_avg_return:+.2f}% average return")
        print(f"   Seen periods: {seen_avg_return:+.2f}% average return")
        print(f"\n   The strategy is OVERFIT to the training periods!")
        print(f"   DO NOT trade this strategy - it won't generalize.")
        print(f"\n   Need to either:")
        print(f"   1. Start over with more conservative changes")
        print(f"   2. Test on much longer historical periods")
        print(f"   3. Reconsider the entire approach")

    # Statistical analysis
    print("\n" + "="*80)
    print("STATISTICAL ANALYSIS")
    print("="*80 + "\n")

    all_returns = [5.80, -0.71, -1.43, 6.50] + [r['return'] for r in results]
    avg_all = sum(all_returns) / len(all_returns)

    # Simple standard deviation
    variance = sum((r - avg_all) ** 2 for r in all_returns) / len(all_returns)
    std_dev = variance ** 0.5

    print(f"Overall Statistics (all 6 periods):")
    print(f"  Average return: {avg_all:+.2f}%")
    print(f"  Std deviation: {std_dev:.2f}%")
    print(f"  Return/Risk ratio: {avg_all / std_dev if std_dev > 0 else 0:.2f}")
    print()

    positive_periods = sum(1 for r in all_returns if r > 0)
    print(f"Positive periods: {positive_periods}/6 ({positive_periods/6*100:.0f}%)")
    print()

    if positive_periods >= 4:
        print("✅ Good: Strategy profitable in most periods (66%+)")
    elif positive_periods >= 3:
        print("⚠️  Acceptable: Strategy profitable in half the periods")
    else:
        print("❌ Poor: Strategy unprofitable in most periods")

    # Save results
    output = {
        'validation_type': 'walk_forward',
        'seen_periods': ['Q1 2024', 'Q2 2024', 'Q2 2025', 'Q3 2025'],
        'unseen_periods': ['Q3 2024', 'Q4 2024'],
        'unseen_results': results,
        'seen_avg_return': seen_avg_return,
        'unseen_avg_return': unseen_avg_return,
        'difference': difference,
        'validation_passed': unseen_avg_return > 2.0,
    }

    output_file = Path(__file__).parent.parent.parent / "final_validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n📊 Results saved to: {output_file}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
