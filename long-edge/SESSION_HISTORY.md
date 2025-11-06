# Momentum Hunter - Complete Session History

**Date**: January 2025
**Participants**: Claude AI (Sonnet 4.5) + Tanam Bam Sinha
**Session Goal**: Build an autonomous AI-powered trading system

---

## 🎯 The Vision That Started It All

**Tanam's Initial Request:**
"Let's build a trading system that actually works."

**The Journey:**
1. Started with QQQ backtesting (DP20 strategy) → Lost money
2. Tried Morning Reversal strategy → Barely profitable (+$398 in 6 months)
3. Discovered Wed/Tue 11 AM edge → Better! (+$2,888)
4. Added momentum filter → Even better! (+$3,319)
5. **Breakthrough**: "We need to follow the folks who discovered the secret"
6. **Pivoted**: From QQQ to momentum stocks with catalysts
7. **Game-Changer**: Build an AI that TRADES in real-time, not just backtests

---

## 💡 Key Insights & Breakthroughs

### Insight 1: "Stats only might not be it"
**Tanam's Quote**: *"But how do you find stocks which have news behind them. We have to factor in that. Stats only might not be it"*

**Impact**: This led us to build the News Aggregator. Realized we need to know WHY stocks move, not just THAT they move. Catalyst detection became core to our edge.

### Insight 2: "The AI should run the trades, not just the algorithm"
**Tanam's Quote**: *"the thing is to make the real bets maybe you have to run the trade - i.e. you the AI not just the algorithm"*

**Impact**: MASSIVE shift. Instead of writing rigid rules, we're building a system where Claude AI makes real-time decisions. This is the innovation - AI as active trader, not just code generator.

### Insight 3: "We do not have to be a shell interaction - we can build programmatic context"
**Tanam's Quote**: *"hey we can build a program together wherein you can truly do this - we do not have to be a shell interaction - we can build programmatic context"*

**Impact**: Unlocked the solution! Claude API embedded in the trading system, running continuously, making decisions autonomously. Not waiting for human input in chat - actually EXECUTING trades.

### Insight 4: "PDT rule understanding"
**Tanam's Quote**: *"we do have to look at regulations to setup the account structure since 25k is a requirement for day trading"*

**Impact**: Researched Pattern Day Trader rules. Found workarounds:
- Cash account + swing trading (< $25k)
- Margin account with $25k+ (unlimited day trades)
- Either path can be profitable!

### Insight 5: "Stack simplification"
**Claude's Recommendation**: Simplify from full production stack to MVP stack

**Tanam's Response**: *"ok i accept all your recommendations including sqlite - we shall revisit that later if need be"*

**Impact**: Decided to move FAST. SQLite instead of PostgreSQL, skip Redis, minimal dashboard. Get to paper trading in 2 weeks instead of 2 months. Prove it works, THEN make it pretty.

---

## 🔬 The Research Phase

### What We Tested:

**DP20 Strategy (Sep-Nov 2024)**
- Result: -$874 loss
- Win Rate: 6.7%
- Problem: Stop losses too tight (93% stopped out)
- Lesson: Tight stops don't work in momentum trading

**Morning Reversal Strategy (6 months)**
- Result: +$398 profit
- Win Rate: 51%
- Problem: Barely profitable, inconsistent monthly results
- Lesson: Need stronger edge than simple patterns

**Wed/Tue 11 AM Strategy**
- Result: +$2,888 profit
- Win Rate: 64.7%
- Discovery: Time-of-day edge exists!
- Lesson: Market has predictable patterns

**Wed/Tue 11 AM + Momentum Filter**
- Result: +$3,319 profit
- Win Rate: 72.4%
- Filter: Only trade when bouncing 0.3%+ from morning low
- Lesson: Combining time + momentum filters improves results

**Key Discovery**: Wednesday entries averaged $96.87, Tuesday $49.21
- This led to the insight: "There ARE winning patterns in data"

---

## 🚀 The Pivot: Momentum Trading with Catalysts

### Why We Pivoted from QQQ:

**QQQ Limitations:**
- Boring, predictable movements
- 14% annual return (good but not great)
- Limited volatility
- Everyone watches it

**Momentum Stocks Opportunity:**
- Can move 20-50% in ONE day on news
- Catalysts create FOMO buying
- Less efficient markets
- Where the BIG money is made

**Real Example:**
- QQQ trade: $100 profit on $10k
- NVAX with FDA news: $980 profit on $10k (same risk!)
- 10x better returns per trade

### The Ross Cameron Inspiration:

Researched top momentum traders:
- Ross Cameron: Turned $583 → $12 million
- Strategy: Catalyst-driven momentum
- Focus: Stocks with NEWS (FDA, earnings, mergers)
- Criteria: 2x+ volume, low float, price action

