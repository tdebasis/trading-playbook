"""
Analyze PLTR performance during test periods.

Why didn't we capture more of PLTR's upswing?
Let's see what actually happened.
"""

from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import sys
from pathlib import Path

backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from scanner.daily_breakout_scanner import DailyBreakoutScanner

load_dotenv()

api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

client = StockHistoricalDataClient(api_key, secret_key)
scanner = DailyBreakoutScanner(api_key, secret_key)


def analyze_pltr_period(start_date, end_date, period_name):
    """Analyze PLTR during a specific period."""

    print(f"\n{'='*80}")
    print(f"{period_name}: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"{'='*80}\n")

    # Get PLTR data
    request = StockBarsRequest(
        symbol_or_symbols=['PLTR'],
        timeframe=TimeFrame.Day,
        start=start_date - timedelta(days=60),  # Extra for MA calculations
        end=end_date
    )

    bars_response = client.get_stock_bars(request)

    if 'PLTR' not in bars_response.data:
        print("No PLTR data available")
        return

    bars = list(bars_response.data['PLTR'])

    # Find bars within test period
    period_bars = [b for b in bars if start_date.date() <= b.timestamp.date() <= end_date.date()]

    if not period_bars:
        print("No bars in period")
        return

    # Calculate price movement
    start_price = float(period_bars[0].close)
    end_price = float(period_bars[-1].close)
    high_price = max(float(b.high) for b in period_bars)
    low_price = min(float(b.low) for b in period_bars)

    total_return = ((end_price - start_price) / start_price) * 100
    max_gain = ((high_price - start_price) / start_price) * 100
    max_drawdown = ((low_price - start_price) / start_price) * 100

    print(f"📊 PRICE ACTION:")
    print(f"   Start: ${start_price:.2f}")
    print(f"   End: ${end_price:.2f}")
    print(f"   High: ${high_price:.2f}")
    print(f"   Low: ${low_price:.2f}")
    print(f"   Total Return: {total_return:+.1f}%")
    print(f"   Max Gain: {max_gain:+.1f}%")
    print(f"   Max Drawdown: {max_drawdown:+.1f}%")

    # Check when scanner would have detected it
    print(f"\n🔍 SCANNER DETECTIONS:")

    detections = []
    trading_days = [b.timestamp for b in period_bars]

    for day in trading_days:
        try:
            candidate = scanner._analyze_symbol('PLTR', day)
            if candidate:
                detections.append({
                    'date': day,
                    'price': candidate.close,
                    'score': candidate.score(),
                    'volume_ratio': candidate.breakout_volume_ratio,
                    'base_days': candidate.consolidation_days,
                    'distance_from_high': candidate.distance_from_52w_high
                })
        except:
            pass

    if detections:
        print(f"\n   ✅ Scanner detected PLTR {len(detections)} times:")
        for i, d in enumerate(detections[:5], 1):  # Show first 5
            entry_price = d['price']
            # Calculate what return would have been if held to end
            potential_return = ((end_price - entry_price) / entry_price) * 100
            # Calculate max return if sold at high
            max_potential = ((high_price - entry_price) / entry_price) * 100

            print(f"\n   {i}. {d['date'].strftime('%Y-%m-%d')}:")
            print(f"      Entry: ${entry_price:.2f}")
            print(f"      Score: {d['score']:.1f}/10")
            print(f"      Volume: {d['volume_ratio']:.1f}x")
            print(f"      Base: {d['base_days']} days")
            print(f"      Potential return (to end): {potential_return:+.1f}%")
            print(f"      Potential return (to high): {max_potential:+.1f}%")
    else:
        print(f"   ❌ Scanner never detected PLTR breakout")
        print(f"\n   WHY NOT? Let's check the filters:")

        # Check a sample day in the middle of the period
        mid_point = len(period_bars) // 2
        sample_day = period_bars[mid_point].timestamp

        # Manually check filters
        all_bars = [b for b in bars if b.timestamp <= sample_day]
        if len(all_bars) >= 50:
            current_bar = all_bars[-1]

            print(f"\n   Sample check on {sample_day.strftime('%Y-%m-%d')}:")
            print(f"   Price: ${current_bar.close:.2f}")

            # Check SMA trend
            sma_20 = sum(float(b.close) for b in all_bars[-20:]) / 20
            sma_50 = sum(float(b.close) for b in all_bars[-50:]) / 50

            trend_ok = current_bar.close > sma_20 and sma_20 > sma_50
            print(f"   Trend (Close > SMA20 > SMA50): {'✅' if trend_ok else '❌'}")
            print(f"      Close: ${current_bar.close:.2f}, SMA20: ${sma_20:.2f}, SMA50: ${sma_50:.2f}")

            # Check 52w high distance
            high_52w = max(float(b.high) for b in all_bars)
            distance = ((high_52w - current_bar.close) / high_52w) * 100
            distance_ok = distance <= 25
            print(f"   Distance from 52w high: {distance:.1f}% {'✅' if distance_ok else '❌ (>25%)'}")

            # Check volume
            avg_volume = sum(float(b.volume) for b in all_bars[-20:-1]) / 19
            volume_ratio = float(current_bar.volume) / avg_volume
            volume_ok = volume_ratio >= 1.2
            print(f"   Volume ratio: {volume_ratio:.1f}x {'✅' if volume_ok else '❌ (<1.2x)'}")

    # Show actual daily movements to see choppiness
    print(f"\n📈 DAILY MOVEMENTS (first 10 days):")
    for i, bar in enumerate(period_bars[:10], 1):
        day_change = ((float(bar.close) - float(bar.open)) / float(bar.open)) * 100
        print(f"   {bar.timestamp.strftime('%Y-%m-%d')}: "
              f"${bar.open:.2f} → ${bar.close:.2f} ({day_change:+.1f}%)")


# Test all periods
periods = [
    ("Q1 2024", datetime(2024, 1, 1), datetime(2024, 3, 31)),
    ("Q2 2024", datetime(2024, 4, 1), datetime(2024, 6, 30)),
    ("Q3 2024", datetime(2024, 7, 1), datetime(2024, 9, 30)),
    ("Q4 2024", datetime(2024, 10, 1), datetime(2024, 12, 31)),
    ("Q1 2025", datetime(2025, 1, 1), datetime(2025, 3, 31)),
    ("Q2 2025", datetime(2025, 4, 1), datetime(2025, 6, 30)),
    ("Q3 2025", datetime(2025, 7, 1), datetime(2025, 9, 30)),
]

print("\n" + "="*80)
print("PALANTIR (PLTR) ANALYSIS - All Test Periods")
print("="*80)
print("\nLet's see how PLTR moved and when we could have caught it...\n")

for period_name, start, end in periods:
    analyze_pltr_period(start, end, period_name)

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("\nThis analysis shows:")
print("1. How much PLTR actually moved in each period")
print("2. Whether scanner detected the breakouts")
print("3. What potential returns we missed")
print("4. Why scanner might have filtered it out")
print("\n")
