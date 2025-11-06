"""
Simple SQLite Database Layer - Stores all trading data.

Keeps it simple with SQLite for MVP. Can upgrade to PostgreSQL later if needed.

Author: Claude AI + Tanam Bam Sinha
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingDatabase:
    """
    Simple SQLite database for trading data.
    """

    def __init__(self, db_path: str = "momentum_hunter.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts
        self.create_tables()
        logger.info(f"Database initialized: {db_path}")

    def create_tables(self):
        """Create all necessary tables if they don't exist."""

        cursor = self.conn.cursor()

        # Trades table - completed trades
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                entry_time TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_time TEXT,
                exit_price REAL,
                shares INTEGER NOT NULL,
                stop_loss REAL NOT NULL,
                profit_target REAL NOT NULL,
                pnl REAL,
                pnl_percent REAL,
                exit_reason TEXT,
                status TEXT DEFAULT 'open',

                -- Claude's decision data
                confidence REAL,
                reasoning TEXT,
                catalyst_summary TEXT,
                technical_analysis TEXT,
                risk_analysis TEXT,

                -- Risk metrics
                risk_amount REAL,
                reward_amount REAL,
                risk_reward_ratio REAL,

                -- Tracking
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Decisions table - every decision Claude makes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                symbol TEXT,
                confidence REAL,
                reasoning TEXT,
                candidates_analyzed TEXT,
                market_conditions TEXT,
                account_state TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Positions table - current open positions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                entry_time TEXT NOT NULL,
                entry_price REAL NOT NULL,
                shares INTEGER NOT NULL,
                stop_loss REAL NOT NULL,
                profit_target REAL NOT NULL,
                unrealized_pnl REAL,
                current_price REAL,

                -- Decision context
                confidence REAL,
                reasoning TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Daily summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                trades_count INTEGER DEFAULT 0,
                winners INTEGER DEFAULT 0,
                losers INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                win_rate REAL,
                best_trade REAL,
                worst_trade REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL,
                total_trades INTEGER,
                win_rate REAL,
                profit_factor REAL,
                total_pnl REAL,
                avg_win REAL,
                avg_loss REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                calculated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()
        logger.info("Database tables created/verified")

    def save_trade(self, trade_data: Dict) -> int:
        """
        Save a trade to database.

        Args:
            trade_data: Dictionary with trade details

        Returns:
            Trade ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO trades (
                symbol, entry_time, entry_price, exit_time, exit_price,
                shares, stop_loss, profit_target, pnl, pnl_percent,
                exit_reason, status, confidence, reasoning,
                catalyst_summary, technical_analysis, risk_analysis,
                risk_amount, reward_amount, risk_reward_ratio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data.get('symbol'),
            trade_data.get('entry_time'),
            trade_data.get('entry_price'),
            trade_data.get('exit_time'),
            trade_data.get('exit_price'),
            trade_data.get('shares'),
            trade_data.get('stop_loss'),
            trade_data.get('profit_target'),
            trade_data.get('pnl'),
            trade_data.get('pnl_percent'),
            trade_data.get('exit_reason'),
            trade_data.get('status', 'open'),
            trade_data.get('confidence'),
            trade_data.get('reasoning'),
            trade_data.get('catalyst_summary'),
            trade_data.get('technical_analysis'),
            trade_data.get('risk_analysis'),
            trade_data.get('risk_amount'),
            trade_data.get('reward_amount'),
            trade_data.get('risk_reward_ratio')
        ))

        self.conn.commit()
        trade_id = cursor.lastrowid
        logger.info(f"Trade saved: {trade_data.get('symbol')} (ID: {trade_id})")
        return trade_id

    def update_trade(self, trade_id: int, updates: Dict):
        """
        Update a trade with new data.

        Args:
            trade_id: Trade ID to update
            updates: Dictionary of fields to update
        """
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(trade_id)

        cursor = self.conn.cursor()
        cursor.execute(f"""
            UPDATE trades
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, values)

        self.conn.commit()
        logger.info(f"Trade {trade_id} updated")

    def save_decision(self, decision_data: Dict) -> int:
        """
        Save a Claude decision to database.

        Args:
            decision_data: Decision details

        Returns:
            Decision ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO decisions (
                timestamp, action, symbol, confidence, reasoning,
                candidates_analyzed, market_conditions, account_state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision_data.get('timestamp', datetime.now().isoformat()),
            decision_data.get('action'),
            decision_data.get('symbol'),
            decision_data.get('confidence'),
            decision_data.get('reasoning'),
            json.dumps(decision_data.get('candidates_analyzed', [])),
            json.dumps(decision_data.get('market_conditions', {})),
            json.dumps(decision_data.get('account_state', {}))
        ))

        self.conn.commit()
        return cursor.lastrowid

    def add_position(self, position_data: Dict) -> int:
        """
        Add a new open position.

        Args:
            position_data: Position details

        Returns:
            Position ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO positions (
                symbol, entry_time, entry_price, shares,
                stop_loss, profit_target, current_price,
                unrealized_pnl, confidence, reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            position_data.get('symbol'),
            position_data.get('entry_time'),
            position_data.get('entry_price'),
            position_data.get('shares'),
            position_data.get('stop_loss'),
            position_data.get('profit_target'),
            position_data.get('current_price'),
            position_data.get('unrealized_pnl', 0),
            position_data.get('confidence'),
            position_data.get('reasoning')
        ))

        self.conn.commit()
        return cursor.lastrowid

    def update_position(self, symbol: str, updates: Dict):
        """Update an existing position."""
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(symbol)

        cursor = self.conn.cursor()
        cursor.execute(f"""
            UPDATE positions
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ?
        """, values)

        self.conn.commit()

    def remove_position(self, symbol: str):
        """Remove a closed position."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))
        self.conn.commit()
        logger.info(f"Position removed: {symbol}")

    def get_open_positions(self) -> List[Dict]:
        """Get all currently open positions."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM positions")
        return [dict(row) for row in cursor.fetchall()]

    def get_trades(self, days: Optional[int] = None) -> List[Dict]:
        """
        Get trades from database.

        Args:
            days: Only get trades from last N days (None = all)

        Returns:
            List of trades
        """
        cursor = self.conn.cursor()

        if days:
            cursor.execute("""
                SELECT * FROM trades
                WHERE DATE(entry_time) >= DATE('now', ?)
                ORDER BY entry_time DESC
            """, (f'-{days} days',))
        else:
            cursor.execute("SELECT * FROM trades ORDER BY entry_time DESC")

        return [dict(row) for row in cursor.fetchall()]

    def get_daily_pnl(self, date: Optional[str] = None) -> float:
        """
        Get total P&L for a specific date.

        Args:
            date: Date string (YYYY-MM-DD) or None for today

        Returns:
            Total P&L for that date
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(pnl), 0) as total_pnl
            FROM trades
            WHERE DATE(entry_time) = ?
            AND status = 'closed'
        """, (date,))

        result = cursor.fetchone()
        return result['total_pnl'] if result else 0.0

    def get_performance_summary(self) -> Dict:
        """
        Calculate overall performance metrics.

        Returns:
            Dictionary with performance stats
        """
        cursor = self.conn.cursor()

        # Get all closed trades
        cursor.execute("""
            SELECT * FROM trades
            WHERE status = 'closed'
            ORDER BY entry_time
        """)

        trades = [dict(row) for row in cursor.fetchall()]

        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }

        winners = [t for t in trades if t['pnl'] > 0]
        losers = [t for t in trades if t['pnl'] <= 0]

        total_wins = sum(t['pnl'] for t in winners)
        total_losses = abs(sum(t['pnl'] for t in losers))

        return {
            'total_trades': len(trades),
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': len(winners) / len(trades) * 100 if trades else 0,
            'total_pnl': sum(t['pnl'] for t in trades),
            'avg_win': total_wins / len(winners) if winners else 0,
            'avg_loss': total_losses / len(losers) if losers else 0,
            'profit_factor': total_wins / total_losses if total_losses > 0 else float('inf'),
            'best_trade': max((t['pnl'] for t in trades), default=0),
            'worst_trade': min((t['pnl'] for t in trades), default=0)
        }

    def close(self):
        """Close database connection."""
        self.conn.close()
        logger.info("Database connection closed")


