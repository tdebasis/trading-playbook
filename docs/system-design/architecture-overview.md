# System Architecture Overview

**Version:** 1.0
**Last Updated:** 2025-11-04
**Status:** Design Phase

---

## Purpose

This document describes the high-level architecture of the trading-playbook backtesting system for the QQQ DP20 strategy.

---

## Design Philosophy: Core vs Periphery

The system follows **Hexagonal Architecture** (Ports & Adapters pattern) to separate:

**CORE (Strategy Logic):**
- Pure Python functions with no I/O dependencies
- Signal detection algorithms
- Indicator calculations
- Risk management rules
- **Never changes** - stable, testable, reusable

**PERIPHERY (Adapters):**
- Data sources (Alpaca API, CSV files, etc.)
- Output destinations (CSV, GCS, MongoDB)
- Scheduling/orchestration
- **Changes freely** - swap implementations without touching core

```
┌─────────────────────────────────────────┐
│         PERIPHERY (Adapters)            │
│  ┌──────────────┐    ┌──────────────┐  │
│  │ Data Sources │    │   Writers    │  │
│  │  - Alpaca    │    │   - CSV      │  │
│  │  - CSV       │    │   - GCS      │  │
│  │  - Cache     │    │   - MongoDB  │  │
│  └──────┬───────┘    └──────▲───────┘  │
│         │                    │          │
└─────────┼────────────────────┼──────────┘
          │                    │
┌─────────▼────────────────────┴──────────┐
│           CORE STRATEGY                  │
│  ┌────────────────────────────────────┐ │
│  │  Indicators (EMA20, ATR, SMA200)   │ │
│  │  Signal Detection (DP20 Logic)     │ │
│  │  Risk Management (Stops, Exits)    │ │
│  └────────────────────────────────────┘ │
│                                          │
│  Pure Python • No I/O • Fully Testable  │
└──────────────────────────────────────────┘
```

**Benefits:**
- ✅ Core strategy testable in isolation
- ✅ Easy to swap data sources (development → production)
- ✅ Same core for backtesting, paper trading, live trading
- ✅ Changes to I/O don't break strategy logic

---

## Component Architecture

### 1. **Data Fetcher (Periphery)**

**Responsibility:** Fetch market data from external sources

**Interface:**
```python
class DataFetcher(Protocol):
    def fetch_intraday_bars(self, symbol: str, start: date, end: date) -> pd.DataFrame
    def fetch_daily_bars(self, symbol: str, start: date, end: date) -> pd.DataFrame
```

**Implementations:**
- `AlpacaDataFetcher` - Fetch from Alpaca API (Phase 1)
- `CSVDataFetcher` - Load from local files (testing)
- `CachedDataFetcher` - Wrapper with local cache logic

---

### 2. **Indicator Calculator (Core)**

**Responsibility:** Calculate technical indicators from raw price data

**Functions:**
```python
def calculate_ema(prices: pd.Series, period: int) -> pd.Series
def calculate_atr(bars: pd.DataFrame, period: int) -> pd.Series
def calculate_sma(prices: pd.Series, period: int) -> pd.Series
```

**Pure functions:**
- Input: pandas Series/DataFrame
- Output: pandas Series with calculated values
- No side effects, fully testable

---

### 3. **Signal Detector (Core)**

**Responsibility:** Implement DP20 strategy entry logic

**Function:**
```python
def detect_dp20_signals(
    intraday_bars: pd.DataFrame,
    daily_sma200: float,
    signal_window_start: time,
    signal_window_end: time
) -> pd.DataFrame:
    """
    Returns DataFrame with one row per day containing:
    - Signal detected (yes/no)
    - Entry details (time, price)
    - Technical context (EMA20, ATR at entry)
    """
```

**Logic implemented:**
1. Trend filter (open > SMA200)
2. Time window filter (10:00-10:30 AM ET)
3. Pullback detection (close < EMA20)
4. Reversal detection (close > EMA20)
5. Strength filter ((Close - Low)/(High - Low) > 0.60)
6. Confirmation (one bar, must close > EMA20)

