"""
Multi-Day Backtest - Test strategy across 10 random days to get real statistics.

This will test the simple momentum strategy (3% stops) on 10 different days
and calculate overall performance metrics.

Run this overnight to get REAL validation of the strategy!

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime, timedelta
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


def test_multiple_days():
    """Test strategy across 10 random trading days."""

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    # Select 10 random trading days (August - September 2025)
    test_dates = [
        datetime(2025, 8, 6),   # Day 1 (we already know this one)
        datetime(2025, 8, 7),   # Day 2
        datetime(2025, 8, 11),  # Day 3 (Monday)
        datetime(2025, 8, 13),  # Day 4
        datetime(2025, 8, 18),  # Day 5
        datetime(2025, 8, 20),  # Day 6
        datetime(2025, 8, 25),  # Day 7
        datetime(2025, 8, 27),  # Day 8
        datetime(2025, 9, 3),   # Day 9
        datetime(2025, 9, 8),   # Day 10
    ]

    print("\n" + "="*80)
    print("MULTI-DAY BACKTEST - 10 TRADING DAYS")
    print("="*80)
    print(f"Testing: Aug-Sep 2025")
    print(f"Strategy: Simple Momentum (3% stops, 6% targets, 2:1 R/R)")
    print(f"Symbols: NVDA, TSLA, NVAX, SNAP, PTON")
    print("="*80 + "\n")

    all_results = []
    daily_returns = []
    all_trades = []

    for i, date in enumerate(test_dates, 1):
        print(f"\n{'='*80}")
        print(f"DAY {i}/10: {date.strftime('%Y-%m-%d (%A)')}")
        print(f"{'='*80}\n")

        # Create backtester with optimal settings (3% stops)
        backtester = SimpleMomentumBacktester(api_key, secret_key)
        backtester.stop_loss_percent = 0.03
        backtester.profit_target_percent = 0.06

        # Run backtest
        try:
            results = backtester.run(date, date)

            # Store results
            daily_result = {
                "date": date.strftime('%Y-%m-%d'),
                "day_of_week": date.strftime('%A'),
                "return_pct": results['total_return_percent'],
                "return_dollars": results['total_return'],
                "trades": results['total_trades'],
                "winners": results['winning_trades'],
                "losers": results['losing_trades'],
                "win_rate": results['win_rate']
            }
            all_results.append(daily_result)
            daily_returns.append(results['total_return_percent'])
            all_trades.extend(results['trades'])

            # Show summary
            emoji = "✅" if results['total_return_percent'] > 0 else "❌"
            print(f"\n{emoji} Day {i} Result: {results['total_return_percent']:+.2f}%")
            print(f"   Trades: {results['total_trades']} ({results['winning_trades']}W / {results['losing_trades']}L)")
            print(f"   P&L: ${results['total_return']:+,.2f}\n")

        except Exception as e:
            print(f"❌ Error on {date.strftime('%Y-%m-%d')}: {e}")
            daily_result = {
                "date": date.strftime('%Y-%m-%d'),
                "day_of_week": date.strftime('%A'),
                "return_pct": 0,
                "return_dollars": 0,
                "trades": 0,
                "winners": 0,
                "losers": 0,
                "win_rate": 0,
                "error": str(e)
            }
            all_results.append(daily_result)
            daily_returns.append(0)

    # Calculate overall statistics
    print("\n" + "="*80)
    print("OVERALL STATISTICS (10 DAYS)")
    print("="*80 + "\n")

    total_return = sum(daily_returns)
    winning_days = [r for r in daily_returns if r > 0]
    losing_days = [r for r in daily_returns if r < 0]

    daily_win_rate = (len(winning_days) / len(daily_returns) * 100) if daily_returns else 0
    avg_win_day = (sum(winning_days) / len(winning_days)) if winning_days else 0
    avg_loss_day = (sum(losing_days) / len(losing_days)) if losing_days else 0

    # Trade statistics
    total_trades = sum(r['trades'] for r in all_results)
    total_winners = sum(r['winners'] for r in all_results)
    total_losers = sum(r['losers'] for r in all_results)
    trade_win_rate = (total_winners / total_trades * 100) if total_trades > 0 else 0

    # Calculate profit factor
    winning_trades = [t for t in all_trades if t['pnl'] > 0]
    losing_trades = [t for t in all_trades if t['pnl'] < 0]
    total_wins = sum(t['pnl'] for t in winning_trades)
    total_losses = abs(sum(t['pnl'] for t in losing_trades))
    profit_factor = (total_wins / total_losses) if total_losses > 0 else 0

    # Calculate max drawdown
    cumulative = 0
    peak = 0
    max_dd = 0
    for ret in daily_returns:
        cumulative += ret
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    print(f"📊 DAILY PERFORMANCE:")
    print(f"   Total Return: {total_return:+.2f}%")
    print(f"   Winning Days: {len(winning_days)}/10 ({daily_win_rate:.0f}%)")
    print(f"   Losing Days: {len(losing_days)}/10")
    print(f"   Avg Winning Day: {avg_win_day:+.2f}%")
    print(f"   Avg Losing Day: {avg_loss_day:+.2f}%")
    print(f"   Max Drawdown: {max_dd:.2f}%")
    print()

    print(f"📈 TRADE STATISTICS:")
    print(f"   Total Trades: {total_trades}")
    print(f"   Winners: {total_winners} ({trade_win_rate:.1f}%)")
    print(f"   Losers: {total_losers}")
    print(f"   Profit Factor: {profit_factor:.2f}x")
    print()

    # Best and worst days
    best_day = max(all_results, key=lambda x: x['return_pct'])
    worst_day = min(all_results, key=lambda x: x['return_pct'])

    print(f"🏆 BEST DAY: {best_day['date']} ({best_day['day_of_week']})")
    print(f"   Return: {best_day['return_pct']:+.2f}%")
    print(f"   Trades: {best_day['trades']} ({best_day['winners']}W / {best_day['losers']}L)")
    print()

    print(f"💔 WORST DAY: {worst_day['date']} ({worst_day['day_of_week']})")
    print(f"   Return: {worst_day['return_pct']:+.2f}%")
    print(f"   Trades: {worst_day['trades']} ({worst_day['winners']}W / {worst_day['losers']}L)")
    print()

    # Day-by-day breakdown
    print("="*80)
    print("DAY-BY-DAY BREAKDOWN")
    print("="*80 + "\n")

    for i, result in enumerate(all_results, 1):
        emoji = "✅" if result['return_pct'] > 0 else "❌"
        print(f"{i:2}. {emoji} {result['date']} ({result['day_of_week'][:3]}): "
              f"{result['return_pct']:+6.2f}% | "
              f"{result['trades']} trades ({result['winners']}W/{result['losers']}L)")

    # Save results
    output_file = Path(__file__).parent.parent.parent / "10_day_backtest_results.json"
    summary = {
        "test_period": "Aug-Sep 2025",
        "total_days": len(test_dates),
        "total_return_pct": total_return,
        "daily_win_rate": daily_win_rate,
        "trade_win_rate": trade_win_rate,
        "profit_factor": profit_factor,
        "max_drawdown": max_dd,
        "total_trades": total_trades,
        "daily_results": all_results
    }

    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📊 Results saved to: {output_file}")

    # Final verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80 + "\n")

    if total_return > 0:
        print(f"✅ STRATEGY IS PROFITABLE!")
        print(f"   Overall return: {total_return:+.2f}% over 10 days")
        print(f"   Win rate: {daily_win_rate:.0f}% of days")
        print(f"   Profit factor: {profit_factor:.2f}x")

        if profit_factor > 1.5:
            print(f"\n   💪 STRONG EDGE - Profit factor {profit_factor:.2f}x is excellent")
        elif profit_factor > 1.2:
            print(f"\n   👍 DECENT EDGE - Profit factor {profit_factor:.2f}x is acceptable")
        else:
            print(f"\n   ⚠️  WEAK EDGE - Profit factor {profit_factor:.2f}x is marginal")

    else:
        print(f"❌ STRATEGY IS NOT PROFITABLE")
        print(f"   Overall return: {total_return:+.2f}% over 10 days")
        print(f"   Win rate: {daily_win_rate:.0f}% of days")
        print(f"   This suggests:")
        print(f"   - Strategy needs major changes")
        print(f"   - Consider different timeframes or filters")
        print(f"   - Maybe momentum trading isn't working in this market")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    test_multiple_days()
