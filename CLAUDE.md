# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**trading-playbook** is a Python-based quantitative trading backtesting and analysis toolkit focused on systematic strategy development. Currently implementing the QQQ DP20 (Deep Pullback 20) strategy - an intraday trend continuation strategy using EMA20 pullbacks, ATR-based stops, and end-of-day exits.

**Purpose:**
- Backtest trading strategies on historical data with statistical rigor
- Generate structured trade journals for performance analysis
- Calculate expectancy, R-multiples, time-of-day effects, volatility regime analysis
- Provide AI-powered insights and optimization recommendations
- Enable transition from backtesting → paper trading → live trading

**Tech Stack:**
- Python 3.9+ with Poetry for dependency management
- Data: pandas (vectorized analysis), numpy (calculations)
- Market data: Alpaca API (free IEX data, $9/mo for SIP data)
- Storage: Parquet (cache), CSV (journals)
- Future: GCP Cloud Run, MongoDB, real-time WebSockets

**Current Status:** Design phase complete, implementation ready to begin

---

## Repository Structure

```
trading-playbook/
├── docs/
│   ├── strategies/              # Strategy specifications
│   │   ├── qqq_dp20_strategy_spec.md        # Core DP20 rules
│   │   └── qqq_pullback_strategy.md         # Extended journaling schema
│   │
│   ├── system-design/           # Technical architecture docs
│   │   ├── architecture-overview.md         # Core vs Periphery design
│   │   ├── data-pipeline.md                 # Alpaca, caching, IEX vs SIP
│   │   ├── backtest-engine.md               # Vectorized simulation
│   │   ├── signal-detection.md              # DP20 implementation details
│   │   └── deployment.md                    # Local → Cloud strategy
│   │
│   ├── analysis/                # Performance analysis frameworks
│   │   ├── performance-metrics.md           # Expectancy, win rate, MAE/MFE
│   │   └── ai-analysis-guide.md             # Claude-powered insights
│   │
│   └── journal-templates/       # Trade journal templates
│       └── qqq_journal_template.csv         # 29-column schema
│
├── src/trading_playbook/        # (To be created)
│   ├── core/                    # Pure strategy logic (no I/O)
│   ├── adapters/                # Data fetchers, writers (I/O)
│   └── cli/                     # Command-line interface
│
├── tests/                       # (To be created)
├── data/cache/                  # Local parquet cache
├── output/                      # Backtest results
├── pyproject.toml               # Poetry dependencies
├── CLAUDE.md                    # This file
└── README.md
```

---

## Core Architecture (Hexagonal Design)

### Design Philosophy: Core vs Periphery

**CORE (Never Changes):**
- Pure Python functions, no I/O dependencies
- Strategy signal detection (DP20 6-step logic)
- Indicator calculations (EMA, ATR, SMA)
- Risk management (stops, exits)
- Fully testable, reusable across environments

**PERIPHERY (Flexible):**
- Data sources: Alpaca API, CSV files, cache
- Writers: CSV, GCS, MongoDB
- Orchestration: CLI, cloud schedulers
- Changes freely without touching core logic

**Benefits:**
- Same core for backtesting, paper trading, live trading
- Easy to swap data sources (dev → prod)
- Testable in isolation
- Future-proof

**See:** [docs/system-design/architecture-overview.md](docs/system-design/architecture-overview.md)

---

## DP20 Strategy Summary

**Full Spec:** [docs/strategies/qqq_dp20_strategy_spec.md](docs/strategies/qqq_dp20_strategy_spec.md)

**6-Step Entry Logic:**
1. **Trend Filter:** QQQ open > 200-day SMA (bullish bias)
2. **Time Window:** Signals only between 10:00-10:30 AM ET
3. **Pullback:** Price closes below EMA20 (2-min)
4. **Reversal:** Price closes back above EMA20
5. **Strength Filter:** Reversal candle body ≥ 60% of range
6. **Confirmation:** Next candle closes above EMA20 (or invalidate)

**Entry:** Open of candle after confirmation
**Stop:** Entry - (1.2 × ATR(14, 2-min))
**Exit:** 3:55 PM ET (end-of-day)

**Risk Rules:**
- One trade per day maximum
- Fixed share size (20 shares for paper trading)
- No averaging down or re-entry

**Journal Output:** 29 columns capturing entry signals, execution, P&L, R-multiples, time-of-day, volatility metrics

---

## Data Pipeline

### Data Source: Alpaca Markets

**Phase 1 (Current):** Free tier
- IEX data (2-3% of market volume)
- Good enough for strategy development
- 2-3 months historical lookback
- $0 cost

**Phase 2 (Later):** Paid tier ($9/mo)
- SIP data (all exchanges consolidated)
- Unlimited historical lookback
- More accurate volume/ATR

### What is IEX vs SIP?

**IEX Data:**
- One exchange only (Investors Exchange)
- ~2-3% of total US market volume
- Misses trades on NYSE, NASDAQ, etc.
- Price patterns accurate, volume understated

**SIP Data:**
- Consolidated from ALL exchanges
- 100% complete market picture
- Professional-grade accuracy

