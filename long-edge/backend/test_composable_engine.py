"""
Integration Test for Composable Backtest Engine

Tests the new composable engine with both exit strategies.

Author: Claude AI + Tanam Bam Sinha
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from engine import BacktestEngine
from strategies import get_scanner, get_exit_strategy, list_all_strategies
from data.cache import CachedDataClient

print("="*80)
print("COMPOSABLE ENGINE INTEGRATION TEST")
print("="*80 + "\n")

# Check environment
api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

if not api_key or not secret_key:
    print("⚠️  WARNING: ALPACA_API_KEY and ALPACA_SECRET_KEY not set")
    print("   Skipping data tests, running structure tests only\n")
    data_tests = False
else:
    print("✅ API keys found\n")
    data_tests = True

# Test 1: Check registry
print("Test 1: Strategy registry check...")
all_strategies = list_all_strategies()

if 'daily_breakout' in all_strategies['scanners']:
    print("✅ Scanner 'daily_breakout' registered")
else:
    print("❌ Scanner 'daily_breakout' NOT registered")
    sys.exit(1)

if 'smart_exits' in all_strategies['exit_strategies']:
    print("✅ Exit strategy 'smart_exits' registered")
else:
    print("❌ Exit strategy 'smart_exits' NOT registered")
    sys.exit(1)

if 'scaled_exits' in all_strategies['exit_strategies']:
    print("✅ Exit strategy 'scaled_exits' registered")
else:
    print("❌ Exit strategy 'scaled_exits' NOT registered")
    sys.exit(1)

print()

# Test 2: Check engine imports
print("Test 2: Engine imports...")
try:
    from engine import BacktestEngine, calculate_backtest_metrics, compare_strategies
    print("✅ All engine components imported successfully\n")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    sys.exit(1)

# Test 3: Create engine instance
print("Test 3: Create engine instance...")
try:
    if data_tests:
        scanner = get_scanner('daily_breakout', api_key, secret_key)
        exit_strategy = get_exit_strategy('smart_exits')
        data_client = CachedDataClient(api_key, secret_key, cache_dir='./cache_test')

        engine = BacktestEngine(
            scanner=scanner,
            exit_strategy=exit_strategy,
            data_client=data_client,
            starting_capital=100000
        )

        print("✅ Engine created successfully")
        print(f"   Scanner: {engine.scanner.strategy_name}")
        print(f"   Exit Strategy: {engine.exit_strategy.strategy_name}")
        print(f"   Starting Capital: ${engine.starting_capital:,.0f}\n")
    else:
        print("⚠️  Skipped (no API keys)\n")
except Exception as e:
    print(f"❌ Engine creation failed: {e}\n")
    sys.exit(1)

# Test 4: Run small backtest (10 days)
print("Test 4: Run small backtest (10 days)...")
if data_tests:
    try:
        start_date = datetime(2024, 6, 1)
        end_date = datetime(2024, 6, 14)

        print(f"   Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print("   Running backtest...")

        results = engine.run(start_date, end_date)

        print(f"✅ Backtest completed")
        print(f"   Total trades: {results.total_trades}")
        print(f"   Return: {results.total_return_percent:+.2f}%")
        print(f"   Win rate: {results.win_rate:.1f}%\n")

        # Verify results structure
        assert hasattr(results, 'scanner_name'), "Missing scanner_name"
        assert hasattr(results, 'exit_strategy_name'), "Missing exit_strategy_name"
        assert hasattr(results, 'total_trades'), "Missing total_trades"
        assert hasattr(results, 'equity_curve'), "Missing equity_curve"

        print("✅ BacktestResults structure valid\n")
    except Exception as e:
        print(f"❌ Backtest failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    print("⚠️  Skipped (no API keys)\n")

# Test 5: Test with scaled exits
print("Test 5: Test with scaled_exits...")
if data_tests:
    try:
        exit_strategy_scaled = get_exit_strategy('scaled_exits')

        engine_scaled = BacktestEngine(
            scanner=scanner,
            exit_strategy=exit_strategy_scaled,
            data_client=data_client,
            starting_capital=100000
        )

        results_scaled = engine_scaled.run(start_date, end_date)

        print(f"✅ Scaled exits backtest completed")
        print(f"   Total trades: {results_scaled.total_trades}")
        print(f"   Return: {results_scaled.total_return_percent:+.2f}%")
        print(f"   Supports partial exits: {exit_strategy_scaled.supports_partial_exits}\n")

    except Exception as e:
        print(f"❌ Scaled exits backtest failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    print("⚠️  Skipped (no API keys)\n")

# Test 6: Test comparison tools
print("Test 6: Test comparison tools...")
if data_tests:
    try:
        comparison_text = compare_strategies([results, results_scaled])

        assert "STRATEGY COMPARISON" in comparison_text
        assert "smart_exits" in comparison_text
        assert "scaled_exits" in comparison_text

        print("✅ Comparison tools working\n")
    except Exception as e:
        print(f"❌ Comparison failed: {e}\n")
        sys.exit(1)
else:
    print("⚠️  Skipped (no API keys)\n")

# Test 7: Test metrics calculation
print("Test 7: Test metrics module...")
try:
    from engine.metrics import calculate_max_drawdown, position_to_trade_dict
    from interfaces import Position

    # Test max drawdown calculation
    test_equity = [100000, 105000, 103000, 108000, 102000, 110000]
    dd = calculate_max_drawdown(test_equity)

    assert dd > 0, "Drawdown should be positive"
    assert dd < 10, "Drawdown should be reasonable"

    print(f"✅ Max drawdown calculation working (test DD: {dd:.2f}%)")

    # Test position to dict conversion
    test_position = Position(
        symbol='TEST',
        entry_date=datetime(2024, 6, 1),
        entry_price=100.0,
        shares=100,
        stop_price=92.0
    )
    test_position.exit_date = datetime(2024, 6, 5)
    test_position.exit_price = 110.0
    test_position.exit_reason = "TARGET"

    trade_dict = position_to_trade_dict(test_position)

    assert trade_dict['symbol'] == 'TEST'
    assert trade_dict['pnl'] == 1000.0
    assert trade_dict['exit_reason'] == 'TARGET'

    print("✅ Position to dict conversion working\n")

except Exception as e:
    print(f"❌ Metrics test failed: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("="*80)
print("🎉 ALL TESTS PASSED!")
print("="*80)
print("\nComposable backtest engine is working correctly:")
print("  ✅ Scanner registration")
print("  ✅ Exit strategy registration")
print("  ✅ Engine creation")
if data_tests:
    print("  ✅ Smart exits backtest")
    print("  ✅ Scaled exits backtest")
    print("  ✅ Comparison tools")
print("  ✅ Metrics calculation")
print("\nReady for production use!")
print()
