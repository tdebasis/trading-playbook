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

**Location:** `/backend/engine/backtest_engine.py`

**Purpose:** Orchestrate strategy testing without hardcoding logic

**Interface:**
```python
from backend.engine.backtest_engine import BacktestEngine
from backend.scanner.long.daily_breakout_moderate import DailyBreakoutScannerModerate
from backend.strategies import get_exit_strategy

scanner = DailyBreakoutScannerModerate(api_key, secret_key)
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

**Location:** `/backend/scanner/long/` (long positions), `/backend/scanner/short/` (short positions - placeholder)

**Implementations:**
- `daily_breakout_scanner.py` - Minervini/O'Neil base breakouts (original)
- `daily_breakout_moderate.py` - Moderate risk breakouts (PRODUCTION)
- `daily_breakout_relaxed.py` - Relaxed entry criteria
- `daily_breakout_very_relaxed.py` - Very relaxed entry criteria
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

**Location:** `/backend/strategies/long/exits/` (long positions), `/backend/strategies/short/` (short positions - placeholder)

**Implementations:**
- `smart_exits.py` - Adaptive trailing + MA breaks + momentum (PRODUCTION)
- `scaled_exits.py` - Profit-taking at 25% increments
- `trend_following_75.py` - Trend-following with 75% win rate target

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

**Location:** `/backend/data/`

**Components:**
- `cache.py` - SQLite + Parquet caching
- `database.py` - Database utilities

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

**Location:** `/backend/execution/position_manager.py`

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
- `/backend/scanner/long/` and `/backend/scanner/short/` (entry detection)
- `/backend/strategies/long/exits/` and `/backend/strategies/short/` (exit logic)
- `/backend/engine/` (orchestration)
- `/backend/interfaces/` (protocol definitions)

**Adapters (External Dependencies):**
- `/backend/data/` (data management and caching)
- `/backend/execution/` (trade execution)
- Backtest scripts (CLI entry points)
- Report generators (JSON, Markdown)

**Benefits:**
1. **Testability:** Core logic testable without API keys
2. **Flexibility:** Swap data sources (Alpaca → Polygon → CSV)
3. **Reusability:** Same core for backtesting and live trading

### Strategy Registry Pattern

**Problem:** Hardcoded strategy instantiation in every script

**Solution:** Centralized factory functions in `backend/strategies/long/registry.py`
```python
# backend/strategies/long/registry.py
_EXIT_STRATEGIES = {}

def register_exit_strategy(name: str):
    def decorator(cls):
        _EXIT_STRATEGIES[name] = cls
        return cls
    return decorator

@register_exit_strategy('smart_exits')
class SmartExits:
    def check_exit(self, position, current_bar, bars_held):
        # Exit logic...
        pass

def get_exit_strategy(name: str, *args, **kwargs):
    return _EXIT_STRATEGIES[name](*args, **kwargs)
