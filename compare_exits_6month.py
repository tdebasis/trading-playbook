#!/usr/bin/env python3
"""
Compare Exit Strategies - 6 Month Backtest

Compares smart_exits vs scaled_exits performance over the last 6 months
using the daily_breakout scanner.

Author: Tanam Bam Sinha
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
import os
import logging

from strategies import get_exit_strategy
from scanner.long.daily_breakout_scanner import DailyBreakoutScanner
from engine.backtest_engine import BacktestEngine
from alpaca.data.historical import StockHistoricalDataClient

# Setup unbuffered logging for real-time progress
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None
sys.stderr.reconfigure(line_buffering=True) if hasattr(sys.stderr, 'reconfigure') else None

# Setup logging with immediate flush
class FlushStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/backtests/comparison_6month_{datetime.now().strftime("%Y%m%d")}.log'),
        FlushStreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def run_comparison_backtest():
    """Run comparison backtest: smart_exits vs scaled_exits."""

    # Load credentials
    load_dotenv()
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        print("❌ ERROR: Missing Alpaca API credentials in .env file")
        return 1

    # Calculate 6-month date range (using past data, not future)
    # Use Q2-Q3 2024 for now (known good data period)
    # TODO: Switch back to rolling 6 months once data access issue is resolved
    end_date = datetime(2024, 9, 30)  # End of Q3 2024
    start_date = datetime(2024, 4, 1)  # Start of Q2 2024

    print("\n" + "=" * 80, flush=True)
    print("EXIT STRATEGY COMPARISON - 6 MONTH BACKTEST", flush=True)
    print("=" * 80, flush=True)
    print(f"\nPeriod: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", flush=True)
    print(f"Scanner: daily_breakout", flush=True)
    print(f"Exit Strategies: smart_exits vs scaled_exits", flush=True)
    print(f"Starting Capital: $100,000", flush=True)
    print(f"Position Size: 6.67% (max 20% exposure)", flush=True)
    print(f"Max Positions: 3", flush=True)
    print("=" * 80 + "\n", flush=True)

    # Setup components
    logger.info("Initializing components...")
    data_client = StockHistoricalDataClient(api_key, secret_key)
    scanner = DailyBreakoutScanner(api_key, secret_key, universe='default')

    # Backtest configuration
    config = {
        'starting_capital': 100000,
        'max_positions': 3,
        'position_size_percent': 0.0667  # 6.67% per position
    }

    results = {}

    # ========== BACKTEST 1: Smart Exits ==========
    print("\n" + "=" * 80, flush=True)
    print("BACKTEST 1/2: SMART EXITS (All-or-Nothing)", flush=True)
    print("=" * 80 + "\n", flush=True)
    print("⏳ Running backtest... (this may take 2-5 minutes)", flush=True)
    print("📊 Progress will be shown for each trading day\n", flush=True)

    exit_strategy_1 = get_exit_strategy('smart_exits')
    engine_1 = BacktestEngine(
        scanner=scanner,
        exit_strategy=exit_strategy_1,
        data_client=data_client,
        **config
    )

    results['smart_exits'] = engine_1.run(start_date, end_date)

    # Show interim results
    print("\n" + "=" * 80, flush=True)
    print("✅ SMART EXITS COMPLETE - Interim Results:", flush=True)
    print(f"   Total Return: {results['smart_exits'].total_return_percent:.2f}%", flush=True)
    print(f"   Total Trades: {results['smart_exits'].total_trades}", flush=True)
    print(f"   Win Rate: {results['smart_exits'].win_rate:.1f}%", flush=True)
    print("=" * 80 + "\n", flush=True)

    # ========== BACKTEST 2: Scaled Exits ==========
    print("\n" + "=" * 80, flush=True)
    print("BACKTEST 2/2: SCALED EXITS (Profit-Taking)", flush=True)
    print("=" * 80 + "\n", flush=True)
    print("⏳ Running backtest... (this may take 2-5 minutes)", flush=True)
    print("📊 Progress will be shown for each trading day\n", flush=True)

    exit_strategy_2 = get_exit_strategy('scaled_exits')
    engine_2 = BacktestEngine(
        scanner=scanner,
        exit_strategy=exit_strategy_2,
        data_client=data_client,
        **config
    )

    results['scaled_exits'] = engine_2.run(start_date, end_date)

    # Show interim results
    print("\n" + "=" * 80, flush=True)
    print("✅ SCALED EXITS COMPLETE - Interim Results:", flush=True)
    print(f"   Total Return: {results['scaled_exits'].total_return_percent:.2f}%", flush=True)
    print(f"   Total Trades: {results['scaled_exits'].total_trades}", flush=True)
    print(f"   Win Rate: {results['scaled_exits'].win_rate:.1f}%", flush=True)
    print("=" * 80 + "\n", flush=True)

    # ========== COMPARISON REPORT ==========
    print("\n" + "=" * 80, flush=True)
    print("COMPARISON RESULTS", flush=True)
    print("=" * 80 + "\n", flush=True)

    smart = results['smart_exits']
    scaled = results['scaled_exits']

    print(f"{'Metric':<30} {'Smart Exits':>15} {'Scaled Exits':>15} {'Winner':>15}")
    print("-" * 80)

    # Total Return
    smart_return = smart.total_return_percent
    scaled_return = scaled.total_return_percent
    return_winner = "Smart" if smart_return > scaled_return else "Scaled"
    print(f"{'Total Return':<30} {smart_return:>14.2f}% {scaled_return:>14.2f}% {return_winner:>15}")

    # Win Rate
    smart_wr = smart.win_rate
    scaled_wr = scaled.win_rate
    wr_winner = "Smart" if smart_wr > scaled_wr else "Scaled"
    print(f"{'Win Rate':<30} {smart_wr:>14.2f}% {scaled_wr:>14.2f}% {wr_winner:>15}")

    # Profit Factor
    smart_pf = smart.profit_factor
    scaled_pf = scaled.profit_factor
    pf_winner = "Smart" if smart_pf > scaled_pf else "Scaled"
    print(f"{'Profit Factor':<30} {smart_pf:>15.2f} {scaled_pf:>15.2f} {pf_winner:>15}")

    # Max Drawdown
    smart_dd = smart.max_drawdown_percent
    scaled_dd = scaled.max_drawdown_percent
    dd_winner = "Smart" if smart_dd > scaled_dd else "Scaled"  # Lower is better
    print(f"{'Max Drawdown':<30} {smart_dd:>14.2f}% {scaled_dd:>14.2f}% {dd_winner:>15}")

    # Total Trades
    smart_trades = smart.total_trades
    scaled_trades = scaled.total_trades
    print(f"{'Total Trades':<30} {smart_trades:>15} {scaled_trades:>15}")

    # Average Win/Loss (in dollars)
    smart_avg_win = smart.avg_win
    scaled_avg_win = scaled.avg_win
    print(f"{'Avg Win ($)':<30} ${smart_avg_win:>14,.2f} ${scaled_avg_win:>14,.2f}")

    smart_avg_loss = smart.avg_loss
    scaled_avg_loss = scaled.avg_loss
    print(f"{'Avg Loss ($)':<30} ${smart_avg_loss:>14,.2f} ${scaled_avg_loss:>14,.2f}")

    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)

    # Simple scoring system
    smart_score = 0
    scaled_score = 0

    if smart_return > scaled_return:
        smart_score += 2
    else:
        scaled_score += 2

    if smart_pf > scaled_pf:
        smart_score += 1
    else:
        scaled_score += 1

    if smart_dd < scaled_dd:  # Lower drawdown is better
        smart_score += 1
    else:
        scaled_score += 1

    if smart_score > scaled_score:
        print(f"\n✅ WINNER: Smart Exits (Score: {smart_score} vs {scaled_score})")
        print("   Better for aggressive traders who want to let winners run.")
    elif scaled_score > smart_score:
        print(f"\n✅ WINNER: Scaled Exits (Score: {scaled_score} vs {smart_score})")
        print("   Better for conservative traders who prefer to lock in profits.")
    else:
        print(f"\n🤝 TIE: Both strategies performed similarly (Score: {smart_score} - {scaled_score})")
        print("   Choice depends on your risk tolerance and trading psychology.")

    # Save results
    output_file = f"backtest-results/comparison_6month_{datetime.now().strftime('%Y%m%d')}.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump({
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'configuration': config,
            'smart_exits': smart.to_dict(),
            'scaled_exits': scaled.to_dict(),
            'winner': 'smart_exits' if smart_score > scaled_score else 'scaled_exits' if scaled_score > smart_score else 'tie'
        }, f, indent=2, default=str)

    print(f"\n✅ Results saved to: {output_file}")
    print(f"✅ Logs saved to: logs/backtests/comparison_6month_{datetime.now().strftime('%Y%m%d')}.log\n")

    return 0


if __name__ == "__main__":
    sys.exit(run_comparison_backtest())
