#!/usr/bin/env python3
"""
Quick 3-Month Verification Backtest

Tests the reorganized codebase with a simple 3-month backtest.
Verifies all imports work correctly after flattening long-edge/ to root.

Author: Claude AI + Tanam Bam Sinha
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
import os

print("=" * 80)
print("3-MONTH VERIFICATION BACKTEST")
print("=" * 80)
print("\nTesting reorganized codebase...\n")

# Load credentials
load_dotenv()
api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

if not api_key or not secret_key:
    print("❌ ERROR: Missing Alpaca API credentials in .env file")
    sys.exit(1)

print("✓ Credentials loaded")

# Test imports from reorganized structure
print("\nTesting imports...")

from scanner.long.daily_breakout_moderate import DailyBreakoutScannerModerate
print("✓ Scanner import: scanner.long.daily_breakout_moderate")

from strategies import get_exit_strategy
print("✓ Strategy import: strategies.get_exit_strategy")

from engine.backtest_engine import BacktestEngine
print("✓ Engine import: engine.backtest_engine")

from alpaca.data.historical import StockHistoricalDataClient
print("✓ Alpaca import: StockHistoricalDataClient")

# Setup backtest
print("\nSetting up backtest...")

# Last 3 months
end_date = datetime.now() - timedelta(days=1)  # Yesterday
start_date = end_date - timedelta(days=90)  # ~3 months ago

print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print(f"Scanner: daily_breakout_moderate")
print(f"Exit Strategy: scaled_exits")
print(f"Capital: $100,000")
print(f"Position Size: 6.67% (max 3 positions)")

# Initialize components
data_client = StockHistoricalDataClient(api_key, secret_key)
scanner = DailyBreakoutScannerModerate(api_key, secret_key, universe='default')
exit_strategy = get_exit_strategy('scaled_exits')

# Create backtest engine
engine = BacktestEngine(
    scanner=scanner,
    exit_strategy=exit_strategy,
    data_client=data_client,
    starting_capital=100000,
    max_positions=3,
    position_size_percent=0.0667
)

print("\n" + "=" * 80)
print("RUNNING BACKTEST...")
print("=" * 80 + "\n")

# Run backtest
results = engine.run(start_date, end_date)

# Display results
print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80 + "\n")

print(f"Starting Capital:  ${results.starting_capital:,.2f}")
print(f"Ending Capital:    ${results.ending_capital:,.2f}")
print(f"Total Return:      {results.total_return_percent:,.2f}%")
print(f"Max Drawdown:      {results.max_drawdown_percent:,.2f}%")
print(f"")
print(f"Total Trades:      {results.total_trades}")
print(f"Winning Trades:    {results.winning_trades}")
print(f"Losing Trades:     {results.losing_trades}")
print(f"Win Rate:          {results.win_rate:.1f}%")
print(f"")
print(f"Profit Factor:     {results.profit_factor:.2f}")
print(f"Avg Win:           ${results.avg_win:,.2f}")
print(f"Avg Loss:          ${results.avg_loss:,.2f}")
print(f"Expectancy:        ${results.expectancy:,.2f}")
print(f"Avg Hold Days:     {results.avg_hold_days:.1f}")

print("\n" + "=" * 80)
print("✅ VERIFICATION COMPLETE")
print("=" * 80)
print("\nReorganized codebase is fully functional!")
print("All imports working correctly from new structure:")
print("  - scanner.long.*")
print("  - strategies.*")
print("  - engine.*")
print()