def main():
    """Test database operations."""

    print("\n" + "="*80)
    print("MOMENTUM HUNTER - Database Test")
    print("="*80 + "\n")

    # Initialize database
    db = TradingDatabase("test_momentum_hunter.db")

    # Test saving a trade
    print("Testing trade save...")
    trade_data = {
        'symbol': 'NVAX',
        'entry_time': datetime.now().isoformat(),
        'entry_price': 16.50,
        'shares': 500,
        'stop_loss': 15.80,
        'profit_target': 18.50,
        'status': 'open',
        'confidence': 8.5,
        'reasoning': 'FDA approval catalyst, bull flag setup',
        'risk_reward_ratio': 2.8
    }

    trade_id = db.save_trade(trade_data)
    print(f"✓ Trade saved with ID: {trade_id}")

    # Test saving a decision
    print("\nTesting decision save...")
    decision_data = {
        'action': 'BUY',
        'symbol': 'NVAX',
        'confidence': 8.5,
        'reasoning': 'Strong FDA catalyst, optimal entry on pullback'
    }

    decision_id = db.save_decision(decision_data)
    print(f"✓ Decision saved with ID: {decision_id}")

    # Test adding position
    print("\nTesting position add...")
    position_data = {
        'symbol': 'NVAX',
        'entry_time': datetime.now().isoformat(),
        'entry_price': 16.50,
        'shares': 500,
        'stop_loss': 15.80,
        'profit_target': 18.50,
        'current_price': 16.75,
        'unrealized_pnl': 125.00
    }

    position_id = db.add_position(position_data)
    print(f"✓ Position added with ID: {position_id}")

    # Test retrieving data
    print("\nRetrieving open positions...")
    positions = db.get_open_positions()
    for pos in positions:
        print(f"  {pos['symbol']}: {pos['shares']} shares @ ${pos['entry_price']}")

    print("\nRetrieving trades...")
    trades = db.get_trades()
    for trade in trades:
        print(f"  {trade['symbol']}: ${trade['pnl'] if trade['pnl'] else 'open'}")

    # Get performance summary
    print("\nPerformance Summary:")
    summary = db.get_performance_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Cleanup
    db.close()
    print("\n✓ Database test complete!")

    # Remove test database
    Path("test_momentum_hunter.db").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
