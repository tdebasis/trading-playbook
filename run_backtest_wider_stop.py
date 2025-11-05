"""
Run DP20 backtest with WIDER STOP (1.8x ATR instead of 1.2x).

Testing if wider stop improves results.
"""

import os
from datetime import date
from dotenv import load_dotenv

from trading_playbook.adapters.alpaca_fetcher import AlpacaDataFetcher
from trading_playbook.adapters.cached_fetcher import CachedDataFetcher
from trading_playbook.core.backtest_engine import DP20Backtest


def main():
    load_dotenv()
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    print("Setting up data fetcher...")
    alpaca_fetcher = AlpacaDataFetcher(api_key, secret_key, paper=True)
    cached_fetcher = CachedDataFetcher(alpaca_fetcher, cache_dir="./data/cache")

    backtest = DP20Backtest(
        data_fetcher=cached_fetcher,
        symbol="QQQ",
        shares_per_trade=100
    )

    # WIDER STOP: 1.8x ATR instead of 1.2x
    strategy_params = {
        'stop_atr_multiplier': 1.8  # CHANGE THIS
    }

    print("\nTESTING WITH WIDER STOP: 1.8x ATR (was 1.2x)")
    print("=" * 80)

    results = backtest.run(
        start_date=date(2024, 9, 1),
        end_date=date(2024, 11, 1),
        strategy_params=strategy_params
    )

    print(results.summary())

    # Compare to baseline
    print("\nCOMPARISON TO BASELINE (1.2x ATR):")
    print("=" * 80)
    print("Baseline:  Win Rate 6.7%,  P&L: -$874.72,  Profit Factor: 0.11")
    print(f"New:       Win Rate {results.win_rate:.1f}%,  P&L: ${results.total_pnl:,.2f},  Profit Factor: {results.profit_factor:.2f}")

    if results.trades:
        stop_outs = sum(1 for t in results.trades if t.exit_reason.value == "stop_loss")
        eod_exits = sum(1 for t in results.trades if t.exit_reason.value == "end_of_day")
        print(f"\nStopped Out: {stop_outs}/{results.total_trades} ({stop_outs/results.total_trades*100:.1f}%)")
        print(f"EOD Exits:   {eod_exits}/{results.total_trades} ({eod_exits/results.total_trades*100:.1f}%)")


if __name__ == "__main__":
    main()
