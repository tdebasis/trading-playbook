#!/usr/bin/env python3
"""
Momentum Hunter - Live Monitor

Shows real-time status while the system is running.

Usage:
    python monitor.py

Author: Claude AI + Tanam Bam Sinha
"""

import sys
import os
from pathlib import Path
import time
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
from data.database import TradingDatabase


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def display_dashboard(db: TradingDatabase):
    """Display live trading dashboard."""

    clear_screen()

    # Header
    print("=" * 80)
    print(" " * 25 + "MOMENTUM HUNTER - LIVE")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Account summary
    performance = db.get_performance_summary()

    print("\n📊 PERFORMANCE SUMMARY")
    print("-" * 80)
    print(f"Total Trades:     {performance['total_trades']}")
    print(f"Win Rate:         {performance['win_rate']:.1f}%")
    print(f"Total P&L:        ${performance['total_pnl']:+,.2f}")
    print(f"Profit Factor:    {performance['profit_factor']:.2f}" if performance['profit_factor'] != float('inf') else "Profit Factor:    N/A")
    print(f"Best Trade:       ${performance['best_trade']:+,.2f}")
    print(f"Worst Trade:      ${performance['worst_trade']:+,.2f}")

    # Today's P&L
    today_pnl = db.get_daily_pnl()
    print(f"\nToday's P&L:      ${today_pnl:+,.2f}")

    # Open positions
    positions = db.get_open_positions()

    print("\n💼 OPEN POSITIONS")
    print("-" * 80)

    if positions:
        for pos in positions:
            symbol = pos['symbol']
            shares = pos['shares']
            entry = pos['entry_price']
            current = pos['current_price']
            pnl = pos['unrealized_pnl']
            pnl_pct = (pnl / (entry * shares)) * 100 if shares > 0 else 0

            print(f"\n{symbol}:")
            print(f"  Shares:   {shares}")
            print(f"  Entry:    ${entry:.2f}")
            print(f"  Current:  ${current:.2f}")
            print(f"  P&L:      ${pnl:+,.2f} ({pnl_pct:+.1f}%)")
            if pos['stop_loss']:
                print(f"  Stop:     ${pos['stop_loss']:.2f}")
            if pos['profit_target']:
                print(f"  Target:   ${pos['profit_target']:.2f}")
    else:
        print("No open positions")

    # Recent trades
    recent_trades = db.get_trades(days=1)

    print("\n📈 RECENT TRADES (Today)")
    print("-" * 80)

    if recent_trades:
        for trade in recent_trades[:5]:  # Show last 5
            symbol = trade['symbol']
            status = trade['status']
            pnl = trade.get('pnl', 0)

            if status == 'closed':
                result = "✅" if pnl > 0 else "❌"
                print(f"{result} {symbol}: ${pnl:+,.2f} ({trade.get('exit_reason', 'unknown')})")
            else:
                print(f"⏳ {symbol}: Open")
    else:
        print("No trades today")

    # Footer
    print("\n" + "=" * 80)
    print("Press Ctrl+C to exit")
    print("=" * 80)


def main():
    """Run the live monitor."""

    load_dotenv()

    db_path = "momentum_hunter.db"

    # Check if database exists
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        print("\nStart the trading system first:")
        print("  python run.py")
        return 1

    db = TradingDatabase(db_path)

    print("Starting live monitor...")
    print("This will refresh every 10 seconds.")
    print("Press Ctrl+C to exit.\n")

    time.sleep(2)

    try:
        while True:
            display_dashboard(db)
            time.sleep(10)  # Update every 10 seconds

    except KeyboardInterrupt:
        print("\n\n👋 Monitor closed. Trading system is still running!")
        db.close()
        return 0

    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        db.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())
