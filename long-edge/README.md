# LongEdge 📈

**Daily Breakout Momentum Trading System - Long Only**

A systematic momentum trading system that identifies growth stocks breaking out of consolidation bases using Minervini/O'Neil methodology. Combines quantitative screening with AI-powered decision making for bull market alpha generation.

## What is LongEdge?

LongEdge is a **long-only** momentum strategy designed for bull markets. It catches institutional accumulation during consolidation breakouts and rides the trend until momentum breaks.

**Sister Project:** ShortEdge (coming soon) - Bear market short strategy

## Vision

Unlike traditional algorithmic trading that follows rigid rules, LongEdge combines:
- **Systematic screening** - Quantitative filters for quality breakouts
- **AI analysis** - Claude AI evaluates setups with nuanced reasoning (optional)
- **Adaptive exits** - Smart trailing stops that tighten as profits grow
- **Rigorous testing** - Walk-forward validation before any live trading

## Strategy Summary

### Entry Criteria (ALL must pass):
1. **Price Quality**: >$10 (no penny stocks)
2. **Trend Confirmation**: Close > SMA20 > SMA50 (Stage 2 uptrend)
3. **Relative Strength**: Within 25% of 52-week high
4. **Consolidation Base**: 10-90 days, <12% volatility
5. **Breakout**: Current close > consolidation high
6. **Volume Expansion**: ≥1.2x average volume (or 0.8x for mega-caps)

### Exit Criteria (FIRST to trigger):
1. **Hard Stop**: -8% from entry
2. **Trailing Stop**: Adaptive (2x ATR → 1x ATR → 5% as profit grows)
3. **5-Day MA Break**: Close below 5-day SMA (after +3% profit)
4. **Lower High**: Momentum weakening (after +5% profit)
5. **Time Stop**: 15 days maximum hold

### Risk Management:
- Max 2% risk per trade
- 30% position size per trade
- Max 3 simultaneous positions (90% capital deployed)
- $500 daily loss limit

## Technology Stack

- **Language**: Python 3.11+
- **Data**: Alpaca Markets API (SIP feed, $99/month)
- **AI**: Anthropic Claude Sonnet 4.5 (optional decision engine)
- **Database**: SQLite (trades, positions, journal)
- **Analysis**: pandas, numpy (vectorized backtesting)

## Project Structure

```
long-edge/
├── backend/
│   ├── scanner/
│   │   └── daily_breakout_scanner.py    # Main scanner
│   ├── brain/
│   │   └── claude_engine.py             # AI decision engine
│   ├── backtest/
│   │   └── daily_momentum_smart_exits.py # Backtest engine
│   ├── data/
│   │   └── database.py                   # SQLite journal
│   └── execution/
│       └── trade_executor.py             # Alpaca execution
├── config/
│   └── universe.py                       # Stock watchlist
├── docs/
│   └── STRATEGY_THESIS.md                # Full strategy spec
└── tests/
```

## Stock Universe

**Current: 26 Hand-Picked Growth Stocks**

- **Tech Leaders**: NVDA, PLTR, SNOW, CRWD, AMD, TSLA
- **Mega-Caps**: AAPL, MSFT, GOOGL, AMZN, META
- **Biotech**: MRNA, BNTX, SAVA, SGEN
- **Fintech**: SHOP, SQ, COIN, RBLX
- **Others**: GME, AMC, SNAP, PTON

See `config/universe.py` for full list and alternative universes.

## Performance (Backtests)

**Optimized Periods (Q1-Q3 2024/2025):**
- Average Return: +2.54% per quarter
- Win Rate: 56.9%
- Profit Factor: 1.5x
- Max Drawdown: -3.3%

**Validation Periods (Unseen Q3-Q4 2024):**
- Status: Testing in progress
- Required: >2% average return to validate

**Key Finding:** Strategy works in trending markets, struggles in consolidation periods.

## Getting Started

### Prerequisites
```bash
Python 3.11+
Alpaca API account (paper trading)
Anthropic API key (optional, for Claude decision engine)
```

