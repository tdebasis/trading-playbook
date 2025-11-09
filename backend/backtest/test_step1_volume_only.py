"""
Step 1: Test Volume 1.2x ONLY

Single change validation - avoid overfitting by testing one change at a time.

Change made:
- Volume threshold: 1.5x → 1.2x (industry standard)

Everything else unchanged:
- SMA20 (not EMA20)
- 8% base volatility
- Price must be above base high
- 15-day time stop active
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

    return {
        'period': name,
        'return': results.total_return_percent,
        'win_rate': results.win_rate,
        'profit_factor': results.profit_factor,
        'trades': results.total_trades,
        'avg_win': results.avg_win,
        'avg_loss': results.avg_loss,
    }


def main():
    """Test volume change only on 4 periods."""

    logging.basicConfig(level=logging.WARNING)

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    print("\n" + "="*80)
    print("STEP 1: VOLUME 1.2X ONLY - VALIDATION TEST")
    print("="*80)
    print("Change: Volume threshold 1.5x → 1.2x")
    print("Everything else: UNCHANGED")
    print("Testing on 4 periods to validate improvement")
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

    # Summary
    print("\n\n" + "="*80)
    print("BEFORE vs AFTER - VOLUME 1.2X")
    print("="*80 + "\n")

    print(f"{'Period':<12} {'BEFORE':<12} {'AFTER':<12} {'Trades Before':<15} {'Trades After':<15}")
    print("-" * 80)

    # Previous results (with 1.5x volume)
    before_results = {
        'Q1 2024': -1.94,
        'Q2 2024': -4.78,
        'Q2 2025': +1.21,
        'Q3 2025': +1.87,
    }

    before_trades = {
        'Q1 2024': 5,
        'Q2 2024': 6,
        'Q2 2025': 7,
        'Q3 2025': 11,
    }

    total_before = 0
    total_after = 0

    for r in results:
        before = before_results[r['period']]
        after = r['return']
        trades_before = before_trades[r['period']]
        trades_after = r['trades']

        print(f"{r['period']:<12} {before:>+8.2f}% {after:>10.2f}% {trades_before:>13} {trades_after:>13}")
        total_before += before
        total_after += after

    print("-" * 80)
    avg_before = total_before / len(results)
    avg_after = total_after / len(results)

    print(f"{'AVERAGE':<12} {avg_before:>+8.2f}% {avg_after:>10.2f}%")

    improvement = avg_after - avg_before
    print(f"\nIMPROVEMENT: {improvement:+.2f}%")

    # Verdict
    print("\n\n" + "="*80)
    print("STEP 1 VERDICT: VOLUME 1.2X")
    print("="*80 + "\n")

    if improvement > 2:
        print(f"✅ SIGNIFICANT IMPROVEMENT: +{improvement:.2f}%")
        print(f"   Volume change helps! Keep this change.")
        print(f"   Proceed to Step 2: Add EMA20")
    elif improvement > 0.5:
        print(f"✅ MODEST IMPROVEMENT: +{improvement:.2f}%")
        print(f"   Volume change helps a bit. Keep it.")
        print(f"   Proceed to Step 2: Add EMA20")
    elif improvement > -0.5:
        print(f"⚠️  NO REAL CHANGE: {improvement:+.2f}%")
        print(f"   Volume change doesn't help much.")
        print(f"   Decision: Try Step 2 (EMA20) anyway - might work together")
    else:
        print(f"❌ WORSE RESULTS: {improvement:+.2f}%")
        print(f"   Volume change hurts performance.")
        print(f"   Decision: REVERT to 1.5x volume, try different approach")

    # Trade count analysis
    print("\n" + "="*80)
    print("TRADE COUNT ANALYSIS")
    print("="*80 + "\n")

    total_trades_before = sum(before_trades.values())
    total_trades_after = sum(r['trades'] for r in results)

    print(f"Total trades BEFORE (1.5x): {total_trades_before} across 4 periods")
    print(f"Total trades AFTER (1.2x): {total_trades_after} across 4 periods")
    print(f"Increase: +{total_trades_after - total_trades_before} trades ({((total_trades_after / total_trades_before - 1) * 100):+.0f}%)")

    if total_trades_after > total_trades_before * 1.3:
        print("\n✅ Good: More opportunities (30%+ increase)")
    elif total_trades_after > total_trades_before:
        print("\n⚠️  Modest: Slight increase in opportunities")
    else:
        print("\n❌ Problem: No increase in opportunities")

    # Save results
    output = {
        'step': 1,
        'change': 'Volume 1.5x → 1.2x',
        'results': results,
        'avg_before': avg_before,
        'avg_after': avg_after,
        'improvement': improvement,
    }

    output_file = Path(__file__).parent.parent.parent / "step1_volume_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n📊 Results saved to: {output_file}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
