#!/usr/bin/env python3
"""Debug why scoring system produces 0 trades"""
import sys
from pathlib import Path
from datetime import datetime
import os

backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

from scanner.daily_breakout_scanner_scoring import DailyBreakoutScannerScoring
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

scanner = DailyBreakoutScannerScoring(api_key, secret_key)

# Test on a date we know had candidates
# NOTE: We are in Nov 2025, so May 2025 is in the PAST
test_date = datetime(2025, 5, 23)  # SNOW and GME showed up in logs

print(f"\n{'='*80}")
print(f"DEBUGGING SCORING SYSTEM - {test_date.date()}")
print(f"{'='*80}\n")

candidates = scanner.scan(test_date)

print(f"\nFound {len(candidates)} candidates that passed scoring\n")

if len(candidates) == 0:
    print("❌ NO CANDIDATES PASSED!")
    print("\nLet's check what's happening with individual stocks...")
    
    # Manually check a few stocks we know had signals
    test_symbols = ['SNOW', 'GME', 'BNTX']
    
    for symbol in test_symbols:
        print(f"\n{'='*60}")
        print(f"DIAGNOSING: {symbol}")
        print(f"{'='*60}")

        # Manually run through each filter to see which one fails
        from datetime import timedelta
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        end_date = test_date
        start_date = test_date - timedelta(days=250)

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date
        )

        try:
            bars_dict = scanner.client.get_stock_bars(request)
            print(f"  📦 bars_dict type: {type(bars_dict)}")
            print(f"  📦 bars_dict keys/attrs: {dir(bars_dict) if hasattr(bars_dict, '__dict__') else list(bars_dict.keys()) if hasattr(bars_dict, 'keys') else 'N/A'}")

            # Handle both regular API response and cached response
            if hasattr(bars_dict, 'data'):
                # Regular Alpaca API response
                if symbol not in bars_dict.data:
                    print(f"  ❌ No data available in bars_dict.data")
                    continue
                bars = list(bars_dict.data[symbol])
            else:
                # Dict response (from cache or different format)
                if symbol not in bars_dict:
                    print(f"  ❌ No data available in bars_dict")
                    continue
                bars = list(bars_dict[symbol])
            print(f"  ✅ Data: {len(bars)} bars")

            if len(bars) < 150:
                print(f"  ❌ FAILED: Insufficient data ({len(bars)} < 150)")
                continue

            latest = bars[-1]
            print(f"  ✅ Price: ${latest.close:.2f}")

            # Check price filter
            if latest.close < scanner.min_price:
                print(f"  ❌ FAILED: Price ${latest.close:.2f} < ${scanner.min_price}")
                continue
            print(f"  ✅ Price filter passed")

            # Calculate indicators
            closes = [b.close for b in bars]
            sma_20 = sum(closes[-20:]) / 20
            sma_50 = sum(closes[-50:]) / 50
            sma_200 = sum(closes) / len(closes) if len(closes) < 200 else sum(closes[-200:]) / 200

            print(f"  📊 Close: ${latest.close:.2f}, SMA20: ${sma_20:.2f}, SMA50: ${sma_50:.2f}")

            # Check trend filter
            if not (latest.close > sma_20 > sma_50):
                print(f"  ❌ FAILED: Trend filter (need Close > SMA20 > SMA50)")
                print(f"     Close > SMA20: {latest.close > sma_20} ({latest.close:.2f} vs {sma_20:.2f})")
                print(f"     SMA20 > SMA50: {sma_20 > sma_50} ({sma_20:.2f} vs {sma_50:.2f})")
                continue
            print(f"  ✅ Trend filter passed")

            # Check 52w high
            highs_52w = [b.high for b in bars[-252:]]
            high_52w = max(highs_52w)
            distance_from_high = ((high_52w - latest.close) / high_52w) * 100

            print(f"  📊 52w High: ${high_52w:.2f}, Distance: {distance_from_high:.1f}%")

            if distance_from_high > scanner.max_distance_from_high:
                print(f"  ❌ FAILED: Too far from 52w high ({distance_from_high:.1f}% > {scanner.max_distance_from_high}%)")
                continue
            print(f"  ✅ Distance from 52w high passed")

            # Check consolidation base
            base_result = scanner._find_consolidation_base(bars)
            if not base_result:
                print(f"  ❌ FAILED: No consolidation base found (10-90 days, <12% range)")
                continue

            consolidation_high, consolidation_days, base_tightness = base_result
            print(f"  ✅ Consolidation base found: {consolidation_days} days, {base_tightness*100:.1f}% tight")
            print(f"     Base high: ${consolidation_high:.2f}")

            # Check breakout
            if latest.close <= consolidation_high:
                print(f"  ❌ FAILED: Not breaking out (${latest.close:.2f} <= ${consolidation_high:.2f})")
                continue

            print(f"  ✅ Breakout confirmed (${latest.close:.2f} > ${consolidation_high:.2f})")

            # If we got here, all filters passed!
            print(f"\n  🎉 ALL FILTERS PASSED! Getting candidate...")
            candidate = scanner._check_symbol(symbol, test_date)
            if candidate:
                scoring = candidate.score_with_volume_compensation()
                print(f"\n  📊 SCORING RESULTS:")
                print(f"     Total Score: {scoring['total']:.1f}")
                print(f"     Required: {scoring['required']:.1f}")
                print(f"     Passes: {scoring['passes']}")
                print(f"     Volume Tier: {scoring['volume_tier']}")
                print(f"     Breakdown: {scoring['breakdown']}")
            else:
                print(f"  ⚠️  Candidate returned None despite passing all checks!")

        except Exception as e:
            print(f"  ❌ ERROR: {e}")

