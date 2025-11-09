#!/usr/bin/env python3
"""
Quick Volume Test (2025 only) - 4 approaches

Just test 2025 to see if scoring system works.
Much faster than 7-year test.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

from backtest.daily_momentum_smart_exits import SmartExitBacktester
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

start = datetime(2025, 1, 1)
end = datetime(2025, 10, 31)

print("\n" + "="*80)
print("QUICK TEST: 2025 YTD - 4 Approaches")
print("="*80 + "\n")

# Test 1: No filter
print("1️⃣  No Filter (0.0x)...")
print("   📥 Creating backtester...")
bt1 = SmartExitBacktester(api_key, secret_key, starting_capital=100000)
bt1.scanner.min_volume_ratio = 0.0
print("   🏃 Running backtest (this may take 2-3 minutes)...")
r1 = bt1.run(start, end)
print(f"   ✅ DONE: {r1.total_return_percent:+.2f}% ({r1.total_trades} trades)\n")

# Test 2: Soft filter
print("2️⃣  Soft Filter (0.5x)...")
print("   📥 Creating backtester...")
bt2 = SmartExitBacktester(api_key, secret_key, starting_capital=100000)
bt2.scanner.min_volume_ratio = 0.5
print("   🏃 Running backtest...")
r2 = bt2.run(start, end)
print(f"   ✅ DONE: {r2.total_return_percent:+.2f}% ({r2.total_trades} trades)\n")

# Test 3: Current
print("3️⃣  Current Filter (1.2x)...")
print("   📥 Creating backtester...")
bt3 = SmartExitBacktester(api_key, secret_key, starting_capital=100000)
bt3.scanner.min_volume_ratio = 1.2
print("   🏃 Running backtest...")
r3 = bt3.run(start, end)
print(f"   ✅ DONE: {r3.total_return_percent:+.2f}% ({r3.total_trades} trades)\n")

# Test 4: Scoring
print("4️⃣  Scoring System...")
print("   📥 Loading scoring scanner...")
from scanner.daily_breakout_scanner_scoring import DailyBreakoutScannerScoring
print("   📥 Creating backtester...")
bt4 = SmartExitBacktester(api_key, secret_key, starting_capital=100000)
bt4.scanner = DailyBreakoutScannerScoring(api_key, secret_key)
print("   🏃 Running backtest (may be slower)...")
r4 = bt4.run(start, end)
print(f"   ✅ DONE: {r4.total_return_percent:+.2f}% ({r4.total_trades} trades)\n")

print("="*80)
print("RESULTS")
print("="*80)
print(f"{'Approach':<25} {'Return':<12} {'Trades':<10}")
print("-"*80)
print(f"{'No Filter (0.0x)':<25} {r1.total_return_percent:>+10.2f}%  {r1.total_trades:>8}")
print(f"{'Soft Filter (0.5x)':<25} {r2.total_return_percent:>+10.2f}%  {r2.total_trades:>8}")
print(f"{'Current (1.2x)':<25} {r3.total_return_percent:>+10.2f}%  {r3.total_trades:>8}")
print(f"{'🎯 Scoring System':<25} {r4.total_return_percent:>+10.2f}%  {r4.total_trades:>8}")
print("="*80 + "\n")

results = [
    ('No Filter', r1.total_return_percent),
    ('Soft Filter', r2.total_return_percent),
    ('Current', r3.total_return_percent),
    ('Scoring', r4.total_return_percent)
]

best = max(results, key=lambda x: x[1])
print(f"🏆 Winner: {best[0]} ({best[1]:+.2f}%)\n")
