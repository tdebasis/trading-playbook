# System Architecture

**Trading Playbook** - Production-grade backtesting infrastructure for systematic strategy research

---

## Design Philosophy

### Operationalizing Research

This platform bridges the gap between research and production by treating backtesting as a first-class engineering problem. Key principles:

1. **Composability Over Monoliths** - Mix and match scanners, exit strategies, and position sizers
2. **Testability Through Separation** - Pure logic decoupled from data sources
3. **Speed Through Vectorization** - Pandas operations 10x faster than event loops
4. **Rigor Through Validation** - Walk-forward, out-of-sample testing

### Target Users

- Systematic traders validating strategy ideas
- Quantitative researchers testing hypotheses
- Engineering teams building trading infrastructure
- Portfolio managers evaluating strategy combinations

---

## System Components

### 1. Composable Backtest Engine

**Location:** `/long-edge/backend/engine/backtest_engine.py`

**Purpose:** Orchestrate strategy testing without hardcoding logic

**Interface:**
```python
from engine import BacktestEngine
from strategies import get_scanner, get_exit_strategy

scanner = get_scanner('daily_breakout', api_key, secret_key)
exit_strategy = get_exit_strategy('smart_exits')

engine = BacktestEngine(
    scanner=scanner,
    exit_strategy=exit_strategy,
    data_client=client,
    starting_capital=100000
)

results = engine.run(start_date='2024-01-01', end_date='2024-12-31')
```

**Key Innovation:** Strategy Registry pattern allows runtime composition without modifying engine code.

**Benefits:**
- Test multiple exit strategies on same entries
- A/B test scanner variations
- Eliminate 70% code duplication between backtest scripts

### 2. Scanner Layer (Entry Detection)

**Location:** `/long-edge/backend/scanner/`

**Implementations:**
- `daily_breakout_scanner.py` - Minervini/O'Neil base breakouts
- `daily_breakout_scanner_scoring.py` - Adds quality scoring (abandoned)

**Protocol:** Python PEP 544 runtime_checkable
```python
@runtime_checkable
class ScannerProtocol(Protocol):
    def scan_for_setups(self, date: str, data: pd.DataFrame) -> List[Setup]:
        """Return list of valid entry signals for given date"""
        ...
```

**Responsibilities:**
- Fetch/cache historical data
- Apply trend filters (SMA20 > SMA50)
- Detect base patterns (10-90 day consolidation)
- Validate breakouts (price > base high, volume confirmation)
- Return Setup objects with entry price, stop loss, size

**Data Flow:**
```
Alpaca API → Cache Layer → Scanner → Setup Objects → Engine
```

### 3. Exit Strategy Layer

**Location:** `/long-edge/backend/exit_strategies/`

**Implementations:**
- `smart_exits.py` - Adaptive trailing + MA breaks + momentum (PRODUCTION)
- `scaled_exits.py` - Profit-taking at 25% increments
- `hybrid_trailing.py` - Simpler adaptive trailing (DEPRECATED)

**Protocol:**
```python
@runtime_checkable
class ExitStrategyProtocol(Protocol):
    def check_exit(
        self,
        position: Position,
        current_bar: pd.Series,
        bars_held: int
    ) -> Tuple[bool, str, float]:
        """
        Returns: (should_exit, reason, exit_price)
        """
        ...
```

**Smart Exits Logic (5 Rules):**
1. **Hard Stop:** -8% from entry (intraday low)
2. **Trailing Stop:** 2× ATR → 1× ATR → 5% (profit-adaptive)
3. **MA Break:** Close < 5-day SMA (if profit <3%)
4. **Lower High:** Momentum fading after +5% profit
5. **Time Stop:** 17 days maximum hold

**Design Note:** Uses CLOSE prices only (no lookahead bias)

### 4. Data Management Layer

**Location:** `/long-edge/backend/data/`

**Components:**
- `cache.py` - SQLite + Parquet caching
- `data_client.py` - Alpaca API wrapper
- `historical_bars.py` - Batch fetching logic

**Caching Strategy:**
```
1. Check SQLite metadata (symbol, date range)
2. If cached: Load from Parquet (95% faster)
3. If missing: Fetch from Alpaca → Cache → Return
4. Cache invalidation: Manual (data immutable after market close)
```

**Performance Impact:**
- Cold run: ~30 seconds (API calls)
- Warm run: ~0.5 seconds (cache hits)
- Enables rapid iteration during development

### 5. Position Management

**Location:** `/long-edge/backend/engine/position_manager.py`

**Responsibilities:**
- Track open positions (entry, size, cost basis)
- Calculate unrealized P&L
- Enforce max position limits (3 concurrent)
- Handle exit execution (market orders at EOD)

**State Machine:**
```
PENDING → OPEN → CLOSED
         ↓
    (track highest/lowest for trailing stops)
```

---

