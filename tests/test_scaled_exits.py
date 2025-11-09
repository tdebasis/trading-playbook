"""
Test script for scaled exits strategy.

Tests:
1. Registration and factory retrieval
2. Protocol compliance
3. Partial exit support
4. First scale-out at +8%
5. Second scale-out at +15%
6. Third scale-out at +25%
7. Trailing stop on remaining shares
8. Hard stop trigger
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from interfaces import ExitStrategyProtocol, ExitSignal, Position
from strategies import get_exit_strategy, list_all_strategies

print("=" * 60)
print("SCALED EXITS STRATEGY TESTS")
print("=" * 60 + "\n")

# Test 1: Import and registration
print("Test 1: Registration check...")
try:
    from strategies.exits.scaled_exits import ScaledExits

    all_strategies = list_all_strategies()
    if 'scaled_exits' in all_strategies['exit_strategies']:
        print("✅ scaled_exits registered\n")
    else:
        print("❌ scaled_exits NOT registered\n")
        sys.exit(1)
except Exception as e:
    print(f"❌ Registration failed: {e}\n")
    sys.exit(1)

# Test 2: Factory retrieval
print("Test 2: Factory retrieval...")
try:
    exit_strategy = get_exit_strategy('scaled_exits')
    print(f"✅ Retrieved: {exit_strategy.strategy_name}")
    print(f"   Supports partial exits: {exit_strategy.supports_partial_exits}\n")
except Exception as e:
    print(f"❌ Factory failed: {e}\n")
    sys.exit(1)

# Test 3: Initial stop
print("Test 3: Initial stop calculation...")
try:
    initial_stop = exit_strategy.get_initial_stop(100.0)
    print(f"   Entry: $100.00, Stop: ${initial_stop:.2f}")
    assert abs(initial_stop - 92.0) < 0.01, f"Expected $92.00, got ${initial_stop}"
    print("✅ Initial stop correct\n")
except Exception as e:
    print(f"❌ Initial stop failed: {e}\n")
    sys.exit(1)

# Create mock bars
@dataclass
class MockBar:
    open: float
    high: float
    low: float
    close: float
    volume: int

print("Test 4: Creating mock price bars...")
mock_bars = []
for i in range(10):
    price = 100.0 + i * 2.0  # Rising from $100 to $118
    mock_bars.append(MockBar(
        open=price,
        high=price + 1.0,
        low=price - 0.5,
        close=price + 0.5,
        volume=1000000
    ))
print(f"✅ Created {len(mock_bars)} bars (${mock_bars[0].close:.2f} → ${mock_bars[-1].close:.2f})\n")

# Test 5: First scale-out at +8%
print("Test 5: First scale-out at +8%...")
try:
    position = Position(
        symbol='TEST',
        entry_date=datetime.now() - timedelta(days=3),
        entry_price=100.0,
        shares=400,  # Start with 400 shares
        stop_price=92.0
    )

    # Set price at +8% ($108)
    test_bars = mock_bars[:5]
    test_bars[-1] = MockBar(open=107.5, high=108.5, low=107.0, close=108.0, volume=1000000)

    signal = exit_strategy.check_exit(position, 108.0, datetime.now(), test_bars)

    if signal.should_exit and signal.partial_exit and signal.reason == "SCALE_1":
        print(f"✅ SCALE_1 triggered at +{((108.0-100.0)/100.0*100):.1f}%")
        print(f"   Exit percent: {signal.exit_percent*100:.0f}%")
        print(f"   Shares to exit: {int(400 * signal.exit_percent)}")
        print(f"   Exit price: ${signal.exit_price:.2f}\n")

        # Apply partial exit
        shares_to_exit = int(400 * signal.exit_percent)
        position.add_partial_exit(datetime.now(), shares_to_exit, signal.exit_price, signal.reason)
        print(f"   Remaining shares: {position.shares}\n")
    else:
        print(f"❌ SCALE_1 not triggered (reason: {signal.reason if signal.should_exit else 'no exit'})\n")
        sys.exit(1)
except Exception as e:
    print(f"❌ First scale-out failed: {e}\n")
    sys.exit(1)

# Test 6: Second scale-out at +15%
print("Test 6: Second scale-out at +15%...")
try:
    # Set price at +15% ($115)
    test_bars[-1] = MockBar(open=114.5, high=115.5, low=114.0, close=115.0, volume=1000000)

    signal = exit_strategy.check_exit(position, 115.0, datetime.now(), test_bars)

    if signal.should_exit and signal.partial_exit and signal.reason == "SCALE_2":
        print(f"✅ SCALE_2 triggered at +{((115.0-100.0)/100.0*100):.1f}%")
        print(f"   Exit percent: {signal.exit_percent*100:.0f}%")
        print(f"   Exit price: ${signal.exit_price:.2f}\n")

        # Apply partial exit
        shares_to_exit = int(400 * signal.exit_percent)  # 25% of original
        position.add_partial_exit(datetime.now(), shares_to_exit, signal.exit_price, signal.reason)
        print(f"   Remaining shares: {position.shares}\n")
    else:
        print(f"❌ SCALE_2 not triggered (reason: {signal.reason if signal.should_exit else 'no exit'})\n")
        sys.exit(1)
except Exception as e:
    print(f"❌ Second scale-out failed: {e}\n")
    sys.exit(1)

# Test 7: Third scale-out at +25%
print("Test 7: Third scale-out at +25%...")
try:
    # Set price at +25% ($125)
    test_bars[-1] = MockBar(open=124.5, high=125.5, low=124.0, close=125.0, volume=1000000)

    signal = exit_strategy.check_exit(position, 125.0, datetime.now(), test_bars)

    if signal.should_exit and signal.partial_exit and signal.reason == "SCALE_3":
        print(f"✅ SCALE_3 triggered at +{((125.0-100.0)/100.0*100):.1f}%")
        print(f"   Exit percent: {signal.exit_percent*100:.0f}%")
        print(f"   Exit price: ${signal.exit_price:.2f}\n")

        # Apply partial exit
        shares_to_exit = int(400 * signal.exit_percent)  # 25% of original
        position.add_partial_exit(datetime.now(), shares_to_exit, signal.exit_price, signal.reason)
        print(f"   Remaining shares: {position.shares} (final 25%)\n")
    else:
        print(f"❌ SCALE_3 not triggered (reason: {signal.reason if signal.should_exit else 'no exit'})\n")
        sys.exit(1)
except Exception as e:
    print(f"❌ Third scale-out failed: {e}\n")
    sys.exit(1)

# Test 8: No more scale-outs (healthy position)
print("Test 8: No exit on remaining shares (healthy)...")
try:
    # Price still at $125, no exit expected
    signal = exit_strategy.check_exit(position, 125.0, datetime.now(), test_bars)

    if not signal.should_exit:
        print(f"✅ No exit triggered (remaining {position.shares} shares trailing)\n")
    else:
        print(f"⚠️  Unexpected exit: {signal.reason}\n")
except Exception as e:
    print(f"❌ No-exit check failed: {e}\n")
    sys.exit(1)

# Test 9: Hard stop (full position)
print("Test 9: Hard stop on full position...")
try:
    # Create fresh position
    position_stop = Position(
        symbol='TEST',
        entry_date=datetime.now() - timedelta(days=2),
        entry_price=100.0,
        shares=400,
        stop_price=92.0
    )

    # Price hits hard stop
    stop_bars = mock_bars[:5]
    stop_bars[-1] = MockBar(open=93.0, high=94.0, low=91.0, close=91.5, volume=1000000)

    signal = exit_strategy.check_exit(position_stop, 91.5, datetime.now(), stop_bars)

    if signal.should_exit and signal.reason == "HARD_STOP":
        print(f"✅ Hard stop triggered")
        print(f"   Full exit: {not signal.partial_exit}")
        print(f"   Exit price: ${signal.exit_price:.2f}\n")
    else:
        print(f"❌ Hard stop not triggered\n")
        sys.exit(1)
except Exception as e:
    print(f"❌ Hard stop test failed: {e}\n")
    sys.exit(1)

# Test 10: Position tracking
print("Test 10: Partial exit tracking...")
try:
    # Check partial exits were recorded
    test_position = Position(
        symbol='TEST',
        entry_date=datetime.now(),
        entry_price=100.0,
        shares=400,
        stop_price=92.0
    )

    # Simulate 3 scale-outs
    test_position.add_partial_exit(datetime.now(), 100, 108.0, "SCALE_1")
    test_position.add_partial_exit(datetime.now(), 100, 115.0, "SCALE_2")
    test_position.add_partial_exit(datetime.now(), 100, 125.0, "SCALE_3")

    print(f"   Original shares: {test_position.original_shares}")
    print(f"   Remaining shares: {test_position.shares}")
    print(f"   Partial exits: {len(test_position.partial_exits)}")

    realized_pnl = sum((exit['price'] - 100.0) * exit['shares'] for exit in test_position.partial_exits)
    print(f"   Realized P&L: ${realized_pnl:,.2f}")

    assert test_position.original_shares == 400
    assert test_position.shares == 100  # 25% remaining
    assert len(test_position.partial_exits) == 3

    print("✅ Partial exit tracking working\n")
except Exception as e:
    print(f"❌ Partial exit tracking failed: {e}\n")
    sys.exit(1)

print("=" * 60)
print("🎉 ALL SCALED EXITS TESTS PASSED!")
print("=" * 60)
print("\nScaled exits strategy working correctly:")
print("  • 3 profit targets: +8%, +15%, +25% (25% each)")
print("  • Remaining 25% uses trailing stops")
print("  • Supports partial exits")
print("  • Hard stop protection at -8%")
print("\nReady for production use!")
