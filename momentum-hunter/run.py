#!/usr/bin/env python3
"""
Momentum Hunter - Startup Script

Run this to start the autonomous AI trading system.

Usage:
    python run.py                  # Start with default settings
    python run.py --live           # Run live trading (BE CAREFUL!)
    python run.py --account 50000  # Set custom account size

Author: Claude AI + Tanam Bam Sinha
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

import argparse
from dotenv import load_dotenv
from core.orchestrator import MomentumHunter

def main():
    """Run Momentum Hunter with command-line options."""

    parser = argparse.ArgumentParser(
        description="Momentum Hunter - Autonomous AI Trading System"
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help="Run LIVE trading (default: paper trading). USE WITH CAUTION!"
    )

    parser.add_argument(
        "--account",
        type=float,
        default=100000,
        help="Account size in dollars (default: 100000)"
    )

    parser.add_argument(
        "--db",
        type=str,
        default="momentum_hunter.db",
        help="Database file path (default: momentum_hunter.db)"
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    alpaca_key = os.getenv('ALPACA_API_KEY')
    alpaca_secret = os.getenv('ALPACA_SECRET_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    if not all([alpaca_key, alpaca_secret, anthropic_key]):
        print("❌ ERROR: Missing API keys!")
        print("\nPlease create a .env file with:")
        print("  ALPACA_API_KEY=your_key")
        print("  ALPACA_SECRET_KEY=your_secret")
        print("  ANTHROPIC_API_KEY=your_anthropic_key")
        return 1

    # Safety check for live trading
    if args.live:
        print("\n" + "="*80)
        print("⚠️  WARNING: LIVE TRADING MODE")
        print("="*80)
        print("\nYou are about to run Momentum Hunter with REAL MONEY.")
        print(f"Account size: ${args.account:,.2f}")
        print("\nThis will:")
        print("  - Place real orders with real money")
        print("  - Trade automatically without human intervention")
        print("  - Risk capital based on AI decisions")
        print("\n" + "="*80)

        confirm = input("\nType 'I UNDERSTAND THE RISKS' to proceed: ")

        if confirm != "I UNDERSTAND THE RISKS":
            print("\n✅ Live trading cancelled. Good choice!")
            print("   Run without --live flag for paper trading.")
            return 0

        print("\n🚀 Starting LIVE trading...")

    else:
        print("\n" + "="*80)
        print("📄 PAPER TRADING MODE")
        print("="*80)
        print(f"\nAccount size: ${args.account:,.2f} (simulated)")
        print("This is safe - no real money at risk!")
        print("="*80 + "\n")

    # Create and run Momentum Hunter
    try:
        hunter = MomentumHunter(
            alpaca_api_key=alpaca_key,
            alpaca_secret_key=alpaca_secret,
            anthropic_api_key=anthropic_key,
            paper_trading=not args.live,
            account_size=args.account,
            db_path=args.db
        )

        hunter.run()

        return 0

    except KeyboardInterrupt:
        print("\n\n👋 Shutdown requested. Goodbye!")
        return 0

    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
