# Momentum Hunter 🚀

**Autonomous AI-Powered Day Trading System**

An intelligent trading bot that uses Claude AI to make real-time trading decisions based on momentum patterns, news catalysts, and market data.

## Vision

Unlike traditional algorithmic trading that follows rigid rules, Momentum Hunter uses Claude AI as its "brain" to:
- Analyze market-moving news in real-time
- Identify high-probability momentum setups
- Make nuanced trading decisions with human-like reasoning
- Adapt to changing market conditions
- Learn from every trade

## Architecture

```
Data Layer → Scanner → Claude AI Brain → Risk Manager → Execution → Monitoring
```

### Components

1. **Market Scanner**: Identifies stocks with unusual volume and price movement
2. **News Aggregator**: Pulls real-time news and catalyst data
3. **Claude Decision Engine**: AI analyzes opportunities and makes trading decisions
4. **Risk Manager**: Validates trades against safety rules
5. **Trade Executor**: Executes orders via Alpaca API
6. **Position Monitor**: Tracks open positions and manages exits
7. **Dashboard**: Real-time UI showing trades, P&L, and Claude's reasoning

## Trading Strategy

**Entry Criteria:**
- Catalyst-driven (news, earnings, FDA approvals, etc.)
- Relative volume > 2x normal
- Price range: $3-$30
- Float < 100M shares
- Clear technical setup (bull flag, breakout, etc.)
- Trade window: 9:30-11:30 AM EST

**Risk Management:**
- Max 2% risk per trade
- 2:1 minimum reward/risk ratio
- Max 3 positions simultaneously
- Hard stop losses on every trade
- $500 max daily loss limit

**Exit Strategy:**
- Profit target hit (2:1 R/R)
- Stop loss hit
- Pattern breaks down
- 3:30 PM close all positions
- News reverses

## Technology Stack

- **Backend**: Python (scanner, execution, data)
- **AI Engine**: Anthropic Claude API
- **Database**: PostgreSQL + TimescaleDB
- **Cache**: Redis
- **Frontend**: React + TypeScript
- **Broker**: Alpaca Trading API
- **Deployment**: Docker + AWS/DigitalOcean

## Development Phases

### Phase 1: Core Engine (Current)
- [x] Market scanner
- [x] News aggregation
- [ ] Claude decision engine
- [ ] Paper trading execution
- [ ] Basic logging

### Phase 2: Risk & Monitoring
- [ ] Risk management layer
- [ ] Position monitoring
- [ ] Stop loss management
- [ ] Performance analytics

### Phase 3: User Interface
- [ ] Real-time dashboard
- [ ] Trade history viewer
- [ ] Claude reasoning log
- [ ] Manual override controls

### Phase 4: Testing & Optimization
- [ ] 1-month paper trading test
- [ ] Performance analysis
- [ ] Strategy refinement
- [ ] Production readiness

### Phase 5: Production
- [ ] Small capital deployment
- [ ] Monitoring & alerting
- [ ] Scale based on performance

## Getting Started

### Prerequisites
```bash
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for dashboard)
- Alpaca API account (paper trading)
- Anthropic API key
```

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/momentum-hunter.git
cd momentum-hunter

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Start services with Docker
docker-compose up -d

# Run the trading bot
python -m core.orchestrator
```

## Configuration

Edit `config/trading_rules.yaml` to customize:
- Risk limits
- Position sizing
- Scan criteria
- Entry/exit rules
- Trading hours

## Safety Features

- **Paper Trading First**: Test with fake money before risking real capital
- **Kill Switch**: Instant shutdown button in dashboard
- **Daily Loss Limits**: Automatic trading halt if limit exceeded
- **Position Size Caps**: Never risk more than 2% per trade
- **Human Override**: You can always manually override or stop trades

## Performance Tracking

The system logs every decision and trade:
- Entry/exit prices and times
- Claude's reasoning for each decision
- Win/loss outcomes
- Daily/weekly/monthly P&L
- Performance metrics (win rate, profit factor, Sharpe ratio)

## Legal & Disclaimer

**This is experimental software. Trading involves substantial risk of loss.**

- Start with paper trading only
- Never invest more than you can afford to lose
- Past performance doesn't guarantee future results
- You are responsible for all trading decisions
- Consult a financial advisor before live trading

## Credits

Built with:
- 💡 Vision and strategy by Tanam Bam Sinha
- 🤖 AI architecture powered by Anthropic Claude
- 📊 Market data via Alpaca
- ❤️ Built for traders who want an AI partner, not just an algorithm

## License

MIT License - See LICENSE file

---

**Status**: 🚧 In Active Development

**Current Phase**: Building core scanner and decision engine

**Next Milestone**: Complete 1-month paper trading test

---

*"We're not building a robot trader. We're building an AI partner that thinks."*