---

### 4. **Backtest Engine (Core + Orchestration)**

**Responsibility:** Run strategy over historical data, track trades

**Function:**
```python
def run_backtest(
    intraday_data: pd.DataFrame,
    daily_data: pd.DataFrame,
    strategy_params: dict
) -> BacktestResults:
    """
    Returns:
    - Trade journal (one row per day)
    - Summary statistics
    """
```

**Process:**
1. Group intraday data by day
2. For each day:
   - Calculate indicators (EMA20, ATR from intraday, SMA200 from daily)
   - Detect entry signals
   - If entered, simulate trade through end of day
   - Track stop loss hits
   - Record exit at 3:55 PM (or stop price if hit)
3. Aggregate all trades into journal
4. Calculate summary stats (expectancy, win rate, etc.)

---

### 5. **Trade Journal Writer (Periphery)**

**Responsibility:** Output trade results

**Interface:**
```python
class TradeWriter(Protocol):
    def write_trade(self, trade_record: dict) -> None
    def finalize(self) -> None  # Close file, upload to cloud, etc.
```

**Implementations:**
- `CSVTradeWriter` - Write to local CSV (Phase 1)
- `GCSTradeWriter` - Write to Google Cloud Storage (Phase 2)
- `MongoTradeWriter` - Write to MongoDB (Phase 2)

---

### 6. **Summary Statistics Calculator (Core)**

**Responsibility:** Calculate performance metrics from trade journal

**Function:**
```python
def calculate_summary_stats(trades: pd.DataFrame) -> dict:
    """
    Returns:
    - Total trades, winners, losers
    - Win rate, average R-multiple
    - Expectancy
    - Max drawdown
    - By time-of-day stats
    - By volatility regime stats
    """
```

---

## Data Flow

### Backtesting Flow:

```
1. Data Fetcher → Fetch 2-min bars + daily bars
                ↓
2. Cache Layer → Save to local parquet (optional)
                ↓
3. Indicator Calculator → Calculate EMA20, ATR, SMA200
                ↓
4. Signal Detector → Detect entry signals (DP20 logic)
                ↓
5. Backtest Engine → Simulate trades, track stops, exits
                ↓
6. Trade Journal Writer → Output CSV with 29 columns
                ↓
7. Summary Stats → Calculate performance metrics
                ↓
8. Output → Display results + AI analysis (optional)
```

---

## Technology Stack

### Core Technologies:
- **Python 3.9+** - Primary language
- **pandas** - Data manipulation, time series analysis
- **numpy** - Numerical calculations (indicators)

### Data & API:
- **Alpaca API** - Market data provider
- **alpaca-py** - Official Python SDK

### Project Management:
- **Poetry** - Dependency management, virtual environments
- **pytest** - Testing framework
- **ruff** - Linting and formatting

### Storage:
- **Parquet** - Local data caching (fast, efficient)
- **CSV** - Trade journal output (human-readable)

### Future (Phase 2):
- **Google Cloud Storage** - Cloud data storage
- **Cloud Run** - Serverless execution
- **Cloud Scheduler** - Automated daily runs
- **MongoDB** - Trade journal database

---

## Phased Approach

### Phase 1: Local Backtesting (Current)
**Goal:** Validate DP20 strategy logic on 2-3 months of data

**Components:**
- Alpaca data fetcher (free tier, IEX data)
- Local parquet caching
- Vectorized backtest engine
- CSV output
- Summary statistics

**Environment:** Local laptop
**Cost:** $0

---

### Phase 2: Extended Backtesting
**Goal:** Test strategy on years of historical data

**Additions:**
- Alpaca paid subscription ($9/mo) for unlimited historical
- Or: slow fetching on free tier over time
- Enhanced caching strategy
- AI-powered analysis reports

**Environment:** Local laptop
**Cost:** $0-9/mo

---

### Phase 3: Paper Trading
**Goal:** Test strategy in real-time with paper money

