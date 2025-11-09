"""
Test "Let Winners Run" Strategy - No Time Stop

Pure trend following approach:
- Remove 15-day time stop
- Only exit on price action (hard stop, MA break, lower high, trailing stop)
- Let big winners develop over weeks/months

Testing across 4 periods to compare with previous strategy.
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
    print(f"   Max Drawdown: {results.max_drawdown_percent:.2f}%")

    return {
        'period': name,
        'return': results.total_return_percent,
        'win_rate': results.win_rate,
        'profit_factor': results.profit_factor,
        'trades': results.total_trades,
        'avg_win': results.avg_win,
        'avg_loss': results.avg_loss,
        'max_dd': results.max_drawdown_percent,
        'trades_detail': results.trades
    }


def main():
    """Test all periods and compare."""

    # Suppress verbose logging
    logging.basicConfig(level=logging.WARNING)

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    print("\n" + "="*80)
    print("LET WINNERS RUN STRATEGY - MULTI-PERIOD BACKTEST")
    print("="*80)
    print("Strategy: Daily breakouts + NO TIME STOP")
    print("Exit Criteria:")
    print("  1. Hard stop (-8%)")
    print("  2. MA break (trend reversal)")
    print("  3. Lower high (momentum fading)")
    print("  4. Hybrid trailing stop (progressive tightening)")
    print("  5. NO TIME STOP - Let winners run!")
    print("="*80)

    # Test all periods
    periods = [
        ("Q1 2024", datetime(2024, 1, 2), datetime(2024, 3, 31)),
        ("Q2 2024", datetime(2024, 5, 1), datetime(2024, 7, 31)),
        ("Q2 2025", datetime(2025, 5, 1), datetime(2025, 7, 31)),
        ("Q3 2025", datetime(2025, 8, 1), datetime(2025, 10, 31)),
    ]

    results = []
    for name, start, end in periods:
        result = test_period(name, start, end, api_key, secret_key)
        results.append(result)

    # Summary comparison
    print("\n\n" + "="*80)
    print("COMPREHENSIVE RESULTS - LET WINNERS RUN")
    print("="*80 + "\n")

    print(f"{'Period':<12} {'Return':<10} {'Win Rate':<10} {'PF':<8} {'Trades':<8} {'Avg Win':<12} {'Avg Loss':<12}")
    print("-" * 80)

    total_return = 0
    total_win_rate = 0
    total_pf = 0

    for r in results:
        print(f"{r['period']:<12} {r['return']:>+8.2f}% {r['win_rate']:>8.1f}% "
              f"{r['profit_factor']:>6.2f}x {r['trades']:>6} "
              f"${r['avg_win']:>9,.0f} ${r['avg_loss']:>10,.0f}")
        total_return += r['return']
        total_win_rate += r['win_rate']
        total_pf += r['profit_factor']

    print("-" * 80)
    avg_return = total_return / len(results)
    avg_win_rate = total_win_rate / len(results)
    avg_pf = total_pf / len(results)

    print(f"{'AVERAGE':<12} {avg_return:>+8.2f}% {avg_win_rate:>8.1f}% {avg_pf:>6.2f}x")

    # Load previous results for comparison
    print("\n\n" + "="*80)
    print("BEFORE vs AFTER COMPARISON")
    print("="*80 + "\n")

    print("BEFORE (With 15-day time stop):")
    print("  Q1 2024: -1.94%")
    print("  Q2 2024: -4.78%")
    print("  Q2 2025: +1.21%")
    print("  Q3 2025: +1.87%")
    print("  AVERAGE: -0.91%")
    print("  Annualized: ~-3.6%")
    print()

    print("AFTER (Let winners run - no time stop):")
    for r in results:
        print(f"  {r['period']}: {r['return']:+.2f}%")
    print(f"  AVERAGE: {avg_return:+.2f}%")
    print(f"  Annualized: ~{avg_return * 4:+.1f}%")

    improvement = avg_return - (-0.91)
    print(f"\n  IMPROVEMENT: {improvement:+.2f}%")

    # Verdict
    print("\n\n" + "="*80)
    print("VERDICT")
    print("="*80 + "\n")

    if avg_return > 5:
        print("🚀 MAJOR IMPROVEMENT!")
        print(f"   Removing time stop increased returns from -0.91% to {avg_return:+.2f}%")
        print(f"   Annualized: ~{avg_return * 4:+.1f}% per year")
        print(f"   Profit Factor: {avg_pf:.2f}x")
        print()
        print("   This validates the trend following principle:")
        print("   'Let winners run, cut losers short'")
        print()
        print("   READY FOR PAPER TRADING!")

    elif avg_return > 2:
        print("✅ SIGNIFICANT IMPROVEMENT!")
        print(f"   Returns improved from -0.91% to {avg_return:+.2f}%")
        print(f"   Annualized: ~{avg_return * 4:+.1f}% per year")
        print(f"   Profit Factor: {avg_pf:.2f}x")
        print()
        print("   Strategy is now profitable, though modest.")
        print()
        print("   NEXT STEPS:")
        print("   1. Paper trade for 2-4 weeks")
        print("   2. Consider expanding universe (more stocks)")
        print("   3. Test on additional periods")

    elif avg_return > 0:
        print("⚠️  MARGINAL IMPROVEMENT")
        print(f"   Returns improved from -0.91% to {avg_return:+.2f}%")
        print(f"   Now profitable but barely")
        print()
        print("   Removing time stop helped but not enough.")
        print()
        print("   CONSIDER:")
        print("   - Wider trailing stops (let winners breathe)")
        print("   - Remove MA break exit (too early)")
        print("   - Expand stock universe")

    else:
        print("❌ NO IMPROVEMENT")
        print(f"   Returns: {avg_return:+.2f}% (vs -0.91% before)")
        print(f"   Still losing money")
        print()
        print("   The problem is not the time stop.")
        print("   Fundamental issues:")
        print("   - Entry criteria may be too selective")
        print("   - Market conditions unfavorable")
        print("   - Need different approach")

    # Exit reason breakdown
    print("\n\n" + "="*80)
    print("EXIT REASON BREAKDOWN")
    print("="*80 + "\n")

    exit_counts = {}
    for r in results:
        for trade in r['trades_detail']:
            reason = trade['exit_reason']
            exit_counts[reason] = exit_counts.get(reason, 0) + 1

    total_trades = sum(exit_counts.values())
    print(f"Total trades: {total_trades}\n")

    for reason, count in sorted(exit_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_trades) * 100
        print(f"  {reason:<15} {count:>3} trades ({pct:>5.1f}%)")

    print("\n" + "="*80 + "\n")

    # Save results
    output = {
        'strategy': 'Let Winners Run (No Time Stop)',
        'periods': results,
        'summary': {
            'avg_return': avg_return,
            'avg_win_rate': avg_win_rate,
            'avg_profit_factor': avg_pf,
            'improvement_vs_previous': improvement
        }
    }

    output_file = Path(__file__).parent.parent.parent / "let_winners_run_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"📊 Results saved to: {output_file}\n")


if __name__ == "__main__":
    main()
