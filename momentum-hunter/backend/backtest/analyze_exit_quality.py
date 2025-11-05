"""
Exit Quality Analysis - Are we exiting too early?

Questions to answer:
1. When we exit on MA break or trailing stop, does the stock continue higher?
2. Are we getting shaken out of positions on normal pullbacks?
3. Could we capture more upside by adjusting our exit logic?

We'll analyze:
- Exit reason breakdown
- Price action 5 days after exit
- Price action 10 days after exit
- How much upside we left on the table
- Which exit reasons work well vs. poorly
"""

from datetime import datetime, timedelta
import sys
from pathlib import Path
import logging

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from backtest.daily_momentum_smart_exits import SmartExitBacktester
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import os
from dotenv import load_dotenv

load_dotenv()


def analyze_exit_quality(period_name, start, end, api_key, secret_key, data_client):
    """Analyze exit quality for a period."""

    print(f"\n{'='*80}")
    print(f"ANALYZING: {period_name}")
    print(f"{'='*80}\n")

    backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)
    results = backtester.run(start, end)

    print(f"Total trades: {len(results.trades)}")
    print(f"Period return: {results.total_return_percent:+.2f}%\n")

    # Analyze each trade's exit quality
    exit_analysis = []

    for trade in results.trades:
        symbol = trade['symbol']
        exit_date = datetime.strptime(trade['exit_date'], '%Y-%m-%d')
        exit_price = trade['exit_price']
        exit_reason = trade['exit_reason']
        pnl_pct = trade['pnl_pct']

        # Get price 5 and 10 days after exit
        future_start = exit_date + timedelta(days=1)
        future_end = exit_date + timedelta(days=15)

        try:
            request = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Day,
                start=future_start,
                end=future_end
            )
            future_bars = data_client.get_stock_bars(request)

            if symbol in future_bars.data and future_bars.data[symbol]:
                bars = list(future_bars.data[symbol])

                # Get prices 5 and 10 days out (or max available)
                price_5d = float(bars[min(4, len(bars)-1)].close) if len(bars) >= 1 else None
                price_10d = float(bars[min(9, len(bars)-1)].close) if len(bars) >= 1 else None

                # Calculate missed opportunity
                missed_5d = ((price_5d - exit_price) / exit_price * 100) if price_5d else None
                missed_10d = ((price_10d - exit_price) / exit_price * 100) if price_10d else None

                exit_analysis.append({
                    'symbol': symbol,
                    'exit_date': trade['exit_date'],
                    'exit_reason': exit_reason,
                    'pnl_pct': pnl_pct,
                    'exit_price': exit_price,
                    'price_5d': price_5d,
                    'price_10d': price_10d,
                    'missed_5d': missed_5d,
                    'missed_10d': missed_10d,
                })

        except Exception as e:
            # Skip if can't get future data
            pass

    return exit_analysis


