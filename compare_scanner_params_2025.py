#!/usr/bin/env python3
"""
Scanner Parameter Comparison - 2025 Full Year

Compares 3 scanner parameter configurations across full 2025:
1. Relaxed (0.8x vol, 40% from high, 5d base, 18% vol)
2. Moderate (1.0x vol, 35% from high, 7d base, 15% vol)
3. Very Relaxed (0.5x vol, 50% from high, 3d base, 25% vol)

All using scaled_exits strategy for fair comparison.

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

# Setup unbuffered logging for real-time progress
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None
sys.stderr.reconfigure(line_buffering=True) if hasattr(sys.stderr, 'reconfigure') else None

class FlushStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/backtests/scanner_comparison_2025_{datetime.now().strftime("%Y%m%d")}.log'),
        FlushStreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

from strategies import get_exit_strategy
from scanner.long.daily_breakout_relaxed import DailyBreakoutScannerRelaxed
from scanner.long.daily_breakout_moderate import DailyBreakoutScannerModerate
from scanner.long.daily_breakout_very_relaxed import DailyBreakoutScannerVeryRelaxed
from engine.backtest_engine import BacktestEngine
from alpaca.data.historical import StockHistoricalDataClient


def run_scanner_comparison():
    """Run 3-way scanner parameter comparison for 2025."""

    # Load credentials
    load_dotenv()
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        print("❌ ERROR: Missing Alpaca API credentials in .env file", flush=True)
        return 1

    # 2025 full year (to date)
    start_date = datetime(2025, 1, 1)
    end_date = datetime.now() - timedelta(days=1)  # Yesterday

    print("\n" + "=" * 80, flush=True)
    print("SCANNER PARAMETER COMPARISON - 2025 FULL YEAR", flush=True)
    print("=" * 80, flush=True)
    print(f"\nPeriod: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", flush=True)
    print(f"Exit Strategy: scaled_exits (same for all)", flush=True)
    print(f"Starting Capital: $100,000", flush=True)
    print(f"Position Size: 6.67% (max 20% exposure)", flush=True)
    print(f"Max Positions: 3", flush=True)
    print("\nTesting 3 parameter configurations:", flush=True)
    print("  1. RELAXED:      0.8x vol, 40% from high, 5d base, 18% volatility", flush=True)
    print("  2. MODERATE:     1.0x vol, 35% from high, 7d base, 15% volatility", flush=True)
    print("  3. VERY RELAXED: 0.5x vol, 50% from high, 3d base, 25% volatility", flush=True)
    print("=" * 80 + "\n", flush=True)

    # Setup components
    logger.info("Initializing components...")
    data_client = StockHistoricalDataClient(api_key, secret_key)
    exit_strategy = get_exit_strategy('scaled_exits')

    # Backtest configuration
    config = {
        'starting_capital': 100000,
        'max_positions': 3,
        'position_size_percent': 0.0667  # 6.67% per position
    }

    results = {}

    # ========== BACKTEST 1: Relaxed ==========
    print("\n" + "=" * 80, flush=True)
    print("BACKTEST 1/3: RELAXED PARAMETERS", flush=True)
    print("=" * 80 + "\n", flush=True)
    print("⏳ Running backtest... (may take 10-15 minutes)", flush=True)
    print("📊 Progress will be shown for each trading day\n", flush=True)

    scanner_1 = DailyBreakoutScannerRelaxed(api_key, secret_key, universe='default')
    engine_1 = BacktestEngine(
        scanner=scanner_1,
        exit_strategy=exit_strategy,
        data_client=data_client,
        **config
    )

    results['relaxed'] = engine_1.run(start_date, end_date)

    print("\n" + "=" * 80, flush=True)
    print("✅ RELAXED COMPLETE - Interim Results:", flush=True)
    print(f"   Total Return: {results['relaxed'].total_return_percent:.2f}%", flush=True)
    print(f"   Total Trades: {results['relaxed'].total_trades}", flush=True)
    print(f"   Win Rate: {results['relaxed'].win_rate:.1f}%", flush=True)
    print("=" * 80 + "\n", flush=True)

    # ========== BACKTEST 2: Moderate ==========
    print("\n" + "=" * 80, flush=True)
    print("BACKTEST 2/3: MODERATE PARAMETERS", flush=True)
    print("=" * 80 + "\n", flush=True)
    print("⏳ Running backtest... (may take 10-15 minutes)", flush=True)
    print("📊 Progress will be shown for each trading day\n", flush=True)

    scanner_2 = DailyBreakoutScannerModerate(api_key, secret_key, universe='default')
    engine_2 = BacktestEngine(
        scanner=scanner_2,
        exit_strategy=exit_strategy,
        data_client=data_client,
        **config
    )

    results['moderate'] = engine_2.run(start_date, end_date)

    print("\n" + "=" * 80, flush=True)
    print("✅ MODERATE COMPLETE - Interim Results:", flush=True)
    print(f"   Total Return: {results['moderate'].total_return_percent:.2f}%", flush=True)
    print(f"   Total Trades: {results['moderate'].total_trades}", flush=True)
    print(f"   Win Rate: {results['moderate'].win_rate:.1f}%", flush=True)
    print("=" * 80 + "\n", flush=True)

    # ========== BACKTEST 3: Very Relaxed ==========
    print("\n" + "=" * 80, flush=True)
    print("BACKTEST 3/3: VERY RELAXED PARAMETERS", flush=True)
    print("=" * 80 + "\n", flush=True)
    print("⏳ Running backtest... (may take 10-15 minutes)", flush=True)
    print("📊 Progress will be shown for each trading day\n", flush=True)

    scanner_3 = DailyBreakoutScannerVeryRelaxed(api_key, secret_key, universe='default')
    engine_3 = BacktestEngine(
        scanner=scanner_3,
        exit_strategy=exit_strategy,
        data_client=data_client,
        **config
    )

    results['very_relaxed'] = engine_3.run(start_date, end_date)

    print("\n" + "=" * 80, flush=True)
    print("✅ VERY RELAXED COMPLETE - Interim Results:", flush=True)
    print(f"   Total Return: {results['very_relaxed'].total_return_percent:.2f}%", flush=True)
    print(f"   Total Trades: {results['very_relaxed'].total_trades}", flush=True)
    print(f"   Win Rate: {results['very_relaxed'].win_rate:.1f}%", flush=True)
    print("=" * 80 + "\n", flush=True)

    # ========== COMPARISON REPORT ==========
    print("\n" + "=" * 80, flush=True)
    print("COMPARISON RESULTS", flush=True)
    print("=" * 80 + "\n", flush=True)

    relaxed = results['relaxed']
    moderate = results['moderate']
    very_relaxed = results['very_relaxed']

    print(f"{'Metric':<30} {'Relaxed':>15} {'Moderate':>15} {'Very Relaxed':>15}", flush=True)
    print("-" * 80, flush=True)

    # Total Return
    print(f"{'Total Return':<30} {relaxed.total_return_percent:>14.2f}% {moderate.total_return_percent:>14.2f}% {very_relaxed.total_return_percent:>14.2f}%", flush=True)

    # Win Rate
    print(f"{'Win Rate':<30} {relaxed.win_rate:>14.2f}% {moderate.win_rate:>14.2f}% {very_relaxed.win_rate:>14.2f}%", flush=True)

    # Profit Factor
    print(f"{'Profit Factor':<30} {relaxed.profit_factor:>15.2f} {moderate.profit_factor:>15.2f} {very_relaxed.profit_factor:>15.2f}", flush=True)

    # Max Drawdown
    print(f"{'Max Drawdown':<30} {relaxed.max_drawdown_percent:>14.2f}% {moderate.max_drawdown_percent:>14.2f}% {very_relaxed.max_drawdown_percent:>14.2f}%", flush=True)

    # Total Trades
    print(f"{'Total Trades':<30} {relaxed.total_trades:>15} {moderate.total_trades:>15} {very_relaxed.total_trades:>15}", flush=True)

    # Avg Win/Loss
    print(f"{'Avg Win ($)':<30} ${relaxed.avg_win:>14,.2f} ${moderate.avg_win:>14,.2f} ${very_relaxed.avg_win:>14,.2f}", flush=True)
    print(f"{'Avg Loss ($)':<30} ${relaxed.avg_loss:>14,.2f} ${moderate.avg_loss:>14,.2f} ${very_relaxed.avg_loss:>14,.2f}", flush=True)

    print("\n" + "=" * 80, flush=True)
    print("RECOMMENDATION", flush=True)
    print("=" * 80, flush=True)

    # Determine winner based on total return
    winner_name = max(
        [('Relaxed', relaxed.total_return_percent),
         ('Moderate', moderate.total_return_percent),
         ('Very Relaxed', very_relaxed.total_return_percent)],
        key=lambda x: x[1]
    )[0]

    print(f"\n✅ BEST PERFORMER: {winner_name}", flush=True)
    print(f"\nKey Insights:", flush=True)
    print(f"  - Trade Volume: Very Relaxed ({very_relaxed.total_trades}) > Relaxed ({relaxed.total_trades}) > Moderate ({moderate.total_trades})", flush=True)
    print(f"  - Quality vs Quantity: Compare profit factor to see if more trades helped or hurt", flush=True)
    print(f"  - Risk: Check max drawdown - tighter filters may reduce risk", flush=True)

    # Save results
    output_file = f"backtest-results/scanner_comparison_2025_{datetime.now().strftime('%Y%m%d')}.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump({
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'configuration': config,
            'relaxed': relaxed.to_dict(),
            'moderate': moderate.to_dict(),
            'very_relaxed': very_relaxed.to_dict(),
            'winner': winner_name.lower().replace(' ', '_')
        }, f, indent=2, default=str)

    print(f"\n✅ Results saved to: {output_file}", flush=True)
    print(f"✅ Logs saved to: logs/backtests/scanner_comparison_2025_{datetime.now().strftime('%Y%m%d')}.log\n", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(run_scanner_comparison())
