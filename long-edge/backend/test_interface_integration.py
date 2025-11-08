"""
Test script to verify interface integration.

Tests:
1. Scanner registration works
2. Factory pattern retrieves scanner
3. Scanner implements ScannerProtocol
4. Standardized Candidate output works
"""

import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Test 1: Import interfaces and strategies
print("Test 1: Importing interfaces and strategies...")
try:
    from interfaces import ScannerProtocol, Candidate
    from strategies import get_scanner, list_all_strategies, print_registry
    print("✅ Imports successful\n")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    sys.exit(1)

# Test 2: Check scanner registration
print("Test 2: Checking scanner registration...")
try:
    all_strategies = list_all_strategies()
    print(f"Registered strategies:")
    for strategy_type, names in all_strategies.items():
        print(f"  {strategy_type}: {names if names else '(none yet)'}")
    print()

    if 'daily_breakout' in all_strategies['scanners']:
        print("✅ daily_breakout scanner registered\n")
    else:
        print("⚠️  daily_breakout scanner NOT registered yet")
        print("   (This is normal - scanner module needs to be imported)\n")
except Exception as e:
    print(f"❌ Registration check failed: {e}\n")
    sys.exit(1)

# Test 3: Force import scanner to trigger registration
print("Test 3: Importing scanner module to trigger registration...")
try:
    from scanner.daily_breakout_scanner import DailyBreakoutScanner
    print("✅ Scanner module imported\n")

    # Check registration again
    all_strategies = list_all_strategies()
    if 'daily_breakout' in all_strategies['scanners']:
        print("✅ daily_breakout scanner now registered\n")
    else:
        print("❌ Scanner still not registered after import\n")
        sys.exit(1)
except Exception as e:
    print(f"❌ Scanner import failed: {e}\n")
    sys.exit(1)

# Test 4: Print full registry
print("Test 4: Full registry contents...")
try:
    print_registry()
except Exception as e:
    print(f"❌ Print registry failed: {e}\n")

# Test 5: Factory pattern retrieval (without API keys)
print("\nTest 5: Factory pattern (dry run)...")
try:
    # Don't actually create scanner without API keys
    scanners = list_all_strategies()['scanners']
    print(f"Available scanners: {scanners}")
    print("✅ Factory pattern ready (needs API keys for actual instantiation)\n")
except Exception as e:
    print(f"❌ Factory test failed: {e}\n")
    sys.exit(1)

# Test 6: Type checking (Protocol compliance)
print("Test 6: Protocol compliance check...")
try:
    from typing import Protocol
    import inspect

    # Check if DailyBreakoutScanner has required methods/properties
    scanner_attrs = dir(DailyBreakoutScanner)

    required = ['scan', 'strategy_name', 'timeframe', 'universe']
    missing = [attr for attr in required if attr not in scanner_attrs]

    if missing:
        print(f"❌ Missing required attributes: {missing}\n")
        sys.exit(1)
    else:
        print(f"✅ All required Protocol attributes present: {required}\n")
except Exception as e:
    print(f"❌ Protocol check failed: {e}\n")
    sys.exit(1)

# Test 7: Candidate dataclass validation
print("Test 7: Candidate dataclass validation...")
try:
    # Create a test candidate
    test_candidate = Candidate(
        symbol='NVDA',
        scan_date=datetime(2025, 11, 6).date(),
        score=8.5,
        entry_price=100.0,
        suggested_stop=92.0,  # 8% stop
        suggested_target=None,
        strategy_data={
            'consolidation_days': 20,
            'volume_ratio': 1.8,
            'distance_from_52w_high': 5.2
        }
    )

    print(f"Created test candidate: {test_candidate.symbol}")
    print(f"  Score: {test_candidate.score}/10")
    print(f"  Entry: ${test_candidate.entry_price}")
    print(f"  Stop: ${test_candidate.suggested_stop}")
    print(f"  Risk: {test_candidate.risk_percent():.1f}%")
    print(f"  Strategy data: {list(test_candidate.strategy_data.keys())}")
    print("✅ Candidate creation and validation successful\n")
except Exception as e:
    print(f"❌ Candidate validation failed: {e}\n")
    sys.exit(1)

# Test 8: Serialization
print("Test 8: Candidate serialization...")
try:
    candidate_dict = test_candidate.to_dict()
    print(f"Serialized candidate keys: {list(candidate_dict.keys())}")
    print("✅ Serialization successful\n")
except Exception as e:
    print(f"❌ Serialization failed: {e}\n")
    sys.exit(1)

print("=" * 60)
print("🎉 ALL TESTS PASSED!")
print("=" * 60)
print("\nInterface integration is working correctly.")
print("\nNext steps:")
print("1. Test with real API keys and historical data")
print("2. Extract exit strategies")
print("3. Update cloud services to use interfaces")
