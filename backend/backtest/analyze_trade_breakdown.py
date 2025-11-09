"""
Analyze Trade Breakdown - Which stocks contributed to returns?

Critical question: Did we actually capture NVDA/PLTR gains, or are
returns coming from other stocks?

This will show:
1. Trade-by-trade breakdown for each quarter
2. Which symbols were traded
3. How much each symbol contributed to total returns
4. Whether NVDA/PLTR were actually captured
"""

from datetime import datetime
import sys
from pathlib import Path
import logging

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from backtest.daily_momentum_smart_exits import SmartExitBacktester
import os
from dotenv import load_dotenv

load_dotenv()


def analyze_period_trades(name, start, end, api_key, secret_key):
    """Analyze trades for a single period in detail."""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {name}")
    print(f"{'='*80}\n")

    backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)
    results = backtester.run(start, end)

    print(f"\n📊 {name} SUMMARY:")
    print(f"   Return: {results.total_return_percent:+.2f}%")
    print(f"   Trades: {results.total_trades}")
    print()

    # Analyze trades by symbol
    symbol_stats = {}

    for trade in results.trades:
        symbol = trade['symbol']
        pnl = trade['pnl']

        if symbol not in symbol_stats:
            symbol_stats[symbol] = {
                'trades': 0,
                'total_pnl': 0,
                'wins': 0,
                'losses': 0,
                'trade_list': []
            }

        symbol_stats[symbol]['trades'] += 1
        symbol_stats[symbol]['total_pnl'] += pnl

        if pnl > 0:
            symbol_stats[symbol]['wins'] += 1
        else:
            symbol_stats[symbol]['losses'] += 1

        symbol_stats[symbol]['trade_list'].append(trade)

    # Sort by total P&L contribution
    sorted_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True)

    print(f"TRADES BY SYMBOL:")
    print("-" * 80)
    print(f"{'Symbol':<8} {'Trades':<8} {'Total P&L':<15} {'Win%':<8} {'Contribution':<15}")
    print("-" * 80)

    total_pnl = sum(stats['total_pnl'] for _, stats in sorted_symbols)

    for symbol, stats in sorted_symbols:
        win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
        contribution = (stats['total_pnl'] / total_pnl * 100) if total_pnl != 0 else 0

        print(f"{symbol:<8} {stats['trades']:<8} ${stats['total_pnl']:>+10,.0f}   {win_rate:>5.1f}%  {contribution:>+6.1f}%")

    print("-" * 80)
    print(f"{'TOTAL':<8} {len(results.trades):<8} ${total_pnl:>+10,.0f}")
    print()

    # Detailed trade list
    print(f"\nDETAILED TRADE LOG:")
    print("-" * 80)
    print(f"{'Symbol':<8} {'Entry':<12} {'Exit':<12} {'Days':<6} {'P&L':<12} {'%':<8} {'Reason':<15}")
    print("-" * 80)

    for trade in results.trades:
        pnl_pct = trade['pnl_pct']
        print(f"{trade['symbol']:<8} {trade['entry_date']:<12} {trade['exit_date']:<12} "
              f"{trade['hold_days']:<6} ${trade['pnl']:>+8,.0f}  {pnl_pct:>+6.1f}%  {trade['exit_reason']:<15}")

    print()

    # Check if NVDA/PLTR were traded
    print("="*80)
    print("KEY MOMENTUM STOCKS ANALYSIS")
    print("="*80 + "\n")

    key_stocks = ['NVDA', 'PLTR']

    for symbol in key_stocks:
        if symbol in symbol_stats:
            stats = symbol_stats[symbol]
            print(f"✅ {symbol} WAS TRADED:")
            print(f"   Trades: {stats['trades']}")
            print(f"   Total P&L: ${stats['total_pnl']:+,.0f}")
            print(f"   Win rate: {stats['wins']/stats['trades']*100:.1f}%")
            print(f"   Contribution to returns: {stats['total_pnl']/total_pnl*100:+.1f}%")
            print()

            # Show individual trades
            print(f"   Individual {symbol} trades:")
            for trade in stats['trade_list']:
                print(f"      {trade['entry_date']} → {trade['exit_date']}: "
                      f"${trade['pnl']:+,.0f} ({trade['pnl_pct']:+.1f}%) - {trade['exit_reason']}")
            print()
        else:
            print(f"❌ {symbol} WAS NOT TRADED")
            print(f"   The scanner did not pick up {symbol} during this period")
            print(f"   This means {symbol} didn't meet our entry criteria:")
            print(f"      - Price > SMA20 > SMA50")
            print(f"      - Volume 1.2x+ average")
            print(f"      - Consolidation base with <12% volatility")
            print(f"      - Breaking above base high")
            print()

    return {
        'period': name,
        'total_pnl': total_pnl,
        'symbol_stats': symbol_stats,
        'trades': results.trades,
    }


