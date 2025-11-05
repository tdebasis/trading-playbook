"""
Orchestrator - The main event loop that runs Momentum Hunter.

This is the heart of the system. It coordinates:
- Scanner (finds opportunities)
- News Aggregator (detects catalysts)
- Claude Brain (makes decisions)
- Executor (places trades)
- Position Manager (monitors trades)

Runs continuously during market hours, making Claude an autonomous trader.

Author: Claude AI + Tanam Bam Sinha
"""

import os
import time
from datetime import datetime, time as dt_time
from typing import Optional
import logging
from dotenv import load_dotenv

# Imports
from scanner.market_scanner import MomentumScanner
from scanner.news_aggregator import NewsAggregator
from brain.claude_engine import ClaudeTrader
from execution.trade_executor import TradeExecutor
from execution.position_manager import PositionManager
from data.database import TradingDatabase

from alpaca.data.historical import StockHistoricalDataClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MomentumHunter:
    """
    The autonomous AI trading system.

    This orchestrator runs the complete trading loop:
    1. Scan for momentum candidates
    2. Analyze catalysts
    3. Claude makes decision
    4. Execute trades
    5. Monitor positions
    6. Repeat
    """

    def __init__(
        self,
        alpaca_api_key: str,
        alpaca_secret_key: str,
        anthropic_api_key: str,
        paper_trading: bool = True,
        account_size: float = 100000,
        db_path: str = "momentum_hunter.db"
    ):
        """
        Initialize Momentum Hunter.

        Args:
            alpaca_api_key: Alpaca API key
            alpaca_secret_key: Alpaca secret key
            anthropic_api_key: Anthropic Claude API key
            paper_trading: Use paper trading (True) or live (False)
            account_size: Total account value
            db_path: Path to SQLite database
        """
        logger.info("="*80)
        logger.info("MOMENTUM HUNTER - Initializing")
        logger.info("="*80)

        # Initialize components
        logger.info("Initializing Market Scanner...")
        self.scanner = MomentumScanner(alpaca_api_key, alpaca_secret_key)

        logger.info("Initializing News Aggregator...")
        self.news = NewsAggregator(alpaca_api_key, alpaca_secret_key)

        logger.info("Initializing Claude Decision Engine...")
        self.claude = ClaudeTrader(anthropic_api_key, account_size=account_size)

        logger.info("Initializing Database...")
        self.db = TradingDatabase(db_path)

        logger.info("Initializing Trade Executor...")
        self.executor = TradeExecutor(
            alpaca_api_key,
            alpaca_secret_key,
            paper=paper_trading,
            database=self.db
        )

        logger.info("Initializing Data Client...")
        self.data_client = StockHistoricalDataClient(alpaca_api_key, alpaca_secret_key)

        logger.info("Initializing Position Manager...")
        self.position_manager = PositionManager(
            self.executor,
            self.data_client,
            database=self.db
        )

        # Configuration
        self.paper_trading = paper_trading
        self.account_size = account_size
        self.scan_interval = 300  # 5 minutes
        self.position_check_interval = 30  # 30 seconds

        # State
        self.running = False
        self.daily_pnl = 0
        self.trades_today = 0
        self.last_scan_time = None
        self.last_position_check = None

        mode = "PAPER" if paper_trading else "LIVE"
        logger.info(f"Momentum Hunter initialized successfully ({mode} mode)")
        logger.info("="*80)

    def is_market_open(self) -> bool:
        """Check if market is currently open."""
        now = datetime.now()

        # Market hours: 9:30 AM - 4:00 PM EST (TODO: handle holidays)
        market_open = dt_time(9, 30)
        market_close = dt_time(16, 0)

        # Check if weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        current_time = now.time()
        return market_open <= current_time <= market_close

    def is_trading_window(self) -> bool:
        """Check if we're in our preferred trading window (9:30 AM - 11:30 AM)."""
        now = datetime.now().time()
        trading_start = dt_time(9, 30)
        trading_end = dt_time(11, 30)
        return trading_start <= now <= trading_end

    def should_scan(self) -> bool:
        """Check if it's time to scan for new opportunities."""
        if not self.last_scan_time:
            return True

        elapsed = (datetime.now() - self.last_scan_time).total_seconds()
        return elapsed >= self.scan_interval

    def should_check_positions(self) -> bool:
        """Check if it's time to monitor positions."""
        if not self.last_position_check:
            return True

        elapsed = (datetime.now() - self.last_position_check).total_seconds()
        return elapsed >= self.position_check_interval

    def scan_and_decide(self):
        """
        Main trading logic: Scan → Analyze → Decide → Execute
        """
        logger.info("\n" + "="*80)
        logger.info("SCANNING FOR OPPORTUNITIES")
        logger.info("="*80)

        # Step 1: Scan for momentum candidates
        candidates = self.scanner.scan()

        if not candidates:
            logger.info("No momentum candidates found.")
            return

        logger.info(f"Found {len(candidates)} momentum candidates")

        # Step 2: Analyze catalysts for top candidates
        catalysts = {}
        for candidate in candidates[:5]:  # Top 5 only
            logger.info(f"Analyzing catalyst for {candidate.symbol}...")
            catalyst = self.news.analyze_catalyst(candidate.symbol)
            if catalyst:
                catalysts[candidate.symbol] = catalyst
                logger.info(f"  ✓ {catalyst.catalyst_type} catalyst detected (strength: {catalyst.catalyst_strength:.1f}/10)")
            else:
                logger.info(f"  - No significant catalyst")

        # Step 3: Ask Claude to make a decision
        logger.info("\n" + "="*80)
        logger.info("CLAUDE ANALYZING...")
        logger.info("="*80)

        decision = self.claude.make_decision(candidates, catalysts)

        # Log decision to database
        decision_data = {
            'timestamp': datetime.now().isoformat(),
            'action': decision.action,
            'symbol': decision.symbol,
            'confidence': decision.confidence,
            'reasoning': decision.reasoning,
            'candidates_analyzed': [c.symbol for c in candidates],
            'account_state': {
                'daily_pnl': self.daily_pnl,
                'trades_today': self.trades_today,
                'positions': self.position_manager.get_position_count()
            }
        }
        self.db.save_decision(decision_data)

        # Step 4: Execute decision
        if decision.action == "BUY":
            logger.info("\n" + "="*80)
            logger.info(f"CLAUDE DECISION: BUY {decision.symbol}")
            logger.info("="*80)
            logger.info(f"Confidence: {decision.confidence}/10")
            logger.info(f"Entry: ${decision.entry_price:.2f}")
            logger.info(f"Stop: ${decision.stop_loss:.2f}")
            logger.info(f"Target: ${decision.profit_target:.2f}")
            logger.info(f"R/R: {decision.risk_reward_ratio:.2f}:1")
            logger.info(f"\nReasoning: {decision.reasoning}")

            # Validate decision
            is_valid, reason = self.claude.validate_decision(decision)

            if is_valid:
                logger.info(f"\n✅ Validation passed: {reason}")
                logger.info("Executing trade...")

                result = self.executor.execute_buy(decision)

                if result.success:
                    logger.info(f"✅ {result.message}")
                    self.trades_today += 1
                else:
                    logger.error(f"❌ Trade execution failed: {result.error}")
            else:
                logger.warning(f"❌ Validation failed: {reason}")
                logger.info("Trade NOT executed")

        elif decision.action == "HOLD":
            logger.info(f"\nClaude Decision: HOLD")
            logger.info(f"Reasoning: {decision.reasoning}")

        elif decision.action == "CLOSE":
            logger.info(f"\nClaude Decision: CLOSE {decision.symbol}")
            logger.info(f"Reasoning: {decision.reasoning}")
            # TODO: Implement position closing logic

    def monitor_positions(self):
        """Monitor open positions and check for exits."""
        if self.position_manager.get_position_count() == 0:
            return

        result = self.position_manager.monitor_once()

        # Log any exits
        if result['exits']:
            for exit in result['exits']:
                logger.info(f"\n{'='*80}")
                logger.info(f"POSITION CLOSED: {exit['symbol']}")
                logger.info(f"{'='*80}")
                logger.info(f"Reason: {exit['reason']}")
                logger.info(f"Exit Price: ${exit['price']:.2f}")
                logger.info(f"P&L: ${exit['pnl']:+,.2f}")

                # Update daily P&L
                self.daily_pnl += exit['pnl']

    def end_of_day_cleanup(self):
        """Close all positions and prepare for next day."""
        logger.info("\n" + "="*80)
        logger.info("END OF DAY - Closing all positions")
        logger.info("="*80)

        exits = self.position_manager.close_all_at_eod()

        # Update daily P&L
        for exit in exits:
            self.daily_pnl += exit['pnl']
            logger.info(f"Closed {exit['symbol']}: ${exit['pnl']:+,.2f}")

        # Log daily summary
        logger.info("\n" + "="*80)
        logger.info("DAILY SUMMARY")
        logger.info("="*80)
        logger.info(f"Trades Today: {self.trades_today}")
        logger.info(f"Total P&L: ${self.daily_pnl:+,.2f}")
        logger.info(f"Account Value: ${self.account_size + self.daily_pnl:,.2f}")

        # Reset for next day
        self.trades_today = 0
        self.daily_pnl = 0

    def run(self):
        """
        Main run loop - runs continuously during market hours.
        """
        logger.info("\n" + "="*80)
        logger.info("MOMENTUM HUNTER - STARTING")
        logger.info("="*80)

        self.running = True

        try:
            while self.running:
                # Check if market is open
                if not self.is_market_open():
                    logger.info("Market is closed. Waiting...")
                    time.sleep(60)  # Check every minute
                    continue

                current_time = datetime.now()

                # Check for end of day
                if current_time.time() >= dt_time(15, 45):
                    self.end_of_day_cleanup()
                    logger.info("Trading day complete. System going idle.")
                    self.running = False
                    break

                # Scan for new opportunities (every 5 minutes during trading window)
                if self.is_trading_window() and self.should_scan():
                    self.scan_and_decide()
                    self.last_scan_time = datetime.now()

                # Monitor positions (every 30 seconds)
                if self.should_check_positions():
                    self.monitor_positions()
                    self.last_position_check = datetime.now()

                # Small sleep to prevent tight loop
                time.sleep(5)

        except KeyboardInterrupt:
            logger.info("\n\nShutdown requested by user...")
            self.shutdown()

        except Exception as e:
            logger.error(f"\n\nFATAL ERROR: {e}")
            logger.error("Emergency shutdown initiated...")
            self.shutdown(emergency=True)

    def shutdown(self, emergency: bool = False):
        """
        Graceful shutdown.

        Args:
            emergency: If True, close all positions immediately
        """
        logger.info("\n" + "="*80)
        logger.info("MOMENTUM HUNTER - SHUTTING DOWN")
        logger.info("="*80)

        self.running = False

        if emergency:
            logger.warning("EMERGENCY SHUTDOWN - Closing all positions")
            self.position_manager.emergency_exit_all("emergency_shutdown")

        # Final summary
        logger.info(f"\nFinal Account Value: ${self.account_size + self.daily_pnl:,.2f}")
        logger.info(f"Today's P&L: ${self.daily_pnl:+,.2f}")
        logger.info(f"Trades Today: {self.trades_today}")

        # Close database
        self.db.close()

        logger.info("\nShutdown complete. Stay profitable! 🚀")


def main():
    """Run Momentum Hunter."""
    load_dotenv()

    # Get API keys from environment
    alpaca_key = os.getenv('ALPACA_API_KEY')
    alpaca_secret = os.getenv('ALPACA_SECRET_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    if not all([alpaca_key, alpaca_secret, anthropic_key]):
        logger.error("Missing API keys! Check your .env file.")
        return

    # Create and run the system
    hunter = MomentumHunter(
        alpaca_api_key=alpaca_key,
        alpaca_secret_key=alpaca_secret,
        anthropic_api_key=anthropic_key,
        paper_trading=True,  # ALWAYS start with paper trading!
        account_size=100000,  # $100k paper account
        db_path="momentum_hunter.db"
    )

    # Start the trading loop
    hunter.run()


if __name__ == "__main__":
    main()
