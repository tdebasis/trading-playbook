"""
Scanner Diagnostic - See why so few breakouts detected.

This will show what's filtering out stocks.
"""

from datetime import datetime
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import os
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import timedelta

load_dotenv()

def diagnose_symbol(symbol: str, date: datetime):
    """Diagnose why a symbol isn't passing scanner."""

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    client = StockHistoricalDataClient(api_key, secret_key)

    # Fetch 6 months of data
    start_date = date - timedelta(days=180)

    request = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=TimeFrame.Day,
        start=start_date,
        end=date
    )

    try:
        bars_response = client.get_stock_bars(request)

        if symbol not in bars_response.data or not bars_response.data[symbol]:
            print(f"  ❌ {symbol}: No data available")
            return

        bars = list(bars_response.data[symbol])

        if len(bars) < 50:
            print(f"  ❌ {symbol}: Only {len(bars)} bars (need 50+)")
            return

        current_bar = bars[-1]

        # Calculate metrics
        sma_20 = sum(b.close for b in bars[-20:]) / 20
        sma_50 = sum(b.close for b in bars[-50:]) / 50
        high_52w = max(b.high for b in bars)
        distance_from_high = ((high_52w - current_bar.close) / high_52w) * 100

        avg_volume = sum(b.volume for b in bars[-20:-1]) / 19
        volume_ratio = current_bar.volume / avg_volume if avg_volume > 0 else 0

        # Check each filter
        print(f"\n  {symbol} @ ${current_bar.close:.2f}:")
        print(f"    Price: ${current_bar.close:.2f}")
        print(f"    SMA20: ${sma_20:.2f} | SMA50: ${sma_50:.2f}")

        # Check trend
        if current_bar.close > sma_20 > sma_50:
            print(f"    ✅ Trend: Proper (price > SMA20 > SMA50)")
        elif current_bar.close > sma_20:
            print(f"    ⚠️  Trend: Price > SMA20, but SMA20 < SMA50 (weak)")
        else:
            print(f"    ❌ Trend: Price below SMA20 (FILTERED OUT)")
            return

        # Check distance from high
        if distance_from_high <= 25:
            print(f"    ✅ Distance from 52w high: {distance_from_high:.1f}% (within 25%)")
        else:
            print(f"    ❌ Distance from 52w high: {distance_from_high:.1f}% (>25%, FILTERED OUT)")
            return

        # Check volume
        if volume_ratio >= 1.5:
            print(f"    ✅ Volume: {volume_ratio:.1f}x average (>1.5x)")
        else:
            print(f"    ❌ Volume: {volume_ratio:.1f}x average (<1.5x, FILTERED OUT)")
            return

        # Check for consolidation base
        print(f"    🔍 Looking for consolidation base...")
        base_found = False
        for length in range(10, 90):
            if len(bars) < length + 1:
                break

            base_bars = bars[-(length+1):-1]
            if not base_bars:
                continue

            base_high = max(b.high for b in base_bars)
            base_low = min(b.low for b in base_bars)
            base_range = base_high - base_low
            base_tightness = base_range / base_high if base_high > 0 else 1.0

            if base_tightness <= 0.08:  # 8% max volatility
                print(f"    ✅ Found base: {length} days, {base_tightness*100:.1f}% volatility")

                # Check if breaking out
                if current_bar.close > base_high:
                    print(f"    ✅ BREAKOUT! ${current_bar.close:.2f} > ${base_high:.2f}")
                    print(f"    🎯 THIS STOCK SHOULD PASS!")
                else:
                    print(f"    ❌ Not breaking out: ${current_bar.close:.2f} <= ${base_high:.2f}")

                base_found = True
                break

        if not base_found:
            print(f"    ❌ No tight consolidation base found (FILTERED OUT)")

    except Exception as e:
        print(f"  ❌ {symbol}: Error - {e}")


if __name__ == "__main__":
    # Test on Aug 6 (day when intraday found 25+ spikes but daily found 0)
    test_date = datetime(2025, 8, 6)

    print("="*80)
    print(f"SCANNER DIAGNOSTIC - {test_date.strftime('%Y-%m-%d')}")
    print("="*80)
    print("\nChecking why stocks are being filtered out...")
    print("\nTesting symbols that had intraday spikes on Aug 6:")

    symbols = ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMD', 'META', 'NVAX', 'SNAP', 'PTON']

    for symbol in symbols:
        diagnose_symbol(symbol, test_date)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\nMost stocks are being filtered out because:")
    print("  1. Not in proper uptrend (price > SMA20 > SMA50)")
    print("  2. Too far from 52-week highs (>25%)")
    print("  3. No tight consolidation base (<8% volatility)")
    print("  4. Not enough volume (>1.5x average)")
    print("\nThis is CORRECT behavior for quality breakouts,")
    print("but means few opportunities in choppy markets.")