def main():
    """Analyze exit quality across periods."""

    logging.basicConfig(level=logging.WARNING)

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    data_client = StockHistoricalDataClient(api_key, secret_key)

    print("\n" + "="*80)
    print("EXIT QUALITY ANALYSIS")
    print("="*80)
    print("\nQuestion: Are we exiting too early and leaving money on the table?")
    print("We'll check what happened 5 and 10 days after each exit...")
    print("="*80)

    # Test a few recent periods
    periods = [
        ("Q4 2024", datetime(2024, 11, 1), datetime(2025, 1, 31)),
        ("Q3 2025", datetime(2025, 8, 1), datetime(2025, 10, 31)),
    ]

    all_exits = []

    for name, start, end in periods:
        period_exits = analyze_exit_quality(name, start, end, api_key, secret_key, data_client)
        all_exits.extend(period_exits)

    print("\n\n" + "="*80)
    print("OVERALL EXIT ANALYSIS")
    print("="*80 + "\n")

    print(f"Total exits analyzed: {len(all_exits)}")
    print()

    # Group by exit reason
    exit_reasons = {}
    for exit in all_exits:
        reason = exit['exit_reason']
        if reason not in exit_reasons:
            exit_reasons[reason] = []
        exit_reasons[reason].append(exit)

    # Analyze each exit reason
    print("="*80)
    print("EXIT REASON ANALYSIS")
    print("="*80 + "\n")

    for reason in sorted(exit_reasons.keys()):
        exits = exit_reasons[reason]
        count = len(exits)

        avg_pnl = sum(e['pnl_pct'] for e in exits) / count

        exits_with_5d = [e for e in exits if e['missed_5d'] is not None]
        exits_with_10d = [e for e in exits if e['missed_10d'] is not None]

        avg_missed_5d = sum(e['missed_5d'] for e in exits_with_5d) / len(exits_with_5d) if exits_with_5d else 0
        avg_missed_10d = sum(e['missed_10d'] for e in exits_with_10d) / len(exits_with_10d) if exits_with_10d else 0

        # Count how many continued higher
        continued_up_5d = sum(1 for e in exits_with_5d if e['missed_5d'] > 2)
        continued_up_10d = sum(1 for e in exits_with_10d if e['missed_10d'] > 5)

        print(f"{reason}:")
        print(f"  Count: {count} trades")
        print(f"  Avg P&L at exit: {avg_pnl:+.1f}%")
        print(f"  Avg missed (5d): {avg_missed_5d:+.1f}%")
        print(f"  Avg missed (10d): {avg_missed_10d:+.1f}%")
        print(f"  Continued up 5d later: {continued_up_5d}/{len(exits_with_5d)} ({continued_up_5d/len(exits_with_5d)*100:.0f}%)" if exits_with_5d else "")
        print(f"  Continued up 10d later: {continued_up_10d}/{len(exits_with_10d)} ({continued_up_10d/len(exits_with_10d)*100:.0f}%)" if exits_with_10d else "")
        print()

        # Show specific examples
        if avg_missed_5d > 3:
            print(f"  ⚠️  HIGH MISSED OPPORTUNITY: Exiting {avg_missed_5d:+.1f}% too early on average")
            print(f"  Examples:")
            for e in sorted(exits_with_5d, key=lambda x: x['missed_5d'], reverse=True)[:3]:
                print(f"    {e['symbol']} on {e['exit_date']}: exited at ${e['exit_price']:.2f}, "
                      f"was ${e['price_5d']:.2f} 5d later ({e['missed_5d']:+.1f}%)")
        print()

    # Overall statistics
    print("="*80)
    print("OVERALL STATISTICS")
    print("="*80 + "\n")

    all_with_5d = [e for e in all_exits if e['missed_5d'] is not None]
    all_with_10d = [e for e in all_exits if e['missed_10d'] is not None]

    overall_missed_5d = sum(e['missed_5d'] for e in all_with_5d) / len(all_with_5d) if all_with_5d else 0
    overall_missed_10d = sum(e['missed_10d'] for e in all_with_10d) / len(all_with_10d) if all_with_10d else 0

    print(f"Average missed opportunity (5 days): {overall_missed_5d:+.2f}%")
    print(f"Average missed opportunity (10 days): {overall_missed_10d:+.2f}%")
    print()

    # Categorize
    too_early = sum(1 for e in all_with_5d if e['missed_5d'] > 3)
    just_right = sum(1 for e in all_with_5d if -2 <= e['missed_5d'] <= 3)
    good_exit = sum(1 for e in all_with_5d if e['missed_5d'] < -2)

    print(f"Exit timing analysis (5 days out):")
    print(f"  Too early (stock up 3%+): {too_early}/{len(all_with_5d)} ({too_early/len(all_with_5d)*100:.0f}%)")
    print(f"  Good timing (-2% to +3%): {just_right}/{len(all_with_5d)} ({just_right/len(all_with_5d)*100:.0f}%)")
    print(f"  Saved losses (stock down 2%+): {good_exit}/{len(all_with_5d)} ({good_exit/len(all_with_5d)*100:.0f}%)")
    print()

    # Verdict
    print("="*80)
    print("VERDICT: EXIT STRATEGY QUALITY")
    print("="*80 + "\n")

    if overall_missed_5d > 5:
        print(f"❌ EXITS TOO EARLY: Missing {overall_missed_5d:+.1f}% on average")
        print(f"   Strategy is cutting winners short")
        print(f"\n   Recommendations:")
        print(f"   1. Widen trailing stops (currently 2x ATR → try 3x ATR)")
        print(f"   2. Be less sensitive to MA breaks (5-day MA → try 10-day MA)")
        print(f"   3. Remove lower high exit (may be too aggressive)")
        print(f"   4. Extend time stop (15 days → 20 days)")

    elif overall_missed_5d > 2:
        print(f"⚠️  MODEST ROOM FOR IMPROVEMENT: Missing {overall_missed_5d:+.1f}% on average")
        print(f"   Exits are reasonable but could be optimized")
        print(f"\n   Consider:")
        print(f"   1. Slightly wider trailing stops for highly profitable trades")
        print(f"   2. Allow one MA violation before exiting")

    elif overall_missed_5d > -2:
        print(f"✅ GOOD EXIT TIMING: Missing {overall_missed_5d:+.1f}% on average")
        print(f"   This is acceptable - you can't catch every move")
        print(f"   Exit strategy is well-balanced")

    else:
        print(f"✅ EXCELLENT EXIT TIMING: Saving {abs(overall_missed_5d):.1f}% by exiting early")
        print(f"   Stocks declined after exit - strategy protected profits well")

    # Specific exit reason recommendations
    print("\n" + "="*80)
    print("EXIT REASON RECOMMENDATIONS")
    print("="*80 + "\n")

    for reason in sorted(exit_reasons.keys()):
        exits = exit_reasons[reason]
        exits_with_5d = [e for e in exits if e['missed_5d'] is not None]
        if not exits_with_5d:
            continue

        avg_missed = sum(e['missed_5d'] for e in exits_with_5d) / len(exits_with_5d)

        print(f"{reason}:")
        if avg_missed > 5:
            print(f"  ❌ TOO AGGRESSIVE: Missing {avg_missed:+.1f}% on average")
            print(f"  → Consider removing or loosening this exit")
        elif avg_missed > 2:
            print(f"  ⚠️  SLIGHTLY EARLY: Missing {avg_missed:+.1f}% on average")
            print(f"  → Consider slight adjustments")
        elif avg_missed > -2:
            print(f"  ✅ GOOD: Missing {avg_missed:+.1f}% (acceptable)")
        else:
            print(f"  ✅ EXCELLENT: Saved {abs(avg_missed):.1f}% by exiting")
        print()

    print("="*80 + "\n")


if __name__ == "__main__":
    main()
