"""
3-Month Daily Momentum Backtest - The REAL Test (Take 2)

Tests daily breakout strategy (Minervini/O'Neil style) over 3 months.

Key differences from failed intraday test:
- Daily bars instead of 2-minute
- Multi-day holds instead of intraday scalps
- 8% stops / 20% targets instead of 3%/6%
- Quality breakouts instead of any spike

This is what actually works for swing trading.

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime
import json
import sys
from pathlib import Path
import logging

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from backtest.daily_momentum_backtest import DailyMomentumBacktester
import os
from dotenv import load_dotenv

load_dotenv()


def test_daily_3_months():
    """
    Test daily breakout strategy over 3 months (Aug-Oct 2025).

    This is the REAL test of swing trading approach.
    """

    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.FileHandler(Path(__file__).parent.parent.parent / 'daily_3_month_results.log'),
            logging.StreamHandler()
        ]
    )

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    # Test same period as intraday test (for comparison)
    start_date = datetime(2025, 8, 1)
    end_date = datetime(2025, 10, 31)

    print("\n" + "="*80)
    print("3-MONTH DAILY MOMENTUM BACKTEST (MINERVINI/O'NEIL STYLE)")
    print("="*80)
    print(f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
    print(f"Strategy: Daily breakouts from consolidation")
    print(f"Risk Management: 8% stops, 20% targets, max 10 days hold")
    print(f"Position Sizing: 30% of capital per trade, max 3 positions")
    print(f"Starting Capital: $100,000")
    print("="*80 + "\n")

    # Create backtester
    backtester = DailyMomentumBacktester(
        api_key=api_key,
        secret_key=secret_key,
        starting_capital=100000
    )

    # Run backtest
    print("Starting backtest... this will take 3-5 minutes\n")
    results = backtester.run(start_date, end_date)

    # Print results
    print("\n" + "="*80)
    print("3-MONTH DAILY BACKTEST RESULTS")
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
        print(f"{'#':<4} {'Symbol':<6} {'Entry':<12} {'Exit':<12} {'Days':<5} {'P&L':<12} {'%':<8} {'Reason':<8}")
        print("-" * 80)

        for i, trade in enumerate(results.trades, 1):
            pnl_emoji = "✅" if trade['pnl'] > 0 else "❌"
            print(f"{i:<4} {trade['symbol']:<6} "
                  f"{trade['entry_date']:<12} {trade['exit_date']:<12} "
                  f"{trade['hold_days']:<5} "
                  f"{pnl_emoji} ${trade['pnl']:>8,.0f} "
                  f"{trade['pnl_pct']:>6.1f}% "
                  f"{trade['exit_reason']:<8}")

    # Save results
    output_file = Path(__file__).parent.parent.parent / "daily_3_month_results.json"
    summary = {
        "test_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "strategy": "Daily Breakout (Minervini/O'Neil)",
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

    # Comparison to intraday
    print("\n" + "="*80)
    print("COMPARISON: DAILY vs INTRADAY STRATEGY")
    print("="*80 + "\n")

    print("INTRADAY (2-min bars, failed):")
    print("  Return: -54.09% (-$54,087)")
    print("  Win Rate: 0% of days (50% of trades)")
    print("  Profit Factor: 0.05x")
    print("  Max Drawdown: 54%")
    print("  Verdict: ❌ DOES NOT WORK\n")

    print("DAILY (swing trading, this test):")
    print(f"  Return: {results.total_return_percent:+.2f}% (${results.total_return:+,.0f})")
    print(f"  Win Rate: {results.win_rate:.1f}% of trades")
    print(f"  Profit Factor: {results.profit_factor:.2f}x")
    print(f"  Max Drawdown: {results.max_drawdown_percent:.1f}%")

    # Final verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80 + "\n")

    if results.total_return_percent > 10:
        print(f"✅ DAILY STRATEGY IS PROFITABLE!")
        print(f"   Return: {results.total_return_percent:+.2f}% over 3 months")
        print(f"   Annualized: {results.total_return_percent * 4:+.1f}% (if consistent)")
        print(f"   Max Drawdown: {results.max_drawdown_percent:.2f}%")

        if results.profit_factor > 2.0:
            print(f"\n   💪 STRONG EDGE - Profit factor {results.profit_factor:.2f}x is excellent")
            print(f"   Avg win (${results.avg_win:,.0f}) is {results.avg_win / abs(results.avg_loss):.1f}x avg loss (${results.avg_loss:,.0f})")
        elif results.profit_factor > 1.5:
            print(f"\n   👍 DECENT EDGE - Profit factor {results.profit_factor:.2f}x is good")
        else:
            print(f"\n   ⚠️  WEAK EDGE - Profit factor {results.profit_factor:.2f}x is marginal")

        if results.max_drawdown_percent < 15:
            print(f"   ✅ LOW RISK - Drawdown {results.max_drawdown_percent:.2f}% is manageable")
        elif results.max_drawdown_percent < 25:
            print(f"   ⚠️  MODERATE RISK - Drawdown {results.max_drawdown_percent:.2f}% is acceptable")
        else:
            print(f"   🚨 HIGH RISK - Drawdown {results.max_drawdown_percent:.2f}% is concerning")

        print("\n   NEXT STEPS:")
        print("   1. Test additional 3 months to confirm consistency")
        print("   2. Add filters (ADR, daily trend strength)")
        print("   3. Paper trade for 2 weeks")
        print("   4. Go live with small size ($5k-10k per trade)")

    elif results.total_return_percent > 0:
        print(f"⚠️  DAILY STRATEGY IS BARELY PROFITABLE")
        print(f"   Return: {results.total_return_percent:+.2f}% over 3 months")
        print(f"   This is marginal - might work with improvements")
        print("\n   IMPROVEMENTS TO TRY:")
        print("   - Tighter filters (only trade A+ setups)")
        print("   - Better entry timing (wait for pullback)")
        print("   - Different stop placement (ATR-based)")

    else:
        print(f"❌ DAILY STRATEGY IS NOT PROFITABLE")
        print(f"   Return: {results.total_return_percent:+.2f}% over 3 months")
        print(f"   Lost ${abs(results.total_return):,.2f}")
        print(f"   Max Drawdown: {results.max_drawdown_percent:.2f}%")
        print("\n   This approach also doesn't work.")
        print("   Consider Option 3: Complete strategy pivot")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    test_daily_3_months()