**Additions:**
- Real-time data feed (WebSocket)
- Event-driven architecture (candle-by-candle processing)
- Paper order execution via Alpaca
- Live signal notifications
- Daily trade journaling

**Environment:** Local or cloud
**Cost:** $0-9/mo (Alpaca)

---

### Phase 4: Cloud Deployment
**Goal:** Automated, reliable, scalable execution

**Additions:**
- Containerize with Docker
- Deploy to Cloud Run
- Schedule via Cloud Scheduler
- GCS for data storage
- MongoDB for trade journal
- Monitoring and alerting

**Environment:** Google Cloud Platform
**Cost:** ~$10-20/mo (compute + storage)

---

### Phase 5: Live Trading (Future)
**Goal:** Real money trading

**Additions:**
- Risk management layer (position sizing, portfolio limits)
- Enhanced monitoring and alerts
- Trade approval workflow
- Performance tracking dashboard

**Environment:** Cloud
**Cost:** TBD

---

## Design Decisions & Rationale

### Why Alpaca?
- ✅ Free paper trading account
- ✅ Trading + data in one platform
- ✅ Good Python SDK
- ✅ Cheaper than alternatives ($9/mo vs $29/mo)
- ✅ Commission-free trading

### Why IEX Data (Free Tier)?
- ✅ Good enough for strategy development
- ✅ Price patterns identical to consolidated data
- ✅ Can upgrade to SIP later if needed
- ⚠️ Slightly incomplete volume (2-3% of market)

### Why Local Caching?
- ✅ Faster iteration during development
- ✅ Saves API quota
- ✅ Can work offline
- ✅ Reproducible backtests
- ⚠️ Only ~30 lines of code, minimal complexity

### Why Vectorized Backtesting?
- ✅ Simpler pandas operations
- ✅ Faster execution
- ✅ Same core logic can be adapted to event-driven later
- ⚠️ Need to carefully implement stateful logic (confirmations)

### Why CSV Output?
- ✅ Human-readable
- ✅ Easy to import to Excel/Google Sheets
- ✅ Compatible with all analysis tools
- ✅ Simple to implement

### Why Poetry?
- ✅ Modern Python project management
- ✅ Automatic virtual environment handling
- ✅ Lock file for reproducibility
- ✅ Easy to publish if needed

---

## Project Structure

```
trading-playbook/
├── src/
│   └── trading_playbook/
│       ├── core/               # Core strategy (pure Python)
│       │   ├── indicators.py
│       │   ├── signals.py
│       │   └── backtest.py
│       ├── adapters/           # Periphery (I/O)
│       │   ├── data_fetchers.py
│       │   ├── writers.py
│       │   └── cache.py
│       └── cli/                # Command-line interface
│           └── main.py
├── tests/
│   ├── core/                   # Core unit tests
│   └── adapters/               # Integration tests
├── data/
│   └── cache/                  # Local parquet cache
├── output/                     # Backtest results
│   ├── trades/                 # Trade journals
│   └── reports/                # Analysis reports
├── docs/                       # Documentation
│   ├── strategies/
│   ├── system-design/
│   ├── analysis/
│   └── journal-templates/
├── pyproject.toml              # Poetry config
├── CLAUDE.md                   # AI context
└── README.md
```

---

## Next Steps

1. **Implement Core Indicators** - EMA, ATR, SMA calculations
2. **Implement Signal Detector** - DP20 6-step logic
3. **Implement Alpaca Data Fetcher** - Fetch 2-min + daily bars
4. **Implement Cache Layer** - Simple parquet caching
5. **Implement Backtest Engine** - Day-by-day simulation
6. **Implement CSV Writer** - Trade journal output
7. **Test on 2-3 Months** - Validate strategy logic
8. **Iterate & Refine** - Based on backtest results

---

**Related Documents:**
- [Data Pipeline](./data-pipeline.md)
- [Backtest Engine](./backtest-engine.md)
- [Signal Detection](./signal-detection.md)
- [Deployment Strategy](./deployment.md)
