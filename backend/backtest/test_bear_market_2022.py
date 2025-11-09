"""
Bear Market Test - 2022

Test the validated momentum strategy during a significant bear market.

2022 Bear Market Context:
- S&P 500 dropped ~25% (Jan-Oct 2022)
- Fed rate hikes, inflation fears
- Tech stocks crushed (NVDA -50%, many growth stocks -60-80%)
- Classic bear market conditions

Key Question: Does our momentum strategy:
1. Lose less than the market? (good)
2. Break even? (excellent)
3. Make money? (exceptional, unlikely)
4. Lose catastrophically? (strategy fails in bear markets)

Our Strategy:
- Volume: 1.2x
- Base: 12% volatility
- Trend: SMA20 > SMA50
- Smart exits with 15-day time stop
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


def test_bear_market_period(name, start, end, spy_return, api_key, secret_key):
    """Test a bear market period."""
    print(f"\n{'='*80}")
    print(f"TESTING: {name}")
    print(f"{'='*80}")
    print(f"S&P 500 return during this period: {spy_return:+.1f}%")
    print(f"{'='*80}\n")

    backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)
    results = backtester.run(start, end)

    print(f"\n📊 {name} RESULTS:")
    print(f"   Return: {results.total_return_percent:+.2f}%")
    print(f"   S&P 500: {spy_return:+.1f}%")
    print(f"   Outperformance: {results.total_return_percent - spy_return:+.2f}%")
    print(f"   Win Rate: {results.win_rate:.1f}%")
    print(f"   Profit Factor: {results.profit_factor:.2f}x")
    print(f"   Trades: {results.total_trades}")
    print(f"   Max Drawdown: {results.max_drawdown_percent:.1f}%")
    print(f"   Avg Win: ${results.avg_win:+,.0f}")
    print(f"   Avg Loss: ${results.avg_loss:+,.0f}")

    return {
        'period': name,
        'return': results.total_return_percent,
        'spy_return': spy_return,
        'outperformance': results.total_return_percent - spy_return,
        'win_rate': results.win_rate,
        'profit_factor': results.profit_factor,
        'trades': results.total_trades,
        'max_drawdown': results.max_drawdown_percent,
        'avg_win': results.avg_win,
        'avg_loss': results.avg_loss,
    }


def main():
    """Test strategy during 2022 bear market."""

    logging.basicConfig(level=logging.WARNING)

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    print("\n" + "="*80)
    print("BEAR MARKET TEST - 2022")
    print("="*80)
    print("\n2022 was a brutal bear market:")
    print("  • S&P 500: -25% peak-to-trough")
    print("  • Tech stocks: -50% to -80%")
    print("  • Fed rate hikes, inflation, recession fears")
    print("\nHow does our momentum strategy perform when markets decline?")
    print("="*80)

    # Test 2022 bear market periods
    # S&P 500 returns are approximate
    periods = [
        ("Q1 2022", datetime(2022, 1, 3), datetime(2022, 3, 31), -4.9),   # S&P -4.9%
        ("Q2 2022", datetime(2022, 4, 1), datetime(2022, 6, 30), -16.1),  # S&P -16.1% (worst quarter)
        ("Q3 2022", datetime(2022, 7, 1), datetime(2022, 9, 30), -4.9),   # S&P -4.9%
        ("Q4 2022", datetime(2022, 10, 1), datetime(2022, 12, 31), 7.1),  # S&P +7.1% (recovery)
    ]

    results = []
    for name, start, end, spy_return in periods:
        result = test_bear_market_period(name, start, end, spy_return, api_key, secret_key)
        results.append(result)

    # Summary
    print("\n\n" + "="*80)
    print("2022 BEAR MARKET SUMMARY")
    print("="*80 + "\n")

    print(f"{'Period':<12} {'Strategy':<12} {'S&P 500':<12} {'Outperf':<12} {'Trades':<10} {'Max DD':<10}")
    print("-" * 80)

    total_strategy = 0
    total_spy = 0
    total_trades = 0

    for r in results:
        print(f"{r['period']:<12} {r['return']:>+8.2f}% {r['spy_return']:>10.1f}% "
              f"{r['outperformance']:>+10.2f}% {r['trades']:>8} {r['max_drawdown']:>8.1f}%")
        total_strategy += r['return']
        total_spy += r['spy_return']
        total_trades += r['trades']

    print("-" * 80)
    print(f"{'TOTAL':<12} {total_strategy:>+8.2f}% {total_spy:>10.1f}% "
          f"{total_strategy - total_spy:>+10.2f}% {total_trades:>8}")
    print()

    # Analysis
    print("="*80)
    print("BEAR MARKET PERFORMANCE ANALYSIS")
    print("="*80 + "\n")

    avg_strategy = total_strategy / len(results)
    avg_spy = total_spy / len(results)
    avg_outperformance = avg_strategy - avg_spy

    print(f"Average quarterly return:")
    print(f"  Strategy: {avg_strategy:+.2f}%")
    print(f"  S&P 500: {avg_spy:+.1f}%")
    print(f"  Outperformance: {avg_outperformance:+.2f}%")
    print()

    # Calculate full year compound returns
    strategy_multiplier = 1.0
    spy_multiplier = 1.0
    for r in results:
        strategy_multiplier *= (1 + r['return'] / 100)
        spy_multiplier *= (1 + r['spy_return'] / 100)

    strategy_year_return = (strategy_multiplier - 1) * 100
    spy_year_return = (spy_multiplier - 1) * 100

    print(f"Full year 2022 (compounded):")
    print(f"  Strategy: {strategy_year_return:+.2f}%")
    print(f"  S&P 500: {spy_year_return:+.1f}%")
    print(f"  Outperformance: {strategy_year_return - spy_year_return:+.2f}%")
    print()

    # Verdict
    print("="*80)
    print("VERDICT: BEAR MARKET RESILIENCE")
    print("="*80 + "\n")

    if strategy_year_return > 0:
        print(f"✅ EXCEPTIONAL: Strategy made money (+{strategy_year_return:.2f}%) in a bear market!")
        print(f"   S&P 500 lost {spy_year_return:.1f}%")
        print(f"   This is rare - most strategies lose in bear markets")
        print(f"\n   💡 Strategy shows strong defensive characteristics:")
        print(f"      • 15-day time stop cuts losers quickly")
        print(f"      • Requires SMA20 > SMA50 (filters out downtrends)")
        print(f"      • Only enters when stocks break out (limited entries in bear market)")

    elif strategy_year_return > spy_year_return + 5:
        print(f"✅ GOOD: Strategy outperformed by {strategy_year_return - spy_year_return:+.1f}%")
        print(f"   Strategy: {strategy_year_return:+.2f}%")
        print(f"   S&P 500: {spy_year_return:+.1f}%")
        print(f"\n   Lost less than the market - this is a win in bear markets")

    elif strategy_year_return > spy_year_return:
        print(f"⚠️  MODEST: Strategy outperformed slightly ({strategy_year_return - spy_year_return:+.1f}%)")
        print(f"   Strategy: {strategy_year_return:+.2f}%")
        print(f"   S&P 500: {spy_year_return:+.1f}%")
        print(f"\n   Better than the market, but still lost money")

    else:
        print(f"❌ POOR: Strategy underperformed the market")
        print(f"   Strategy: {strategy_year_return:+.2f}%")
        print(f"   S&P 500: {spy_year_return:+.1f}%")
        print(f"   Underperformance: {strategy_year_return - spy_year_return:+.2f}%")
        print(f"\n   ⚠️  WARNING: Strategy does not protect capital in bear markets")
        print(f"   Consider:")
        print(f"      • Using this only in bull markets")
        print(f"      • Adding market regime filter (SMA200 slope)")
        print(f"      • Reducing position size in volatile markets")

    # Trade activity analysis
    print("\n" + "="*80)
    print("TRADE ACTIVITY IN BEAR MARKET")
    print("="*80 + "\n")

    print(f"Total trades in 2022: {total_trades}")
    print(f"Average per quarter: {total_trades / len(results):.1f}")
    print()

    if total_trades < 20:
        print(f"✅ GOOD: Low trade activity ({total_trades} trades)")
        print(f"   Strategy correctly avoided most setups in bear market")
        print(f"   SMA20 > SMA50 filter kept us out of downtrending stocks")
    elif total_trades < 40:
        print(f"⚠️  MODERATE: Some trade activity ({total_trades} trades)")
        print(f"   Strategy found some momentum even in bear market")
    else:
        print(f"❌ CONCERNING: High trade activity ({total_trades} trades)")
        print(f"   Strategy may be generating too many false signals in bear market")

    # Compare to bull market performance
    print("\n" + "="*80)
    print("BULL vs BEAR MARKET COMPARISON")
    print("="*80 + "\n")

    # Bull market avg from our previous tests: +2.54%
    bull_market_avg = 2.54

    print(f"Momentum strategies typically perform better in bull markets:")
    print(f"  Bull market avg (2024-2025): {bull_market_avg:+.2f}% per quarter")
    print(f"  Bear market avg (2022): {avg_strategy:+.2f}% per quarter")
    print(f"  Difference: {avg_strategy - bull_market_avg:+.2f}%")
    print()

    if avg_strategy > 0:
        print(f"💡 INSIGHT: Strategy is ALL-WEATHER")
        print(f"   Works in both bull and bear markets (rare!)")
    elif avg_strategy > bull_market_avg - 5:
        print(f"💡 INSIGHT: Strategy has moderate drawdown in bear markets")
        print(f"   This is normal for momentum strategies")
    else:
        print(f"⚠️  INSIGHT: Strategy struggles significantly in bear markets")
        print(f"   Consider market regime filters or position sizing adjustments")

    # Save results
    output = {
        'test_type': 'bear_market_2022',
        'results': results,
        'total_strategy_return': total_strategy,
        'total_spy_return': total_spy,
        'year_strategy_return': strategy_year_return,
        'year_spy_return': spy_year_return,
        'outperformance': strategy_year_return - spy_year_return,
        'total_trades': total_trades,
    }

    output_file = Path(__file__).parent.parent.parent / "bear_market_2022_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n📊 Results saved to: {output_file}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
