#!/usr/bin/env python3
"""
Test Scaled Exits vs Smart Exits - 2025 YTD

Compares two exit strategies on 2025 data with 1.2x volume filter:

1. SMART EXITS (current):
   - All-or-nothing exits
   - Trailing stops, MA breaks, etc.

2. SCALED EXITS (new):
   - Take 25% profit at +8%
   - Take 25% profit at +15%
   - Take 25% profit at +25%
   - Trail final 25%

Goal: See if scaled exits improve risk-adjusted returns
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

from backtest.daily_momentum_smart_exits import SmartExitBacktester
from backtest.daily_momentum_scaled_exits import ScaledExitBacktester
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

load_dotenv()

api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

start = datetime(2025, 1, 1)
end = datetime(2025, 10, 31)

print("\n" + "="*80)
print("EXIT STRATEGY COMPARISON - 2025 YTD")
print("="*80)
print(f"\nPeriod: {start.date()} to {end.date()}")
print(f"Volume Filter: 1.2x (best performer)")
print(f"Capital: $100,000")
print("="*80 + "\n")

# Test 1: Current Smart Exits
print("🔵 TEST 1: SMART EXITS (All-or-Nothing)")
print("-" * 80)
print("Strategy: Exit full position on trailing stop, MA break, or time stop")
print()

smart_bt = SmartExitBacktester(api_key, secret_key, starting_capital=100000)
smart_results = smart_bt.run(start, end)

print("\n💾 Note: Data is being cached for fast iteration on scaled exits test...")

print("\n" + "="*80)
print("SMART EXITS RESULTS")
print("="*80)
print(f"Return:        {smart_results.total_return_percent:+.2f}%")
print(f"Trades:        {smart_results.total_trades}")
print(f"Win Rate:      {smart_results.win_rate:.1f}%")
print(f"Profit Factor: {smart_results.profit_factor:.2f}x")
print(f"Avg Win:       ${smart_results.avg_win:+,.0f}")
print(f"Avg Loss:      ${smart_results.avg_loss:+,.0f}")
print(f"Max Drawdown:  {smart_results.max_drawdown_percent:.1f}%")
print("="*80)

# Test 2: New Scaled Exits
print("\n\n🟢 TEST 2: SCALED EXITS (Take Profits + Trail)")
print("-" * 80)
print("Strategy: Scale out 25% at +8%, +15%, +25%, trail final 25%")
print()

scaled_bt = ScaledExitBacktester(api_key, secret_key, starting_capital=100000, use_cache=True)
scaled_results = scaled_bt.run(start, end)

print("\n" + "="*80)
print("SCALED EXITS RESULTS")
print("="*80)
print(f"Return:        {scaled_results.total_return_percent:+.2f}%")
print(f"Trades:        {scaled_results.total_trades}")
print(f"Win Rate:      {scaled_results.win_rate:.1f}%")
print(f"Profit Factor: {scaled_results.profit_factor:.2f}x")
print(f"Avg Win:       ${scaled_results.avg_win:+,.0f}")
print(f"Avg Loss:      ${scaled_results.avg_loss:+,.0f}")
print(f"Max Drawdown:  {scaled_results.max_drawdown_percent:.1f}%")
print("="*80)

# Comparison
print("\n\n" + "="*80)
print("📊 COMPARISON")
print("="*80)

return_diff = scaled_results.total_return_percent - smart_results.total_return_percent
pf_diff = scaled_results.profit_factor - smart_results.profit_factor
dd_diff = smart_results.max_drawdown_percent - scaled_results.max_drawdown_percent

print(f"\nReturn Difference:        {return_diff:+.2f}% ({scaled_results.total_return_percent:.2f}% vs {smart_results.total_return_percent:.2f}%)")
print(f"Profit Factor Difference: {pf_diff:+.2f}x ({scaled_results.profit_factor:.2f}x vs {smart_results.profit_factor:.2f}x)")
print(f"Drawdown Improvement:     {dd_diff:+.1f}% ({scaled_results.max_drawdown_percent:.1f}% vs {smart_results.max_drawdown_percent:.1f}%)")

if return_diff > 0:
    print(f"\n🏆 WINNER: SCALED EXITS by {return_diff:.2f}%")
elif return_diff < 0:
    print(f"\n🏆 WINNER: SMART EXITS by {abs(return_diff):.2f}%")
else:
    print(f"\n🤝 TIE: Both strategies returned {smart_results.total_return_percent:.2f}%")

print("\n💡 KEY INSIGHTS:")
if scaled_results.avg_loss < smart_results.avg_loss:
    reduction = ((smart_results.avg_loss - scaled_results.avg_loss) / smart_results.avg_loss) * 100
    print(f"   ✅ Scaled exits reduced avg loss by {reduction:.1f}% (${smart_results.avg_loss:,.0f} → ${scaled_results.avg_loss:,.0f})")

if scaled_results.max_drawdown_percent < smart_results.max_drawdown_percent:
    print(f"   ✅ Scaled exits improved max drawdown by {dd_diff:.1f}%")

if scaled_results.profit_factor > smart_results.profit_factor:
    print(f"   ✅ Scaled exits improved profit factor by {pf_diff:.2f}x")

print("\n💭 INTERPRETATION:")
if return_diff > 2:
    print("   Scaled exits significantly improved returns - consider adopting!")
elif return_diff > 0:
    print("   Scaled exits marginally better - consider risk-adjusted benefits")
elif return_diff > -2:
    print("   Similar performance - consider psychological benefits of taking profits")
else:
    print("   Smart exits performed better - 'let winners run' approach works better")

print("\n" + "="*80 + "\n")