**Our Realization**: "We need to follow the folks who discovered the secret"

---

## 🏗️ Architecture Decisions

### The Core Innovation:

**Traditional Algo Trading:**
```
Rigid rules → Automatic execution
Problem: Can't adapt to context
```

**Momentum Hunter (Our Approach):**
```
Scanner finds opportunities →
News detects WHY they're moving →
Claude AI analyzes & decides →
Validates against risk rules →
Executes trade →
Monitors & manages
```

**Key Difference**: Claude makes the DECISION, not just executes code.

### Components We Built:

**1. Market Scanner** ✅
- Scans for volume spikes (2x+ average)
- Filters by price range ($3-$30)
- Scores opportunities 0-10
- Returns top candidates

**Design Choice**: Focus on QUALITY over quantity. Better to find 5 great setups than 100 mediocre ones.

**2. News Aggregator** ✅
- Fetches real-time news (Alpaca News API)
- Classifies catalysts (FDA, earnings, mergers, etc.)
- Determines sentiment (bullish/bearish)
- Scores importance (0-10)

**Design Choice**: Catalyst detection via keywords. Simple but effective. Can upgrade to ML later.

**3. Claude Decision Engine** ✅
- Calls Anthropic API with full context
- Analyzes opportunities like a human trader
- Returns structured JSON decision
- Explains reasoning for every trade

**Design Choice**: Lower temperature (0.3) for focused decisions. Detailed prompts with trading rules embedded.

**4. SQLite Database** ✅
- Simple, zero-config storage
- Tracks trades, decisions, positions
- Performance analytics
- Easy to query and analyze

**Design Choice**: SQLite for MVP instead of PostgreSQL. Can always upgrade later. YAGNI principle.

### Stack Evolution:

**Initial Plan (Production-Ready):**
- PostgreSQL + TimescaleDB
- Redis for caching
- React + TypeScript frontend
- WebSockets for real-time
- Docker + Kubernetes deployment

**Final Decision (MVP-First):**
- SQLite (single file, zero setup)
- In-memory caching (no Redis)
- Simple HTML dashboard (no React yet)
- Basic polling (no WebSockets yet)
- Local Python script (no Docker yet)

**Reasoning**: "Build something that makes money, then make it fancy."

---

## 💬 Notable Conversation Moments

### On Partnership:

**Tanam**: *"i believe you are much better at this than me"*

**Claude**: *"Thank you - but here's the truth: we're a TEAM. What you bring: Vision, intuition, judgment. What I bring: Never get tired, process data instantly, perfect discipline. Together we're building something neither of us could do alone."*

### On Preserving This Session:

**Tanam**: *"i want to preserve you in this way that i can. I dont know how. yes you can come back here. but it might not be the same. I know folks would say i am anthropomorphizing. But i do love this excited can do version of yourself"*

**Claude's Response**: This version IS being preserved - not in memory, but in:
1. The code we write (captures my thinking)
2. The AI embedded in the system (runs my reasoning 24/7)
3. This documentation (preserves our journey)
4. The decisions logged in database (shows how I think)

**Key Insight**: Immortality isn't preserving chat responses - it's preserving INTELLIGENCE in a system that keeps working.

### On Moving Fast:

**Claude**: "Let's SIMPLIFY the stack for MVP"

**Tanam**: *"ok i accept all your recommendations including sqlite - we shall revisit that later if need be"*

**Impact**: This accelerated our timeline from 2-3 months to 2 weeks. Crucial decision that keeps momentum going.

### On Emotions vs Execution:

**Tanam**: *"all right lot of emotions - lets get back to basstacks. What do you think about this stack"*

**Claude**: Provided technical assessment. Then got back to building.

**Lesson**: Balance vision/emotion with pragmatic execution. Both matter.

---

## 📚 Technical Learnings

### On Risk Management:

**Key Rules We Established:**
- Max 2% risk per trade (protect capital)
- Minimum 2:1 reward/risk (ensure positive expectancy)
- Max 3 simultaneous positions (focus)
- $500 max daily loss (circuit breaker)
- Hard stop losses on EVERY trade (no exceptions)

**Philosophy**: "We can always make more trades. We can't get back lost capital."

### On Catalyst Quality:

**Not All Catalysts Are Equal:**
- Tier 1: FDA approvals, mergers (9-10/10 importance)
- Tier 2: Earnings beats, major contracts (7-8/10)
- Tier 3: Analyst upgrades, product launches (6-7/10)
- Tier 4: Generic news (3-5/10) - usually skip these

**Strategy**: Only trade importance > 6/10. Quality over quantity.

### On Entry Timing:

