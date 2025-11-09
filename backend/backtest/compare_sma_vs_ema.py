"""
Compare SMA20 vs EMA20 - Would EMA have caught the missed entries?

Direct comparison on the exact dates where stocks were filtered out.
"""

from datetime import datetime, timedelta
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import os
from dotenv import load_dotenv

load_dotenv()


def calculate_ema(prices, period):
    """Calculate Exponential Moving Average."""
    if len(prices) < period:
        return None

    # Start with SMA for first value
    ema = sum(prices[:period]) / period
    multiplier = 2 / (period + 1)

    # Calculate EMA for remaining values
    for price in prices[period:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))

    return ema


def analyze_date(client, symbol, date, scenario):
    """Analyze a specific date where stock was filtered out."""

    print(f"\n{'='*80}")
    print(f"{symbol} - {date.strftime('%Y-%m-%d')} - {scenario}")
    print(f"{'='*80}\n")

    start = date - timedelta(days=180)

    try:
        request = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Day,
            start=start,
            end=date
        )
        response = client.get_stock_bars(request)

        if symbol not in response.data or len(response.data[symbol]) == 0:
            print("❌ No data")
            return

        bars = list(response.data[symbol])
        if len(bars) < 50:
            print(f"❌ Insufficient data ({len(bars)} bars)")
            return

        current_bar = bars[-1]
        current_price = float(current_bar.close)
        closes = [float(b.close) for b in bars]

        # Calculate both SMAs and EMAs
        sma_20 = sum(closes[-20:]) / 20
        sma_50 = sum(closes[-50:]) / 50
        ema_20 = calculate_ema(closes, 20)
        ema_50 = calculate_ema(closes, 50)

        print(f"📊 PRICE: ${current_price:.2f}\n")

        print(f"📈 SMA20: ${sma_20:.2f}")
        print(f"   Price vs SMA20: {((current_price - sma_20) / sma_20 * 100):+.2f}%")
        sma_above = current_price > sma_20
        if sma_above:
            print(f"   ✅ Price ABOVE SMA20")
        else:
            print(f"   ❌ Price BELOW SMA20 → FILTERED OUT")
        print()

        print(f"📈 EMA20: ${ema_20:.2f}")
        print(f"   Price vs EMA20: {((current_price - ema_20) / ema_20 * 100):+.2f}%")
        ema_above = current_price > ema_20
        if ema_above:
            print(f"   ✅ Price ABOVE EMA20 → WOULD PASS!")
        else:
            print(f"   ❌ Price BELOW EMA20 → Still filtered")
        print()

        print(f"📊 SMA50: ${sma_50:.2f}")
        sma20_above_50 = sma_20 > sma_50
        print(f"   SMA20 vs SMA50: {((sma_20 - sma_50) / sma_50 * 100):+.2f}%")
        if sma20_above_50:
            print(f"   ✅ SMA20 > SMA50")
        else:
            print(f"   ❌ SMA20 < SMA50")
        print()

        print(f"📊 EMA50: ${ema_50:.2f}")
        ema20_above_50 = ema_20 > ema_50
        print(f"   EMA20 vs EMA50: {((ema_20 - ema_50) / ema_50 * 100):+.2f}%")
        if ema20_above_50:
            print(f"   ✅ EMA20 > EMA50")
        else:
            print(f"   ❌ EMA20 < EMA50")
        print()

        # Verdict
        print(f"{'='*40}")
        print(f"VERDICT:")
        print(f"{'='*40}\n")

        sma_pass = sma_above and sma20_above_50
        ema_pass = ema_above and ema20_above_50

        print(f"SMA20 approach: {'✅ WOULD PASS' if sma_pass else '❌ FILTERED OUT'}")
        print(f"EMA20 approach: {'✅ WOULD PASS' if ema_pass else '❌ FILTERED OUT'}")

        if not sma_pass and ema_pass:
            print(f"\n🎯 EMA20 CATCHES THIS! (+1 entry)")
        elif sma_pass and not ema_pass:
            print(f"\n⚠️  SMA20 better here (EMA too sensitive)")
        elif not sma_pass and not ema_pass:
            print(f"\n❌ Neither catches it (need other changes)")

        return {
            'symbol': symbol,
            'date': date.strftime('%Y-%m-%d'),
            'scenario': scenario,
            'price': current_price,
            'sma_20': sma_20,
            'ema_20': ema_20,
            'sma_pass': sma_pass,
            'ema_pass': ema_pass,
            'ema_advantage': not sma_pass and ema_pass
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Compare SMA vs EMA on missed opportunities."""

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    client = StockHistoricalDataClient(api_key, secret_key)

    print("\n" + "="*80)
    print("SMA20 vs EMA20 COMPARISON")
    print("="*80)
    print("\nAnalyzing missed entries: Would EMA20 have caught them?\n")

    # Key dates where stocks were filtered out
    test_cases = [
        ('NVDA', datetime(2024, 1, 2), 'Start of Q1 - just below SMA20'),
        ('NVDA', datetime(2024, 2, 22), 'Post-earnings - 0.03% below SMA20'),
        ('NVDA', datetime(2024, 8, 1), 'Q3 start - pullback to SMA'),
        ('PLTR', datetime(2024, 1, 2), 'Start of year - in base'),
        ('PLTR', datetime(2024, 8, 1), 'Mid-year - pullback'),
        ('PLTR', datetime(2024, 11, 1), 'Pre-rally - 2.8% below SMA20'),
    ]

    results = []
    for symbol, date, scenario in test_cases:
        result = analyze_date(client, symbol, date, scenario)
        if result:
            results.append(result)

    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY: SMA20 vs EMA20")
    print("="*80 + "\n")

    sma_passes = sum(1 for r in results if r['sma_pass'])
    ema_passes = sum(1 for r in results if r['ema_pass'])
    ema_advantages = sum(1 for r in results if r['ema_advantage'])

    print(f"Test Cases: {len(results)}")
    print(f"SMA20 would pass: {sma_passes}/{len(results)}")
    print(f"EMA20 would pass: {ema_passes}/{len(results)}")
    print(f"EMA catches but SMA misses: {ema_advantages}/{len(results)}")
    print()

    if ema_advantages > 0:
        print(f"✅ EMA20 ADVANTAGE: Catches {ema_advantages} additional entries!")
        print(f"   These are entries SMA20 missed but EMA20 would have caught.")
        print()

        print("Entries EMA20 would catch:")
        for r in results:
            if r['ema_advantage']:
                print(f"  • {r['symbol']} on {r['date']}: {r['scenario']}")
        print()

    if ema_passes > sma_passes:
        improvement = ema_passes - sma_passes
        pct_improvement = (improvement / len(results)) * 100
        print(f"📈 OVERALL: EMA20 is {pct_improvement:.0f}% better at catching entries")
        print(f"   EMA20: {ema_passes}/{len(results)} vs SMA20: {sma_passes}/{len(results)}")
        print()
        print("✅ RECOMMENDATION: Switch to EMA20 (no 0.97 buffer needed)")
    elif sma_passes > ema_passes:
        print(f"⚠️  SURPRISING: SMA20 caught more entries")
        print(f"   This suggests the problem is NOT the moving average type")
        print(f"   Need to relax OTHER filters (volume, base, etc.)")
    else:
        print(f"⚠️  TIE: Both catch same number of entries")
        print(f"   EMA20 doesn't help much by itself")
        print(f"   Need to relax OTHER filters (volume, base, etc.)")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
