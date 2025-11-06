"""
Test Smart Exits - Price Action Based

Compare results:
- Original: Fixed 20% target, 10-day time stop
- Smart: Trailing stops, MA breaks, momentum signals

This should capture the moves we missed!
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


def test_smart_exits():
    """Test strategy with smart exits."""

    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.FileHandler(Path(__file__).parent.parent.parent / 'smart_exits_results.log'),
            logging.StreamHandler()
        ]
    )

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    start_date = datetime(2025, 8, 1)
    end_date = datetime(2025, 10, 31)

    print("\n" + "="*80)
    print("DAILY MOMENTUM BACKTEST - SMART EXITS (PRICE ACTION)")
    print("="*80)
    print(f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
    print(f"Exit Strategy: Price action based")
    print(f"  - Trailing stops (2x ATR below highest high)")
    print(f"  - Close below 5-day MA (trend break)")
    print(f"  - Lower highs (momentum weakening)")
    print(f"  - Hard stop at -8% (risk management)")
    print("="*80 + "\n")

    backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)

    print("Running backtest...\n")
    results = backtester.run(start_date, end_date)

    # Print results
    print("\n" + "="*80)
    print("RESULTS - SMART EXITS")
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
    output_file = Path(__file__).parent.parent.parent / "smart_exits_results.json"
    summary = {
        "test_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "strategy": "Daily Breakout - Smart Exits (Price Action)",
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

    # Comparison
    print("\n" + "="*80)
    print("COMPARISON: SMART EXITS vs FIXED TARGETS")
    print("="*80 + "\n")

    print("ORIGINAL (Fixed 20% target, 10-day time stop):")
    print("  Return: -1.75% (-$1,748)")
    print("  Win Rate: 45.5%")
    print("  Profit Factor: 0.66x")
    print("  Max Drawdown: 3.4%")
    print("  Problem: Left money on table (stocks hit +10-14%, we got +0-5%)\n")

    print("SMART EXITS (Trailing stops, MA breaks, momentum):")
    print(f"  Return: {results.total_return_percent:+.2f}% (${results.total_return:+,.0f})")
    print(f"  Win Rate: {results.win_rate:.1f}%")
    print(f"  Profit Factor: {results.profit_factor:.2f}x")
    print(f"  Max Drawdown: {results.max_drawdown_percent:.1f}%")

    improvement = results.total_return_percent - (-1.75)
    print(f"  Improvement: {improvement:+.2f}% ({improvement / 1.75 * 100:+.0f}%)")

    # Verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80 + "\n")

    if results.total_return_percent > 5:
        print(f"✅ SMART EXITS WORK!")
        print(f"   Return: {results.total_return_percent:+.2f}% over 3 months")
        print(f"   Profit Factor: {results.profit_factor:.2f}x")
        print(f"   The key was exiting based on price action, not arbitrary targets!")

        if results.profit_factor > 1.5:
            print(f"\n   💪 STRONG EDGE - Ready to paper trade!")
        elif results.profit_factor > 1.2:
            print(f"\n   👍 DECENT EDGE - Could paper trade cautiously")

        print("\n   NEXT STEPS:")
        print("   1. Test on additional periods to confirm")
        print("   2. Paper trade for 2 weeks")
        print("   3. Go live with small size")

    elif results.total_return_percent > 0:
        print(f"⚠️  BETTER, BUT STILL MARGINAL")
        print(f"   Return: {results.total_return_percent:+.2f}%")
        print(f"   Smart exits helped but not enough for live trading")
        print("\n   Consider:")
        print("   - Tighter filters (only A+ setups)")
        print("   - Test different market periods")
        print("   - Add market regime filter")

    else:
        print(f"❌ STILL NOT PROFITABLE")
        print(f"   Return: {results.total_return_percent:+.2f}%")
        print(f"   Exit strategy helped but not enough")
        print(f"   Market conditions (Aug-Oct) too choppy")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    test_smart_exits()