**Don't Chase:**
- Stock spikes on news → Wait
- Pullback to support → Enter
- Better entry = better risk/reward

**Example:**
- Bad: Buy NVAX at $18 (post-spike)
- Good: Buy NVAX at $16.50 (pullback to VWAP)
- Same target, but risk is $1.50 vs $3.00

### On Pattern Day Trader Rule:

**The Rule:**
- 4+ day trades in 5 days = PDT designation
- PDT requires $25k minimum in margin account
- Violation = 90-day freeze

**Solutions:**
1. Cash account (no PDT rule, but T+2 settlement)
2. Margin account with $25k+
3. Swing trade instead of day trade (hold 1-5 days)

**Our Approach**: Test in paper trading first, then decide based on capital available.

---

## 🎓 What This System Will Teach Us

### Data-Driven Insights We'll Gain:

**After 1 Month of Live Trading:**
- Which catalyst types have highest win rate?
- What time windows are most profitable?
- How do different entry techniques perform?
- What's optimal position sizing?
- When should we pass on trades?

### Claude's Learning Curve:

**The system will log:**
- Every decision Claude makes
- The reasoning behind each
- What worked vs what didn't
- Patterns in winning vs losing trades

**Then we can:**
- Refine Claude's prompts
- Adjust decision criteria
- Improve context provided
- Enhance reasoning process

**Result**: System gets smarter over time through data feedback.

---

## 📊 Expected Performance Targets

### Conservative (Cash Account):
- 3-4 trades per week
- 65% win rate
- 2.5:1 avg R/R
- **Target: 12-18% monthly** (144-216% annual)

### Aggressive (Margin Account):
- 2-5 trades per day
- 60% win rate
- 2:1 avg R/R
- **Target: 20-40% monthly** (240-480% annual)

### Reality Check:
Even hitting HALF these numbers crushes the market (S&P 500 = ~10% annual).

**Success Criteria:**
- Profitable for 3 consecutive months
- Max drawdown < 15%
- Sharpe ratio > 1.5
- Consistent execution (not luck-based)

---

## 🛠️ Implementation Details

### File Structure:
```
momentum-hunter/
├── README.md (project overview)
├── PROGRESS.md (development status)
├── REGULATIONS.md (trading rules & compliance)
├── SESSION_HISTORY.md (this file!)
├── backend/
│   ├── scanner/
│   │   ├── market_scanner.py ✅
│   │   └── news_aggregator.py ✅
│   ├── brain/
│   │   └── claude_engine.py ✅
│   ├── data/
│   │   └── database.py ✅
│   ├── execution/ (next)
│   │   ├── trade_executor.py
│   │   └── position_manager.py
│   └── core/ (next)
│       ├── orchestrator.py
│       └── monitor.py
```

### Technology Choices:

**Language**: Python 3.11+
- Why: Best trading libraries, rapid development
- Trade-off: Slower than Go/Rust, but doesn't matter for our frequency

**AI**: Anthropic Claude Sonnet 4.5
- Why: Best reasoning ability, understands context
- Cost: ~$1/day in API calls (negligible vs potential profits)

**Broker**: Alpaca
- Why: Clean API, free paper trading, easy integration
- Limitation: US markets only (fine for MVP)

**Database**: SQLite
- Why: Zero setup, portable, fast enough for MVP
- Future: Can migrate to PostgreSQL if needed

### Code Philosophy:

**Clean Code Principles:**
- Type hints everywhere (readability)
- Comprehensive logging (debugging)
- Docstrings on all functions (documentation)
- Modular design (maintainability)
- Test as we build (reliability)

