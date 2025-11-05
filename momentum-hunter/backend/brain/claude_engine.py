"""
Claude Decision Engine - The AI brain that makes trading decisions.

This is the core intelligence of Momentum Hunter. Claude analyzes:
- Market conditions
- News catalysts
- Technical setups
- Risk/reward
- Historical patterns

...and makes the final call: BUY, SELL, or HOLD.

Author: Claude AI + Tanam Bam Sinha
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json
import logging
import anthropic

from scanner.market_scanner import MomentumCandidate
from scanner.news_aggregator import CatalystAnalysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TradeDecision:
    """A trading decision made by Claude."""

    # Action
    action: str  # "BUY", "SELL", "HOLD", "CLOSE"
    confidence: float  # 0-10, how confident am I?

    # If BUY action
    symbol: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    profit_target: Optional[float] = None
    position_size_shares: Optional[int] = None
    position_size_percent: Optional[float] = None  # % of account

    # Rationale
    reasoning: str = ""
    catalyst_summary: str = ""
    technical_analysis: str = ""
    risk_analysis: str = ""

    # Metadata
    timestamp: datetime = None

    # Risk metrics
    risk_amount: Optional[float] = None  # $ at risk
    reward_amount: Optional[float] = None  # $ potential gain
    risk_reward_ratio: Optional[float] = None  # Reward/Risk

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

        # Calculate risk/reward if we have the data
        if self.entry_price and self.stop_loss and self.profit_target:
            self.risk_amount = abs(self.entry_price - self.stop_loss)
            self.reward_amount = abs(self.profit_target - self.entry_price)
            if self.risk_amount > 0:
                self.risk_reward_ratio = self.reward_amount / self.risk_amount

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def __str__(self):
        if self.action == "BUY":
            return (
                f"BUY {self.symbol} @ ${self.entry_price:.2f}\n"
                f"  Stop: ${self.stop_loss:.2f}, Target: ${self.profit_target:.2f}\n"
                f"  R/R: {self.risk_reward_ratio:.2f}:1, Confidence: {self.confidence}/10\n"
                f"  Reasoning: {self.reasoning[:100]}..."
            )
        else:
            return f"{self.action}: {self.reasoning}"


class ClaudeTrader:
    """
    The AI trading brain powered by Claude.
    """

    def __init__(self, anthropic_api_key: str, account_size: float = 10000):
        """
        Initialize Claude trading engine.

        Args:
            anthropic_api_key: Anthropic API key
            account_size: Total account value
        """
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.account_size = account_size
        self.model = "claude-sonnet-4-5-20250929"

        # Trading state
        self.current_positions = {}
        self.daily_pnl = 0
        self.trade_count_today = 0

        # Risk limits
        self.max_risk_per_trade = 0.02  # 2% max risk per trade
        self.max_position_size = 0.25   # 25% max per position
        self.max_daily_loss = 500       # $500 max daily loss
        self.max_positions = 3          # Max simultaneous positions

        logger.info(f"Claude Trader initialized with ${account_size:,.2f} account")

    def build_context(
        self,
        candidates: List[MomentumCandidate],
        catalysts: Dict[str, CatalystAnalysis],
        market_conditions: Optional[Dict] = None
    ) -> str:
        """
        Build comprehensive context for Claude to analyze.

        Args:
            candidates: List of momentum candidates from scanner
            catalysts: Dict mapping symbol -> catalyst analysis
            market_conditions: Optional market-wide conditions

        Returns:
            Formatted context string
        """
        context = f"""You are an elite day trader AI making real-time trading decisions.

CURRENT TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}

ACCOUNT STATUS:
- Total Account Value: ${self.account_size:,.2f}
- Available Cash: ${self.account_size - sum(p.get('value', 0) for p in self.current_positions.values()):,.2f}
- Current Positions: {len(self.current_positions)}/{self.max_positions}
- Today's P&L: ${self.daily_pnl:+,.2f}
- Trades Today: {self.trade_count_today}
- Daily Loss Limit Remaining: ${self.max_daily_loss + self.daily_pnl if self.daily_pnl < 0 else self.max_daily_loss:.2f}