## Architecture Patterns

### Hexagonal Architecture (Ports & Adapters)

**Core Domain (Pure Logic):**
- `/long-edge/backend/scanner/` (entry detection)
- `/long-edge/backend/exit_strategies/` (exit logic)
- `/long-edge/backend/engine/` (orchestration)

**Adapters (External Dependencies):**
- `/long-edge/backend/data/` (Alpaca API, cache)
- Backtest scripts (CLI entry points)
- Report generators (JSON, Markdown)

**Benefits:**
1. **Testability:** Core logic testable without API keys
2. **Flexibility:** Swap data sources (Alpaca → Polygon → CSV)
3. **Reusability:** Same core for backtesting and live trading

### Strategy Registry Pattern

**Problem:** Hardcoded strategy instantiation in every script

**Solution:** Centralized factory functions
```python
# strategies/__init__.py
_SCANNERS = {}
_EXIT_STRATEGIES = {}

def register_scanner(name: str):
    def decorator(factory_fn):
        _SCANNERS[name] = factory_fn
        return factory_fn
    return decorator

@register_scanner('daily_breakout')
def create_daily_breakout_scanner(api_key, secret):
    return DailyBreakoutScanner(api_key, secret)

def get_scanner(name: str, *args, **kwargs):
    return _SCANNERS[name](*args, **kwargs)
```

**Usage:**
```python
scanner = get_scanner('daily_breakout', api_key, secret)
# vs hardcoded: scanner = DailyBreakoutScanner(api_key, secret)
```

**Benefits:**
- Register new strategies without modifying engine
- Runtime strategy selection (config-driven)
- Easier A/B testing

### Walk-Forward Validation

**Problem:** Overfitting to historical data

**Approach:**
1. **Training Window:** Optimize parameters on 2024 data
2. **Validation Window:** Test on 2025 data (out-of-sample)
3. **Walk Forward:** Roll windows forward (train 2024 Q1-Q2, test Q3, etc.)

**Implementation Status:** Framework ready, not yet automated

---

## Data Flow

### Backtest Execution Flow

```
1. User: python test_smart_exits.py --start 2024-01-01 --end 2024-12-31

2. Engine Initialization:
   ├─ Load scanner (daily_breakout)
   ├─ Load exit strategy (smart_exits)
   ├─ Initialize data client (Alpaca + cache)
   └─ Create position manager

3. Daily Loop (for each trading day):
   ├─ Scanner.scan_for_setups(date) → List[Setup]
   ├─ Position Manager: Open new positions (if space available)
   ├─ For each open position:
   │  ├─ Fetch current day bar
   │  ├─ ExitStrategy.check_exit() → (exit?, reason, price)
   │  └─ If exit: Close position, record trade
   └─ Update portfolio equity

4. Results Generation:
   ├─ JSON: trade_list, summary_stats, equity_curve
   ├─ Markdown: Human-readable report
   └─ Return to caller
```

### Data Fetching Flow

```
Scanner.scan_for_setups(date='2024-03-15')
  └─> DataClient.get_historical_bars('AAPL', start='2024-01-01', end='2024-03-15')
       └─> Cache.check('AAPL', '2024-01-01', '2024-03-15')
            ├─ HIT: Return pd.DataFrame from Parquet (0.1s)
            └─ MISS:
                 ├─> Alpaca API fetch (5s)
                 ├─> Cache.store(parquet_file)
                 └─> Return pd.DataFrame
```

---

## Performance Characteristics

### Vectorized vs Event-Driven

**Vectorized (Current):**
- Entire date range loaded into pandas DataFrame
- Operations: `df[df['close'] > df['sma20']]`
- Speed: 0.5s for 3-month backtest (cached)
- Limitation: Requires all data upfront

**Event-Driven (Future for live trading):**
- Process bar-by-bar in real-time
- Operations: `if bar.close > bar.sma20:`
- Speed: Real-time (one bar at a time)
- Benefit: Adapts to live data streams

**Current Strategy:** Use vectorized for backtesting, adapt to event-driven for paper/live trading.

### Bottlenecks

1. **API Calls:** 5-30s per symbol (mitigated by cache)
2. **Indicator Calculations:** Negligible with pandas
3. **File I/O:** Parquet read ~0.01s per file
4. **Exit Logic:** 0.001s per position per day

**Optimization:** Caching provides 95%+ speedup. Further optimization not needed.

---

## Technology Choices

### Why Python?

- **Pandas:** Vectorized timeseries operations
- **NumPy:** Fast numerical computations
- **Rich Ecosystem:** TA-Lib, scipy, scikit-learn available
- **Alpaca SDK:** Official Python client

**Alternative Considered:** Rust (10x faster but 10x slower development)

### Why Alpaca?

- **Unified Platform:** Data + paper trading + live trading
- **Cost:** $99/month SIP data (vs $300+ for competitors)
- **Commission-Free:** No execution costs
- **Python SDK:** Well-maintained, documented

