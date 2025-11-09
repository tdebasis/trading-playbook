#!/usr/bin/env python3
"""
Exit Strategy Optimization - 2025 Full Year

Compares exit strategies to optimize for 40%+ annual returns:
1. Scaled Exits (baseline): 3 positions, 6.67% size, partial exits at +8/+15/+25
2. Trend Following 75 (optimized): 8 positions, 12.5% size, 25% at +10 then ride

Key Changes in Trend Following 75:
- Higher capital deployment: 20% → 100%
- Fewer profit targets: 3 → 1 (only 25% at +10%)
- Let 75% ride for +50-100% moves
- No time stops (exit on trend break only)

All using Moderate scanner (winner from parameter comparison) + same period.

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
        logging.FileHandler(f'logs/backtests/exit_optimization_2025_{datetime.now().strftime("%Y%m%d")}.log'),
        FlushStreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

from strategies import get_exit_strategy
from scanner.long.daily_breakout_moderate import DailyBreakoutScannerModerate
from engine.backtest_engine import BacktestEngine
from alpaca.data.historical import StockHistoricalDataClient


def run_exit_optimization():
    """Run exit strategy optimization for 2025."""

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
    print("EXIT STRATEGY OPTIMIZATION - 2025 FULL YEAR", flush=True)
    print("=" * 80, flush=True)
    print(f"\nPeriod: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", flush=True)
    print(f"Scanner: daily_breakout_moderate (winner from parameter comparison)", flush=True)
    print(f"Starting Capital: $100,000", flush=True)
    print("\nTesting 2 configurations:", flush=True)
    print("  1. BASELINE (Scaled Exits):    3 pos × 6.67% = 20% deployed", flush=True)
    print("  2. OPTIMIZED (Trend Follow 75): 8 pos × 12.5% = 100% deployed", flush=True)
    print("\nGoal: Achieve 40%+ annual returns by letting winners run", flush=True)
    print("=" * 80 + "\n", flush=True)

    # Setup components
    logger.info("Initializing components...")
    data_client = StockHistoricalDataClient(api_key, secret_key)
    scanner = DailyBreakoutScannerModerate(api_key, secret_key, universe='default')

    results = {}

    # ========== BACKTEST 1: Scaled Exits (Baseline) ==========
    print("\n" + "=" * 80, flush=True)
    print("BACKTEST 1/2: BASELINE - SCALED EXITS", flush=True)
    print("=" * 80, flush=True)
    print("Configuration:", flush=True)
    print("  Exit Strategy: scaled_exits", flush=True)
    print("  Max Positions: 3", flush=True)
    print("  Position Size: 6.67%", flush=True)
    print("  Capital Deployed: ~20% max", flush=True)
    print("  Profit Targets: 25% at +8%, +15%, +25%", flush=True)
    print("\n⏳ Running backtest... (may take 10 minutes)\n", flush=True)

    exit_strategy_1 = get_exit_strategy('scaled_exits')
    engine_1 = BacktestEngine(
        scanner=scanner,
        exit_strategy=exit_strategy_1,
        data_client=data_client,
        starting_capital=100000,
        max_positions=3,
        position_size_percent=0.0667  # 6.67% per position
    )

    results['scaled_exits'] = engine_1.run(start_date, end_date)

    print("\n" + "=" * 80, flush=True)
    print("✅ SCALED EXITS COMPLETE - Results:", flush=True)
    print(f"   Total Return: {results['scaled_exits'].total_return_percent:.2f}%", flush=True)
    print(f"   Ending Capital: ${results['scaled_exits'].ending_capital:,.2f}", flush=True)
    print(f"   Total Trades: {results['scaled_exits'].total_trades}", flush=True)
    print(f"   Win Rate: {results['scaled_exits'].win_rate:.1f}%", flush=True)
    print(f"   Avg Win: ${results['scaled_exits'].avg_win:,.2f}", flush=True)
    print(f"   Expectancy: ${results['scaled_exits'].expectancy:,.2f}", flush=True)
    print("=" * 80 + "\n", flush=True)

    # ========== BACKTEST 2: Trend Following 75 (Optimized) ==========
    print("\n" + "=" * 80, flush=True)
    print("BACKTEST 2/2: OPTIMIZED - TREND FOLLOWING 75", flush=True)
    print("=" * 80, flush=True)
    print("Configuration:", flush=True)
    print("  Exit Strategy: trend_following_75", flush=True)
    print("  Max Positions: 8 (4x more opportunities)", flush=True)
    print("  Position Size: 12.5%", flush=True)
    print("  Capital Deployed: ~100% max", flush=True)
    print("  Profit Taking: 25% at +10%, then let 75% ride", flush=True)
    print("  No Time Stops: Exit on trend break only", flush=True)
    print("\n⏳ Running backtest... (may take 10 minutes)\n", flush=True)

    exit_strategy_2 = get_exit_strategy('trend_following_75')
    engine_2 = BacktestEngine(
        scanner=scanner,
        exit_strategy=exit_strategy_2,
        data_client=data_client,
        starting_capital=100000,
        max_positions=8,
        position_size_percent=0.125  # 12.5% per position (8 × 12.5% = 100%)
    )

    results['trend_following_75'] = engine_2.run(start_date, end_date)

    print("\n" + "=" * 80, flush=True)
    print("✅ TREND FOLLOWING 75 COMPLETE - Results:", flush=True)
    print(f"   Total Return: {results['trend_following_75'].total_return_percent:.2f}%", flush=True)
    print(f"   Ending Capital: ${results['trend_following_75'].ending_capital:,.2f}", flush=True)
    print(f"   Total Trades: {results['trend_following_75'].total_trades}", flush=True)
    print(f"   Win Rate: {results['trend_following_75'].win_rate:.1f}%", flush=True)
    print(f"   Avg Win: ${results['trend_following_75'].avg_win:,.2f}", flush=True)
    print(f"   Expectancy: ${results['trend_following_75'].expectancy:,.2f}", flush=True)
    print("=" * 80 + "\n", flush=True)

    # ========== COMPARISON REPORT ==========
    print("\n" + "=" * 80, flush=True)
    print("OPTIMIZATION RESULTS", flush=True)
    print("=" * 80 + "\n", flush=True)

    baseline = results['scaled_exits']
    optimized = results['trend_following_75']

    print(f"{'Metric':<30} {'Baseline':>15} {'Optimized':>15} {'Improvement':>15}", flush=True)
    print("-" * 80, flush=True)

    # Total Return
    return_improvement = optimized.total_return_percent - baseline.total_return_percent
    print(f"{'Total Return':<30} {baseline.total_return_percent:>14.2f}% {optimized.total_return_percent:>14.2f}% {return_improvement:>+14.2f}%", flush=True)

    # Ending Capital
    capital_improvement = optimized.ending_capital - baseline.ending_capital
    print(f"{'Ending Capital':<30} ${baseline.ending_capital:>13,.0f} ${optimized.ending_capital:>13,.0f} ${capital_improvement:>+13,.0f}", flush=True)

    # Win Rate
    wr_improvement = optimized.win_rate - baseline.win_rate
    print(f"{'Win Rate':<30} {baseline.win_rate:>14.2f}% {optimized.win_rate:>14.2f}% {wr_improvement:>+14.2f}%", flush=True)

    # Profit Factor
    pf_improvement = optimized.profit_factor - baseline.profit_factor
    print(f"{'Profit Factor':<30} {baseline.profit_factor:>15.2f} {optimized.profit_factor:>15.2f} {pf_improvement:>+15.2f}", flush=True)

    # Max Drawdown
    dd_improvement = optimized.max_drawdown_percent - baseline.max_drawdown_percent
    print(f"{'Max Drawdown':<30} {baseline.max_drawdown_percent:>14.2f}% {optimized.max_drawdown_percent:>14.2f}% {dd_improvement:>+14.2f}%", flush=True)

    # Total Trades
    trades_improvement = optimized.total_trades - baseline.total_trades
    print(f"{'Total Trades':<30} {baseline.total_trades:>15} {optimized.total_trades:>15} {trades_improvement:>+15}", flush=True)

    # Avg Win/Loss
    avg_win_improvement = optimized.avg_win - baseline.avg_win
    print(f"{'Avg Win ($)':<30} ${baseline.avg_win:>14,.2f} ${optimized.avg_win:>14,.2f} ${avg_win_improvement:>+14,.0f}", flush=True)
    print(f"{'Avg Loss ($)':<30} ${baseline.avg_loss:>14,.2f} ${optimized.avg_loss:>14,.2f}", flush=True)

    # Expectancy
    expectancy_improvement = optimized.expectancy - baseline.expectancy
    print(f"{'Expectancy':<30} ${baseline.expectancy:>14,.2f} ${optimized.expectancy:>14,.2f} ${expectancy_improvement:>+14,.0f}", flush=True)

    # Avg Hold Days
    print(f"{'Avg Hold Days':<30} {baseline.avg_hold_days:>15.1f} {optimized.avg_hold_days:>15.1f}", flush=True)

    print("\n" + "=" * 80, flush=True)
    print("ANALYSIS", flush=True)
    print("=" * 80, flush=True)

    # Determine success
    target_return = 40.0  # 40% target
    annualized_return = (optimized.total_return_percent / 10) * 12  # 10 months → annual

    print(f"\n📊 Optimization Impact:", flush=True)
    print(f"   Return Improvement: +{return_improvement:.2f} percentage points", flush=True)
    print(f"   Capital Gain: ${capital_improvement:,.2f}", flush=True)
    print(f"   Avg Win Increase: ${avg_win_improvement:,.2f} ({(avg_win_improvement/baseline.avg_win*100):.1f}%)", flush=True)
    print(f"   Expectancy Increase: ${expectancy_improvement:,.2f} per trade", flush=True)

    print(f"\n🎯 Target Achievement:", flush=True)
    print(f"   10-Month Return: {optimized.total_return_percent:.2f}%", flush=True)
    print(f"   Annualized (est): {annualized_return:.2f}%", flush=True)
    print(f"   Target: {target_return:.2f}%", flush=True)

    if annualized_return >= target_return:
        print(f"   ✅ TARGET MET! (+{annualized_return - target_return:.2f}% above goal)", flush=True)
    else:
        print(f"   ⚠️  Below target by {target_return - annualized_return:.2f}%", flush=True)
        print(f"   Next steps: Consider higher-quality setups or larger position sizes", flush=True)

    print(f"\n💡 Key Insights:", flush=True)
    print(f"   - Capital Deployment: {baseline.max_concurrent_positions * 6.67:.0f}% → 100% (5x improvement)", flush=True)
    print(f"   - Fewer Profit Targets: Let winners run to +{optimized.trades[0]['pnl_pct'] if optimized.trades else 0:.0f}%+", flush=True)
    print(f"   - No Time Stops: Positions held avg {optimized.avg_hold_days:.1f} days", flush=True)

    # Save results
    output_file = f"backtest-results/exit_optimization_2025_{datetime.now().strftime('%Y%m%d')}.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump({
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'baseline': {
                'name': 'scaled_exits',
                'max_positions': 3,
                'position_size': 0.0667,
                'results': baseline.to_dict()
            },
            'optimized': {
                'name': 'trend_following_75',
                'max_positions': 8,
                'position_size': 0.125,
                'results': optimized.to_dict()
            },
            'improvement': {
                'return_pct': return_improvement,
                'capital_gain': capital_improvement,
                'avg_win_increase': avg_win_improvement,
                'expectancy_increase': expectancy_improvement
            },
            'target_met': annualized_return >= target_return
        }, f, indent=2, default=str)

    print(f"\n✅ Results saved to: {output_file}", flush=True)
    print(f"✅ Logs saved to: logs/backtests/exit_optimization_2025_{datetime.now().strftime('%Y%m%d')}.log\n", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(run_exit_optimization())
