# Trading Playbook

Python-based quantitative trading backtesting infrastructure for systematic strategy research and development.

## Overview

**trading-playbook** is a composable backtesting platform designed for rigorous strategy validation. The project demonstrates production-grade engineering practices: hexagonal architecture, walk-forward validation, vectorized computations, and comprehensive testing documentation.

### Production Strategy: LongEdge Daily Breakout

The **LongEdge** strategy (in `/long-edge/`) is a fully implemented daily breakout momentum system:
- **Entry:** Minervini/O'Neil style base breakouts with volume confirmation
- **Exit:** Adaptive trailing stops with MA breaks and momentum detection
- **Performance:** +1.87% (Q3 2025), 54.5% win rate, controlled risk
- **Status:** Yellow light - promising but requires more validation data

See: [`/long-edge/README.md`](long-edge/README.md) for full strategy details and backtest results.

### Key Engineering Highlights

- **Composable Architecture:** Mix-and-match scanners, exit strategies, and position sizers
- **Vectorized Backtesting:** Pandas-based simulation 10x faster than event-driven approaches
- **Walk-Forward Validation:** Out-of-sample testing to prevent overfitting
- **Interface Standardization:** Python protocols (PEP 544) for consistent component APIs
- **Comprehensive Reporting:** Detailed markdown reports with trade-by-trade analysis
- **Data Management:** Intelligent caching layer (Alpaca API → SQLite/Parquet)

## Quick Start

**Current Status:** LongEdge strategy implemented and tested. Additional strategies in research phase.

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

## Development Status

### Completed ✅
- **LongEdge Strategy:** Fully implemented daily breakout system
- **Composable Engine:** Mix-and-match scanners and exit strategies
- **Interface Standardization:** 86% complete - PEP 544 protocols
- **Backtest Infrastructure:** Walk-forward validation framework
- **Documentation:** Comprehensive reports and analysis

### In Progress 🔄
- **Volume Filter Optimization:** Testing 0.0x vs 0.5x vs 1.2x thresholds
- **Exit Strategy Comparison:** Smart vs Scaled vs Hybrid trailing
- **Statistical Validation:** Building 50+ trade sample size across multiple periods

### Research Phase 📋
- **QQQ DP20 Intraday Strategy:** Design complete, implementation pending
- **Parameter Optimization:** Gradient-free methods for exit tuning
- **Multi-Strategy Portfolio:** Combining complementary approaches

## Project Structure

```
trading-playbook/
├── long-edge/                        # Production strategy (daily breakout momentum)
│   ├── backend/
│   │   ├── scanner/                  # Entry signal detection
│   │   ├── exit_strategies/          # Exit logic (smart, scaled, hybrid)
│   │   ├── engine/                   # Composable backtest engine
│   │   └── data/                     # Data clients and caching
│   ├── docs/
│   │   ├── backtest-reports/         # Detailed performance analysis
│   │   ├── session-history/          # Development log
│   │   └── archived/                 # Abandoned experiments
│   ├── backtest-results/             # JSON outputs organized by year
│   └── config/                       # Strategy configurations
├── docs/                             # Research documentation
│   ├── strategies/                   # Strategy specifications (QQQ DP20, etc.)
│   ├── system-design/                # Architecture documentation
│   └── analysis/                     # Performance frameworks
├── src/trading_playbook/             # Shared infrastructure
│   ├── core/                         # Pure strategy logic
│   └── adapters/                     # Data fetchers, writers
└── tests/                            # Test suites
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

### Research Strategies

**QQQ DP20 Intraday (Research Phase)**

Original intraday pullback strategy - research revealed better approaches:
- **DP20 Results:** Failed (-$874, 6.7% win rate)
- **Best Discovery:** Wed/Tue 11 AM strategy (+$2,888, 64.7% win rate)
- **Status:** Research complete, not in production
- **Documentation:** [research/qqq-intraday/README.md](research/qqq-intraday/README.md)

The research journey (DP20 → exploratory analysis → Wed/Tue discovery) demonstrates systematic strategy development methodology.

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

## Getting Started

### Running LongEdge Strategy

```bash
# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Add your Alpaca API keys to .env

# Run backtest (see long-edge/README.md for details)
cd long-edge
python backend/scanner/test_daily_breakout_scanner.py
```

For comprehensive setup and usage, see:
- [`/long-edge/README.md`](long-edge/README.md) - Strategy overview and quickstart
- [`/long-edge/QUICKSTART.md`](long-edge/QUICKSTART.md) - Detailed setup instructions
- [`/long-edge/BACKTEST_GUIDE.md`](long-edge/BACKTEST_GUIDE.md) - Running backtests

## Documentation Standards

This project follows structured documentation practices:
- Detailed system design in `docs/system-design/`
- Strategy specifications separate from implementation
- Comprehensive backtesting reports in `docs/backtest-reports/`

## Contributing

Open source trading infrastructure project. Design discussions and architecture:
- [docs/system-design/](docs/system-design/) - Detailed technical specs
- [docs/strategies/](docs/strategies/) - Strategy specifications

## License

MIT License - See individual project LICENSE files for details.

---

**Status:** LongEdge strategy implemented and tested | Research platform for systematic trading
**Last Updated:** 2025-11-08
