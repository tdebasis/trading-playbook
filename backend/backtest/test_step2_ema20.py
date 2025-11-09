"""
Step 2: Test Volume 1.2x + EMA20

Incremental validation - build on Step 1's success.

Changes made:
- Volume threshold: 1.5x → 1.2x (from Step 1) ✅
- Trend detection: SMA20 → EMA20 (this step)

Everything else unchanged:
- 8% base volatility (will test 12% in Step 3)
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
    """Test Volume 1.2x + EMA20 on 4 periods."""

    logging.basicConfig(level=logging.WARNING)

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    print("\n" + "="*80)
    print("STEP 2: VOLUME 1.2X + EMA20 - VALIDATION TEST")
    print("="*80)
    print("Changes:")
    print("  1. Volume threshold 1.5x → 1.2x (from Step 1)")
    print("  2. Trend detection SMA20 → EMA20 (this step)")
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
    print("BEFORE vs AFTER - VOLUME 1.2X + EMA20")
    print("="*80 + "\n")

    print(f"{'Period':<12} {'BASELINE':<12} {'STEP 1':<12} {'STEP 2':<12} {'Trades':<15}")
    print("-" * 80)

    # Baseline results (with 1.5x volume, SMA20)
    baseline_results = {
        'Q1 2024': -1.94,
        'Q2 2024': -4.78,
        'Q2 2025': +1.21,
        'Q3 2025': +1.87,
    }

    # Step 1 results (with 1.2x volume, SMA20)
    step1_results = {
        'Q1 2024': +0.53,
        'Q2 2024': -4.11,
        'Q2 2025': +1.99,
        'Q3 2025': +3.29,
    }

    total_baseline = 0
    total_step1 = 0
    total_step2 = 0

    for r in results:
        baseline = baseline_results[r['period']]
        step1 = step1_results[r['period']]
        step2 = r['return']
        trades = r['trades']

        print(f"{r['period']:<12} {baseline:>+8.2f}% {step1:>10.2f}% {step2:>10.2f}% {trades:>13}")
        total_baseline += baseline
        total_step1 += step1
        total_step2 += step2

    print("-" * 80)
    avg_baseline = total_baseline / len(results)
    avg_step1 = total_step1 / len(results)
    avg_step2 = total_step2 / len(results)

    print(f"{'AVERAGE':<12} {avg_baseline:>+8.2f}% {avg_step1:>10.2f}% {avg_step2:>10.2f}%")

    improvement_from_baseline = avg_step2 - avg_baseline
    improvement_from_step1 = avg_step2 - avg_step1

    print(f"\nIMPROVEMENT FROM BASELINE: {improvement_from_baseline:+.2f}%")
    print(f"IMPROVEMENT FROM STEP 1: {improvement_from_step1:+.2f}%")

    # Verdict
    print("\n\n" + "="*80)
    print("STEP 2 VERDICT: VOLUME 1.2X + EMA20")
    print("="*80 + "\n")

    if improvement_from_step1 > 2:
        print(f"✅ SIGNIFICANT IMPROVEMENT: +{improvement_from_step1:.2f}% vs Step 1")
        print(f"   EMA20 helps significantly! Keep this change.")
        print(f"   Total improvement from baseline: {improvement_from_baseline:+.2f}%")
        print(f"   Proceed to Step 3: Add wider base (12%)")
    elif improvement_from_step1 > 0.5:
        print(f"✅ MODEST IMPROVEMENT: +{improvement_from_step1:.2f}% vs Step 1")
        print(f"   EMA20 helps a bit. Keep it.")
        print(f"   Total improvement from baseline: {improvement_from_baseline:+.2f}%")
        print(f"   Proceed to Step 3: Add wider base (12%)")
    elif improvement_from_step1 > -0.5:
        print(f"⚠️  NO REAL CHANGE: {improvement_from_step1:+.2f}% vs Step 1")
        print(f"   EMA20 doesn't help much.")
        print(f"   Decision: Keep Step 1 (volume 1.2x), skip EMA20, try Step 3 (wider base)")
    else:
        print(f"❌ WORSE RESULTS: {improvement_from_step1:+.2f}% vs Step 1")
        print(f"   EMA20 hurts performance.")
        print(f"   Decision: REVERT to Step 1 (volume 1.2x only), try different approach")

    # Trade count analysis
    print("\n" + "="*80)
    print("TRADE COUNT ANALYSIS")
    print("="*80 + "\n")

    step1_trades = {
        'Q1 2024': 6,
        'Q2 2024': 7,
        'Q2 2025': 8,
        'Q3 2025': 19,
    }

    total_trades_step1 = sum(step1_trades.values())
    total_trades_step2 = sum(r['trades'] for r in results)

    print(f"Total trades STEP 1 (1.2x vol, SMA20): {total_trades_step1} across 4 periods")
    print(f"Total trades STEP 2 (1.2x vol, EMA20): {total_trades_step2} across 4 periods")

    if total_trades_step2 > total_trades_step1:
        increase = total_trades_step2 - total_trades_step1
        pct_increase = ((total_trades_step2 / total_trades_step1 - 1) * 100)
        print(f"Increase: +{increase} trades ({pct_increase:+.0f}%)")

        if total_trades_step2 > total_trades_step1 * 1.2:
            print("\n✅ Good: More opportunities (20%+ increase)")
        else:
            print("\n⚠️  Modest: Slight increase in opportunities")
    elif total_trades_step2 < total_trades_step1:
        decrease = total_trades_step1 - total_trades_step2
        pct_decrease = ((total_trades_step1 / total_trades_step2 - 1) * 100)
        print(f"Decrease: -{decrease} trades (-{pct_decrease:.0f}%)")
        print("\n❌ Problem: EMA20 is MORE selective than SMA20 (unexpected)")
    else:
        print("\n⚠️  No change in trade count")

    # Save results
    output = {
        'step': 2,
        'changes': ['Volume 1.5x → 1.2x', 'SMA20 → EMA20'],
        'results': results,
        'avg_baseline': avg_baseline,
        'avg_step1': avg_step1,
        'avg_step2': avg_step2,
        'improvement_from_baseline': improvement_from_baseline,
        'improvement_from_step1': improvement_from_step1,
    }

    output_file = Path(__file__).parent.parent.parent / "step2_ema20_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n📊 Results saved to: {output_file}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
