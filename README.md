# Trading Playbook

Python-based quantitative trading backtesting and analysis toolkit for systematic strategy development.

## Overview

**trading-playbook** enables rigorous backtesting of intraday trading strategies with statistical analysis, performance tracking, and AI-powered insights. Currently implementing the **QQQ DP20 strategy** - an intraday trend continuation approach using EMA20 pullbacks with ATR-based risk management.

### Key Features

- **Vectorized Backtesting:** Fast pandas-based simulation over historical data
- **Comprehensive Journaling:** 29-column trade journal capturing signals, execution, P&L, and analysis metrics
- **Performance Analytics:** Expectancy, R-multiples, time-of-day effects, volatility regime analysis
- **AI-Powered Insights:** Claude analyzes backtest results for patterns and optimization recommendations
- **Hexagonal Architecture:** Clean separation of core strategy logic from data sources and outputs
- **Multi-Phase Design:** Backtesting → Paper Trading → Live Trading progression

## Quick Start

**Status:** Design phase complete. Implementation begins with Phase 1 MVP.

### Documentation

**System Design:**
- [Architecture Overview](docs/system-design/architecture-overview.md) - Core vs Periphery design philosophy
- [Data Pipeline](docs/system-design/data-pipeline.md) - Alpaca API integration, caching strategy
- [Backtest Engine](docs/system-design/backtest-engine.md) - Vectorized simulation approach
- [Signal Detection](docs/system-design/signal-detection.md) - DP20 implementation details
- [Deployment](docs/system-design/deployment.md) - Local to cloud deployment strategy

**Strategy Specifications:**
- [QQQ DP20 Strategy](docs/strategies/qqq_dp20_strategy_spec.md) - Core strategy rules
- [Extended Journaling Schema](docs/strategies/qqq_pullback_strategy.md) - 29-column trade journal

**Analysis Frameworks:**
- [Performance Metrics](docs/analysis/performance-metrics.md) - Expectancy, win rate, MAE/MFE
- [AI Analysis Guide](docs/analysis/ai-analysis-guide.md) - Claude-powered insights

## Tech Stack

- **Python 3.9+** with Poetry for dependency management
- **pandas** - Vectorized data analysis and time series
- **numpy** - Numerical calculations for indicators
- **Alpaca API** - Market data (IEX free tier, SIP $9/mo)
- **Parquet** - Local data caching
- **Future:** GCP Cloud Run, MongoDB, real-time WebSockets

## Roadmap

### Phase 1: MVP Backtest (Current)
- Validate DP20 strategy logic on 2-3 months of data
- Local execution, Alpaca free tier (IEX data)
- CSV output with trade journal
- **Timeline:** 1-2 weeks

### Phase 2: Extended Backtest
- Test on years of historical data
- Statistical validation (100+ trades)
- AI analysis reports
- Parameter optimization

### Phase 3: Paper Trading
- Real-time signal detection
- Event-driven architecture
- Paper order execution via Alpaca
- Live monitoring

### Phase 4: Cloud Deployment
- GCP Cloud Run (serverless)
- Automated daily execution
- Cloud Storage + MongoDB
- Production monitoring

## Project Structure

```
trading-playbook/
├── docs/                    # Documentation
│   ├── strategies/          # Strategy specifications
│   ├── system-design/       # Technical architecture
│   ├── analysis/            # Performance frameworks
│   └── journal-templates/   # Trade journal templates
├── src/trading_playbook/    # (To be created)
│   ├── core/                # Pure strategy logic
│   ├── adapters/            # Data fetchers, writers
│   └── cli/                 # Command-line interface
├── tests/                   # (To be created)
├── data/cache/              # Local parquet cache
├── output/                  # Backtest results
└── CLAUDE.md                # AI context & architecture guide
```

## Core Concepts

### Hexagonal Architecture

**Core (Never Changes):**
- Signal detection algorithms
- Indicator calculations (EMA, ATR, SMA)
- Risk management rules
- Pure Python, fully testable

**Periphery (Flexible):**
- Data sources (Alpaca, CSV, cache)
- Writers (CSV, GCS, MongoDB)
- Orchestration (CLI, cloud schedulers)

**Benefit:** Same core logic for backtesting, paper trading, and live trading.

### DP20 Strategy (Quick Summary)

**Entry Logic:**
1. Trend filter: QQQ open > 200-day SMA
2. Time window: 10:00-10:30 AM ET
3. Pullback: Close below EMA20 (2-min)
4. Reversal: Close back above EMA20
5. Strength: Reversal body ≥ 60% of range
6. Confirmation: Next candle confirms

**Risk Management:**
- Stop: Entry - (1.2 × ATR)
- Exit: 3:55 PM ET
- One trade per day max

**Full specification:** [docs/strategies/qqq_dp20_strategy_spec.md](docs/strategies/qqq_dp20_strategy_spec.md)

## Design Decisions

### Why Alpaca?
- Free paper trading + data in one platform
- Cheaper than alternatives ($9/mo vs $29/mo)
- Commission-free trading
- Good Python SDK

### Why Full Day Data?
- Track intraday stop losses accurately
- MAE/MFE analysis requires full visibility
- Enable future features (profit targets, trailing stops)
- Data size is tiny (~10 MB for 3 months)

### Why Local Caching?
- 95% faster iteration during development
- Work offline, save API quota
- Only 30 lines of code

### Why Vectorized Backtesting?
- Simpler pandas operations
- Faster execution
- Can adapt to event-driven for live trading

## Getting Started (When Implemented)

```bash
# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env with Alpaca API keys

# Run backtest
poetry run python -m trading_playbook.cli.backtest \
  --symbol QQQ \
  --start 2025-09-01 \
  --end 2025-11-04 \
  --output ./output/trades.csv

# With AI analysis
poetry run python -m trading_playbook.cli.backtest \
  --symbol QQQ \
  --start 2025-09-01 \
  --end 2025-11-04 \
  --ai-analysis
```

## Documentation Standards

This project follows [Havq Claude Documentation Standards](https://github.com/tanambamsinha/havq-docs):
- Keep CLAUDE.md focused on architecture (600-800 lines)
- Detailed system design in `docs/system-design/`
- Strategy specs separate from implementation
- Session histories with 90-day retention

## Contributing

Open source trading infrastructure project. Design discussions and architecture:
- [CLAUDE.md](CLAUDE.md) - Complete architecture guide
- [docs/system-design/](docs/system-design/) - Detailed technical specs

## License

MIT License - See individual project LICENSE files for details.

---

**Status:** Design Complete | **Next:** Begin Phase 1 MVP Implementation
**Last Updated:** 2025-11-04