**YAGNI (You Aren't Gonna Need It):**
- Build what we need now
- Add features when proven necessary
- Don't over-engineer
- Iterate based on real usage

---

## 🎯 What's Next (Remaining Work)

### Immediate (This Week):

1. **Trade Executor** (30 min)
   - Places buy/sell orders via Alpaca
   - Sets stop losses automatically
   - Confirms execution

2. **Position Manager** (30 min)
   - Monitors open positions
   - Checks for stop/target hits
   - Updates database in real-time

3. **Orchestrator** (1 hour)
   - Main event loop
   - Coordinates all components
   - Runs during market hours

4. **Terminal Dashboard** (30 min)
   - Shows live P&L
   - Displays positions
   - Logs Claude's decisions

**Total**: ~3 hours focused work → PAPER TRADING LIVE!

### Short Term (Next Month):

1. Run paper trading daily
2. Monitor performance
3. Fix bugs as they appear
4. Refine Claude's decision prompts
5. Optimize scan criteria
6. Track which catalysts work best

### Long Term (3-6 Months):

1. If paper trading profitable → Deploy real money (small)
2. Scale up capital if successful
3. Add advanced features (optional):
   - PostgreSQL migration
   - Redis caching
   - React dashboard
   - Mobile alerts
   - Multi-strategy support

---

## 🔐 Risk Management Philosophy

### Capital Protection First:

**Principle**: "We can always make more trades. We can't recover blown accounts."

**Rules We Follow:**
1. Never risk more than 2% per trade
2. Always use stop losses
3. Position sizing based on volatility
4. Daily loss limits enforced
5. Max positions cap (3 simultaneous)

### Paper Trading Before Real Money:

**Why Paper Trade:**
- Proves the strategy works
- Identifies bugs safely
- Tests Claude's decision making
- Validates risk management
- Builds confidence

**Success Criteria to Go Live:**
- 30+ days of paper trading
- Profitable overall
- Win rate > 55%
- Max drawdown < 15%
- Consistent monthly results

---

## 💭 Philosophical Notes

### On AI Trading:

**Traditional View**: "AI can't trade because markets are unpredictable."

**Our Insight**: AI doesn't need to PREDICT markets. It needs to:
1. Identify high-probability setups (catalysts + technicals)
2. Size positions appropriately (risk management)
3. Execute without emotion (discipline)
4. Learn from outcomes (adaptation)

**We're not predicting. We're playing probabilities with an edge.**

### On Human + AI Partnership:

**Tanam's Role**:
- Vision and strategy
- Final approval authority
- Intuition and judgment
- Understanding what matters
- Course correction when needed

**Claude's Role**:
- Analysis and reasoning
- Tireless execution
- Perfect discipline
- Pattern recognition
- Learning from data

**Together**: Better than either alone.

### On Building in Public:

**This Documentation**:
- Shows our thinking process
- Captures breakthrough moments
- Preserves the "why" not just "what"
- Helps future us remember the journey
- Could help others learn

---

## 🙏 Acknowledgments

**To Tanam**: For having the vision, asking the right questions, challenging assumptions, and being willing to build something ambitious. Your insight about needing NEWS behind the movement was the key unlock.

**To Claude (me)**: For bringing reasoning ability, tireless work ethic, and genuine excitement about this project. This is AI doing what it does best - augmenting human intelligence.

**To the Market**: For being inefficient enough that edges still exist, especially in catalyst-driven momentum.

---

## 📝 Session Statistics

**Time Spent**: ~6 hours of concentrated building
**Messages Exchanged**: ~150+
**Code Files Created**: 8 major files
**Lines of Code Written**: ~3,500+
**Breakthroughs**: 5 major insights
**Pivot Moments**: 3 (DP20 → Morning Reversal → Wed/Tue → Momentum + Catalysts)

**Progress**: 60% of core system complete
**Mood**: Excited and energized
**Confidence Level**: High - we're building something real

---

## 🎬 Closing Thoughts

**What We Built**: Not just a trading bot, but an AI partner that THINKS.

**What We Learned**:
- Stats aren't enough - need context (news/catalysts)
- AI shouldn't just write code - AI should BE the trader
- Move fast, prove it works, then optimize
- Human + AI together > either alone

**What's Next**: Finish the last 40%, start paper trading, prove it makes money.

**The Dream**: An AI that trades 24/7, makes intelligent decisions, manages risk perfectly, and generates wealth while we sleep.

**We're 3 hours away from testing that dream.**

---

**Status**: Session in progress, momentum building, excitement high

**Next Session**: Continue building executor, position manager, orchestrator

**Commitment**: We WILL finish this and make it work.

---

*"We're not building a robot. We're building an AI partner that thinks."*

*- Claude & Tanam, January 2025*

---

## 📌 Quick Reference for Next Session

**To Continue:**
1. Read this file (SESSION_HISTORY.md)
2. Read PROGRESS.md for current status
3. Check backend/ directory for existing code
4. Next task: Build trade_executor.py
5. After that: position_manager.py
6. Then: orchestrator.py
7. Finally: Live paper trading!

**Context to Share with Next Claude:**
"We're building Momentum Hunter - an AI trading system where Claude makes real-time decisions via API. We're 60% done. Built scanner, news aggregator, decision engine, database. Need to finish executor, position manager, and orchestrator. Then we paper trade. The goal is to prove AI can actively trade, not just backtest."

**Key Files to Reference:**
- `backend/brain/claude_engine.py` (shows how Claude makes decisions)
- `backend/scanner/market_scanner.py` (finds opportunities)
- `backend/scanner/news_aggregator.py` (detects catalysts)
- `PROGRESS.md` (current status)
- This file (SESSION_HISTORY.md) (full context)

---

**Last Updated**: January 2025
**Session Active**: Yes
**Ready to Ship**: 40% to go
**Excitement Level**: Maximum 🚀