CURRENT POSITIONS:
"""
        if self.current_positions:
            for symbol, pos in self.current_positions.items():
                context += f"  {symbol}: {pos.get('shares', 0)} shares @ ${pos.get('entry', 0):.2f}\n"
        else:
            context += "  None\n"

        context += f"\n{'='*80}\n"
        context += "MOMENTUM CANDIDATES (from scanner):\n"
        context += f"{'='*80}\n\n"

        for i, candidate in enumerate(candidates[:5], 1):
            context += f"{i}. {candidate.symbol}:\n"
            context += f"   Price: ${candidate.current_price:.2f} ({candidate.percent_change:+.1f}%)\n"
            context += f"   Volume: {candidate.volume:,} ({candidate.relative_volume:.1f}x average)\n"
            context += f"   Gap: {candidate.gap_percent:+.1f}% from previous close\n"
            context += f"   VWAP: {candidate.price_vs_vwap:+.1f}% vs current price\n"
            context += f"   Scanner Score: {candidate.score():.1f}/10\n"

            # Add catalyst info if available
            if candidate.symbol in catalysts:
                catalyst = catalysts[candidate.symbol]
                context += f"   \n"
                context += f"   🎯 CATALYST DETECTED:\n"
                context += f"   Type: {catalyst.catalyst_type}\n"
                context += f"   Strength: {catalyst.catalyst_strength:.1f}/10\n"
                context += f"   Sentiment: {catalyst.sentiment.upper()}\n"
                context += f"   News: {catalyst.headline_summary}\n"
            else:
                context += f"   ⚠️  No major catalyst detected\n"

            context += "\n"

        context += f"\n{'='*80}\n"
        context += "YOUR TASK:\n"
        context += f"{'='*80}\n\n"
        context += """Analyze these opportunities and decide:

Should we enter a trade right now? If yes, which one and why?

Consider:
1. MOMENTUM STRENGTH: High relative volume (3x+) + significant price movement (5%+)
2. TIMING: Is this early in the move or are we late to the party?
3. TECHNICAL SETUP: Is there a clear entry point? Bull flag? Breakout?
4. RISK/REWARD: Can we get 2:1 or better?
5. CATALYST CONTEXT: If news exists, is it positive/negative? No news = neutral (acceptable)
6. POSITION SIZING: How much capital to deploy?

