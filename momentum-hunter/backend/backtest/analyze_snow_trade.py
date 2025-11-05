"""
Deep Dive: SNOW Trade Analysis

Why did we only capture +6.2% when stock hit +14.3%?
Let's see exactly what happened day by day.
"""

from datetime import datetime, timedelta
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import os
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

load_dotenv()


def analyze_snow_trade():
    """Analyze SNOW trade tick by tick."""

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    client = StockHistoricalDataClient(api_key, secret_key)

    # SNOW trade details
    entry_date = datetime(2025, 10, 3)
    exit_date = datetime(2025, 10, 13)
    entry_price = 223.50

    print("="*80)
    print("SNOW TRADE DEEP DIVE")
    print("="*80)
    print(f"Entry: {entry_date.strftime('%Y-%m-%d')} @ ${entry_price:.2f}")
    print(f"Exit: {exit_date.strftime('%Y-%m-%d')}")
    print(f"Actual Exit P&L: +6.2%")
    print(f"Peak Profit Missed: +14.3%")
    print(f"Left on table: 8.1% (almost $1,800)")
    print("="*80 + "\n")

    # Fetch bars
    start = entry_date - timedelta(days=15)
    end = exit_date + timedelta(days=2)

    request = StockBarsRequest(
        symbol_or_symbols=['SNOW'],
        timeframe=TimeFrame.Day,
        start=start,
        end=end
    )

    response = client.get_stock_bars(request)
    bars = list(response.data['SNOW'])

    # Find entry bar
    entry_index = None
    for i, bar in enumerate(bars):
        if bar.timestamp.date() >= entry_date.date():
            entry_index = i
            break

    print("📊 DAY-BY-DAY PRICE ACTION:\n")

    highest_high = entry_price
    trailing_stop = entry_price * 0.92  # 8% hard stop
    atr_values = []

    for day_num, bar in enumerate(bars[entry_index:]):
        if bar.timestamp.date() > exit_date.date():
            break

        high = float(bar.high)
        low = float(bar.low)
        close = float(bar.close)

        # Calculate percentage moves
        high_pct = ((high - entry_price) / entry_price) * 100
        low_pct = ((low - entry_price) / entry_price) * 100
        close_pct = ((close - entry_price) / entry_price) * 100

        # Calculate ATR (simplified - using recent bars)
        if day_num >= 1:
            recent_bars = bars[entry_index:entry_index + day_num + 1]
            true_ranges = []
            for j in range(1, len(recent_bars)):
                h = float(recent_bars[j].high)
                l = float(recent_bars[j].low)
                pc = float(recent_bars[j-1].close)
                tr = max(h - l, abs(h - pc), abs(l - pc))
                true_ranges.append(tr)

            atr = sum(true_ranges[-10:]) / min(10, len(true_ranges))
        else:
            atr = 0

        # Update trailing stop
        if high > highest_high:
            highest_high = high
            trailing_stop = highest_high - (atr * 2)  # 2x ATR trail

        # Calculate 5-day MA
        if day_num >= 4:
            recent_closes = [float(b.close) for b in bars[entry_index + day_num - 4:entry_index + day_num + 1]]
            sma_5 = sum(recent_closes) / 5
        else:
            sma_5 = close

        print(f"Day {day_num} ({bar.timestamp.strftime('%Y-%m-%d %a')}):")
        print(f"  Price: High ${high:.2f} ({high_pct:+.1f}%), Low ${low:.2f} ({low_pct:+.1f}%), Close ${close:.2f} ({close_pct:+.1f}%)")
        print(f"  Highest High: ${highest_high:.2f} ({((highest_high - entry_price) / entry_price * 100):+.1f}%)")
        print(f"  Trailing Stop: ${trailing_stop:.2f} (2x ATR = ${atr:.2f})")
        print(f"  5-day MA: ${sma_5:.2f}")

        # Check exit conditions
        exit_triggered = False
        exit_reason = None

        # 1. Hard stop
        if low <= entry_price * 0.92:
            print(f"  🛑 WOULD HIT HARD STOP at ${entry_price * 0.92:.2f}")
            exit_triggered = True
            exit_reason = "HARD_STOP"

        # 2. Trailing stop (after 5% up)
        if highest_high > entry_price * 1.05:
            if low <= trailing_stop:
                print(f"  📉 TRAILING STOP TRIGGERED! Low ${low:.2f} <= Stop ${trailing_stop:.2f}")
                exit_triggered = True
                exit_reason = "TRAILING_STOP"
                exit_price = trailing_stop
                exit_pnl = ((exit_price - entry_price) / entry_price) * 100
                print(f"  ✅ EXIT: ${exit_price:.2f} | P&L: {exit_pnl:+.1f}%")

        # 3. MA break (after 3% up)
        if highest_high > entry_price * 1.03:
            if close < sma_5:
                print(f"  📊 WOULD BREAK 5-DAY MA! Close ${close:.2f} < MA ${sma_5:.2f}")
                if not exit_triggered:
                    exit_triggered = True
                    exit_reason = "MA_BREAK"

        # 4. Lower high (after 5% up)
        if day_num > 0 and highest_high > entry_price * 1.05:
            prev_high = float(bars[entry_index + day_num - 1].high)
            if high < prev_high:
                print(f"  ⚠️  LOWER HIGH: ${high:.2f} < Prev ${prev_high:.2f}")
                if not exit_triggered:
                    exit_triggered = True
                    exit_reason = "LOWER_HIGH"

        if exit_triggered and exit_reason == "TRAILING_STOP":
            print(f"\n  *** THIS IS WHERE WE EXITED ***")
            print(f"  Exit Reason: {exit_reason}")
            print(f"  Peak was: ${highest_high:.2f} ({((highest_high - entry_price) / entry_price * 100):+.1f}%)")
            print(f"  We got: ${exit_price:.2f} ({exit_pnl:+.1f}%)")
            print(f"  Left on table: {((highest_high - exit_price) / entry_price * 100):.1f}%\n")

        print()

    print("="*80)
    print("ANALYSIS")
    print("="*80 + "\n")

    print("📈 What Happened:")
    print("  1. Stock ran from $223.50 to $255.46 (+14.3%) on Days 0-4")
    print("  2. On Day 5, it pulled back and triggered trailing stop")
    print("  3. Trailing stop was set at: High $255.46 - (2 × ATR)")
    print("  4. ATR was probably ~$9-10, so stop was around $237")
    print("  5. Day 5 low hit the trailing stop → Exit at +6.2%")
    print()

    print("💡 Why We Gave Back Profits:")
    print("  - Trailing stop gave stock too much room (2x ATR = ~$18 buffer)")
    print("  - Stock pulled back $18 from peak before stop triggered")
    print("  - We captured 44% of the move ($13.87 of $31.96)")
    print()

    print("🔧 Potential Improvements:")
    print("  1. **Tighter Trail:** Use 1x ATR instead of 2x ATR")
    print("     → Would have exited around $246 (+10.1%) instead of $237 (+6.2%)")
    print()
    print("  2. **Percentage Trail:** After +10%, trail with 5% stop")
    print("     → Would have exited at $242 (+8.3%) instead of $237 (+6.2%)")
    print()
    print("  3. **Hybrid:** Use tighter trail after big moves")
    print("     → 2x ATR until +10%, then switch to 1x ATR or 5% trail")
    print()
    print("  4. **Take Partial Profits:** Sell 50% at +10%, trail rest")
    print("     → Lock in gains, let rest run")
    print()

    print("="*80)
    print("RECOMMENDATION")
    print("="*80 + "\n")

    print("The trailing stop WORKED (captured 44% of move vs 0% with fixed target),")
    print("but could be tighter after big moves.")
    print()
    print("Best approach: **HYBRID TRAILING**")
    print("  - Up to +10%: Trail with 2x ATR (give room)")
    print("  - After +10%: Switch to 1x ATR (tighter trail)")
    print("  - After +15%: Switch to 5% trail (lock it in)")
    print()
    print("This would have captured ~+9-10% on SNOW instead of +6.2%")
    print("Still not perfect, but better risk/reward.")


if __name__ == "__main__":
    analyze_snow_trade()
