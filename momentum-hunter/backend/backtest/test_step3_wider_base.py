"""
Step 3: Test Volume 1.2x + Wider Base (12%)

Incremental validation - build on Step 1's success, skip Step 2 (EMA didn't help).

Changes made:
- Volume threshold: 1.5x → 1.2x (from Step 1) ✅
- Base volatility: 8% → 12% (this step)

Everything else unchanged:
- Using SMA20 (EMA20 didn't help in Step 2)
- Price must be above base high
- 15-day time stop active

Why 12%? Analysis showed NVDA/PLTR bases were 10-20% wide, not 8%.
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
    """Test Volume 1.2x + Wider Base (12%) on 4 periods."""

    logging.basicConfig(level=logging.WARNING)

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    print("\n" + "="*80)
    print("STEP 3: VOLUME 1.2X + WIDER BASE (12%) - VALIDATION TEST")
    print("="*80)
    print("Changes:")
    print("  1. Volume threshold 1.5x → 1.2x (from Step 1)")
    print("  2. Base volatility 8% → 12% (this step)")
    print("Everything else: UNCHANGED (using SMA20, not EMA20)")
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
    print("BEFORE vs AFTER - VOLUME 1.2X + WIDER BASE")
    print("="*80 + "\n")

    print(f"{'Period':<12} {'BASELINE':<12} {'STEP 1':<12} {'STEP 3':<12} {'Trades':<15}")
    print("-" * 80)

    # Baseline results (with 1.5x volume, 8% base)
    baseline_results = {
        'Q1 2024': -1.94,
        'Q2 2024': -4.78,
        'Q2 2025': +1.21,
        'Q3 2025': +1.87,
    }

    # Step 1 results (with 1.2x volume, 8% base)
    step1_results = {
        'Q1 2024': +0.53,
        'Q2 2024': -4.11,
        'Q2 2025': +1.99,
        'Q3 2025': +3.29,
    }

    total_baseline = 0
    total_step1 = 0
    total_step3 = 0

    for r in results:
        baseline = baseline_results[r['period']]
        step1 = step1_results[r['period']]
        step3 = r['return']
        trades = r['trades']

        print(f"{r['period']:<12} {baseline:>+8.2f}% {step1:>10.2f}% {step3:>10.2f}% {trades:>13}")
        total_baseline += baseline
        total_step1 += step1
        total_step3 += step3

    print("-" * 80)
    avg_baseline = total_baseline / len(results)
    avg_step1 = total_step1 / len(results)
    avg_step3 = total_step3 / len(results)

    print(f"{'AVERAGE':<12} {avg_baseline:>+8.2f}% {avg_step1:>10.2f}% {avg_step3:>10.2f}%")

    improvement_from_baseline = avg_step3 - avg_baseline
    improvement_from_step1 = avg_step3 - avg_step1

    print(f"\nIMPROVEMENT FROM BASELINE: {improvement_from_baseline:+.2f}%")
    print(f"IMPROVEMENT FROM STEP 1: {improvement_from_step1:+.2f}%")

    # Verdict
    print("\n\n" + "="*80)
    print("STEP 3 VERDICT: VOLUME 1.2X + WIDER BASE (12%)")
    print("="*80 + "\n")

    if improvement_from_step1 > 2:
        print(f"✅ SIGNIFICANT IMPROVEMENT: +{improvement_from_step1:.2f}% vs Step 1")
        print(f"   Wider base helps significantly! Keep this change.")
        print(f"   Total improvement from baseline: {improvement_from_baseline:+.2f}%")
        print(f"   Ready for final validation on NEW periods")
    elif improvement_from_step1 > 0.5:
        print(f"✅ MODEST IMPROVEMENT: +{improvement_from_step1:.2f}% vs Step 1")
        print(f"   Wider base helps. Keep it.")
        print(f"   Total improvement from baseline: {improvement_from_baseline:+.2f}%")
        print(f"   Ready for final validation on NEW periods")
    elif improvement_from_step1 > -0.5:
        print(f"⚠️  NO REAL CHANGE: {improvement_from_step1:+.2f}% vs Step 1")
        print(f"   Wider base doesn't help much.")
        print(f"   Decision: Keep Step 1 (volume 1.2x only)")
        print(f"   Need to explore other changes or accept Step 1 as final")
    else:
        print(f"❌ WORSE RESULTS: {improvement_from_step1:+.2f}% vs Step 1")
        print(f"   Wider base hurts performance.")
        print(f"   Decision: REVERT to Step 1 (volume 1.2x, 8% base)")

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
    total_trades_step3 = sum(r['trades'] for r in results)

    print(f"Total trades STEP 1 (1.2x vol, 8% base): {total_trades_step1} across 4 periods")
    print(f"Total trades STEP 3 (1.2x vol, 12% base): {total_trades_step3} across 4 periods")

    if total_trades_step3 > total_trades_step1:
        increase = total_trades_step3 - total_trades_step1
        pct_increase = ((total_trades_step3 / total_trades_step1 - 1) * 100)
        print(f"Increase: +{increase} trades ({pct_increase:+.0f}%)")

        if total_trades_step3 > total_trades_step1 * 1.3:
            print("\n✅ Good: Many more opportunities (30%+ increase)")
            print("   This is what we wanted - catching NVDA/PLTR with wider bases")
        elif total_trades_step3 > total_trades_step1 * 1.1:
            print("\n⚠️  Modest: Some increase in opportunities (10-30%)")
        else:
            print("\n⚠️  Small: Slight increase in opportunities (<10%)")
    elif total_trades_step3 < total_trades_step1:
        decrease = total_trades_step1 - total_trades_step3
        pct_decrease = ((total_trades_step1 / total_trades_step3 - 1) * 100)
        print(f"Decrease: -{decrease} trades (-{pct_decrease:.0f}%)")
        print("\n❌ Problem: Wider base is MORE selective (unexpected)")
    else:
        print("\n⚠️  No change in trade count")

    # Quality analysis
    print("\n" + "="*80)
    print("TRADE QUALITY ANALYSIS")
    print("="*80 + "\n")

    step1_avg_win_rate = (30.0 + 57.1 + 62.5 + 63.2) / 4  # From Step 1 results
    step3_avg_win_rate = sum(r['win_rate'] for r in results) / len(results)

    step1_avg_profit_factor = (0.62 + 1.86 + 0.80 + 1.78) / 4
    step3_avg_profit_factor = sum(r['profit_factor'] for r in results) / len(results)

    print(f"Win Rate:")
    print(f"  Step 1 (8% base): {step1_avg_win_rate:.1f}%")
    print(f"  Step 3 (12% base): {step3_avg_win_rate:.1f}%")

    if step3_avg_win_rate > step1_avg_win_rate + 5:
        print(f"  ✅ Better quality entries with wider base")
    elif step3_avg_win_rate < step1_avg_win_rate - 5:
        print(f"  ❌ Worse quality entries with wider base")
    else:
        print(f"  ⚠️  Similar quality")

    print(f"\nProfit Factor:")
    print(f"  Step 1 (8% base): {step1_avg_profit_factor:.2f}x")
    print(f"  Step 3 (12% base): {step3_avg_profit_factor:.2f}x")

    if step3_avg_profit_factor > step1_avg_profit_factor + 0.3:
        print(f"  ✅ Better risk/reward with wider base")
    elif step3_avg_profit_factor < step1_avg_profit_factor - 0.3:
        print(f"  ❌ Worse risk/reward with wider base")
    else:
        print(f"  ⚠️  Similar risk/reward")

    # Save results
    output = {
        'step': 3,
        'changes': ['Volume 1.5x → 1.2x', 'Base volatility 8% → 12%'],
        'results': results,
        'avg_baseline': avg_baseline,
        'avg_step1': avg_step1,
        'avg_step3': avg_step3,
        'improvement_from_baseline': improvement_from_baseline,
        'improvement_from_step1': improvement_from_step1,
    }

    output_file = Path(__file__).parent.parent.parent / "step3_wider_base_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n📊 Results saved to: {output_file}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