**Decision:** Use IEX for Phase 1, upgrade to SIP when backtesting years of data or going live.

**See:** [docs/system-design/data-pipeline.md](docs/system-design/data-pipeline.md)

### Data Requirements

**Intraday Bars (2-minute):**
- 9:30 AM - 4:00 PM ET (195 bars/day)
- Fields: timestamp, open, high, low, close, volume
- Calculated: EMA20, ATR(14)

**Daily Bars:**
- Need 200+ days for SMA200 calculation
- Fields: date, open, high, low, close, volume
- Calculated: SMA200

### Caching Strategy

**Local parquet caching from day 1:**
- Cache key: `{symbol}_{timeframe}_{start}_{end}.parquet`
- Historical data cached forever (never changes)
- 95% faster iteration during development
- 2-3 months ≈ 10 MB, years ≈ 100 MB (tiny)

**Why:** Faster iteration when tweaking strategy parameters (1 second vs 30 seconds per backtest)

---

## Backtesting Approach

### Vectorized vs Event-Driven

**Phase 1 (Backtesting):** Vectorized
- Load all data at once
- Use pandas boolean masks and operations
- Process entire date ranges together
- Fast, simple, efficient

**Phase 3 (Live Trading):** Event-driven
- Process each candle as it arrives
- Maintain state machine
- React in real-time

**Key:** Core strategy logic same for both, just different execution patterns.

### Backtest Process

1. **Fetch Data:** Alpaca API → intraday (2-min) + daily bars
2. **Calculate Indicators:** EMA20, ATR(14), SMA200
3. **Day-by-Day:**
   - Check trend filter
   - Detect DP20 signal in 10:00-10:30 window
   - If signal → simulate entry
   - Track position through EOD, monitor stop hits
   - Exit at 3:55 PM or stop (whichever first)
4. **Output:**
   - Trade journal CSV (29 columns, one row per day)
   - Summary statistics (expectancy, win rate, etc.)
   - Optional: AI analysis report

**See:** [docs/system-design/backtest-engine.md](docs/system-design/backtest-engine.md)

---

## Signal Detection Implementation

**6-Step Implementation:**

1. **Trend Filter:** `day_open > sma200`
2. **Time Window:** Filter bars between 10:00-10:30 ET
3. **Pullback:** Find first `close < ema20`
4. **Reversal:** Find first `close > ema20` after pullback
5. **Strength:** Calculate `(close - low) / (high - low) > 0.60`
6. **Confirmation:** Next candle must `close > ema20`

**Edge Cases Handled:**
- Multiple pullbacks in window → take first
- Reversal without confirmation → no signal
- Weak reversal (< 60% body) → keep looking
- Confirmation invalidation → skip day

**See:** [docs/system-design/signal-detection.md](docs/system-design/signal-detection.md)

---

## Performance Analysis

### Core Metrics

**Expectancy (Primary):**
- Average R-multiple across all trades
- Position-size independent measure of edge
- Target: > 1.0R for profitable strategy

**Win Rate:**
- Percentage of winning trades
- Target: > 55% for mean-reversion strategy

**Profit Factor:**
- Gross profit / Gross loss
- Target: > 1.5

**Max Drawdown:**
- Largest peak-to-trough decline
- Critical for position sizing

### Advanced Analysis

**Time-of-Day:**
- Bucket entries: 10:00-10:10, 10:10-10:20, 10:20-10:30
- Compare expectancy by bucket
- Optimize time window

**Volatility Regimes:**
- Tertile bucket by ATR % of price (low/med/high)
- Compare expectancy by regime
- Add volatility filters

**MAE/MFE:**
- Maximum Adverse Excursion (how far against you)
- Maximum Favorable Excursion (how far in your favor)
- Optimize stops and profit targets

**See:** [docs/analysis/performance-metrics.md](docs/analysis/performance-metrics.md)

### AI-Powered Insights

**Claude analyzes backtest results to identify:**
- Performance patterns (time, volatility, streaks)
- Stop loss effectiveness
- Entry quality assessment
- Optimization priorities (ranked by impact)
- Risk warnings

**See:** [docs/analysis/ai-analysis-guide.md](docs/analysis/ai-analysis-guide.md)

---

## Development Workflow

### Phase 1: MVP Backtest (Current Focus)

**Goal:** Validate DP20 strategy logic on 2-3 months of data

**Tasks:**
1. Set up Poetry project structure
2. Implement core indicators (EMA, ATR, SMA)
3. Implement Alpaca data fetcher with caching
4. Implement DP20 signal detection
5. Implement backtest engine
6. Implement CSV writer
7. Run backtest on 60 days
8. Analyze results

**Environment:** Local laptop
**Cost:** $0
**Timeline:** 1-2 weeks

### Phase 2: Extended Backtest

**Goal:** Test on years of data, refine parameters

**Additions:**
- Upgrade to Alpaca paid ($9/mo) or slow-fetch on free tier
- Backtest 1-2 years (250-500 trading days)
- Calculate robust statistics (>100 trades)
- AI analysis reports
- Parameter optimization

### Phase 3: Paper Trading

