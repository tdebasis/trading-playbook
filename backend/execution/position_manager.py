"""
Position Manager - Monitors and manages open positions.

Continuously watches open positions and:
- Checks if stop loss hit → close position
- Checks if profit target hit → close position
- Updates unrealized P&L
- Detects pattern breakdown
- Emergency exit if needed

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime
from typing import List, Dict, Optional
import logging
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest

# Allow standalone testing
try:
    from execution.trade_executor import TradeExecutor
    from data.database import TradingDatabase
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from execution.trade_executor import TradeExecutor
    TradingDatabase = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PositionManager:
    """
    Monitors and manages open trading positions.
    """

    def __init__(
        self,
        executor: TradeExecutor,
        data_client: StockHistoricalDataClient,
        database: Optional[TradingDatabase] = None
    ):
        """
        Initialize position manager.

        Args:
            executor: TradeExecutor for closing positions
            data_client: Alpaca data client for price updates
            database: Optional database for logging
        """
        self.executor = executor
        self.data_client = data_client
        self.db = database

        # Tracking
        self.positions = {}  # symbol -> position data
        self.last_update = datetime.now()

        logger.info("Position Manager initialized")

    def update_positions(self) -> Dict[str, Dict]:
        """
        Update all position data with current prices and P&L.

        Returns:
            Dictionary of updated positions
        """
        # Get positions from broker
        broker_positions = self.executor.get_open_positions()

        if not broker_positions:
            self.positions = {}
            return {}

        # Update each position
        for pos in broker_positions:
            symbol = pos['symbol']

            # Get current quote
            try:
                quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
                quotes = self.data_client.get_stock_latest_quote(quote_request)

                if symbol in quotes:
                    quote = quotes[symbol]
                    current_price = float(quote.ask_price)
                else:
                    current_price = pos['current_price']

            except Exception as e:
                logger.warning(f"Could not fetch quote for {symbol}: {e}")
                current_price = pos['current_price']

            # Update position data
            self.positions[symbol] = {
                'symbol': symbol,
                'shares': pos['shares'],
                'entry_price': pos['entry_price'],
                'current_price': current_price,
                'unrealized_pnl': (current_price - pos['entry_price']) * pos['shares'],
                'unrealized_pnl_percent': ((current_price - pos['entry_price']) / pos['entry_price']) * 100,
                'market_value': current_price * pos['shares'],
                'stop_loss': None,  # Will fetch from database
                'profit_target': None,
                'last_updated': datetime.now()
            }

            # Get stop/target from database
            if self.db:
                db_positions = self.db.get_open_positions()
                for db_pos in db_positions:
                    if db_pos['symbol'] == symbol:
                        self.positions[symbol]['stop_loss'] = db_pos['stop_loss']
                        self.positions[symbol]['profit_target'] = db_pos['profit_target']
                        break

                # Update database with current price
                self.db.update_position(symbol, {
                    'current_price': current_price,
                    'unrealized_pnl': self.positions[symbol]['unrealized_pnl']
                })

        self.last_update = datetime.now()

        return self.positions

    def check_exits(self) -> List[Dict]:
        """
        Check if any positions should be exited (stop/target hit).

        Returns:
            List of exit actions taken
        """
        exits = []

        for symbol, pos in self.positions.items():
            current_price = pos['current_price']
            stop_loss = pos.get('stop_loss')
            profit_target = pos.get('profit_target')

            # Check stop loss
            if stop_loss and current_price <= stop_loss:
                logger.warning(f"🛑 STOP LOSS HIT: {symbol} @ ${current_price:.2f} (stop: ${stop_loss:.2f})")

                result = self.executor.execute_sell(symbol, reason="stop_loss")

                if result.success:
                    exits.append({
                        'symbol': symbol,
                        'reason': 'stop_loss',
                        'price': result.filled_price,
                        'pnl': pos['unrealized_pnl']
                    })

                    # Remove from tracking
                    del self.positions[symbol]

            # Check profit target
            elif profit_target and current_price >= profit_target:
                logger.info(f"🎯 PROFIT TARGET HIT: {symbol} @ ${current_price:.2f} (target: ${profit_target:.2f})")

                result = self.executor.execute_sell(symbol, reason="profit_target")

                if result.success:
                    exits.append({
                        'symbol': symbol,
                        'reason': 'profit_target',
                        'price': result.filled_price,
                        'pnl': pos['unrealized_pnl']
                    })

                    # Remove from tracking
                    del self.positions[symbol]

        return exits

    def close_all_at_eod(self) -> List[Dict]:
        """
        Close all positions at end of day.

        Returns:
            List of closed positions
        """
        logger.info("⏰ End of day - closing all positions")

        exits = []

        for symbol in list(self.positions.keys()):
            result = self.executor.execute_sell(symbol, reason="end_of_day")

            if result.success:
                exits.append({
                    'symbol': symbol,
                    'reason': 'end_of_day',
                    'price': result.filled_price,
                    'pnl': self.positions[symbol]['unrealized_pnl']
                })

                # Remove from tracking
                del self.positions[symbol]

        return exits

    def emergency_exit_all(self, reason: str = "emergency") -> List[Dict]:
        """
        Emergency exit - close all positions immediately.

        Args:
            reason: Reason for emergency exit

        Returns:
            List of closed positions
        """
        logger.error(f"🚨 EMERGENCY EXIT: {reason}")

        exits = []

        for symbol in list(self.positions.keys()):
            result = self.executor.execute_sell(symbol, reason=reason)

            if result.success:
                exits.append({
                    'symbol': symbol,
                    'reason': reason,
                    'price': result.filled_price,
                    'pnl': self.positions[symbol]['unrealized_pnl']
                })

                # Remove from tracking
                del self.positions[symbol]

        return exits

    def get_total_pnl(self) -> float:
        """
        Get total unrealized P&L across all positions.

        Returns:
            Total unrealized P&L
        """
        return sum(pos['unrealized_pnl'] for pos in self.positions.values())

    def get_position_count(self) -> int:
        """
        Get number of open positions.

        Returns:
            Position count
        """
        return len(self.positions)

    def get_position_summary(self) -> Dict:
        """
        Get summary of all positions.

        Returns:
            Summary dictionary
        """
        if not self.positions:
            return {
                'count': 0,
                'total_pnl': 0,
                'total_value': 0,
                'positions': []
            }

        total_pnl = sum(pos['unrealized_pnl'] for pos in self.positions.values())
        total_value = sum(pos['market_value'] for pos in self.positions.values())

        position_list = []
        for symbol, pos in self.positions.items():
            position_list.append({
                'symbol': symbol,
                'shares': pos['shares'],
                'entry': pos['entry_price'],
                'current': pos['current_price'],
                'pnl': pos['unrealized_pnl'],
                'pnl_percent': pos['unrealized_pnl_percent'],
                'stop': pos.get('stop_loss'),
                'target': pos.get('profit_target')
            })

        return {
            'count': len(self.positions),
            'total_pnl': total_pnl,
            'total_value': total_value,
            'positions': position_list
        }

    def monitor_once(self) -> Dict:
        """
        Single monitoring cycle - update prices and check exits.

        Returns:
            Monitoring results
        """
        # Update all positions
        self.update_positions()

        # Check for exits
        exits = self.check_exits()

        # Get summary
        summary = self.get_position_summary()

        return {
            'timestamp': datetime.now(),
            'positions': summary,
            'exits': exits,
            'total_pnl': summary['total_pnl']
        }


def main():
    """Test the position manager."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    print("\n" + "="*80)
    print("MOMENTUM HUNTER - Position Manager Test")
    print("="*80 + "\n")

    # Initialize components
    from alpaca.data.historical import StockHistoricalDataClient

    executor = TradeExecutor(api_key, secret_key, paper=True)
    data_client = StockHistoricalDataClient(api_key, secret_key)

    manager = PositionManager(executor, data_client, database=None)

    # Get current state
    print("Monitoring positions...")
    result = manager.monitor_once()

    print(f"\nTimestamp: {result['timestamp']}")
    print(f"\nPosition Summary:")
    print(f"  Count: {result['positions']['count']}")
    print(f"  Total P&L: ${result['positions']['total_pnl']:+,.2f}")
    print(f"  Total Value: ${result['positions']['total_value']:,.2f}")

    if result['positions']['positions']:
        print(f"\nOpen Positions:")
        for pos in result['positions']['positions']:
            print(f"  {pos['symbol']}: {pos['shares']} shares @ ${pos['entry']:.2f}")
            print(f"    Current: ${pos['current']:.2f}, P&L: ${pos['pnl']:+,.2f} ({pos['pnl_percent']:+.1f}%)")
            if pos['stop']:
                print(f"    Stop: ${pos['stop']:.2f}, Target: ${pos['target']:.2f}")
    else:
        print("\n  No open positions")

    if result['exits']:
        print(f"\nExits This Cycle:")
        for exit in result['exits']:
            print(f"  {exit['symbol']}: {exit['reason']} @ ${exit['price']:.2f}, P&L: ${exit['pnl']:+,.2f}")

    print("\n✓ Position manager test complete!")


if __name__ == "__main__":
    main()
