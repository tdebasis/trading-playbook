"""
Test Q1 2024 - Strong Trending Period

Q1 2024 was when AI stocks (NVDA, AMD, etc.) had massive runs.
Let's see if our strategy can capture those moves!

This will answer: Is 1.87% the strategy's limit, or was Aug-Oct just choppy?
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


def test_q1_2024():
    """Test strategy on Q1 2024 trending period."""

    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.FileHandler(Path(__file__).parent.parent.parent / 'q1_2024_results.log'),
            logging.StreamHandler()
        ]
    )

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    start_date = datetime(2024, 1, 2)
    end_date = datetime(2024, 3, 31)

    print("\n" + "="*80)
    print("DAILY MOMENTUM BACKTEST - Q1 2024 (TRENDING MARKET)")
    print("="*80)
    print(f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
    print(f"Market Conditions: Strong AI stock uptrends (NVDA, AMD, etc.)")
    print(f"Exit Strategy: Hybrid Trailing (Progressive tightening)")
    print("="*80 + "\n")

    backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)

    print("Running backtest...\n")
    results = backtester.run(start_date, end_date)

    # Print results
    print("\n" + "="*80)
    print("RESULTS - Q1 2024")
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
    output_file = Path(__file__).parent.parent.parent / "q1_2024_results.json"
    summary = {
        "test_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "strategy": "Daily Breakout - Hybrid Trailing (Q1 2024)",
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

    # Period comparison
    print("\n" + "="*80)
    print("PERIOD COMPARISON")
    print("="*80 + "\n")

    print("Aug-Oct 2025 (CHOPPY MARKET):")
    print("   Return: +1.87%")
    print("   Win Rate: 54.5%")
    print("   Profit Factor: 1.56x")
    print("   Conditions: Choppy, range-bound\n")

    print("Q1 2024 (TRENDING MARKET):")
    print(f"   Return: {results.total_return_percent:+.2f}%")
    print(f"   Win Rate: {results.win_rate:.1f}%")
    print(f"   Profit Factor: {results.profit_factor:.2f}x")
    print(f"   Conditions: Strong AI stock uptrends")

    improvement = results.total_return_percent - 1.87
    print(f"\n   Difference: {improvement:+.2f}%")

    # Annualized returns
    print("\n" + "="*80)
    print("ANNUALIZED PROJECTIONS")
    print("="*80 + "\n")

    aug_oct_annual = 1.87 * 4  # Simple
    q1_annual = results.total_return_percent * 4

    print(f"If Aug-Oct 2025 performance continues: ~{aug_oct_annual:.1f}% per year")
    print(f"If Q1 2024 performance continues: ~{q1_annual:.1f}% per year")

    # Verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80 + "\n")

    if results.total_return_percent > 15:
        print(f"🚀 STRATEGY WORKS GREAT IN TRENDING MARKETS!")
        print(f"   Q1 2024: {results.total_return_percent:+.2f}%")
        print(f"   Annualized: ~{q1_annual:+.1f}%")
        print(f"   This validates the strategy!")
        print()
        print(f"   KEY INSIGHT:")
        print(f"   - Choppy markets (Aug-Oct): +1.87%")
        print(f"   - Trending markets (Q1 2024): {results.total_return_percent:+.2f}%")
        print(f"   - Strategy is MARKET-DEPENDENT (as expected)")
        print()
        print(f"   NEXT STEPS:")
        print(f"   1. Add market regime filter (only trade in uptrends)")
        print(f"   2. Paper trade in next trending period")
        print(f"   3. Go live with $5k-10k per position")

    elif results.total_return_percent > 10:
        print(f"✅ STRATEGY PERFORMS WELL IN TRENDING MARKETS!")
        print(f"   Q1 2024: {results.total_return_percent:+.2f}%")
        print(f"   Annualized: ~{q1_annual:+.1f}%")
        print()
        print(f"   This is tradeable! The strategy:")
        print(f"   - Makes modest gains in choppy markets (+1.87%)")
        print(f"   - Makes good gains in trending markets ({results.total_return_percent:+.2f}%)")
        print()
        print(f"   NEXT STEPS:")
        print(f"   1. Test one more period to confirm")
        print(f"   2. Paper trade for 2 weeks")
        print(f"   3. Go live with small size")

    elif results.total_return_percent > 5:
        print(f"⚠️  BETTER, BUT STILL MODEST")
        print(f"   Q1 2024: {results.total_return_percent:+.2f}%")
        print(f"   Not much better than Aug-Oct")
        print()
        print(f"   Consider:")
        print(f"   - Tighter entry filters (only A+ setups)")
        print(f"   - Position sizing (more capital to winners)")
        print(f"   - Test additional periods")

    else:
        print(f"❌ STRATEGY DOESN'T WORK EVEN IN TRENDING MARKETS")
        print(f"   Q1 2024: {results.total_return_percent:+.2f}%")
        print(f"   Similar to Aug-Oct (+1.87%)")
        print()
        print(f"   This suggests the strategy has fundamental issues")
        print(f"   - Scanner may be too selective")
        print(f"   - Exits may be too conservative")
        print(f"   - Need to reconsider approach")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    test_q1_2024()
