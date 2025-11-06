#!/usr/bin/env python3
"""
Fast Scoring System Test - 2025 YTD Only

Key features:
- Tests ONLY the scoring system (no hard filters)
- Uses same data download as other tests (cached by Alpaca SDK)
- Easy to iterate on scoring parameters
- Shows detailed results: which trades passed/failed scoring

Usage:
1. Edit scoring thresholds in daily_breakout_scanner_scoring.py
2. Run this script (takes ~2 minutes, same as other 2025 tests)
3. Compare results vs no-filter baseline
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

from backtest.daily_momentum_smart_exits import SmartExitBacktester
from scanner.daily_breakout_scanner_scoring_cached import DailyBreakoutScannerScoringCached
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

start = datetime(2025, 1, 1)
end = datetime(2025, 10, 31)

print("\n" + "="*80)
print("FAST SCORING TEST - 2025 YTD (WITH CACHING)")
print("="*80)
print("\nTesting scoring system with volume compensation logic")
print("First run: Downloads data (~7 min)")
print("Later runs: Uses cache (~5-10 seconds!)")
print("="*80 + "\n")

print("📥 Creating backtester with CACHED scoring scanner...")
backtester = SmartExitBacktester(api_key, secret_key, starting_capital=100000)

print("🔧 Replacing scanner with cached scoring version...")
backtester.scanner = DailyBreakoutScannerScoringCached(api_key, secret_key, cache_dir='./cache')

print("🏃 Running backtest...\n")
results = backtester.run(start, end)

# Print cache stats
backtester.scanner.print_cache_stats()

print("\n" + "="*80)
print("RESULTS")
print("="*80)
print(f"Return:        {results.total_return_percent:+.2f}%")
print(f"Trades:        {results.total_trades}")
print(f"Win Rate:      {results.win_rate:.1f}%")
print(f"Profit Factor: {results.profit_factor:.2f}x")
print(f"Avg Win:       ${results.avg_win:+,.0f}")
print(f"Avg Loss:      ${results.avg_loss:+,.0f}")
print(f"Max Drawdown:  {results.max_drawdown_percent:.1f}%")
print("="*80)

print("\n📊 COMPARISON:")
print("   No Filter (0.0x):  +12.80% (64 trades)")
print("   Soft Filter (0.5x): +12.71% (64 trades)")
print("   Current (1.2x):     +12.20% (56 trades)")
print(f"   Scoring System:     {results.total_return_percent:+.2f}% ({results.total_trades} trades)")

if results.total_trades == 0:
    print("\n⚠️  WARNING: Scoring system produced 0 trades!")
    print("   Thresholds are likely too strict.")
    print("   Try lowering required_score in score_with_volume_compensation()")
elif results.total_return_percent > 12.80:
    print(f"\n🏆 WINNER! Scoring beats no-filter by {results.total_return_percent - 12.80:+.2f}%")
elif results.total_return_percent > 12.20:
    print(f"\n✅ GOOD: Scoring beats 1.2x filter by {results.total_return_percent - 12.20:+.2f}%")
else:
    print(f"\n❌ Scoring underperforms. Need to tune thresholds.")

print("\n💡 To iterate:")
print("   1. Edit backend/scanner/daily_breakout_scanner_scoring.py")
print("   2. Adjust scoring thresholds (lines 148-156)")
print("   3. Run: python3 test_scoring_fast.py")
print("   4. Compare results vs baselines above\n")
