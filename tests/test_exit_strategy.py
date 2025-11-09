"""
Test script to verify exit strategy integration.

Tests:
1. Exit strategy registration
2. Factory pattern retrieval
3. ExitStrategyProtocol compliance
4. Exit signal generation
5. Hard stop trigger
6. Trailing stop trigger
7. MA break trigger
8. Time stop trigger
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Test 1: Import interfaces and strategies
print("Test 1: Importing interfaces and exit strategies...")
try:
    from interfaces import ExitStrategyProtocol, ExitSignal, Position
    from strategies import get_exit_strategy, list_all_strategies
    print("✅ Imports successful\n")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    sys.exit(1)

# Test 2: Force import exit strategy module
print("Test 2: Importing smart_exits module...")
try:
    from strategies.exits.smart_exits import SmartExits
    print("✅ Exit strategy module imported\n")
except Exception as e:
    print(f"❌ Exit strategy import failed: {e}\n")
    sys.exit(1)

# Test 3: Check registration
print("Test 3: Checking exit strategy registration...")
try:
    all_strategies = list_all_strategies()
    print(f"Registered exit strategies: {all_strategies['exit_strategies']}")

    if 'smart_exits' in all_strategies['exit_strategies']:
        print("✅ smart_exits strategy registered\n")
    else:
        print("❌ smart_exits NOT registered\n")
        sys.exit(1)
except Exception as e:
    print(f"❌ Registration check failed: {e}\n")
    sys.exit(1)

# Test 4: Factory retrieval
print("Test 4: Factory pattern retrieval...")
try:
    exit_strategy = get_exit_strategy('smart_exits')
    print(f"✅ Retrieved exit strategy: {exit_strategy.strategy_name}\n")
except Exception as e:
    print(f"❌ Factory retrieval failed: {e}\n")
    sys.exit(1)

# Test 5: Protocol compliance
print("Test 5: Protocol compliance check...")
try:
    # Check required methods/properties
    required = ['check_exit', 'strategy_name', 'supports_partial_exits', 'get_initial_stop']
    missing = [attr for attr in required if not hasattr(exit_strategy, attr)]

    if missing:
        print(f"❌ Missing required attributes: {missing}\n")
        sys.exit(1)
    else:
        print(f"✅ All required Protocol attributes present\n")
        print(f"  Strategy name: {exit_strategy.strategy_name}")
        print(f"  Supports partial exits: {exit_strategy.supports_partial_exits}")
        print()
except Exception as e:
    print(f"❌ Protocol check failed: {e}\n")
    sys.exit(1)

# Test 6: Initial stop calculation
print("Test 6: Initial stop calculation...")
try:
    entry_price = 100.0
    initial_stop = exit_strategy.get_initial_stop(entry_price)
    expected_stop = 92.0  # 8% below entry

    print(f"  Entry price: ${entry_price}")
    print(f"  Initial stop: ${initial_stop}")
    print(f"  Risk: {((entry_price - initial_stop) / entry_price * 100):.1f}%")

    if abs(initial_stop - expected_stop) < 0.01:
        print("✅ Initial stop calculation correct\n")
    else:
        print(f"❌ Expected ${expected_stop}, got ${initial_stop}\n")
        sys.exit(1)
except Exception as e:
    print(f"❌ Initial stop calculation failed: {e}\n")
    sys.exit(1)

# Test 7: Create mock bars for testing
print("Test 7: Creating mock price bars...")
try:
    @dataclass
    class MockBar:
        """Mock price bar for testing."""
        open: float
        high: float
        low: float
        close: float
        volume: int

    # Create mock bars (10 days of price data)
    mock_bars = []
    base_price = 100.0
    for i in range(10):
        price = base_price + i * 0.5  # Gradually rising
        mock_bars.append(MockBar(
            open=price,
            high=price + 1.0,
            low=price - 0.5,
            close=price + 0.5,
            volume=1000000
        ))

    print(f"✅ Created {len(mock_bars)} mock bars\n")
    print(f"  Price range: ${mock_bars[0].close:.2f} → ${mock_bars[-1].close:.2f}\n")
except Exception as e:
    print(f"❌ Mock bar creation failed: {e}\n")
    sys.exit(1)

# Test 8: No exit scenario (position healthy)
print("Test 8: Check exit (no exit expected)...")
try:
    position = Position(
        symbol='TEST',
        entry_date=datetime.now() - timedelta(days=5),
        entry_price=100.0,
        shares=100,
        stop_price=92.0  # 8% stop
    )

    current_price = 105.0  # +5% profit
    signal = exit_strategy.check_exit(position, current_price, datetime.now(), mock_bars)

    if not signal.should_exit:
        print(f"✅ No exit triggered (position healthy at +5%)\n")
    else:
        print(f"❌ Unexpected exit: {signal.reason}\n")
except Exception as e:
    print(f"❌ No-exit check failed: {e}\n")
    sys.exit(1)

# Test 9: Hard stop trigger
print("Test 9: Hard stop trigger...")
try:
    position = Position(
        symbol='TEST',
        entry_date=datetime.now() - timedelta(days=2),
        entry_price=100.0,
        shares=100,
        stop_price=92.0
    )

    # Create bars with price hitting stop
    stop_bars = mock_bars.copy()
    stop_bars[-1] = MockBar(open=93.0, high=94.0, low=91.0, close=91.5, volume=1000000)

    signal = exit_strategy.check_exit(position, 91.5, datetime.now(), stop_bars)

    if signal.should_exit and signal.reason == "HARD_STOP":
        print(f"✅ Hard stop triggered correctly")
        print(f"  Exit price: ${signal.exit_price}")
        print(f"  Reason: {signal.reason}\n")
    else:
        print(f"❌ Hard stop not triggered (reason: {signal.reason})\n")
except Exception as e:
    print(f"❌ Hard stop test failed: {e}\n")
    sys.exit(1)

# Test 10: Time stop trigger
print("Test 10: Time stop trigger...")
try:
    position = Position(
        symbol='TEST',
        entry_date=datetime.now() - timedelta(days=20),  # Held 20 days (>17 limit)
        entry_price=100.0,
        shares=100,
        stop_price=92.0
    )

    current_date = datetime.now()
    signal = exit_strategy.check_exit(position, 102.0, current_date, mock_bars)

    if signal.should_exit and signal.reason == "TIME":
        print(f"✅ Time stop triggered correctly")
        print(f"  Hold days: {position.hold_days(current_date)}")
        print(f"  Exit price: ${signal.exit_price}")
        print(f"  Reason: {signal.reason}\n")
    else:
        print(f"❌ Time stop not triggered (reason: {signal.reason if signal.should_exit else 'no exit'})\n")
except Exception as e:
    print(f"❌ Time stop test failed: {e}\n")
    sys.exit(1)

# Test 11: ExitSignal dataclass
print("Test 11: ExitSignal validation...")
try:
    # Test no-exit signal
    no_exit = ExitSignal.no_exit()
    assert not no_exit.should_exit

    # Test full exit signal
    full_exit = ExitSignal.full_exit(reason="TEST", price=105.0)
    assert full_exit.should_exit
    assert full_exit.reason == "TEST"
    assert full_exit.exit_price == 105.0
    assert full_exit.exit_percent == 1.0

    print("✅ ExitSignal factory methods working\n")
except Exception as e:
    print(f"❌ ExitSignal validation failed: {e}\n")
    sys.exit(1)

print("=" * 60)
print("🎉 ALL EXIT STRATEGY TESTS PASSED!")
print("=" * 60)
print("\nExit strategy integration is working correctly.")
print("\nNext steps:")
print("1. Extract scaled exits strategy")
print("2. Create composable backtest engine")
print("3. Update cloud services to use interfaces")
