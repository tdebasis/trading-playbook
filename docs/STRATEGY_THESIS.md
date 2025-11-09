# LongEdge - Daily Breakout Momentum Strategy

**Project Name:** LongEdge
**Strategy Name:** Daily Breakout Momentum (Minervini/O'Neil Style)
**Date Created:** November 5, 2025
**Last Updated:** November 5, 2025
**Status:** Under Development - Walk-Forward Validation Phase
**Timeframe:** Daily (end-of-day analysis)
**Market:** US Equities (Growth Stocks)
**Direction:** Long Only (Bull Market Strategy)

---

## 📋 Strategy Description

This is a systematic momentum strategy that identifies growth stocks breaking out of consolidation bases and rides the trend until momentum breaks. Inspired by Mark Minervini's SEPA methodology and William O'Neil's CAN SLIM framework, we scan a curated universe of high-quality growth stocks daily, enter on confirmed breakouts with volume expansion, and exit using adaptive trailing stops that tighten as profits grow.

**What makes this different:**
- **Daily timeframe** (not intraday noise)
- **Quality over quantity** (23 hand-picked growth leaders, not thousands of penny stocks)
- **Smart exits** (adaptive trailing stops that lock in gains, not fixed profit targets)
- **Trend-following** (only trade Stage 2 uptrends, sit out when market choppy)

**Target trader:** Someone who wants systematic momentum exposure without watching screens all day. Check positions once per day (after market close), make decisions, and let winners run.

---

## 📈 Strategy Thesis

### Core Philosophy

**"Catch institutional accumulation during consolidation breakouts, ride the momentum until it breaks."**

This strategy is based on the proven methodologies of Mark Minervini (US Investing Champion) and William O'Neil (founder of Investor's Business Daily). Both built their fortunes identifying stocks breaking out of consolidation bases with proper trend alignment and volume confirmation.

### Market Edge

Our edge comes from:

1. **Timing:** Enter when stocks break above consolidation bases (supply has been absorbed)
2. **Trend Following:** Only trade stocks in confirmed Stage 2 uptrends (price > MA20 > MA50)
3. **Quality Filter:** Focus on growth stocks near 52-week highs (relative strength leaders)
4. **Smart Exits:** Adaptive trailing stops that tighten as profits grow (lock in gains)

### What We're NOT Doing

