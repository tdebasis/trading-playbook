"""
Run DP20 backtest on QQQ.

This is the main entry point for backtesting the strategy.

Run with: python3 -m poetry run python run_backtest.py
"""

import os
from datetime import date
from dotenv import load_dotenv

from trading_playbook.adapters.alpaca_fetcher import AlpacaDataFetcher
from trading_playbook.adapters.cached_fetcher import CachedDataFetcher
from trading_playbook.core.backtest_engine import DP20Backtest


def main():
    # Load API credentials
    load_dotenv()
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        print("ERROR: ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env")
        return

    # Setup data fetcher with caching
    print("Setting up data fetcher...")
    alpaca_fetcher = AlpacaDataFetcher(api_key, secret_key, paper=True)
    cached_fetcher = CachedDataFetcher(alpaca_fetcher, cache_dir="./data/cache")

    # Create backtest engine
    backtest = DP20Backtest(
        data_fetcher=cached_fetcher,
        symbol="QQQ",
        shares_per_trade=100  # Trade 100 shares per signal
    )

    # Run backtest for ~60 trading days (Sep 1 - Nov 1, 2024)
    results = backtest.run(
        start_date=date(2024, 9, 1),
        end_date=date(2024, 11, 1)
    )

    # Print results
    print(results.summary())

    # Print individual trades
    if results.trades:
        print("\nINDIVIDUAL TRADES:")
        print("=" * 80)
        for trade in results.trades:
            print(trade)

        # Additional analysis
        print("\n" + "=" * 80)
        print("ADDITIONAL METRICS:")
        print("=" * 80)

        # Exit reason breakdown
        stop_outs = sum(1 for t in results.trades if t.exit_reason.value == "stop_loss")
        eod_exits = sum(1 for t in results.trades if t.exit_reason.value == "end_of_day")

        print(f"\nExit Reasons:")
        print(f"  Stopped Out:     {stop_outs} ({stop_outs/results.total_trades*100:.1f}%)")
        print(f"  End of Day:      {eod_exits} ({eod_exits/results.total_trades*100:.1f}%)")

        # MAE/MFE analysis
        avg_mae = sum(t.mae for t in results.trades) / len(results.trades)
        avg_mfe = sum(t.mfe for t in results.trades) / len(results.trades)

        print(f"\nDrawdown/Excursion:")
        print(f"  Avg MAE (worst): ${avg_mae:.2f}")
        print(f"  Avg MFE (best):  ${avg_mfe:.2f}")

    else:
        print("\nNo trades found in this period!")
        print("Try:")
        print("  - Expanding the date range")
        print("  - Checking if trend filter is too restrictive")
        print("  - Adjusting strategy parameters")


if __name__ == "__main__":
    main()
