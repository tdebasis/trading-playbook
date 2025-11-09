# Trading Playbook

Python-based quantitative trading backtesting infrastructure for systematic strategy research and development.

## Overview

**trading-playbook** is a composable backtesting platform designed for rigorous strategy validation. The project demonstrates production-grade engineering practices: hexagonal architecture, walk-forward validation, vectorized computations, and comprehensive testing documentation.

### Production Strategy: Daily Breakout System

A fully implemented daily breakout momentum system with multiple scanner variants and exit strategies:
- **Entry:** Minervini/O'Neil style base breakouts with volume confirmation
- **Scanners:** Moderate (production), Relaxed, Very Relaxed variants
- **Exits:** Smart Exits (adaptive trailing), Scaled Exits, Trend Following
- **Performance:** Multiple validated backtests across 2024-2025 periods
- **Status:** Active development - continuous strategy optimization

See: [`QUICKSTART.md`](QUICKSTART.md) for quick setup and [`ARCHITECTURE.md`](ARCHITECTURE.md) for system design.

### Key Engineering Highlights

- **Composable Architecture:** Mix-and-match scanners, exit strategies, and position sizers
- **Vectorized Backtesting:** Pandas-based simulation 10x faster than event-driven approaches
- **Walk-Forward Validation:** Out-of-sample testing to prevent overfitting
- **Interface Standardization:** Python protocols (PEP 544) for consistent component APIs
- **Comprehensive Reporting:** Detailed markdown reports with trade-by-trade analysis
- **Data Management:** Intelligent caching layer (Alpaca API → SQLite/Parquet)

## Quick Start

**Current Status:** Daily breakout strategy with composable architecture. Multiple exit strategies implemented and tested.

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
- **Daily Breakout System:** Multiple scanner variants (moderate, relaxed, very relaxed)
- **Exit Strategies:** Smart Exits, Scaled Exits, Trend Following 75
- **Composable Engine:** Mix-and-match scanners and exit strategies via registry pattern
- **Interface Standardization:** Complete - PEP 544 protocols throughout
- **Backtest Infrastructure:** Comparison framework for strategy evaluation
- **Documentation:** Comprehensive backtest reports and architecture docs

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
├── backend/                          # Core infrastructure
│   ├── scanner/
│   │   ├── long/                     # Long position scanners (moderate, relaxed, etc.)
│   │   └── short/                    # Short position scanners (placeholder)
│   ├── strategies/
│   │   ├── long/
│   │   │   ├── exits/                # Exit strategies (smart, scaled, trend_following)
│   │   │   └── registry.py           # Strategy factory and registration
│   │   └── short/                    # Short strategies (placeholder)
│   ├── engine/                       # Composable backtest engine
│   ├── execution/                    # Position management and trade execution
│   ├── data/                         # Data caching and management
│   ├── interfaces/                   # Protocol definitions (PEP 544)
│   ├── config/                       # Strategy configurations
│   └── backtest/                     # Historical backtest scripts
├── docs/
│   ├── backtest-reports/             # Performance analysis reports
│   ├── workflows/                    # Trading workflows
│   └── research-private/             # Private research (gitignored)
├── tests/                            # Integration and unit tests
├── backtest.py                       # Main backtest entry point
├── monitor.py                        # System monitor
└── run.py                            # System runner
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for detailed component descriptions.

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

### Running Backtests

```bash
# Set up environment
cp .env.example .env
# Add your Alpaca API keys to .env

# Run a comparison using the template
cp backend/examples/strategy_comparison_template.py tmp-scripts/my_comparison.py
# Edit tmp-scripts/my_comparison.py with your parameters
python3 tmp-scripts/my_comparison.py
```

**Strategy Comparison Template:**
- See [`backend/examples/strategy_comparison_template.py`](backend/examples/strategy_comparison_template.py)
- Copy and modify for your own analysis
- Results can be saved to `docs/backtest-reports/`

**Published Backtest Reports:**
- [`docs/backtest-reports/`](docs/backtest-reports/) - Detailed performance analysis
- Multiple strategy comparisons across 2024-2025
- Trade-by-trade analysis and insights

For comprehensive setup and usage, see:
- [`QUICKSTART.md`](QUICKSTART.md) - Detailed setup instructions
- [`ARCHITECTURE.md`](ARCHITECTURE.md) - System architecture and design

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

**Status:** Production-ready backtesting infrastructure | Active strategy development
**Last Updated:** 2025-11-09
**Commit:** bc35a83 - Complete repository reorganization to flat structure
