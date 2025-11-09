# Scripts Directory

Utility scripts for operations, analysis, and development tasks.

---

## Directory Structure

```
scripts/
├── operations/       # Production and operational scripts
├── analysis/         # Data analysis and research scripts
└── README.md
```

---

## Operations Scripts (`operations/`)

Scripts for running and managing the trading system:

### control.sh
Control script for managing trading operations.

### check_data_access.sh
Diagnostics script to verify Alpaca API connectivity and data access.

### run_all_backtests.sh
Batch script to run multiple backtest configurations sequentially.

**Usage:**
```bash
cd /long-edge
./scripts/operations/run_all_backtests.sh
```

---

## Analysis Scripts (`analysis/`)

Python scripts for analyzing backtest results and trade data:

### analyze_actual_trades.py
Analyzes actual trade execution data.
- Compares entry/exit prices
- Calculates slippage
- Reviews exit reasons

### analyze_pltr_detailed.py
Detailed analysis of PLTR (Palantir) trades.
- Why did PLTR setups pass/fail scanner?
- Pattern analysis specific to PLTR
- Volume filter impact on PLTR

### analyze_smart_exits.py
Analyzes Smart Exits strategy performance.
- Exit reason distribution
- Profit factor by exit type
- Optimal exit parameter analysis

### debug_scoring.py
Debugging script for scoring system (abandoned experiment).
- Tests scoring calculations
- Validates historical data requirements
- Used during scoring system development (Nov 2025)

**Usage:**
```bash
cd /long-edge
python scripts/analysis/analyze_smart_exits.py
```

---

## Main Operational Scripts (Root)

Some operational scripts remain in `/long-edge/` root for easy access:

- `start_trading.sh` - Main launcher (kept in root for convenience)
- `run.py` - Python run script
- `monitor.py` - Monitoring script
- `backtest.py` - Backtest runner

---

## Related Documentation

- **Backtest Guide:** `/docs/BACKTEST_GUIDE.md`
- **Operations Guide:** `/docs/AUTO_START_GUIDE.md`
- **Analysis Framework:** `/docs/BACKTEST_ANALYSIS.md`

---

*Scripts organized by purpose: operations for running the system, analysis for understanding results.*
