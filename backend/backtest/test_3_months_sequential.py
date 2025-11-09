"""
3-Month Sequential Backtest - REALISTIC capital management with drawdowns.

This runs the strategy day-by-day for 3 months (Aug-Oct 2025), accounting for:
- Cumulative P&L (capital grows/shrinks with wins/losses)
- Drawdowns reducing available capital
- Position sizing based on CURRENT capital (not starting capital)
- Real sequential trading (chronological order)

This is the REAL test of the strategy!

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime, timedelta
import json
import sys
from pathlib import Path
import calendar

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from backtest.simple_momentum_test import SimpleMomentumBacktester
import os
from dotenv import load_dotenv

load_dotenv()


def is_trading_day(date):
    """Check if date is a trading day (weekday, not holiday)."""
    # Skip weekends
    if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False

    # For now, skip major holidays (approximate - would need holiday calendar for accuracy)
    # Labor Day 2025: Sept 1
    # Thanksgiving: Nov 27-28
    holidays = [
        datetime(2025, 9, 1),  # Labor Day
    ]

    if date in holidays:
        return False

    return True


def get_trading_days(start_date, end_date):
    """Get all trading days in the date range."""
    trading_days = []
    current = start_date

    while current <= end_date:
        if is_trading_day(current):
            trading_days.append(current)
        current += timedelta(days=1)

    return trading_days


def test_3_months_sequential():
    """
    Test strategy sequentially over 3 months with realistic capital management.

    Key features:
    - Day-by-day chronological testing
    - Capital adjusts after each day (grows/shrinks)
    - Position sizing based on CURRENT capital
    - Drawdowns reduce buying power
    - Realistic compounding
    """

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    # Test period: Aug 1 - Oct 31, 2025 (3 months)
    start_date = datetime(2025, 8, 1)
    end_date = datetime(2025, 10, 31)

    print("\n" + "="*80)
    print("3-MONTH SEQUENTIAL BACKTEST (REALISTIC CAPITAL MANAGEMENT)")
    print("="*80)
    print(f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
    print(f"Strategy: Simple Momentum (3% stops, 6% targets)")
    print(f"Starting Capital: $100,000")
    print(f"Capital Management: Dynamic (adjusts with P&L)")
    print("="*80 + "\n")

    # Get all trading days
    print("Calculating trading days...")
    trading_days = get_trading_days(start_date, end_date)
    print(f"Found {len(trading_days)} trading days\n")

    # Initialize tracking
    starting_capital = 100000
    current_capital = starting_capital
    peak_capital = starting_capital

    daily_results = []
    all_trades = []
    equity_curve = [starting_capital]

    # Track drawdown
    current_drawdown = 0
    max_drawdown = 0
    max_drawdown_date = None

    # Run day by day
    for i, date in enumerate(trading_days, 1):
        print(f"\n{'='*80}")
        print(f"DAY {i}/{len(trading_days)}: {date.strftime('%Y-%m-%d (%A)')}")
        print(f"Starting Capital: ${current_capital:,.2f}")
        print(f"{'='*80}\n")

        # Create backtester with CURRENT capital (not starting capital!)
        backtester = SimpleMomentumBacktester(api_key, secret_key, starting_capital=current_capital)
        backtester.stop_loss_percent = 0.03
        backtester.profit_target_percent = 0.06

        # Run backtest for this day
        try:
            results = backtester.run(date, date)

            # Update capital with day's P&L
            day_pnl = results['total_return']
            day_pnl_pct = results['total_return_percent']
            current_capital = results['ending_capital']

            # Track peak and drawdown
            if current_capital > peak_capital:
                peak_capital = current_capital

            current_drawdown = ((peak_capital - current_capital) / peak_capital) * 100

            if current_drawdown > max_drawdown:
                max_drawdown = current_drawdown
                max_drawdown_date = date

            # Store daily result
            daily_result = {
                "date": date.strftime('%Y-%m-%d'),
                "day_of_week": date.strftime('%A'),
                "day_number": i,
                "starting_capital": current_capital - day_pnl,
                "ending_capital": current_capital,
                "day_pnl": day_pnl,
                "day_pnl_pct": day_pnl_pct,
                "cumulative_pnl": current_capital - starting_capital,
                "cumulative_pnl_pct": ((current_capital - starting_capital) / starting_capital) * 100,
                "peak_capital": peak_capital,
                "current_drawdown": current_drawdown,
                "trades": results['total_trades'],
                "winners": results['winning_trades'],
                "losers": results['losing_trades']
            }
            daily_results.append(daily_result)
            equity_curve.append(current_capital)
            all_trades.extend(results['trades'])

            # Show daily summary
            emoji = "✅" if day_pnl > 0 else "❌" if day_pnl < 0 else "➖"
            print(f"\n{emoji} Day {i} Result:")
            print(f"   Day P&L: ${day_pnl:+,.2f} ({day_pnl_pct:+.2f}%)")
            print(f"   New Capital: ${current_capital:,.2f}")
            print(f"   Cumulative: ${current_capital - starting_capital:+,.2f} ({daily_result['cumulative_pnl_pct']:+.2f}%)")
            print(f"   Drawdown: {current_drawdown:.2f}%")
            print(f"   Trades: {results['total_trades']} ({results['winning_trades']}W/{results['losing_trades']}L)\n")

            # Warning if drawdown is getting large
            if current_drawdown > 10:
                print(f"   ⚠️  WARNING: Drawdown at {current_drawdown:.2f}% (peak was ${peak_capital:,.2f})")

        except Exception as e:
            print(f"❌ Error on {date.strftime('%Y-%m-%d')}: {e}")
            daily_result = {
                "date": date.strftime('%Y-%m-%d'),
                "day_of_week": date.strftime('%A'),
                "day_number": i,
                "starting_capital": current_capital,
                "ending_capital": current_capital,
                "day_pnl": 0,
                "day_pnl_pct": 0,
                "cumulative_pnl": current_capital - starting_capital,
                "cumulative_pnl_pct": ((current_capital - starting_capital) / starting_capital) * 100,
                "peak_capital": peak_capital,
                "current_drawdown": current_drawdown,
                "trades": 0,
                "winners": 0,
                "losers": 0,
                "error": str(e)
            }
            daily_results.append(daily_result)

    # Calculate final statistics
    print("\n" + "="*80)
    print("3-MONTH SEQUENTIAL BACKTEST RESULTS")
    print("="*80 + "\n")

    final_capital = current_capital
    total_return = final_capital - starting_capital
    total_return_pct = (total_return / starting_capital) * 100

    # Calculate statistics
    winning_days = [r for r in daily_results if r['day_pnl'] > 0]
    losing_days = [r for r in daily_results if r['day_pnl'] < 0]
    breakeven_days = [r for r in daily_results if r['day_pnl'] == 0]

    daily_win_rate = (len(winning_days) / len(daily_results) * 100) if daily_results else 0
    avg_win_day = (sum(r['day_pnl'] for r in winning_days) / len(winning_days)) if winning_days else 0
    avg_loss_day = (sum(r['day_pnl'] for r in losing_days) / len(losing_days)) if losing_days else 0

    # Trade statistics
    total_trades = sum(r['trades'] for r in daily_results)
    total_winners = sum(r['winners'] for r in daily_results)
    total_losers = sum(r['losers'] for r in daily_results)
    trade_win_rate = (total_winners / total_trades * 100) if total_trades > 0 else 0

    # Profit factor
    winning_trades = [t for t in all_trades if t['pnl'] > 0]
    losing_trades = [t for t in all_trades if t['pnl'] < 0]
    total_wins = sum(t['pnl'] for t in winning_trades)
    total_losses = abs(sum(t['pnl'] for t in losing_trades))
    profit_factor = (total_wins / total_losses) if total_losses > 0 else 0

    # Monthly breakdown
    monthly_stats = {}
    for result in daily_results:
        month = result['date'][:7]  # YYYY-MM
        if month not in monthly_stats:
            monthly_stats[month] = {
                'days': 0,
                'pnl': 0,
                'trades': 0,
                'winners': 0,
                'losers': 0
            }
        monthly_stats[month]['days'] += 1
        monthly_stats[month]['pnl'] += result['day_pnl']
        monthly_stats[month]['trades'] += result['trades']
        monthly_stats[month]['winners'] += result['winners']
        monthly_stats[month]['losers'] += result['losers']

    print(f"📊 OVERALL PERFORMANCE:")
    print(f"   Starting Capital: ${starting_capital:,.2f}")
    print(f"   Final Capital: ${final_capital:,.2f}")
    print(f"   Total Return: ${total_return:+,.2f} ({total_return_pct:+.2f}%)")
    print(f"   Peak Capital: ${peak_capital:,.2f}")
    print(f"   Max Drawdown: {max_drawdown:.2f}% (on {max_drawdown_date.strftime('%Y-%m-%d') if max_drawdown_date else 'N/A'})")
    print()

    print(f"📅 DAILY PERFORMANCE:")
    print(f"   Trading Days: {len(daily_results)}")
    print(f"   Winning Days: {len(winning_days)} ({daily_win_rate:.1f}%)")
    print(f"   Losing Days: {len(losing_days)}")
    print(f"   Breakeven Days: {len(breakeven_days)}")
    print(f"   Avg Win Day: ${avg_win_day:+,.2f}")
    print(f"   Avg Loss Day: ${avg_loss_day:+,.2f}")
    print()

    print(f"📈 TRADE STATISTICS:")
    print(f"   Total Trades: {total_trades}")
    print(f"   Winners: {total_winners} ({trade_win_rate:.1f}%)")
    print(f"   Losers: {total_losers}")
    print(f"   Profit Factor: {profit_factor:.2f}x")
    print()

    print(f"📆 MONTHLY BREAKDOWN:")
    for month, stats in sorted(monthly_stats.items()):
        month_name = datetime.strptime(month, '%Y-%m').strftime('%B %Y')
        win_rate = (stats['winners'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
        print(f"   {month_name}:")
        print(f"      P&L: ${stats['pnl']:+,.2f} over {stats['days']} days")
        print(f"      Trades: {stats['trades']} ({stats['winners']}W/{stats['losers']}L, {win_rate:.0f}% win rate)")

    # Best and worst days
    best_day = max(daily_results, key=lambda x: x['day_pnl'])
    worst_day = min(daily_results, key=lambda x: x['day_pnl'])

    print(f"\n🏆 BEST DAY: {best_day['date']} ({best_day['day_of_week']})")
    print(f"   P&L: ${best_day['day_pnl']:+,.2f} ({best_day['day_pnl_pct']:+.2f}%)")
    print(f"   Trades: {best_day['trades']} ({best_day['winners']}W/{best_day['losers']}L)")

    print(f"\n💔 WORST DAY: {worst_day['date']} ({worst_day['day_of_week']})")
    print(f"   P&L: ${worst_day['day_pnl']:+,.2f} ({worst_day['day_pnl_pct']:+.2f}%)")
    print(f"   Trades: {worst_day['trades']} ({worst_day['winners']}W/{worst_day['losers']}L)")

    # Consecutive streaks
    current_streak = 0
    max_win_streak = 0
    max_loss_streak = 0

    for result in daily_results:
        if result['day_pnl'] > 0:
            current_streak = current_streak + 1 if current_streak > 0 else 1
            max_win_streak = max(max_win_streak, current_streak)
        elif result['day_pnl'] < 0:
            current_streak = current_streak - 1 if current_streak < 0 else -1
            max_loss_streak = max(max_loss_streak, abs(current_streak))
        else:
            current_streak = 0

    print(f"\n📊 STREAKS:")
    print(f"   Longest Win Streak: {max_win_streak} days")
    print(f"   Longest Loss Streak: {max_loss_streak} days")

    # Save results
    output_file = Path(__file__).parent.parent.parent / "3_month_sequential_results.json"
    summary = {
        "test_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "starting_capital": starting_capital,
        "final_capital": final_capital,
        "total_return": total_return,
        "total_return_pct": total_return_pct,
        "peak_capital": peak_capital,
        "max_drawdown": max_drawdown,
        "max_drawdown_date": max_drawdown_date.strftime('%Y-%m-%d') if max_drawdown_date else None,
        "trading_days": len(daily_results),
        "daily_win_rate": daily_win_rate,
        "trade_win_rate": trade_win_rate,
        "profit_factor": profit_factor,
        "total_trades": total_trades,
        "monthly_stats": monthly_stats,
        "best_day": best_day,
        "worst_day": worst_day,
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
        "daily_results": daily_results,
        "equity_curve": equity_curve
    }

    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📊 Results saved to: {output_file}")

    # Final verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80 + "\n")

    if total_return_pct > 5:
        print(f"✅ STRATEGY IS PROFITABLE!")
        print(f"   Return: {total_return_pct:+.2f}% over 3 months")
        print(f"   Annualized: {total_return_pct * 4:+.1f}% (if consistent)")
        print(f"   Max Drawdown: {max_drawdown:.2f}%")

        if profit_factor > 1.5:
            print(f"\n   💪 STRONG EDGE - Profit factor {profit_factor:.2f}x")
        elif profit_factor > 1.2:
            print(f"\n   👍 DECENT EDGE - Profit factor {profit_factor:.2f}x")
        else:
            print(f"\n   ⚠️  WEAK EDGE - Profit factor {profit_factor:.2f}x")

        if max_drawdown < 10:
            print(f"   ✅ LOW RISK - Drawdown {max_drawdown:.2f}% is manageable")
        elif max_drawdown < 20:
            print(f"   ⚠️  MODERATE RISK - Drawdown {max_drawdown:.2f}% is acceptable")
        else:
            print(f"   🚨 HIGH RISK - Drawdown {max_drawdown:.2f}% is concerning")

    elif total_return_pct > 0:
        print(f"⚠️  STRATEGY IS BARELY PROFITABLE")
        print(f"   Return: {total_return_pct:+.2f}% over 3 months")
        print(f"   This is marginal - needs improvement")

    else:
        print(f"❌ STRATEGY IS NOT PROFITABLE")
        print(f"   Return: {total_return_pct:+.2f}% over 3 months")
        print(f"   Lost ${abs(total_return):,.2f}")
        print(f"   Max Drawdown: {max_drawdown:.2f}%")
        print(f"\n   This strategy does not have edge in current form.")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    test_3_months_sequential()
