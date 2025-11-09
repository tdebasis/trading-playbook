#!/usr/bin/env python3
"""Quick test of Alpaca data client."""

import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import os

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

load_dotenv()
api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

client = StockHistoricalDataClient(api_key, secret_key)

# Test query
request = StockBarsRequest(
    symbol_or_symbols='SPY',
    timeframe=TimeFrame.Day,
    start=datetime(2024, 4, 1),
    end=datetime(2024, 4, 10)
)

print("Fetching SPY bars...")
bars = client.get_stock_bars(request)

print(f"\nType of bars: {type(bars)}")
print(f"Bars object: {bars}")
print(f"\nDir of bars: {[x for x in dir(bars) if not x.startswith('_')]}")

# Try to access SPY
print(f"\nTrying 'SPY' in bars:")
try:
    result = 'SPY' in bars
    print(f"  Result: {result}")
except Exception as e:
    print(f"  Error: {e}")

# Try dict access
print(f"\nTrying bars['SPY']:")
try:
    spy_bars = bars['SPY']
    print(f"  Got {len(spy_bars)} bars")
    if spy_bars:
        print(f"  First bar: {spy_bars[0]}")
except Exception as e:
    print(f"  Error: {e}")

# Try .get()
print(f"\nTrying bars.get('SPY'):")
try:
    spy_bars = bars.get('SPY')
    print(f"  Result: {spy_bars}")
except Exception as e:
    print(f"  Error: {e}")

# Try .data attribute
print(f"\nTrying bars.data:")
try:
    data = bars.data
    print(f"  Type: {type(data)}")
    print(f"  Data: {data}")
    if hasattr(data, '__getitem__'):
        spy_bars = data['SPY']
        print(f"  Got {len(spy_bars)} SPY bars")
except Exception as e:
    print(f"  Error: {e}")