```

**Usage:**
```python
from backend.strategies import get_exit_strategy
exit_strategy = get_exit_strategy('smart_exits')
# vs hardcoded: from backend.strategies.long.exits.smart_exits import SmartExits
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
├── .env.example                 # Environment template (gitignored)
│
├── backend/                     # CORE INFRASTRUCTURE
│   ├── scanner/                 # Entry detection scanners
│   │   ├── long/                # Long position scanners
│   │   │   ├── daily_breakout_scanner.py          # Original Minervini/O'Neil
│   │   │   ├── daily_breakout_moderate.py         # PRODUCTION scanner
│   │   │   ├── daily_breakout_relaxed.py          # Relaxed entry criteria
│   │   │   ├── daily_breakout_very_relaxed.py     # Very relaxed criteria
│   │   │   ├── daily_breakout_scanner_scoring.py  # With quality scoring (abandoned)
│   │   │   └── market_scanner.py                  # Market-wide screening
│   │   └── short/               # Short position scanners (placeholder)
│   │
│   ├── strategies/              # Strategy registry and implementations
│   │   ├── long/                # Long position strategies
│   │   │   ├── exits/           # Exit strategy implementations
│   │   │   │   ├── smart_exits.py           # Adaptive trailing (PRODUCTION)
│   │   │   │   ├── scaled_exits.py          # Profit-taking at 25% increments
│   │   │   │   └── trend_following_75.py    # 75% win rate target
│   │   │   └── registry.py      # Strategy registration and factory functions
│   │   └── short/               # Short position strategies (placeholder)
│   │
│   ├── engine/                  # Backtest orchestration
│   │   ├── backtest_engine.py   # Main backtest engine
│   │   ├── comparison.py        # Strategy comparison framework
│   │   └── metrics.py           # Performance metrics calculation
│   │
│   ├── execution/               # Trade execution and position management
│   │   ├── position_manager.py  # Position tracking and management
│   │   └── trade_executor.py    # Trade execution logic
│   │
│   ├── data/                    # Data management and caching
│   │   ├── cache.py             # SQLite + Parquet caching
│   │   └── database.py          # Database utilities
│   │
│   ├── interfaces/              # Protocol definitions (PEP 544)
│   │   ├── scanner.py           # ScannerProtocol
│   │   ├── exit_strategy.py     # ExitStrategyProtocol
│   │   ├── position_sizer.py    # PositionSizerProtocol
│   │   ├── position.py          # Position data structures
│   │   └── backtest.py          # BacktestProtocol
│   │
│   ├── config/                  # Strategy configurations
│   │   └── universe.py          # Stock universe definitions
│   │
│   ├── brain/                   # ML and optimization (future)
│   │   └── claude_engine.py     # AI-powered analysis
│   │
│   ├── api/                     # API endpoints (future)
│   │
│   ├── core/                    # Core utilities
│   │   └── orchestrator.py      # System orchestration
│   │
│   ├── backtest/                # Historical backtest scripts
│   │   ├── tests/               # Test suite
│   │   └── *.py                 # Various backtest experiments
│   │
│   └── examples/                # Example usage scripts
│       ├── compare_exits.py     # Exit strategy comparison
│       └── simple_backtest.py   # Simple backtest example
│
├── docs/                        # DOCUMENTATION
│   ├── backtest-reports/        # Performance analysis reports
│   │   ├── 2024-Q1-hybrid-trailing.md
│   │   ├── 2024-Q2Q3-exit-strategy-comparison-executed-2025-11-08.md
│   │   ├── 2025-08-10-smart-exits.md
│   │   ├── 2025-Jan-Nov-scanner-parameter-comparison-executed-2025-11-09.md
│   │   └── 2025-exit-optimization-trend-following-75-executed-2025-11-09.md
│   ├── archived/                # Abandoned experiments documentation
│   ├── workflows/               # Trading workflows
│   └── research-private/        # Private research (GITIGNORED)
│       └── session-history/     # Development session logs
│
├── tests/                       # INTEGRATION TESTS
│   ├── backtest_tests/          # Backtest validation tests
│   ├── volume_tests/            # Volume filter tests
│   ├── test_composable_engine.py
│   ├── test_exit_strategy.py
│   ├── test_interface_integration.py
│   └── test_scaled_exits.py
│
├── scripts/                     # UTILITY SCRIPTS
│   ├── analysis/                # Analysis scripts
│   └── operations/              # Operational scripts
│
├── compare_*.py                 # STRATEGY COMPARISON SCRIPTS (root level)
│   ├── compare_exits_6month.py
│   ├── compare_scanner_params_2025.py
│   └── compare_exit_optimization_2025.py
│
├── test_3month_verification.py  # Verification backtest
├── backtest.py                  # Main backtest entry point
├── run.py                       # System runner
├── monitor.py                   # System monitor
└── start_trading.sh             # Trading system startup script
```

**Key Organizational Principles:**

1. **Direction-Based Organization**: Scanners and strategies are organized by long/short direction
2. **Backend Centralization**: All core logic lives in `/backend/`
3. **Security**: Private research and sensitive data gitignored in `docs/research-private/`
4. **Comparison Scripts**: Strategy comparison scripts at root level for easy access
5. **Modularity**: Clear separation between scanners, strategies, execution, and data layers

---

## Contact & Contributing

**Purpose:** Research platform for systematic trading infrastructure

**Status:** Active development, not production trading

**Contributions:** Design discussions welcome - see `/docs/system-design/`

---

**Last Updated:** 2025-11-09
**Author:** Engineering-focused backtesting platform
**Commit:** bc35a83 - Complete repository reorganization to flat structure
