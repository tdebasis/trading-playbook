"""Quick check: Did we capture NVDA/PLTR in Q4 2024 (+17.69% quarter)?"""

from datetime import datetime
import sys
from pathlib import Path
import logging

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from backtest.daily_momentum_smart_exits import SmartExitBacktester
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.WARNING)

api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

print("\n" + "="*80)
print("QUICK CHECK: Q4 2024 (+17.69% - Best Quarter)")
print("="*80 + "\n")

backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)
results = backtester.run(datetime(2024, 11, 1), datetime(2025, 1, 31))

print(f"Total return: {results.total_return_percent:+.2f}%")
print(f"Total trades: {results.total_trades}\n")

# Analyze symbols
symbol_pnl = {}
for trade in results.trades:
    symbol = trade['symbol']
    pnl = trade['pnl']

    if symbol not in symbol_pnl:
        symbol_pnl[symbol] = 0
    symbol_pnl[symbol] += pnl

# Sort by P&L
sorted_symbols = sorted(symbol_pnl.items(), key=lambda x: x[1], reverse=True)

print("Symbols traded (sorted by P&L contribution):")
print("-" * 60)

total_pnl = sum(symbol_pnl.values())

for symbol, pnl in sorted_symbols:
    contribution = (pnl / total_pnl * 100) if total_pnl != 0 else 0
    print(f"{symbol:<8} ${pnl:>+10,.0f}  ({contribution:>+6.1f}%)")

print("-" * 60)
print(f"{'TOTAL':<8} ${total_pnl:>+10,.0f}\n")

# Check NVDA/PLTR
print("="*80)
print("NVDA/PLTR CHECK:")
print("="*80 + "\n")

if 'NVDA' in symbol_pnl:
    nvda_contribution = (symbol_pnl['NVDA'] / total_pnl * 100)
    print(f"✅ NVDA traded: ${symbol_pnl['NVDA']:+,.0f} ({nvda_contribution:+.1f}% of returns)")
else:
    print(f"❌ NVDA NOT traded")

if 'PLTR' in symbol_pnl:
    pltr_contribution = (symbol_pnl['PLTR'] / total_pnl * 100)
    print(f"✅ PLTR traded: ${symbol_pnl['PLTR']:+,.0f} ({pltr_contribution:+.1f}% of returns)")
else:
    print(f"❌ PLTR NOT traded")

print("\n" + "="*80 + "\n")
