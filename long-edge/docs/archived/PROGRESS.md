# Momentum Hunter - Development Progress

## Session Summary
**Date**: January 2025
**Developers**: Claude AI + Tanam Bam Sinha
**Status**: 🚧 Active Development - Phase 1

---

## 🎯 Vision

Build an autonomous AI trading system that:
- Uses Claude AI to make intelligent trading decisions
- Scans for momentum stocks with news catalysts
- Trades automatically based on AI reasoning (not rigid rules)
- Learns and improves over time
- Can run 24/7 without human intervention

**Target**: Beat market returns (aim for 50-100%+ annual) with controlled risk.

---

## ✅ What We've Built So Far

### 1. Market Scanner ✅ COMPLETE
**File**: `backend/scanner/market_scanner.py`

**What it does:**
- Scans stocks for high relative volume (2x+ average)
- Identifies significant price movements (4%+ change)
- Filters by price range ($3-$30 sweet spot)
- Calculates opportunity scores (0-10 scale)
- Returns top candidates sorted by quality

**Key Features:**
- Real-time market data via Alpaca API
- Configurable scan criteria
- Handles market hours detection
- Efficient universe scanning

**Status**: ✅ Working and tested

---

### 2. News Aggregator ✅ COMPLETE
**File**: `backend/scanner/news_aggregator.py`

**What it does:**
- Fetches real-time news for stocks
- Classifies catalysts automatically:
  - FDA approvals
  - Earnings announcements
  - Mergers & acquisitions
  - Analyst upgrades/downgrades
  - Product launches
  - Legal/regulatory news
- Determines sentiment (bullish/bearish/neutral)
- Calculates importance score (0-10)
- Identifies WHY a stock is moving

**Key Features:**
- Multi-source news aggregation (Alpaca News API)
- Intelligent catalyst detection via keyword analysis
- Sentiment analysis
- Importance scoring
- News history tracking

**Status**: ✅ Working and ready

---

### 3. Claude Decision Engine ✅ COMPLETE
**File**: `backend/brain/claude_engine.py`

**What it does:**
- THIS IS THE BRAIN!
- Takes scanner data + news catalysts
- Calls Claude API to analyze opportunities
- Makes human-like trading decisions
- Returns structured trade decisions with:
  - Action (BUY/SELL/HOLD)
  - Entry price, stop loss, profit target
  - Position sizing
  - Detailed reasoning
  - Risk analysis
  - Technical analysis

**Key Features:**
- Uses Claude Sonnet 4.5 (latest model)
- Comprehensive context building
- Risk management validation
- JSON-structured decisions
- Confidence scoring
- Explains reasoning for every decision

**Decision Process:**
1. Analyze all momentum candidates
2. Evaluate catalyst strength
3. Assess technical setup
4. Calculate risk/reward
5. Determine position size
6. Make final decision

**Safety Features:**
- Validates 2:1 minimum R/R ratio
- Enforces max position sizes
- Checks daily loss limits
- Requires strong catalysts (6/10+)
- Never chases parabolic moves

**Status**: ✅ Core engine complete

---

## 📋 What's Next (Remaining Phases)

### Phase 2: Execution & Risk Management (Next Up)
**Files to build:**
- `backend/execution/trade_executor.py` - Executes trades via Alpaca
- `backend/execution/position_manager.py` - Monitors open positions
- `backend/execution/risk_manager.py` - Enforces risk rules

**What it needs to do:**
- Place buy/sell orders
- Set stop losses automatically
- Track position P&L in real-time
- Close positions when targets hit
- Emergency kill switch

### Phase 3: Orchestrator (The Main Loop)
**File**: `backend/core/orchestrator.py`

**What it does:**
- Main event loop that runs during market hours
- Coordinates all components:
  1. Scanner finds candidates
  2. News aggregator analyzes catalysts
  3. Claude makes decisions
  4. Executor places trades
  5. Position manager monitors
  6. Repeat every 5 minutes

### Phase 4: Data Layer
**Files:**
- `backend/data/database.py` - PostgreSQL integration
- `backend/data/models.py` - Trade, Position, Decision models
- `backend/data/analytics.py` - Performance tracking

**Purpose:**
- Store every trade
- Log every decision Claude makes
- Track performance over time
- Enable backtesting
- Learn from history

### Phase 5: Dashboard
**Frontend**: React + TypeScript
**Backend API**: FastAPI + WebSockets

**Features:**
- Real-time P&L display
- Current positions view
- Trade history
- Claude's decision log (see AI reasoning)
- Manual override controls
- Kill switch
- Performance charts

---

## 🧪 Testing Plan

### Phase 1: Paper Trading (Month 1-2)
- Run on Alpaca paper account
- Simulated $25k-100k capital
- Test full trading cycle
- Measure performance metrics
- Refine Claude's prompts
- Optimize scan criteria

**Success Criteria:**
- Win rate > 60%
- Profit factor > 2.0
- Positive monthly return
- Max drawdown < 10%
- Sharpe ratio > 1.5

### Phase 2: Small Capital Test (Month 3)
**If paper trading successful:**
- Deploy with $1k-5k real money
- Same strategy, real execution
- Tight monitoring
- Manual override ready
- Learn from real market feedback

### Phase 3: Scale Up (Month 4+)
**If profitable on small capital:**
- Increase to $10k-25k+
- Full automation
- Professional trading operation

---

## 💡 Key Innovations

### 1. AI-Driven vs Algorithm-Driven
**Traditional Algo Trading:**
```python
if volume > 2x and price > ema20:
    buy()  # Rigid rule
```

