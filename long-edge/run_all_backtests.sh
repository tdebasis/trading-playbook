#!/bin/bash
#
# Run All Backtests - Strategy Validation Suite
#
# This runs multiple backtest variations to find the best strategy
#

echo "=================================="
echo "MOMENTUM HUNTER - STRATEGY VALIDATION"
echo "=================================="
echo ""

# Check if data is available
echo "Checking data subscription..."
python3 -c "
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

request = StockBarsRequest(symbol_or_symbols=['AAPL'], timeframe=TimeFrame.Day, start=start, end=end)
bars = client.get_stock_bars(request)

if 'AAPL' in bars and len(bars['AAPL']) > 0:
    print('✓ Data access confirmed')
else:
    print('✗ Data not available yet')
    print('Wait a few more minutes and try again')
    exit(1)
" 2>&1

if [ $? -ne 0 ]; then
    echo ""
    echo "Data subscription not active yet."
    echo "Try again in 5-10 minutes."
    exit 1
fi

echo ""
echo "=================================="
echo "Running backtests on last 3 months"
echo "This will take 10-15 minutes"
echo "=================================="
echo ""

# Test 1: Full 3-month backtest with current strategy
echo "📊 Test 1: Momentum + News Strategy (3 months)"
echo "   Testing: Current strategy with catalyst filtering"
echo ""
python3 backtest.py \
    --start 2025-08-01 \
    --end 2025-11-01 \
    --output results_momentum_plus_news_3mo.json \
    -y

echo ""
echo "=================================="
echo "BACKTEST COMPLETE"
echo "=================================="
echo ""

# Show summary
echo "Results saved to: results_momentum_plus_news_3mo.json"
echo ""
echo "To view detailed results:"
echo "  cat results_momentum_plus_news_3mo.json | python3 -m json.tool | less"
echo ""
echo "Key metrics to look for:"
echo "  - Win Rate: >55% is good"
echo "  - Profit Factor: >1.5 is good"
echo "  - Total Return: Should be positive"
echo "  - Max Drawdown: <15% is acceptable"
echo ""
