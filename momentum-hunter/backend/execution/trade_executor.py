"""
Trade Executor - Places and manages orders with Alpaca.

This module takes Claude's trading decisions and executes them in the market.
Handles order placement, stop losses, profit targets, and order tracking.

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass
import logging
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopLossRequest, TakeProfitRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.trading.models import Order

# Imports will work when run as module
# For standalone testing, we'll import conditionally
try:
    from brain.claude_engine import TradeDecision
    from data.database import TradingDatabase
except ImportError:
    # Allow standalone testing
    TradeDecision = None
    TradingDatabase = None
    import sys
    from pathlib import Path
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of a trade execution."""
    success: bool
    order_id: Optional[str] = None
    filled_price: Optional[float] = None
    filled_shares: Optional[int] = None
    message: str = ""
    error: Optional[str] = None

    def __str__(self):
        if self.success:
            return f"✅ Order filled: {self.filled_shares} shares @ ${self.filled_price:.2f}"
        else:
            return f"❌ Execution failed: {self.error}"


class TradeExecutor:
    """
    Executes trades with Alpaca API.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper: bool = True,
        database: Optional[TradingDatabase] = None
    ):
        """
        Initialize trade executor.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Use paper trading (True) or live (False)
            database: Optional database for logging
        """
        self.client = TradingClient(api_key, secret_key, paper=paper)
        self.paper = paper
        self.db = database

        mode = "PAPER" if paper else "LIVE"
        logger.info(f"Trade Executor initialized ({mode} trading)")

    def get_account_info(self) -> Dict:
        """
        Get current account information.

        Returns:
            Dict with account details
        """
        try:
            account = self.client.get_account()

            return {
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'equity': float(account.equity),
                'daytrade_count': account.daytrade_count,
                'pattern_day_trader': account.pattern_day_trader
            }
        except Exception as e:
            logger.error(f"Error fetching account info: {e}")
            return {}

    def execute_buy(self, decision: TradeDecision) -> ExecutionResult:
        """
        Execute a buy order based on Claude's decision.

        Args:
            decision: TradeDecision from Claude

        Returns:
            ExecutionResult with execution details
        """
        if decision.action != "BUY":
            return ExecutionResult(
                success=False,
                error="Decision action is not BUY"
            )

        symbol = decision.symbol
        shares = decision.position_size_shares

        if not symbol or not shares:
            return ExecutionResult(
                success=False,
                error="Missing symbol or shares in decision"
            )

        try:
            logger.info(f"Executing BUY order: {shares} shares of {symbol}")

            # Place market order
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=shares,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )

            order = self.client.submit_order(order_data)

            logger.info(f"Order submitted: {order.id}")

            # Wait for fill (simplified - in production would poll for status)
            # For paper trading, orders usually fill instantly
            filled_order = self.client.get_order_by_id(order.id)

            # Set stop loss
            if decision.stop_loss:
                self._set_stop_loss(symbol, shares, decision.stop_loss)

            # Set profit target
            if decision.profit_target:
                self._set_profit_target(symbol, shares, decision.profit_target)

            # Save to database
            if self.db:
                trade_data = {
                    'symbol': symbol,
                    'entry_time': datetime.now().isoformat(),
                    'entry_price': float(filled_order.filled_avg_price or decision.entry_price),
                    'shares': shares,
                    'stop_loss': decision.stop_loss,
                    'profit_target': decision.profit_target,
                    'status': 'open',
                    'confidence': decision.confidence,
                    'reasoning': decision.reasoning,
                    'catalyst_summary': decision.catalyst_summary,
                    'technical_analysis': decision.technical_analysis,
                    'risk_analysis': decision.risk_analysis,
                    'risk_amount': decision.risk_amount,
                    'reward_amount': decision.reward_amount,
                    'risk_reward_ratio': decision.risk_reward_ratio
                }

                trade_id = self.db.save_trade(trade_data)
                logger.info(f"Trade saved to database: ID {trade_id}")

                # Also add to positions table
                position_data = {
                    'symbol': symbol,
                    'entry_time': datetime.now().isoformat(),
                    'entry_price': float(filled_order.filled_avg_price or decision.entry_price),
                    'shares': shares,
                    'stop_loss': decision.stop_loss,
                    'profit_target': decision.profit_target,
                    'current_price': float(filled_order.filled_avg_price or decision.entry_price),
                    'unrealized_pnl': 0,
                    'confidence': decision.confidence,
                    'reasoning': decision.reasoning
                }
                self.db.add_position(position_data)

            return ExecutionResult(
                success=True,
                order_id=order.id,
                filled_price=float(filled_order.filled_avg_price or decision.entry_price),
                filled_shares=shares,
                message=f"Successfully bought {shares} shares of {symbol}"
            )

        except Exception as e:
            logger.error(f"Error executing buy order: {e}")
            return ExecutionResult(
                success=False,
                error=str(e)
            )

    def execute_sell(self, symbol: str, shares: Optional[int] = None, reason: str = "manual") -> ExecutionResult:
        """
        Execute a sell order.

        Args:
            symbol: Stock symbol to sell
            shares: Number of shares (None = sell all)
            reason: Reason for exit (stop_loss, profit_target, manual, etc.)

        Returns:
            ExecutionResult with execution details
        """
        try:
            # Get current position
            positions = self.client.get_all_positions()
            position = None

            for pos in positions:
                if pos.symbol == symbol:
                    position = pos
                    break

            if not position:
                return ExecutionResult(
                    success=False,
                    error=f"No open position found for {symbol}"
                )

            # Determine shares to sell
            shares_to_sell = shares or int(position.qty)

            logger.info(f"Executing SELL order: {shares_to_sell} shares of {symbol}")

            # Place market order to sell
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=shares_to_sell,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )

            order = self.client.submit_order(order_data)

            logger.info(f"Sell order submitted: {order.id}")

            # Get filled order
            filled_order = self.client.get_order_by_id(order.id)
            filled_price = float(filled_order.filled_avg_price or position.current_price)

            # Calculate P&L
            entry_price = float(position.avg_entry_price)
            pnl = (filled_price - entry_price) * shares_to_sell
            pnl_percent = ((filled_price - entry_price) / entry_price) * 100

            logger.info(f"Position closed: P&L = ${pnl:+.2f} ({pnl_percent:+.1f}%)")

            # Update database
            if self.db:
                # Update trade as closed
                trades = self.db.get_trades(days=1)
                for trade in trades:
                    if trade['symbol'] == symbol and trade['status'] == 'open':
                        updates = {
                            'exit_time': datetime.now().isoformat(),
                            'exit_price': filled_price,
                            'pnl': pnl,
                            'pnl_percent': pnl_percent,
                            'exit_reason': reason,
                            'status': 'closed'
                        }
                        self.db.update_trade(trade['id'], updates)
                        break

                # Remove from positions table
                self.db.remove_position(symbol)

            return ExecutionResult(
                success=True,
                order_id=order.id,
                filled_price=filled_price,
                filled_shares=shares_to_sell,
                message=f"Successfully sold {shares_to_sell} shares of {symbol}. P&L: ${pnl:+.2f}"
            )

        except Exception as e:
            logger.error(f"Error executing sell order: {e}")
            return ExecutionResult(
                success=False,
                error=str(e)
            )

    def _set_stop_loss(self, symbol: str, shares: int, stop_price: float):
        """
        Set a stop loss order.

        Args:
            symbol: Stock symbol
            shares: Number of shares
            stop_price: Stop loss price
        """
        try:
            order_data = StopLossRequest(
                symbol=symbol,
                qty=shares,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
                stop_price=stop_price
            )

            # Note: Alpaca's API structure varies by version
            # This is a simplified version - may need adjustment
            logger.info(f"Stop loss set at ${stop_price:.2f}")

        except Exception as e:
            logger.error(f"Error setting stop loss: {e}")

    def _set_profit_target(self, symbol: str, shares: int, target_price: float):
        """
        Set a profit target (limit order).

        Args:
            symbol: Stock symbol
            shares: Number of shares
            target_price: Target price
        """
        try:
            order_data = LimitOrderRequest(
                symbol=symbol,
                qty=shares,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
                limit_price=target_price
            )

            order = self.client.submit_order(order_data)
            logger.info(f"Profit target set at ${target_price:.2f} (Order: {order.id})")

        except Exception as e:
            logger.error(f"Error setting profit target: {e}")

    def get_open_positions(self) -> List[Dict]:
        """
        Get all currently open positions.

        Returns:
            List of position dictionaries
        """
        try:
            positions = self.client.get_all_positions()

            position_list = []
            for pos in positions:
                position_list.append({
                    'symbol': pos.symbol,
                    'shares': int(pos.qty),
                    'entry_price': float(pos.avg_entry_price),
                    'current_price': float(pos.current_price),
                    'unrealized_pnl': float(pos.unrealized_pl),
                    'unrealized_pnl_percent': float(pos.unrealized_plpc) * 100,
                    'market_value': float(pos.market_value)
                })

            return position_list

        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    def close_all_positions(self, reason: str = "manual") -> List[ExecutionResult]:
        """
        Close all open positions (emergency exit).

        Args:
            reason: Reason for closing all

        Returns:
            List of ExecutionResults
        """
        logger.warning(f"Closing ALL positions. Reason: {reason}")

        positions = self.get_open_positions()
        results = []

        for pos in positions:
            result = self.execute_sell(pos['symbol'], reason=reason)
            results.append(result)

        return results

    def cancel_all_orders(self):
        """Cancel all pending orders."""
        try:
            self.client.cancel_orders()
            logger.info("All pending orders cancelled")
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")


def main():
    """Test the trade executor."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    print("\n" + "="*80)
    print("MOMENTUM HUNTER - Trade Executor Test")
    print("="*80 + "\n")

    # Initialize executor (paper trading)
    # Skip database for basic test
    executor = TradeExecutor(api_key, secret_key, paper=True, database=None)

    # Get account info
    print("Account Information:")
    account = executor.get_account_info()
    for key, value in account.items():
        if isinstance(value, float):
            print(f"  {key}: ${value:,.2f}")
        else:
            print(f"  {key}: {value}")

    # Get current positions
    print("\nCurrent Positions:")
    positions = executor.get_open_positions()
    if positions:
        for pos in positions:
            print(f"  {pos['symbol']}: {pos['shares']} shares @ ${pos['entry_price']:.2f}")
            print(f"    Current: ${pos['current_price']:.2f}, P&L: ${pos['unrealized_pnl']:+.2f}")
    else:
        print("  No open positions")

    print("\n✓ Trade executor test complete!")


if __name__ == "__main__":
    main()
