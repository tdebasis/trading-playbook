"""
Test Wider Stops - Compare 2% vs 3% vs 4% stop losses.

This will run the simple momentum strategy with different stop loss settings
to see which performs best. Tests on August 6, 2025.

Run this to see results in the morning!

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime
import json
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from backtest.simple_momentum_test import SimpleMomentumBacktester
import os
from dotenv import load_dotenv

load_dotenv()


def test_stop_loss_variations():
    """Test different stop loss percentages."""

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    # Test different stop loss settings
    stop_variations = [
        {"stop_pct": 0.02, "target_pct": 0.04, "name": "2% Stop, 4% Target (2:1 R/R)"},
        {"stop_pct": 0.03, "target_pct": 0.06, "name": "3% Stop, 6% Target (2:1 R/R)"},
        {"stop_pct": 0.04, "target_pct": 0.08, "name": "4% Stop, 8% Target (2:1 R/R)"},
        {"stop_pct": 0.03, "target_pct": 0.09, "name": "3% Stop, 9% Target (3:1 R/R)"},
    ]

    results_summary = []

    print("\n" + "="*80)
    print("TESTING DIFFERENT STOP LOSS SETTINGS")
    print("="*80)
    print(f"Test Date: August 6, 2025")
    print(f"Symbols: NVDA, TSLA, NVAX, SNAP, PTON")
    print("="*80 + "\n")

    start = datetime(2025, 8, 6)
    end = datetime(2025, 8, 6)

    for i, variation in enumerate(stop_variations, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/4: {variation['name']}")
        print(f"{'='*80}\n")

        # Create backtester with these settings
        backtester = SimpleMomentumBacktester(api_key, secret_key)
        backtester.stop_loss_percent = variation['stop_pct']
        backtester.profit_target_percent = variation['target_pct']

        # Run backtest
        results = backtester.run(start, end)

        # Store summary
        summary = {
            "name": variation['name'],
            "stop_loss_pct": variation['stop_pct'] * 100,
            "profit_target_pct": variation['target_pct'] * 100,
            "total_trades": results['total_trades'],
            "win_rate": results['win_rate'],
            "total_return": results['total_return'],
            "total_return_pct": results['total_return_percent'],
            "avg_win": results['avg_win'],
            "avg_loss": results['avg_loss'],
            "winners": results['winning_trades'],
            "losers": results['losing_trades']
        }
        results_summary.append(summary)

        print(f"\n✅ Test {i} complete: {results['total_return_percent']:+.2f}% return\n")

    # Print comparison
    print("\n" + "="*80)
    print("COMPARISON OF ALL TESTS")
    print("="*80 + "\n")

    # Sort by return
    results_summary.sort(key=lambda x: x['total_return_pct'], reverse=True)

    for i, summary in enumerate(results_summary, 1):
        print(f"{i}. {summary['name']}")
        print(f"   Return: {summary['total_return_pct']:+.2f}% (${summary['total_return']:+,.2f})")
        print(f"   Trades: {summary['total_trades']} ({summary['winners']}W / {summary['losers']}L)")
        print(f"   Win Rate: {summary['win_rate']:.1f}%")
        print(f"   Avg Win: ${summary['avg_win']:+,.2f}, Avg Loss: ${summary['avg_loss']:,.2f}")
        print()

    # Save results to file
    output_file = Path(__file__).parent.parent.parent / "stop_loss_comparison_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "test_date": "2025-08-06",
            "results": results_summary
        }, f, indent=2)

    print(f"📊 Results saved to: {output_file}")
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)

    best = results_summary[0]
    if best['total_return_pct'] > 0:
        print(f"\n✅ BEST PERFORMER: {best['name']}")
        print(f"   Returned {best['total_return_pct']:+.2f}% with {best['win_rate']:.1f}% win rate")
    else:
        print(f"\n⚠️  ALL TESTS LOST MONEY ON THIS DAY")
        print(f"   Best was: {best['name']} with {best['total_return_pct']:+.2f}%")
        print(f"   This suggests:")
        print(f"   - Aug 6 might be a difficult day for this strategy")
        print(f"   - Need to test more days to validate")
        print(f"   - Consider adding filters (avoid choppy stocks like NVAX)")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    test_stop_loss_variations()