**Alternatives:** Interactive Brokers (complex), Polygon (data-only)

### Why SQLite + Parquet?

- **SQLite:** Metadata index (which symbols cached, date ranges)
- **Parquet:** Columnar storage (fast pandas read/write)
- **No Server:** Embedded database (simplicity)

**Alternatives:** PostgreSQL (overkill), CSV (10x slower reads)

### Why Markdown Reports?

- **Readability:** Human-first, version-controllable
- **Tooling:** GitHub renders beautifully
- **Searchability:** Full-text search across all reports

**Alternatives:** Jupyter notebooks (harder to diff), PDFs (not searchable)

---

## Testing Strategy

### Validation Approach

1. **Unit Tests:** Core logic (indicators, entry rules) - **TODO**
2. **Integration Tests:** Scanner + data client - **PARTIAL**
3. **Backtest Validation:** Multiple time periods, market regimes
4. **Walk-Forward:** Out-of-sample performance

### Current Test Coverage

- **Backtests Completed:** 15+ across different periods
- **Reports Generated:** 3 detailed markdown reports
- **Validation Status:** Yellow light (promising but needs more data)

### Sample Size Requirements

- **Minimum:** 30 trades for statistical validity
- **Target:** 50+ trades across multiple market conditions
- **Current:** 11 trades (Q3 2025 Smart Exits) - **INSUFFICIENT**

**Next Steps:** Extend testing to 2024 Q4, 2025 Q1-Q2 for larger sample.

---

## Future Architecture

### Short Term (Next 3 Months)

1. **Complete Interface Standardization** (86% → 100%)
2. **Automated Walk-Forward Testing** (config-driven)
3. **Parameter Optimization** (gradient-free methods)
4. **Multi-Strategy Portfolio** (combine Smart + Scaled exits)

### Medium Term (6-12 Months)

1. **Paper Trading Mode** (real-time signal detection)
2. **Event-Driven Engine** (adapt from vectorized)
3. **WebSocket Integration** (live market data)
4. **Monitoring Dashboard** (track paper trades)

### Long Term (12+ Months)

1. **Cloud Deployment** (GCP Cloud Run)
2. **Live Trading** (if paper trading successful)
3. **Multi-Strategy Manager** (allocate capital across strategies)
4. **Machine Learning** (signal quality scoring)

---

## Lessons Learned

### What Worked ✅

1. **Composable Architecture:** Engine reuse across 15+ backtests
2. **Caching Layer:** 95% speedup enabled rapid iteration
3. **Markdown Reports:** Easy to share, version, and search
4. **Strategy Registry:** Zero engine changes for new strategies

### What Didn't Work ❌

1. **Scoring System:** Losers scored HIGHER than winners (abandoned)
2. **Intraday Strategy:** -54% loss, pivoted to daily
3. **Hybrid Trailing:** 20% win rate (Q1 2024), replaced with Smart Exits

### Key Insights

1. **Entry Quality > Exit Strategy:** Good setups make exits easy
2. **Sample Size Matters:** 5 trades insufficient, need 30+
3. **Market Regime Matters:** Breakouts need trending markets
4. **Caching is Critical:** Don't iterate without it

---

## Repository Structure

```
trading-playbook/
├── ARCHITECTURE.md              # This file
├── README.md                    # Project overview
├── .env.example                 # Environment template
│
├── long-edge/                   # PRODUCTION STRATEGY
│   ├── README.md                # Strategy overview
│   ├── backend/
│   │   ├── scanner/             # Entry detection
│   │   ├── exit_strategies/     # Exit logic
│   │   ├── engine/              # Backtest orchestration
│   │   ├── data/                # Caching + API
│   │   └── strategies/          # Registry pattern
│   ├── docs/
│   │   ├── backtest-reports/    # Performance analysis
│   │   ├── archived/            # Abandoned experiments
│   │   └── session-history/     # Development log (.gitignore'd)
│   ├── backtest-results/        # JSON outputs
│   │   ├── 2024/
│   │   ├── 2025/
│   │   └── experiments/
│   └── config/                  # Strategy configurations
│
├── docs/                        # RESEARCH DOCS
│   ├── strategies/              # QQQ DP20 spec (not implemented)
│   ├── system-design/           # Architecture docs
│   └── analysis/                # Performance frameworks
│
└── src/trading_playbook/        # SHARED INFRASTRUCTURE
    ├── core/                    # Pure logic
    └── adapters/                # Data fetchers
```

---

## Contact & Contributing

**Purpose:** Research platform for systematic trading infrastructure

**Status:** Active development, not production trading

**Contributions:** Design discussions welcome - see `/docs/system-design/`

---

**Last Updated:** 2025-11-08
**Author:** Engineering-focused backtesting platform