def main():
    """Analyze which stocks contributed to returns across all periods."""

    logging.basicConfig(level=logging.WARNING)

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    print("\n" + "="*80)
    print("TRADE BREAKDOWN ANALYSIS")
    print("="*80)
    print("\nQuestion: Did we capture NVDA/PLTR gains?")
    print("Let's analyze which stocks contributed to our returns...")
    print("="*80)

    # All tested periods
    periods = [
        ("Q1 2024", datetime(2024, 1, 2), datetime(2024, 3, 31)),
        ("Q2 2024", datetime(2024, 5, 1), datetime(2024, 7, 31)),
        ("Q3 2024", datetime(2024, 8, 1), datetime(2024, 10, 31)),
        ("Q4 2024", datetime(2024, 11, 1), datetime(2025, 1, 31)),
        ("Q2 2025", datetime(2025, 5, 1), datetime(2025, 7, 31)),
        ("Q3 2025", datetime(2025, 8, 1), datetime(2025, 10, 31)),
    ]

    all_period_results = []

    for name, start, end in periods:
        result = analyze_period_trades(name, start, end, api_key, secret_key)
        all_period_results.append(result)

    # Overall summary
    print("\n\n" + "="*80)
    print("OVERALL SUMMARY - ALL PERIODS")
    print("="*80 + "\n")

    # Aggregate by symbol across all periods
    overall_symbol_stats = {}
    total_trades = 0
    total_pnl = 0

    for period_result in all_period_results:
        for symbol, stats in period_result['symbol_stats'].items():
            if symbol not in overall_symbol_stats:
                overall_symbol_stats[symbol] = {
                    'trades': 0,
                    'total_pnl': 0,
                    'wins': 0,
                    'losses': 0,
                    'periods_traded': set()
                }

            overall_symbol_stats[symbol]['trades'] += stats['trades']
            overall_symbol_stats[symbol]['total_pnl'] += stats['total_pnl']
            overall_symbol_stats[symbol]['wins'] += stats['wins']
            overall_symbol_stats[symbol]['losses'] += stats['losses']
            overall_symbol_stats[symbol]['periods_traded'].add(period_result['period'])

        total_trades += len(period_result['trades'])
        total_pnl += period_result['total_pnl']

    # Sort by contribution
    sorted_overall = sorted(overall_symbol_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True)

    print("TOP CONTRIBUTORS TO RETURNS:")
    print("-" * 80)
    print(f"{'Symbol':<8} {'Trades':<8} {'Total P&L':<15} {'Win%':<8} {'Contribution':<12} {'Periods':<10}")
    print("-" * 80)

    for symbol, stats in sorted_overall[:15]:  # Top 15
        win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
        contribution = (stats['total_pnl'] / total_pnl * 100) if total_pnl != 0 else 0
        periods = len(stats['periods_traded'])

        print(f"{symbol:<8} {stats['trades']:<8} ${stats['total_pnl']:>+10,.0f}   {win_rate:>5.1f}%  "
              f"{contribution:>+6.1f}%    {periods}/6")

    print("-" * 80)
    print(f"{'TOTAL':<8} {total_trades:<8} ${total_pnl:>+10,.0f}")
    print()

    # NVDA/PLTR specific analysis
    print("="*80)
    print("NVDA AND PLTR - DID WE CAPTURE THE BIG MOVES?")
    print("="*80 + "\n")

    key_stocks = ['NVDA', 'PLTR']

    for symbol in key_stocks:
        print(f"\n{symbol} ANALYSIS:")
        print("-" * 80)

        if symbol in overall_symbol_stats:
            stats = overall_symbol_stats[symbol]

            print(f"✅ {symbol} WAS TRADED")
            print(f"   Total trades: {stats['trades']}")
            print(f"   Total P&L: ${stats['total_pnl']:+,.0f}")
            print(f"   Win rate: {stats['wins']/stats['trades']*100:.1f}%")
            print(f"   Contribution to total returns: {stats['total_pnl']/total_pnl*100:+.1f}%")
            print(f"   Periods traded: {len(stats['periods_traded'])}/6")
            print(f"   Periods: {', '.join(sorted(stats['periods_traded']))}")
            print()

            # Show which periods it was traded
            print(f"   {symbol} trades by period:")
            for period_result in all_period_results:
                if symbol in period_result['symbol_stats']:
                    period_stats = period_result['symbol_stats'][symbol]
                    print(f"      {period_result['period']}: {period_stats['trades']} trades, "
                          f"${period_stats['total_pnl']:+,.0f}")

            if stats['total_pnl'] > 1000:
                print(f"\n   🎯 GOOD: We captured {symbol} and it contributed meaningfully!")
            elif stats['total_pnl'] > 0:
                print(f"\n   ⚠️  MODEST: We captured {symbol} but gains were small")
            else:
                print(f"\n   ❌ BAD: We traded {symbol} but lost money")

        else:
            print(f"❌ {symbol} WAS NEVER TRADED")
            print(f"   The scanner never picked up {symbol} across all 6 periods!")
            print(f"   This is a MAJOR ISSUE - {symbol} had huge moves in 2024-2025")
            print()
            print(f"   Why wasn't {symbol} captured?")
            print(f"      1. Too strict entry criteria")
            print(f"      2. Missed the consolidation patterns")
            print(f"      3. Volume requirements too high")
            print(f"      4. Not in watchlist (check scanner watchlist)")

    print()
    print("="*80)
    print("CONCLUSION")
    print("="*80 + "\n")

    nvda_captured = 'NVDA' in overall_symbol_stats
    pltr_captured = 'PLTR' in overall_symbol_stats

    nvda_contribution = (overall_symbol_stats['NVDA']['total_pnl'] / total_pnl * 100) if nvda_captured else 0
    pltr_contribution = (overall_symbol_stats['PLTR']['total_pnl'] / total_pnl * 100) if pltr_captured else 0

    print(f"NVDA captured: {'YES' if nvda_captured else 'NO'}")
    if nvda_captured:
        print(f"   Contribution: {nvda_contribution:+.1f}% of total returns")

    print(f"\nPLTR captured: {'YES' if pltr_captured else 'NO'}")
    if pltr_captured:
        print(f"   Contribution: {pltr_contribution:+.1f}% of total returns")

    print()

    if nvda_captured and pltr_captured:
        total_key_contribution = nvda_contribution + pltr_contribution
        print(f"✅ GOOD: Both NVDA and PLTR were captured")
        print(f"   Combined contribution: {total_key_contribution:+.1f}% of total returns")

        if total_key_contribution > 50:
            print(f"\n   💡 INSIGHT: Strategy is HEAVILY dependent on NVDA/PLTR")
            print(f"   {total_key_contribution:.0f}% of returns came from just 2 stocks!")
            print(f"   Risk: If these stocks stop trending, strategy may struggle")
        elif total_key_contribution > 25:
            print(f"\n   💡 INSIGHT: NVDA/PLTR are important but not dominant")
            print(f"   Strategy is reasonably diversified")
        else:
            print(f"\n   💡 INSIGHT: Returns are well-diversified")
            print(f"   NVDA/PLTR contributed only {total_key_contribution:.0f}%")
            print(f"   Strategy found momentum in other stocks too")

    elif nvda_captured or pltr_captured:
        print(f"⚠️  MIXED: Only one of the two key stocks was captured")
        print(f"   Need to investigate why the other was missed")
    else:
        print(f"❌ PROBLEM: Neither NVDA nor PLTR were captured!")
        print(f"   Returns came from other stocks entirely")
        print(f"   This means our optimization FAILED to achieve its goal")
        print(f"   The strategy changes didn't help us catch the big winners")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
