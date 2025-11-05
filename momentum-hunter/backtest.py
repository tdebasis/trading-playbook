#!/usr/bin/env python3
"""
Momentum Hunter - Backtest Runner

Test Claude's decision-making on historical data.

Usage:
    python backtest.py                 # Last 30 days
    python backtest.py --days 60       # Last 60 days
    python backtest.py --start 2024-10-01 --end 2024-11-01

Author: Claude AI + Tanam Bam Sinha
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
from backtest.historical_backtest import HistoricalBacktester


def main():
    """Run historical backtest with command-line options."""

    parser = argparse.ArgumentParser(
        description="Momentum Hunter - Historical Backtester"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to backtest (default: 30)"
    )

    parser.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--capital",
        type=float,
        default=100000,
        help="Starting capital (default: 100000)"
    )

    parser.add_argument(
        "--max-positions",
        type=int,
        default=3,
        help="Max concurrent positions (default: 3)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="backtest_results.json",
        help="Output file for results (default: backtest_results.json)"
    )

    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt"
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

    # Determine date range
    if args.start and args.end:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
        end_date = datetime.strptime(args.end, "%Y-%m-%d")
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)

    print("\n" + "=" * 80)
    print("MOMENTUM HUNTER - HISTORICAL BACKTEST")
    print("=" * 80)
    print(f"\nPeriod: {start_date.date()} to {end_date.date()}")
    print(f"Starting Capital: ${args.capital:,.0f}")
    print(f"Max Positions: {args.max_positions}")
    print("\nThis will:")
    print("  - Replay historical market conditions")
    print("  - Ask Claude to make decisions on each day")
    print("  - Simulate trade execution and management")
    print("  - Calculate performance metrics")
    print("\n⚠️  Note: This will use Claude API credits (est. $5-20 depending on period)")
    print("=" * 80 + "\n")

    if not args.yes:
        confirm = input("Continue with backtest? (y/n): ")
        if confirm.lower() != 'y':
            print("\n✅ Backtest cancelled.")
            return 0

    # Create backtester
    try:
        backtester = HistoricalBacktester(
            alpaca_api_key=alpaca_key,
            alpaca_secret_key=alpaca_secret,
            anthropic_api_key=anthropic_key,
            starting_capital=args.capital
        )

        # Run backtest
        result = backtester.run_backtest(
            start_date=start_date,
            end_date=end_date,
            max_positions=args.max_positions
        )

        # Save results
        backtester.save_results(result, args.output)

        print(f"\n✅ Backtest complete! Results saved to {args.output}")

        return 0

    except KeyboardInterrupt:
        print("\n\n👋 Backtest cancelled by user.")
        return 0

    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
