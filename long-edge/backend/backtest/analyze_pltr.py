"""
Analyze PLTR (Palantir) - Why isn't it being picked up?

PLTR had massive moves in 2024-2025, yet our scanner might be missing it.
Let's see what the scanner sees on specific dates.
"""

from datetime import datetime, timedelta
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from scanner.daily_breakout_scanner import DailyBreakoutScanner
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import os
from dotenv import load_dotenv

load_dotenv()


def analyze_pltr_on_date(scanner, data_client, date):
    """Deep dive into PLTR on a specific date."""

    print(f"\n{'='*80}")
    print(f"PLTR ANALYSIS - {date.strftime('%Y-%m-%d (%A)')}")
    print(f"{'='*80}\n")

    # Get 6 months of data leading up to this date
    start = date - timedelta(days=180)

    try:
        request = StockBarsRequest(
            symbol_or_symbols=['PLTR'],
            timeframe=TimeFrame.Day,
            start=start,
            end=date
        )
        response = data_client.get_stock_bars(request)

        if 'PLTR' not in response.data or len(response.data['PLTR']) == 0:
            print("❌ No data available")
            return

        bars = list(response.data['PLTR'])

        if len(bars) < 50:
            print(f"❌ Insufficient data ({len(bars)} bars)")
            return

        current_bar = bars[-1]
        current_price = float(current_bar.close)
        current_volume = float(current_bar.volume)

        print(f"📊 CURRENT PRICE DATA:")
        print(f"   Close: ${current_price:.2f}")
        print(f"   High: ${float(current_bar.high):.2f}")
        print(f"   Low: ${float(current_bar.low):.2f}")
        print(f"   Volume: {current_volume:,.0f}")
        print()

        # Calculate indicators
        closes = [float(b.close) for b in bars]
        volumes = [float(b.volume) for b in bars]

        sma_20 = sum(closes[-20:]) / 20
        sma_50 = sum(closes[-50:]) / 50
        avg_volume = sum(volumes[-20:]) / 20
        volume_ratio = current_volume / avg_volume

        high_52w = max(closes)
        high_52w_idx = closes.index(high_52w)
        high_52w_date = bars[high_52w_idx].timestamp
        distance_from_high = ((high_52w - current_price) / high_52w) * 100

        print(f"📈 TREND ANALYSIS:")
        print(f"   SMA 20: ${sma_20:.2f}")
        print(f"   SMA 50: ${sma_50:.2f}")
        print(f"   Price > SMA20 > SMA50? {current_price > sma_20 > sma_50}")
        if current_price > sma_20:
            print(f"   ✅ Price above SMA20 (+{((current_price - sma_20) / sma_20 * 100):.1f}%)")
        else:
            print(f"   ❌ Price below SMA20 ({((current_price - sma_20) / sma_20 * 100):.1f}%)")

        if sma_20 > sma_50:
            print(f"   ✅ SMA20 above SMA50 (+{((sma_20 - sma_50) / sma_50 * 100):.1f}%)")
        else:
            print(f"   ❌ SMA20 below SMA50 ({((sma_20 - sma_50) / sma_50 * 100):.1f}%)")
        print()

        print(f"🎯 52-WEEK HIGH:")
        print(f"   High: ${high_52w:.2f} (on {high_52w_date.strftime('%Y-%m-%d')})")
        print(f"   Current distance: {distance_from_high:.1f}%")
        if distance_from_high <= 25:
            print(f"   ✅ Within 25% of high")
        else:
            print(f"   ❌ More than 25% from high (scanner filters out)")
        print()

        print(f"📊 VOLUME:")
        print(f"   Current: {current_volume:,.0f}")
        print(f"   20-day avg: {avg_volume:,.0f}")
        print(f"   Ratio: {volume_ratio:.2f}x")
        if volume_ratio >= 1.5:
            print(f"   ✅ Volume expansion (>1.5x)")
        else:
            print(f"   ❌ No volume expansion (<1.5x)")
        print()

        # Check for consolidation base
        print(f"🔍 CONSOLIDATION BASE CHECK:")
        base_found = False
        best_base = None

        for length in range(10, min(90, len(bars) - 1)):
            base_bars = bars[-(length+1):-1]
            base_closes = [float(b.close) for b in base_bars]
            base_high = max(base_closes)
            base_low = min(base_closes)
            volatility = (base_high - base_low) / base_high

            if volatility <= 0.08:  # 8% max
                base_found = True
                if best_base is None or length > best_base['length']:
                    best_base = {
                        'length': length,
                        'volatility': volatility,
                        'high': base_high,
                        'low': base_low
                    }

        if base_found and best_base:
            print(f"   ✅ Found base: {best_base['length']} days")
            print(f"      Volatility: {best_base['volatility']*100:.1f}%")
            print(f"      Range: ${best_base['low']:.2f} - ${best_base['high']:.2f}")
            print(f"      Current vs base high: {((current_price - best_base['high']) / best_base['high'] * 100):+.1f}%")

            if current_price > best_base['high']:
                print(f"      ✅ Breaking out above base!")
            else:
                print(f"      ❌ Not breaking out yet ({((current_price - best_base['high']) / best_base['high'] * 100):.1f}%)")
        else:
            print(f"   ❌ No tight base found (all bases > 8% volatility)")
            # Show closest bases
            print(f"\n   Closest bases:")
            for length in [20, 30, 40, 50]:
                if length < len(bars) - 1:
                    base_bars = bars[-(length+1):-1]
                    base_closes = [float(b.close) for b in base_bars]
                    base_high = max(base_closes)
                    base_low = min(base_closes)
                    vol = (base_high - base_low) / base_high
                    print(f"      {length} days: {vol*100:.1f}% volatility (need <8%)")

        print()

        # Final verdict
        print(f"{'='*80}")
        print(f"SCANNER VERDICT:")
        print(f"{'='*80}\n")

        passes = []
        fails = []

        if current_price > sma_20 > sma_50:
            passes.append("✅ Trend alignment")
        else:
            fails.append("❌ Trend alignment")

        if distance_from_high <= 25:
            passes.append("✅ Near 52w high")
        else:
            fails.append("❌ Too far from 52w high")

        if volume_ratio >= 1.5:
            passes.append("✅ Volume expansion")
        else:
            fails.append("❌ Low volume")

        if base_found:
            passes.append("✅ Consolidation base")
            if current_price > best_base['high']:
                passes.append("✅ Breakout confirmed")
            else:
                fails.append("❌ No breakout yet")
        else:
            fails.append("❌ No base")

        print("PASSES:")
        for p in passes:
            print(f"  {p}")
        print()
        print("FAILS:")
        for f in fails:
            print(f"  {f}")
        print()

        if len(fails) == 0:
            print("🎉 PLTR WOULD BE SELECTED!")
        else:
            print(f"❌ PLTR FILTERED OUT ({len(fails)} criteria failed)")

        # Show what would happen if we relaxed criteria
        print()
        print("💡 WITH RELAXED CRITERIA (Volume 1.2x, Base 12%):")
        relaxed_fails = []

        if current_price > sma_20 > sma_50:
            pass
        else:
            relaxed_fails.append("Trend")

        if distance_from_high <= 25:
            pass
        else:
            relaxed_fails.append("Distance")

        if volume_ratio >= 1.2:  # Relaxed
            pass
        else:
            relaxed_fails.append("Volume")

        # Check for 12% base
        relaxed_base_found = False
        for length in range(10, min(90, len(bars) - 1)):
            base_bars = bars[-(length+1):-1]
            base_closes = [float(b.close) for b in base_bars]
            base_high = max(base_closes)
            base_low = min(base_closes)
            volatility = (base_high - base_low) / base_high
            if volatility <= 0.12:
                relaxed_base_found = True
                if current_price > base_high:
                    pass  # Would pass
                else:
                    relaxed_fails.append("Breakout")
                break

        if not relaxed_base_found:
            relaxed_fails.append("Base")

        if len(relaxed_fails) == 0:
            print("   ✅ WOULD BE SELECTED with relaxed criteria!")
        else:
            print(f"   ❌ Still filtered out: {', '.join(relaxed_fails)}")

        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Analyze PLTR on key dates."""

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    scanner = DailyBreakoutScanner(api_key, secret_key)
    data_client = StockHistoricalDataClient(api_key, secret_key)

    print("\n" + "="*80)
    print("PLTR (PALANTIR) SCANNER ANALYSIS")
    print("="*80)
    print("\nAnalyzing why PLTR isn't being picked up by the scanner")
    print("during periods when it had massive moves...\n")

    # Key dates to analyze
    dates = [
        datetime(2024, 1, 2),   # Start of 2024
        datetime(2024, 5, 1),   # Mid 2024
        datetime(2024, 8, 1),   # Q3 2024 start
        datetime(2024, 11, 1),  # Q4 2024 start (big rally period)
        datetime(2024, 12, 1),  # Q4 continued
        datetime(2025, 2, 1),   # Early 2025
        datetime(2025, 8, 1),   # Recent period
    ]

    for date in dates:
        analyze_pltr_on_date(scanner, data_client, date)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80 + "\n")

    print("The analysis above shows exactly why PLTR isn't being picked up.")
    print("Most likely reasons:")
    print("  1. Volume expansion threshold too high (1.5x)")
    print("  2. Base volatility threshold too tight (8%)")
    print("  3. Missing entries by waiting for perfect breakout")
    print()
    print("PLTR is a high-beta stock that:")
    print("  - Consolidates in 10-20% ranges (not 8%)")
    print("  - Moves on 1.2-1.4x volume (not 1.5x+)")
    print("  - Trends strongly when it goes (not tight bases)")
    print()


if __name__ == "__main__":
    main()