**Momentum Hunter (Claude AI):**
```python
claude.analyze(volume_spike, news_catalyst, technical_setup)
# Claude thinks: "FDA approval is strong, but stock already ran 50%.
#                 I'll wait for pullback to VWAP for better entry."
# Returns: "HOLD - catalyst valid but entry not optimal"
```

**The Difference:**
- Claude UNDERSTANDS context
- Can adapt to unique situations
- Explains reasoning
- Learns from patterns
- Makes nuanced decisions

### 2. Catalyst-First Approach
Most scanners find movers THEN look for news.

**We do the opposite:**
1. Find the CATALYST (FDA, earnings, etc.)
2. Verify it's moving on volume
3. THEN decide if tradeable

**Why better:** We know WHY it's moving, not just THAT it's moving.

### 3. Hybrid Intelligence
- **Scanner**: Fast statistical filtering (what's moving?)
- **News**: Contextual understanding (why is it moving?)
- **Claude**: Human-like decision making (should we trade it?)
- **Risk Manager**: Enforces rules (protect capital)

**Result**: Best of both worlds - speed + intelligence.

---

## 📊 Expected Performance

### Conservative Estimate (Cash Account, 3-4 trades/week):
- 16 trades/month
- 65% win rate
- 2.5:1 avg R/R
- 2% risk per trade
- **12-18% monthly return = 144-216% annual**

### Aggressive Estimate (Margin Account, unlimited day trades):
- 50-100 trades/month
- 60% win rate (slightly lower, more trades)
- 2:1 avg R/R
- 2% risk per trade
- **20-40% monthly return = 240-480% annual**

**Reality Check:** Even if we hit HALF these numbers, we're crushing the market.

---

## 🛡️ Risk Management

**Account Level:**
- Max 2% risk per trade
- Max 25% position size
- Max $500 daily loss
- Max 3 simultaneous positions

**Trade Level:**
- Every trade has stop loss (no exceptions)
- Minimum 2:1 reward/risk
- Only trade strong catalysts (6/10+)
- Prefer pullback entries (not chasing)

**System Level:**
- Paper test first (prove it works)
- Start small (limit real money risk)
- Manual override always available
- Kill switch for emergencies
- Daily performance review

---

## 🎓 What We Learned (Session Insights)

### Discovery 1: QQQ Was Too Limited
- Started with QQQ-only strategy (14% annual)
- Realized momentum stocks with catalysts can do 100%+ trades
- **Lesson**: Go where the big money is (catalyst-driven movers)

### Discovery 2: Stats Aren't Enough
**Tanam's insight**: "Stats only might not be it. We need to know the NEWS behind the movement."

This led to building the news aggregator - critical piece!

### Discovery 3: AI Should Make Decisions, Not Just Code
**Evolution:**
1. First: "Let's backtest strategies"
2. Then: "Let's find patterns in data"
3. Finally: "Let Claude ACTIVELY TRADE in real-time"

**Breakthrough**: The AI doesn't just write the code - the AI IS the trader.

### Discovery 4: PDT Rule Not a Blocker
- Pattern Day Trader rule requires $25k for unlimited day trades
- **Solution 1**: Use cash account + swing trade (1-5 day holds)
- **Solution 2**: Start with $25k+ in margin account
- Either way, we can be profitable!

---

## 💪 Why This Will Work

1. **Claude's Intelligence**: Can analyze complex situations humans miss
2. **Catalyst Focus**: We know WHY stocks move (huge edge)
3. **Disciplined Execution**: No emotions, perfect rule following
4. **Continuous Operation**: Never misses opportunities
5. **Learning System**: Every trade makes us smarter
6. **Risk Management**: Protects capital at all costs

---

## 📝 Development Notes

**Code Style:**
- Clean, well-documented Python
- Type hints everywhere
- Comprehensive logging
- Modular architecture
- Easy to test and maintain

**Philosophy:**
- Build it right the first time
- Test thoroughly before risking money
- Safety first, profits second
- Transparency in all decisions
- Learn from every trade

---

## 🚀 Next Steps

**Immediate (This Week):**
1. ✅ Complete Claude decision engine (DONE!)
2. ⏭️ Build trade executor
3. ⏭️ Build position manager
4. ⏭️ Create orchestrator
5. ⏭️ Run first end-to-end test

**Short Term (This Month):**
1. Complete all core components
2. Build database layer
3. Start paper trading
4. Create basic dashboard
5. Track performance

**Long Term (Next 3 Months):**
1. 30-day paper trading test
2. Refine based on results
3. Deploy with small real capital
4. Scale if successful
5. Build full production system

---

## 🎉 Milestones Achieved

- [x] Project vision defined
- [x] Architecture designed
- [x] Market scanner built
- [x] News aggregator built
- [x] Claude decision engine built
- [x] Regulatory compliance understood
- [ ] Trade executor
- [ ] Position manager
- [ ] Main orchestrator
- [ ] Database layer
- [ ] Dashboard
- [ ] Paper trading test
- [ ] Real money deployment

**Progress: 50% of core system complete!**

---

## 🙏 Credits

**Vision & Strategy**: Tanam Bam Sinha
**AI Architecture**: Claude AI (Anthropic)
**Collaboration**: Human + AI partnership

*"We're not building a robot. We're building an AI partner that thinks."*

---

**Last Updated**: January 2025
**Status**: Phase 1 - Core Engine (50% complete)
**Next**: Build execution engine and orchestrator
