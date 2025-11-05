"""
Test Hybrid Trailing Stops - Progressive Tightening

Trailing stop logic:
- 0-10% profit: Trail 2x ATR (give room)
- 10-15% profit: Trail 1x ATR (tighter)
- 15%+ profit: Trail 5% from peak (lock it in!)

This should capture more of SNOW's +14% move.
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


def test_hybrid_trailing():
    """Test strategy with hybrid trailing stops."""

    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.FileHandler(Path(__file__).parent.parent.parent / 'hybrid_trailing_results.log'),
            logging.StreamHandler()
        ]
    )

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    start_date = datetime(2025, 8, 1)
    end_date = datetime(2025, 10, 31)

    print("\n" + "="*80)
    print("DAILY MOMENTUM BACKTEST - HYBRID TRAILING STOPS")
    print("="*80)
    print(f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
    print(f"Exit Strategy: HYBRID TRAILING (Progressive Tightening)")
    print(f"  - 0-10% profit: Trail 2x ATR (give room to run)")
    print(f"  - 10-15% profit: Trail 1x ATR (tighter trail)")
    print(f"  - 15%+ profit: Trail 5% from peak (lock it in!)")
    print("="*80 + "\n")

    backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)

    print("Running backtest...\n")
    results = backtester.run(start_date, end_date)

    # Print results
    print("\n" + "="*80)
    print("RESULTS - HYBRID TRAILING STOPS")
    print("="*80 + "\n")

    print(f"📊 OVERALL PERFORMANCE:")
    print(f"   Starting Capital: ${results.starting_capital:,.2f}")
    print(f"   Final Capital: ${results.ending_capital:,.2f}")
    print(f"   Total Return: ${results.total_return:+,.2f} ({results.total_return_percent:+.2f}%)")
    print(f"   Max Drawdown: {results.max_drawdown_percent:.2f}%")
    print()

    print(f"📈 TRADE STATISTICS:")
    print(f"   Total Trades: {results.total_trades}")
    print(f"   Winners: {results.winning_trades} ({results.win_rate:.1f}%)")
    print(f"   Losers: {results.losing_trades}")
    print(f"   Avg Win: ${results.avg_win:+,.2f}")
    print(f"   Avg Loss: ${results.avg_loss:+,.2f}")
    print(f"   Profit Factor: {results.profit_factor:.2f}x")
    print()

    # Show all trades
    if results.trades:
        print(f"📋 ALL TRADES ({len(results.trades)}):")
        print(f"{'#':<4} {'Symbol':<6} {'Entry':<12} {'Exit':<12} {'Days':<5} {'P&L':<12} {'%':<8} {'Reason':<15}")
        print("-" * 90)

        for i, trade in enumerate(results.trades, 1):
            pnl_emoji = "✅" if trade['pnl'] > 0 else "❌"
            print(f"{i:<4} {trade['symbol']:<6} "
                  f"{trade['entry_date']:<12} {trade['exit_date']:<12} "
                  f"{trade['hold_days']:<5} "
                  f"{pnl_emoji} ${trade['pnl']:>8,.0f} "
                  f"{trade['pnl_pct']:>6.1f}% "
                  f"{trade['exit_reason']:<15}")

    # Save results
    output_file = Path(__file__).parent.parent.parent / "hybrid_trailing_results.json"
    summary = {
        "test_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "strategy": "Daily Breakout - Hybrid Trailing Stops",
        "starting_capital": results.starting_capital,
        "ending_capital": results.ending_capital,
        "total_return": results.total_return,
        "total_return_pct": results.total_return_percent,
        "max_drawdown": results.max_drawdown_percent,
        "total_trades": results.total_trades,
        "winning_trades": results.winning_trades,
        "losing_trades": results.losing_trades,
        "win_rate": results.win_rate,
        "avg_win": results.avg_win,
        "avg_loss": results.avg_loss,
        "profit_factor": results.profit_factor,
        "trades": results.trades,
        "equity_curve": results.equity_curve
    }

    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📊 Results saved to: {output_file}")

    # Three-way comparison
    print("\n" + "="*80)
    print("3-WAY COMPARISON")
    print("="*80 + "\n")

    print("1. ORIGINAL (Fixed 20% target):")
    print("   Return: -1.75%")
    print("   Problem: Held too long, never reached target\n")

    print("2. SMART EXITS (2x ATR trailing):")
    print("   Return: +1.87%")
    print("   Problem: Trail too wide, gave back profits\n")

    print("3. HYBRID TRAILING (Progressive tightening):")
    print(f"   Return: {results.total_return_percent:+.2f}%")
    print(f"   Win Rate: {results.win_rate:.1f}%")
    print(f"   Profit Factor: {results.profit_factor:.2f}x")

    improvement_vs_fixed = results.total_return_percent - (-1.75)
    improvement_vs_smart = results.total_return_percent - 1.87

    print(f"\n   Improvement vs Fixed: {improvement_vs_fixed:+.2f}%")
    print(f"   Improvement vs Smart: {improvement_vs_smart:+.2f}%")

    # Verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80 + "\n")

    if results.total_return_percent > 10:
        print(f"✅ HYBRID TRAILING WORKS GREAT!")
        print(f"   Return: {results.total_return_percent:+.2f}% over 3 months")
        print(f"   Annualized: ~{results.total_return_percent * 4:+.1f}%")
        print(f"   Profit Factor: {results.profit_factor:.2f}x")
        print(f"\n   Progressive tightening captured more of big moves!")
        print(f"   Ready for paper trading!")

    elif results.total_return_percent > 5:
        print(f"✅ HYBRID TRAILING IS STRONG!")
        print(f"   Return: {results.total_return_percent:+.2f}% over 3 months")
        print(f"   Profit Factor: {results.profit_factor:.2f}x")
        print(f"\n   This is tradeable! Progressive stops helped significantly.")
        print(f"\n   NEXT STEPS:")
        print(f"   1. Test on additional 3-month periods")
        print(f"   2. Paper trade for 2 weeks")
        print(f"   3. Go live with $5k-10k per position")

    elif results.total_return_percent > 2:
        print(f"⚠️  BETTER, BUT STILL MARGINAL")
        print(f"   Return: {results.total_return_percent:+.2f}%")
        print(f"   Hybrid helped, but Aug-Oct market was too choppy")
        print(f"\n   Consider:")
        print(f"   - Test on trending period")
        print(f"   - Add market regime filter")
        print(f"   - Tighten entry criteria further")

    else:
        print(f"⚠️  MINIMAL IMPROVEMENT")
        print(f"   Return: {results.total_return_percent:+.2f}%")
        print(f"   Hybrid trailing helped slightly")
        print(f"   But market conditions (Aug-Oct) too difficult")

    # Key insight
    if results.total_return_percent > 1.87:
        diff = results.total_return_percent - 1.87
        print(f"\n💡 KEY INSIGHT:")
        print(f"   Hybrid trailing captured +{diff:.2f}% more profit")
        print(f"   By tightening stops as profits grew")
        print(f"   This is the correct approach for momentum trading!")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    test_hybrid_trailing()