- ❌ **NOT intraday trading** (too noisy, high slippage, failed in testing at -54%)
- ❌ **NOT catalyst-dependent** (news helps but isn't required)
- ❌ **NOT buy-and-hold** (we exit when momentum breaks)
- ❌ **NOT counter-trend** (only trade with the trend)

---

## 🎯 Entry Criteria

### Scanner Universe & Target Profile

#### **Current Universe: 23 Hand-Picked Growth Stocks**

**Tech Momentum Leaders (9):**
- NVDA, TSLA, AMD, PLTR, SNOW, CRWD, NET, DDOG, ZS
- **Why:** High beta, institutional favorites, strong secular trends (AI, cloud, cybersecurity)
- **Characteristics:** $10B+ market cap, high revenue growth (30%+), volatile (perfect for momentum)

**Mega-Cap Quality (5):**
- AAPL, MSFT, GOOGL, AMZN, META
- **Why:** Market leaders, stable but still capable of 20-40% runs
- **Characteristics:** $500B+ market cap, lower volatility but enormous institutional flows

**Biotech Volatility (4):**
- MRNA, BNTX, SAVA, SGEN
- **Why:** Catalyst-rich (FDA approvals, clinical trials), explosive moves
- **Characteristics:** Binary outcomes, high risk/reward, strong trending when working

**Fintech & E-commerce (4):**
- SHOP, SQ, COIN, RBLX
- **Why:** Growth + innovation, retail interest, strong technical setups
- **Characteristics:** Disruptive business models, high growth, sentiment-driven

**Meme/Retail Interest (2):**
- GME, AMC
- **Why:** Extreme momentum when retail piles in, volume spikes
- **Characteristics:** Low fundamental value but incredible momentum potential

#### **What We're Looking For (Company Profile)**

**Ideal Candidate:**
```
Market Cap: $3B - $500B (sweet spot for momentum)
Revenue Growth: 20%+ annually
Price Range: $10 - $500 (liquid, not penny stocks)
Sector: Tech, Biotech, Fintech, Consumer (high-growth sectors)
Volatility: 30-60% annualized (enough movement for profits)
Institutional Ownership: 40-80% (smart money involved, not too crowded)
```

**We AVOID:**
- Utilities, REITs (low volatility, dividend-focused)
- Financial institutions (banks, insurance - regulated, slow)
- Commodity stocks (oil, mining - different dynamics)
- Penny stocks <$10 (manipulation risk, low liquidity)
- Over-owned crowded trades (everyone already in)

#### **Data Source: Alpaca Markets API**

**Current Setup:**
- **API:** Alpaca Market Data API (Stock Historical Data Client)
- **Subscription:** Algo Trader Plus ($99/month) - **ACTIVE**
- **Data Feed:** SIP (Securities Information Processor) - consolidated from all exchanges
- **Coverage:** All US-listed stocks (NYSE, NASDAQ, AMEX)

**Why SIP over IEX:**
- **SIP:** Consolidated data from ALL exchanges (100% market volume)
- **IEX:** Single exchange only (~2-3% of market volume)
- **Impact:** More accurate volume readings, better breakout detection
- **Cost:** Included in $99/month subscription

**What We Pull:**
```python
# Daily bars for trend analysis
- Timeframe: 1 Day
- Fields: Open, High, Low, Close, Volume, VWAP
- Lookback: Unlimited (200+ days for 200-day MA calculation)

# Calculated On-The-Fly:
- SMA 20, SMA 50, SMA 200 (trend filters)
- EMA 20, EMA 50, EMA 200 (alternative trend metrics)
- ATR 10-day (for trailing stops)
- 52-week high (relative strength filter)
- 20-day average volume (for volume ratio)
```

**API Benefits (Paid Tier):**
- **Rate Limits:** 200 requests/minute (more than adequate for 23-stock universe)
- **Historical Data:** Unlimited lookback (can backtest years of data)
- **Data Quality:** SIP consolidated feed (professional-grade accuracy)
- **Real-time:** Available but not needed (we're EOD strategy)
- **Cost:** $99/month (vs $200+/month for alternatives like Polygon.io)

#### **Future Universe Expansion**

**Phase 2 (100+ stocks):**
- Scan all stocks with $5B+ market cap
- Filter by sector (tech, healthcare, consumer)
- Automated screening via Alpaca screener API

**Phase 3 (Full market scan):**
- Scan 3,000+ US stocks
- Requires better data infrastructure (database caching)
- Or switch to Polygon.io / Alpha Vantage for broader coverage

**Current Constraint:** Manual universe keeps strategy focused on quality. Full market scan adds complexity without proven benefit yet.

*Note: Can expand to full market scan with additional data sources*

### Required Filters (ALL must pass)

#### 1. Price Quality
```
Minimum price: $10.00
Purpose: Avoid penny stocks, ensure liquidity
```

#### 2. Trend Confirmation
```
Current close > 20-day SMA
AND
20-day SMA > 50-day SMA

Purpose: Only trade stocks in Stage 2 uptrend
Why SMA not EMA: Testing showed SMA slightly better (EMA didn't help)
```

#### 3. Relative Strength
```
Within 25% of 52-week high

Purpose: Focus on market leaders, not laggards
Logic: Strongest stocks make new highs first
```

#### 4. Consolidation Base
```
Duration: 10-90 days
Volatility: ≤12% (high-low range / base high)

Purpose: Find stocks that have digested prior gains
Pattern: Tight consolidation = supply absorbed
```

#### 5. Breakout Confirmation
```
Current close > consolidation high

Purpose: Trigger when stock breaks resistance
Logic: Breakout = new demand overwhelming supply
```

#### 6. Volume Expansion
```
Current volume ≥ 1.2x average (20-day)

Purpose: Confirm institutional interest
Industry standard: 1.5x (we use 1.2x for quality growth stocks)

⚠️ KNOWN ISSUE: May be too strict for PLTR-style quiet accumulation
Testing 0.8x threshold for mega-caps
```

### Entry Execution

**Timing:** End of day (EOD) analysis
**Entry Price:** Next day's open OR current day's close (backtesting)
**Position Size:** 30% of capital per position
**Max Positions:** 3 simultaneous (90% max capital deployed)

### Scoring System (0-10)

Each candidate gets scored based on:

| Criteria | Points | Thresholds |
|----------|--------|------------|
| **Trend Quality** | 0-3 pts | Price > MA20 > MA50 (+1.5), Within 15% of 52w high (+1.5) |
| **Volume** | 0-2 pts | 2x+ volume (+2.0), 1.2x volume (+1.0) |
| **Base Quality** | 0-3 pts | 15-60 day base (+1.5), <5% volatility (+1.5) |
| **Relative Strength** | 0-2 pts | 1.5x market outperformance (+2.0) |

**Entry Threshold:** Score ≥ 4.0/10 (currently rule-based, not Claude-driven)

---

## 🚪 Exit Criteria

**Philosophy:** "Cut losses quickly, let winners run with adaptive trailing stops"

Exit when **FIRST** of these conditions triggers (checked in order):

### 1. Hard Stop Loss (-8%)
```
Exit Price: Entry price × 0.92
When: Always active from entry
Purpose: Protect capital on failed breakouts
Priority: HIGHEST

Example:
Entry: $100
Hard stop: $92
If price drops to $92 → EXIT immediately
```

### 2. Trailing Stop (Hybrid - Adaptive)
```
Only Active: After +5% unrealized profit
Calculation: Based on highest high achieved

Tightening Schedule:
┌─────────────────┬───────────────────────┐
│ Profit Level    │ Trailing Stop         │
├─────────────────┼───────────────────────┤
│ +5% to +10%     │ 2x ATR below peak     │
│ +10% to +15%    │ 1x ATR below peak     │
│ +15%+           │ 5% below peak (tight) │
└─────────────────┴───────────────────────┘

Purpose: Lock in profits as they grow
Logic: Higher profit = tighter stop (protect gains)

Example:
Entry: $100
Peak: $115 (+15%)
Trailing stop: $115 × 0.95 = $109.25
If price drops to $109.25 → EXIT
```

### 3. 5-Day MA Break
```
Only Active: After +3% unrealized profit
Trigger: Close < 5-day Simple Moving Average
Purpose: Exit when short-term trend breaks
Priority: Medium

Example:
Entry: $100
Current: $105 (+5%)
5-day MA: $104
If close drops to $103.50 (below MA) → EXIT
```

### 4. Lower High Pattern
```
Only Active: After +5% unrealized profit
Trigger: Today's high < Yesterday's high
Purpose: Exit when momentum weakens
Logic: Lower highs = uptrend exhaustion

Example:
Entry: $100
Day 5 high: $108
Day 6 high: $106 (lower high)
→ EXIT (momentum fading)
```

### 5. Time Stop (15 Days)
```
When: Hold period ≥ 15 calendar days
Purpose: Force capital recycling
Logic: If no exit triggered in 15 days, setup likely failed

Note: This is a BACKUP exit only
Most trades exit via stops or MA breaks within 5-10 days
```

---

## 📊 Position Management

### Risk Management Rules

```python
Max Risk Per Trade: 2% of account
Max Position Size: 30% of account
Max Simultaneous Positions: 3
Max Capital Deployed: 90% (3 × 30%)
Daily Loss Limit: $500 (circuit breaker)
```

### Position Sizing Calculation

```
Account Size: $100,000
Position Size: $30,000 (30%)

Entry Price: $50
Shares: $30,000 / $50 = 600 shares

Hard Stop: $50 × 0.92 = $46
Risk Per Share: $50 - $46 = $4
Total Risk: $4 × 600 = $2,400 (2.4% of account)
```

### Trade Frequency

**Expected:** 1-3 trades per week (highly variable)

**Actual Test Results:**
- Q1 2024: 16 trades in 66 days (~1.2/week)
- Q2 2024: 11 trades in 66 days (~0.8/week)
- Q3 2025: 19 trades in 66 days (~1.4/week)

**Market Dependency:** More trades in trending markets, fewer in chop

---

## 🧠 Strategy Logic Flow

```
┌─────────────────────────────────────────────────┐
│         DAILY EOD PROCESS                       │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  1. CHECK EXISTING POSITIONS                    │
│     • Update highest high                       │
│     • Calculate trailing stops                  │
│     • Check all exit conditions                 │
│     • Close positions if triggered              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  2. SCAN FOR NEW ENTRIES (if < 3 positions)     │
│     • Scan 23-stock universe                    │
│     • Apply 6 entry filters                     │
│     • Score candidates (0-10)                   │
│     • Sort by score (highest first)             │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  3. ENTER TOP CANDIDATES                        │
│     • Take top-scoring (≥4.0)                   │
│     • Skip if already held                      │
│     • Fill available position slots             │
│     • Set hard stops immediately                │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  4. UPDATE EQUITY CURVE                         │
│     • Calculate total account value             │
│     • Track daily P&L                           │
│     • Log all decisions                         │
└─────────────────────────────────────────────────┘
```

---

## 📈 Expected Performance

### Target Metrics

```
Win Rate: 55-65%
Average Win: $500-$800 per trade
Average Loss: $500-$700 per trade
Profit Factor: >1.5x
Max Drawdown: <15%
Sharpe Ratio: >1.0
```

### Historical Backtest Results

**Optimized Periods (Used for Tuning):**

| Period | Return | Win Rate | Trades | Max DD |
|--------|--------|----------|--------|--------|
| Q1 2024 | +5.80% | 56.2% | 16 | -3.2% |
| Q2 2024 | -0.71% | 63.6% | 11 | -2.8% |
| Q2 2025 | -1.43% | 50.0% | 20 | -4.1% |
| Q3 2025 | +6.50% | 57.9% | 19 | -2.9% |
| **Average** | **+2.54%** | **56.9%** | **16.5** | **-3.3%** |

**Validation Periods (Unseen - Testing Now):**

| Period | Return | Win Rate | Trades | Status |
|--------|--------|----------|--------|--------|
| Q3 2024 | TBD | TBD | TBD | Testing |
| Q4 2024 | TBD | TBD | TBD | Testing |

*Note: Strategy needs 2%+ average return on unseen data to pass validation*

---

## ⚠️ Known Issues & Limitations

### 1. **Volume Filter Too Strict (Critical)**

**Problem:** 1.2x volume requirement filters out quiet accumulation phases

**Evidence:** PLTR analysis shows:
- Q1 2024: Missed +65.9% move (volume only 0.9x)
- Q1 2025: Missed +66.8% move (volume only 0.7x)
- When scanner caught PLTR, entries were 30-50% late into move

**Impact:** Missing 50%+ of best growth stock moves

**Proposed Fix:**
```python
# Option 1: Lower global threshold
min_volume_ratio = 0.8  # From 1.2

# Option 2: Tier-based by stock quality
if symbol in ['PLTR', 'NVDA', 'AAPL']:
    min_volume_ratio = 0.8  # Mega-caps
else:
    min_volume_ratio = 1.2  # Standard
```

**Status:** Testing required

### 2. **Market Regime Dependency**

**Problem:** Strategy only works in trending markets

**Evidence:**
- Aug-Oct 2025 (choppy): -1.75% (stocks consolidated, didn't trend)
- Q1 2024 (trending): +5.80% (breakouts followed through)

**Impact:** Unprofitable in consolidation/ranging markets

**Proposed Fix:**
```python
# Add market regime filter
def is_market_trending():
    spy_price > spy_50ma > spy_200ma
    AND spy_adx > 25  # Directional movement
    return True/False

# Only trade when market trending
if is_market_trending():
    scan_for_entries()
else:
    close_positions()  # Go to cash
```

**Status:** Not implemented

### 3. **Small Sample Size**

**Problem:** Only 23 stocks scanned

**Impact:** Only 11-20 trades per quarter (low sample for statistics)

**Proposed Fix:** Expand universe to 100+ stocks or full market scan

**Blocker:** Need better data source (Alpaca universe limited)

### 4. **Claude Engine Unused**

**Problem:** Built AI decision engine, but backtests use rule-based entries

**Impact:** Don't know if Claude adds value vs simple rules

**Test Needed:**
- Strategy A: Score ≥ 4.0 = auto-enter
- Strategy B: Claude makes final decision
- Compare results

**Status:** Not tested

---

## 🔬 Optimization History

### Changes Made (September → November 2025)

| Parameter | Original | Current | Reason |
|-----------|----------|---------|--------|
| Volume threshold | 1.5x | 1.2x | Industry standard, more trades |
| Base volatility | 8% | 12% | Matches real growth stock patterns |
| Moving average | EMA20 | SMA20 | EMA didn't improve results |
| Time stop | 10 days | 15 days | Removes false breakout failures |
| Trailing stop | Fixed 2x ATR | Hybrid (tightens) | Better profit capture |

### Walk-Forward Validation

**Methodology:**
1. Optimize on 4 periods (Q1'24, Q2'24, Q2'25, Q3'25)
2. Validate on 2 unseen periods (Q3'24, Q4'24)
3. If unseen avg return >2% → Strategy validated
4. If unseen < seen by >2% → Overfit (fail)

**Status:** In progress

---

## 🎓 Theoretical Foundation

### Why This Works (When It Works)

**1. Stage Analysis (Stan Weinstein)**
- Stage 1: Basing (accumulation)
- **Stage 2: Markup (we trade here)** ✅
- Stage 3: Distribution (topping)
- Stage 4: Decline (avoid)

We only enter Stage 2 stocks (uptrend confirmed).

**2. Volume Price Analysis (Tom Williams)**
- Breakout on volume = demand > supply
- Low volume at highs = distribution (we exit)
- High volume at lows = absorption (we wait for breakout)

**3. Relative Strength (William O'Neil)**
- Leaders make new highs first
- We only trade stocks within 25% of 52w highs
- This filters out 90% of stocks (laggards)

**4. Risk Management (Van Tharp)**
- 2% risk per trade = survive drawdowns
- Position sizing = consistent bet sizes
- R-multiple tracking = expectancy focus

---

## 🚀 Next Steps (Roadmap)

### Phase 1: Validation (Current)
- [ ] Run walk-forward test on Q3'24, Q4'24
- [ ] Validate unseen return >2%
- [ ] If pass → Ready for paper trading
- [ ] If fail → Back to optimization

### Phase 2: Volume Filter Testing
- [ ] Test 0.8x volume threshold
- [ ] Test tier-based (mega-cap vs others)
- [ ] Compare PLTR capture rates
- [ ] Measure impact on win rate

### Phase 3: Market Regime Filter
- [ ] Implement SPY trend + ADX filter
- [ ] Backtest with "go to cash" in chop
- [ ] Measure improvement in Sharpe ratio

### Phase 4: Paper Trading (30 Days)
- [ ] Run live on paper account
- [ ] Track slippage (actual vs assumed)
- [ ] Validate execution assumptions
- [ ] Build confidence

### Phase 5: Live Trading (Small Size)
- [ ] Start with 1/3 intended position size
- [ ] Trade 3 months profitably
- [ ] Scale up gradually
- [ ] Never risk >2% per trade

---

## 📚 References & Inspiration

**Books:**
- *Trade Like a Stock Market Wizard* - Mark Minervini
- *How to Make Money in Stocks* - William O'Neil
- *Stage Analysis* - Stan Weinstein
- *Trade Your Way to Financial Freedom* - Van Tharp

**Key Learnings:**
- Minervini: SEPA criteria (Stage, Entry, Pivot, Add-on)
- O'Neil: CAN SLIM methodology (consolidation + volume)
- Weinstein: Only trade Stage 2 uptrends
- Tharp: Position sizing > entry timing

---

## 📝 Version History

**v1.0 - November 5, 2025**
- Initial strategy documentation
- Current parameters: 1.2x volume, 12% base, SMA20
- Walk-forward validation in progress
- Known issue: Volume filter too strict for PLTR-style moves

---

**Document Status:** Living document - will update as strategy evolves

**Last Review:** November 5, 2025

**Next Review:** After walk-forward validation completes
