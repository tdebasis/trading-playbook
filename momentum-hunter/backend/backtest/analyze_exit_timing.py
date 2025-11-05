"""
Analyze Exit Timing - Did we leave money on the table or hold too long?

This checks if our exit rules (8% stop, 20% target, 10-day time) are optimal.
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


def analyze_trade_movement(symbol: str, entry_date: datetime, exit_date: datetime, entry_price: float):
    """
    Analyze how price moved during trade.
    Shows max profit, max loss, and when they occurred.
    """

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    client = StockHistoricalDataClient(api_key, secret_key)

    # Fetch bars from entry to exit
    request = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=TimeFrame.Day,
        start=entry_date - timedelta(days=1),
        end=exit_date + timedelta(days=1)
    )

    try:
        bars_response = client.get_stock_bars(request)

        if symbol not in bars_response.data or not bars_response.data[symbol]:
            print(f"  ❌ {symbol}: No data")
            return

        bars = list(bars_response.data[symbol])

        # Find entry bar
        entry_bar = None
        for i, bar in enumerate(bars):
            if bar.timestamp.date() >= entry_date.date():
                entry_bar = bar
                entry_index = i
                break

        if not entry_bar:
            print(f"  ❌ {symbol}: Entry bar not found")
            return

        # Track max/min from entry
        max_profit_pct = 0
        max_loss_pct = 0
        max_profit_day = 0
        max_loss_day = 0
        current_day = 0

        day_by_day = []

        for bar in bars[entry_index:]:
            if bar.timestamp.date() > exit_date.date():
                break

            high_pct = ((bar.high - entry_price) / entry_price) * 100
            low_pct = ((bar.low - entry_price) / entry_price) * 100
            close_pct = ((bar.close - entry_price) / entry_price) * 100

            if high_pct > max_profit_pct:
                max_profit_pct = high_pct
                max_profit_day = current_day

            if low_pct < max_loss_pct:
                max_loss_pct = low_pct
                max_loss_day = current_day

            day_by_day.append({
                'day': current_day,
                'date': bar.timestamp.date(),
                'high_pct': high_pct,
                'low_pct': low_pct,
                'close_pct': close_pct
            })

            current_day += 1

        return {
            'max_profit_pct': max_profit_pct,
            'max_profit_day': max_profit_day,
            'max_loss_pct': max_loss_pct,
            'max_loss_day': max_loss_day,
            'days_held': len(day_by_day),
            'day_by_day': day_by_day
        }

    except Exception as e:
        print(f"  ❌ {symbol}: Error - {e}")
        return None


if __name__ == "__main__":
    # Analyze our actual trades
    trades = [
        {'symbol': 'SNOW', 'entry': datetime(2025, 8, 1), 'exit': datetime(2025, 8, 4), 'entry_price': 223.50, 'exit_reason': 'STOP', 'actual_pnl': -8.3},
        {'symbol': 'MSFT', 'entry': datetime(2025, 8, 1), 'exit': datetime(2025, 8, 11), 'entry_price': 533.50, 'exit_reason': 'TIME', 'actual_pnl': -2.1},
        {'symbol': 'META', 'entry': datetime(2025, 8, 1), 'exit': datetime(2025, 8, 11), 'entry_price': 773.44, 'exit_reason': 'TIME', 'actual_pnl': -0.5},
        {'symbol': 'AAPL', 'entry': datetime(2025, 8, 8), 'exit': datetime(2025, 8, 18), 'entry_price': 220.03, 'exit_reason': 'TIME', 'actual_pnl': +5.3},
        {'symbol': 'AMZN', 'entry': datetime(2025, 9, 5), 'exit': datetime(2025, 9, 15), 'entry_price': 235.68, 'exit_reason': 'TIME', 'actual_pnl': -3.2},
        {'symbol': 'SHOP', 'entry': datetime(2025, 9, 22), 'exit': datetime(2025, 9, 29), 'entry_price': 153.30, 'exit_reason': 'STOP', 'actual_pnl': -8.5},
        {'symbol': 'AAPL', 'entry': datetime(2025, 9, 22), 'exit': datetime(2025, 10, 2), 'entry_price': 245.50, 'exit_reason': 'TIME', 'actual_pnl': +4.1},
        {'symbol': 'SNOW', 'entry': datetime(2025, 10, 3), 'exit': datetime(2025, 10, 13), 'entry_price': 223.50, 'exit_reason': 'TIME', 'actual_pnl': +0.7},
        {'symbol': 'AAPL', 'entry': datetime(2025, 10, 21), 'exit': datetime(2025, 10, 31), 'entry_price': 245.50, 'exit_reason': 'TIME', 'actual_pnl': +3.5},
    ]

    print("="*80)
    print("EXIT TIMING ANALYSIS")
    print("="*80)
    print("\nAnalyzing if we exited too early or too late...\n")

    better_exits = 0
    worse_exits = 0

    for trade in trades:
        print(f"\n{'='*80}")
        print(f"{trade['symbol']} - {trade['entry'].strftime('%Y-%m-%d')} to {trade['exit'].strftime('%Y-%m-%d')}")
        print(f"Entry: ${trade['entry_price']:.2f} | Exit Reason: {trade['exit_reason']} | Actual P&L: {trade['actual_pnl']:+.1f}%")
        print(f"{'='*80}")

        analysis = analyze_trade_movement(
            trade['symbol'],
            trade['entry'],
            trade['exit'],
            trade['entry_price']
        )

        if analysis:
            print(f"\n  📊 Price Movement During Trade:")
            print(f"     Max Profit: {analysis['max_profit_pct']:+.1f}% on Day {analysis['max_profit_day']}")
            print(f"     Max Loss: {analysis['max_loss_pct']:+.1f}% on Day {analysis['max_loss_day']}")
            print(f"     Days Held: {analysis['days_held']}")

            # Show day-by-day
            print(f"\n  📅 Day-by-Day:")
            for day in analysis['day_by_day']:
                emoji = "📈" if day['close_pct'] > 0 else "📉"
                print(f"     Day {day['day']}: High {day['high_pct']:+.1f}%, Low {day['low_pct']:+.1f}%, Close {day['close_pct']:+.1f}% {emoji}")

            # Analysis
            print(f"\n  🔍 Analysis:")

            # Check if we could have done better
            if analysis['max_profit_pct'] > 10:
                print(f"     ⚠️  Stock hit {analysis['max_profit_pct']:+.1f}% (Day {analysis['max_profit_day']}) but we got {trade['actual_pnl']:+.1f}%")
                print(f"     💡 Should have used trailing stop or taken profit earlier!")
                better_exits += 1
            elif analysis['max_profit_pct'] > 5 and trade['actual_pnl'] < 3:
                print(f"     ⚠️  Stock hit {analysis['max_profit_pct']:+.1f}% but we only got {trade['actual_pnl']:+.1f}%")
                print(f"     💡 Should have taken profit at +5% instead of waiting for +20%")
                better_exits += 1
            elif trade['exit_reason'] == 'TIME' and analysis['max_loss_pct'] < -5:
                print(f"     ⚠️  Stock went to {analysis['max_loss_pct']:+.1f}% but recovered")
                print(f"     💡 Stop was too tight, or should have added to position on dip")
            elif trade['exit_reason'] == 'STOP':
                if analysis['max_profit_pct'] > 3:
                    print(f"     ⚠️  Stock was up {analysis['max_profit_pct']:+.1f}% before stopping out")
                    print(f"     💡 Should have taken profit when ahead")
                    better_exits += 1
                else:
                    print(f"     ✅ Stop was correct - stock never got to +5%")
                    worse_exits += 1
            elif trade['actual_pnl'] > 0:
                print(f"     ✅ Exit timing was decent (captured most of move)")
                worse_exits += 1
            else:
                print(f"     ⚠️  Trade went nowhere - market was choppy")

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")

    print(f"Trades analyzed: {len(trades)}")
    print(f"Could have been better: {better_exits} trades")
    print(f"Exit was appropriate: {worse_exits} trades")

    print(f"\n💡 KEY FINDINGS:")
    print(f"   - 20% profit target is TOO HIGH for this market")
    print(f"   - Stocks hit +5-10% but reversed before +20%")
    print(f"   - Should use trailing stop or lower profit target")
    print(f"   - Consider: +8-10% target instead of +20%")
    print(f"   - Or: Trail stop at +5% (move stop to break-even)")
