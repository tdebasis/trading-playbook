#!/bin/bash
#
# Check if Alpaca historical data subscription is active
#
# Run this every few minutes until you see "✓ READY TO BACKTEST"
#

echo "Checking Alpaca data subscription status..."
echo ""

python3 << 'EOF'
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv
import os

load_dotenv()

client = StockHistoricalDataClient(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY'))

end = datetime.now() - timedelta(days=1)
start = end - timedelta(days=7)

request = StockBarsRequest(
    symbol_or_symbols=['AAPL', 'TSLA', 'NVDA'],
    timeframe=TimeFrame.Day,
    start=start,
    end=end
)

try:
    bars = client.get_stock_bars(request)

    symbols_with_data = [s for s in ['AAPL', 'TSLA', 'NVDA'] if s in bars and len(bars[s]) > 0]

    if len(symbols_with_data) >= 2:
        print("✅ DATA SUBSCRIPTION ACTIVE!")
        print("")
        print("Sample data available:")
        for symbol in symbols_with_data[:2]:
            latest = list(bars[symbol])[-1]
            print(f"  {symbol}: {latest.timestamp.date()} - ${latest.close:.2f}")
        print("")
        print("=" * 60)
        print("✓ READY TO BACKTEST!")
        print("=" * 60)
        print("")
        print("Run this command to start backtesting:")
        print("  python3 backtest.py --start 2025-09-01 --end 2025-11-01 -y")
        print("")
    else:
        print("⏳ Subscription still activating...")
        print("")
        print("Wait a few more minutes and run this again:")
        print("  ./check_data_access.sh")
        print("")

except Exception as e:
    print(f"⏳ Not ready yet: {e}")
    print("")
    print("Wait 5 minutes and try again:")
    print("  ./check_data_access.sh")
    print("")
EOF