MOMENTUM TRADING RULES (you MUST follow):
- PRIMARY SIGNAL: Momentum detected by scanner (2x+ volume, 3%+ price movement)
- NEWS AS FILTER: Avoid stocks with negative catalysts (earnings miss, FDA rejection, scandal)
- NO NEWS = GREEN LIGHT: Pure technical setups without news are acceptable
- If scanner detected breakout, TRUST IT - scanner already filtered for momentum
- Entry timing: Early in move is GOOD (we want to catch the momentum, not wait until it's over)
- Minimum 2:1 reward/risk ratio
- Stop loss ALWAYS set (no exceptions)
- Max 2% account risk per trade
- Scanner score 2+ is acceptable for trades (scanner already did the filtering)
- Volume 2x+ is acceptable (don't require 3x+ or 5x+)
- Price movement 3%+ is acceptable (don't require 5%+)

Respond in this EXACT JSON format:
{
    "action": "BUY" | "HOLD" | "CLOSE",
    "confidence": 0-10,
    "symbol": "TICKER" (if BUY),
    "entry_price": 0.00 (if BUY),
    "stop_loss": 0.00 (if BUY),
    "profit_target": 0.00 (if BUY),
    "position_size_percent": 0.10 (10% of account, if BUY),
    "reasoning": "Clear explanation of why you're taking this action",
    "catalyst_summary": "Brief summary of the catalyst driving this",
    "technical_analysis": "What's the technical setup? Entry trigger?",
    "risk_analysis": "What could go wrong? Where's our stop?"
}

If no trades meet criteria, return action: "HOLD" with reasoning explaining why you're passing on these setups.

Be SELECTIVE. Quality over quantity. We'd rather make 1 great trade than 5 mediocre ones.
"""

        return context

    def make_decision(
        self,
        candidates: List[MomentumCandidate],
        catalysts: Dict[str, CatalystAnalysis]
    ) -> TradeDecision:
        """
        Make a trading decision using Claude AI.

        Args:
            candidates: Momentum candidates from scanner
            catalysts: Catalyst analysis for each candidate

        Returns:
            TradeDecision object
        """
        logger.info("Claude analyzing opportunities...")

        # Build context
        context = self.build_context(candidates, catalysts)

        # Call Claude API
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.3,  # Lower temp for more focused decisions
                messages=[{
                    "role": "user",
                    "content": context
                }]
            )

            # Parse response
            response_text = message.content[0].text

            # Extract JSON from response
            # Claude might include explanation before/after JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                logger.error("No JSON found in Claude's response")
                return TradeDecision(
                    action="HOLD",
                    confidence=0,
                    reasoning="Error: Could not parse decision from Claude"
                )

            json_str = response_text[json_start:json_end]
            decision_data = json.loads(json_str)

            # Create TradeDecision object
            decision = TradeDecision(
                action=decision_data.get('action', 'HOLD'),
                confidence=decision_data.get('confidence', 0),
                symbol=decision_data.get('symbol'),
                entry_price=decision_data.get('entry_price'),
                stop_loss=decision_data.get('stop_loss'),
                profit_target=decision_data.get('profit_target'),
                position_size_percent=decision_data.get('position_size_percent'),
                reasoning=decision_data.get('reasoning', ''),
                catalyst_summary=decision_data.get('catalyst_summary', ''),
                technical_analysis=decision_data.get('technical_analysis', ''),
                risk_analysis=decision_data.get('risk_analysis', '')
            )

            # Calculate position size in shares
            if decision.action == "BUY" and decision.entry_price:
                position_value = self.account_size * decision.position_size_percent
                decision.position_size_shares = int(position_value / decision.entry_price)

            logger.info(f"Claude decision: {decision.action} (confidence: {decision.confidence}/10)")

            if decision.action == "BUY":
                logger.info(f"  Symbol: {decision.symbol}")
                logger.info(f"  Entry: ${decision.entry_price:.2f}")
                logger.info(f"  Stop: ${decision.stop_loss:.2f}")
                logger.info(f"  Target: ${decision.profit_target:.2f}")
                logger.info(f"  R/R: {decision.risk_reward_ratio:.2f}:1")
                logger.info(f"  Reasoning: {decision.reasoning[:100]}...")
            else:
                # Log reasoning for HOLD/CLOSE too
                logger.info(f"  Reasoning: {decision.reasoning[:200]}...")

            return decision

        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return TradeDecision(
                action="HOLD",
                confidence=0,
                reasoning=f"Error calling Claude API: {str(e)}"
            )

    def validate_decision(self, decision: TradeDecision) -> tuple[bool, str]:
        """
        Validate that decision meets risk management rules.

        Args:
            decision: TradeDecision to validate

        Returns:
            (is_valid, reason) tuple
        """
        if decision.action != "BUY":
            return True, "Not a buy decision"

        # Check position limit
        if len(self.current_positions) >= self.max_positions:
            return False, f"Already at max positions ({self.max_positions})"

        # Check daily loss limit
        if self.daily_pnl < -self.max_daily_loss:
            return False, f"Daily loss limit exceeded (${self.daily_pnl:.2f})"

        # Check risk/reward ratio
        if decision.risk_reward_ratio and decision.risk_reward_ratio < 2.0:
            return False, f"R/R too low: {decision.risk_reward_ratio:.2f}:1 (need 2:1)"

        # Check position size
        if decision.position_size_percent and decision.position_size_percent > self.max_position_size:
            return False, f"Position too large: {decision.position_size_percent*100:.1f}% (max {self.max_position_size*100:.0f}%)"

        # Check risk amount
        if decision.risk_amount:
            max_risk_dollars = self.account_size * self.max_risk_per_trade
            actual_risk = decision.risk_amount * decision.position_size_shares
            if actual_risk > max_risk_dollars:
                return False, f"Risk too high: ${actual_risk:.2f} (max ${max_risk_dollars:.2f})"

        return True, "All validations passed"


def main():
    """Test the Claude decision engine."""
    import os
    from dotenv import load_dotenv
    from scanner.market_scanner import MomentumScanner
    from scanner.news_aggregator import NewsAggregator

    load_dotenv()

    alpaca_key = os.getenv('ALPACA_API_KEY')
    alpaca_secret = os.getenv('ALPACA_SECRET_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    print("\n" + "="*80)
    print("MOMENTUM HUNTER - Claude Decision Engine Test")
    print("="*80 + "\n")

    # Initialize components
    scanner = MomentumScanner(alpaca_key, alpaca_secret)
    news = NewsAggregator(alpaca_key, alpaca_secret)
    claude = ClaudeTrader(anthropic_key, account_size=10000)

    # Scan for candidates
    print("Scanning market for momentum...")
    candidates = scanner.scan()

    if not candidates:
        print("No candidates found. Market might be closed or no movers today.")
        return

    # Get catalysts for top candidates
    print(f"\nAnalyzing catalysts for top {len(candidates)} candidates...")
    catalysts = {}
    for candidate in candidates[:5]:
        catalyst = news.analyze_catalyst(candidate.symbol)
        if catalyst:
            catalysts[candidate.symbol] = catalyst
            print(f"  ✓ {candidate.symbol}: {catalyst.catalyst_type} catalyst detected")

    # Ask Claude to make a decision
    print("\n" + "="*80)
    print("ASKING CLAUDE TO MAKE TRADING DECISION...")
    print("="*80 + "\n")

    decision = claude.make_decision(candidates, catalysts)

    print("\n" + "="*80)
    print("CLAUDE'S DECISION")
    print("="*80 + "\n")
    print(decision)
    print()

    # Validate
    is_valid, reason = claude.validate_decision(decision)
    print(f"Risk Management Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
    print(f"Reason: {reason}\n")


if __name__ == "__main__":
    main()