**Goal:** Real-time signal detection with paper money

**Additions:**
- WebSocket real-time data feed
- Event-driven architecture
- Paper order execution via Alpaca
- Live monitoring dashboard
- Daily journaling

### Phase 4: Cloud Deployment

**Goal:** Automated, reliable execution

**Stack:**
- Google Cloud Run (serverless containers)
- Cloud Scheduler (cron jobs)
- Cloud Storage (GCS for data/journals)
- MongoDB Atlas (journal database)

**See:** [docs/system-design/deployment.md](docs/system-design/deployment.md)

---

## Key Design Decisions & Rationale

### Why Alpaca?
- ✅ Free paper trading + data in one platform
- ✅ Cheaper than alternatives ($9/mo vs $29/mo for Polygon)
- ✅ Commission-free trading
- ✅ Good Python SDK

### Why Full Day Data (9:30-4:00)?
- ✅ Need to track stops intraday (can't just use EOD prices)
- ✅ MAE/MFE analysis requires full day visibility
- ✅ Slippage estimation needs volume patterns
- ✅ Future: profit targets, trailing stops, time-based exits
- ✅ Data is tiny (~10 MB for 3 months), no reason to optimize

### Why Local Caching?
- ✅ 95% faster iteration when tweaking parameters
- ✅ Can work offline
- ✅ Saves API quota
- ✅ Only 30 lines of code

### Why Vectorized Backtesting?
- ✅ Simpler pandas operations
- ✅ Faster than candle-by-candle
- ✅ Can adapt to event-driven later for live trading

### Why Poetry?
- ✅ Modern Python dependency management
- ✅ Virtual env handling automatic
- ✅ Lock file for reproducibility

---

## Commands

### Project Setup
```bash
# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your Alpaca API keys

# Run tests
poetry run pytest

# Check code style
poetry run ruff check src/
```

### Run Backtest
```bash
# Backtest recent 60 days
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
  --output ./output/trades.csv \
  --ai-analysis

# Force refresh cache
poetry run python -m trading_playbook.cli.backtest \
  --symbol QQQ \
  --start 2025-09-01 \
  --end 2025-11-04 \
  --force-refresh
```

---

## Testing Strategy

**Unit Tests:**
- Indicator calculations (EMA, ATR, SMA) - verify against known values
- Signal detection logic - synthetic data with known setups
- Stop loss tracking - bar hits vs doesn't hit stop
- Metric calculations - R-multiple, P&L formulas

**Integration Tests:**
- End-to-end backtest on small dataset (1 week)
- Validate output format (29 columns, correct types)
- Edge cases (no trades, all trades, missing data)

**Validation:**
- Manual review of sample days with chart overlay
- Cross-check against spreadsheet calculations
- Verify stop tracking with real intraday data

---

## Known Challenges & Solutions

### Challenge: Indicator Warm-up
**Problem:** EMA20 needs 20 bars, ATR needs 14 bars to stabilize
**Solution:** Start backtest from day 10, or fetch extra pre-backtest data

### Challenge: Time Zone Handling
**Problem:** Alpaca returns UTC, strategy uses ET
**Solution:** Convert immediately after fetch, store as ET in cache

### Challenge: Stop Loss Slippage
**Problem:** Real stops may fill worse than stop price
**Solution:** Phase 1: assume filled at stop (optimistic), Phase 2: add slippage model

### Challenge: Gap Detection
**Problem:** Missing bars indicate data issues
**Solution:** Validate completeness (expect 195 bars/day), skip days with <95%

---

## Git Workflow

**Branches:**
- `main` - stable code
- Feature branches for development

**Commit Conventions:**
- `feat: Add signal detection logic`
- `fix: Handle edge case in confirmation check`
- `docs: Update architecture overview`
- `test: Add unit tests for EMA calculation`

**Commit Message Policy:**
- ❌ **NEVER include Claude Code attribution or "Co-Authored-By: Claude" in commit messages**
- ✅ Write commit messages as if authored by the human developer
- ✅ Focus on what changed and why, not who wrote it

---

## Documentation Standards

This project follows **Havq Claude Documentation Standards:**
- Reference: `/Users/tanambamsinha/projects/havq-docs/claude/`
- See: `claude-md-best-practices.md`

**Key Principles:**
- Keep CLAUDE.md focused on architecture (600-800 lines target)
- Detailed system design in `docs/system-design/`
- Strategy specs separate from implementation docs
- Session histories in `docs/session-history/` (when needed, 90-day retention)

---

## Next Steps

**Immediate (Phase 1 MVP):**
1. Create Poetry project (`pyproject.toml`)
2. Set up `src/trading_playbook/` structure
3. Implement indicators module
4. Implement Alpaca data fetcher
5. Implement caching layer
6. Implement signal detection
7. Implement backtest engine
8. Run first backtest on 60 days
9. Analyze results, iterate

**See detailed implementation plan in:** [docs/system-design/architecture-overview.md](docs/system-design/architecture-overview.md)

---

*Last Updated: 2025-11-04*
*Status: Design complete, ready for implementation*
*Next: Begin Phase 1 MVP development*