### Installation
```bash
# Clone repository
cd /Users/tanambamsinha/projects/trading-playbook/long-edge

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys:
# - ALPACA_API_KEY
# - ALPACA_SECRET_KEY
# - ANTHROPIC_API_KEY (optional)

# Run a backtest
python backend/backtest/daily_momentum_smart_exits.py
```

### Run Your First Scan
```python
from backend.scanner.daily_breakout_scanner import DailyBreakoutScanner
import os
from dotenv import load_dotenv

load_dotenv()
scanner = DailyBreakoutScanner(
    os.getenv('ALPACA_API_KEY'),
    os.getenv('ALPACA_SECRET_KEY')
)

# Scan for breakouts
candidates = scanner.scan()
for c in candidates:
    print(f"{c.symbol}: Score {c.score():.1f}/10")
```

## Documentation

- **[STRATEGY_THESIS.md](docs/STRATEGY_THESIS.md)** - Complete strategy specification
- **[CODE_ANALYSIS.md](CODE_ANALYSIS.md)** - Architecture deep-dive
- **[SESSION_HISTORY.md](SESSION_HISTORY.md)** - Development journey

## Development Roadmap

### ✅ Phase 1: Core System (Complete)
- [x] Daily breakout scanner
- [x] Smart exit logic (adaptive trailing stops)
- [x] Backtest engine
- [x] Trade journal (SQLite)
- [x] Configuration system

### 🔄 Phase 2: Validation (Current)
- [x] Walk-forward optimization
- [ ] Unseen period testing (Q3-Q4 2024)
- [ ] Volume filter refinement (PLTR analysis)
- [ ] Market regime detection

### 📋 Phase 3: Paper Trading
- [ ] Real-time EOD scanning
- [ ] Paper order execution
- [ ] Daily monitoring dashboard
- [ ] Performance tracking

### 🚀 Phase 4: Live Trading
- [ ] 30 days profitable paper trading
- [ ] Small capital deployment ($10k)
- [ ] Scale based on performance
- [ ] Build ShortEdge (bear market counterpart)

## Known Issues & Future Improvements

### Critical Issue: Volume Filter Too Strict
**Problem:** 1.2x volume requirement filters out quiet institutional accumulation

**Evidence:** PLTR missed moves:
- Q1 2024: +65.9% (0.9x volume) - MISSED
- Q1 2025: +66.8% (0.7x volume) - MISSED

**Solution:** Testing tiered volume filter:
- Mega-caps: 0.8x threshold
- Others: 1.2x threshold

### Market Regime Dependency
**Problem:** Strategy only profitable in trending markets

**Solution:** Add SPY trend filter, sit out during consolidation

See [docs/STRATEGY_THESIS.md](docs/STRATEGY_THESIS.md) for full list.

## Safety & Risk Disclosure

**This is experimental trading software.**

- ⚠️ Start with paper trading ONLY
- ⚠️ Never risk more than you can afford to lose
- ⚠️ Past performance ≠ future results
- ⚠️ Trading involves substantial risk of loss
- ⚠️ Consult a financial advisor before live trading

**You are 100% responsible for all trading decisions.**

## Credits

**Built by:**
- 💡 Strategy & Vision: Tanam Bam Sinha
- 🤖 AI Assistant: Claude (Anthropic)
- 📚 Methodology: Mark Minervini (SEPA) + William O'Neil (CAN SLIM)

**Data & Tools:**
- 📊 Market Data: Alpaca Markets
- 🧠 AI Engine: Anthropic Claude Sonnet 4.5
- 🐍 Language: Python

## License

MIT License - See LICENSE file

---

**Status:** 🔬 Under Development - Walk-Forward Validation Phase

**Current Focus:** Testing volume filter refinements + unseen period validation

**Next Milestone:** Complete validation, begin paper trading

---

*"Catch institutional accumulation during consolidation breakouts, ride the momentum until it breaks."*

**LongEdge** - Bull market alpha generation through systematic breakout momentum.

**Coming Soon:** ShortEdge - Bear market alpha through systematic breakdown momentum.
