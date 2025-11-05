# Data Pipeline Architecture

**Version:** 1.0
**Last Updated:** 2025-11-04
**Status:** Design Phase

---

## Purpose

This document describes how market data flows through the system, from fetching via Alpaca API to local caching to indicator calculation.

---

## Data Sources

### Primary: Alpaca Markets API

**Why Alpaca:**
- Free paper trading account with market data access
- Trading + data in one platform (future phases)
- Good Python SDK (`alpaca-py`)
- Cost-effective ($9/mo for unlimited historical vs $29/mo competitors)
- Commission-free trading

**API Endpoints Used:**
- Stock Bars API - Historical OHLCV data
- Timeframes: 2-minute (intraday), 1-day (for SMA200)

---

## IEX Data vs SIP Data

### Understanding US Stock Market Data

The US stock market has **~13 different exchanges** where stocks trade:
- NYSE (New York Stock Exchange)
- NASDAQ
- IEX (Investors Exchange)
- ARCA, BATS, EDGX, and ~10 others

When you buy/sell a stock, your order can be filled on **any** of these exchanges.

---

### IEX Data (Alpaca Free Tier)

**What it is:**
- Data from **one exchange only**: IEX (Investors Exchange)
- IEX handles ~2-3% of total US stock market volume
- Misses trades that happened on NYSE, NASDAQ, etc.

**Implications:**
- ✅ Price patterns are accurate (pullbacks, reversals, trends look the same)
- ✅ Good enough for most retail strategies
- ⚠️ Volume numbers are lower (only 2-3% of actual volume)
- ⚠️ Occasional price differences (pennies, usually insignificant)
- ⚠️ ATR might be slightly understated (less volume = less range data)

**For DP20 Strategy:**
- ✅ Entry/exit logic based on price patterns → IEX is fine
- ✅ QQQ is highly liquid → trades on all exchanges, IEX representative
- ✅ Not doing HFT or scalping → small price differences don't matter
- ⚠️ ATR calculation might be 5-10% lower than reality

**Decision:** Use IEX for Phase 1 development, upgrade if needed.

---

### SIP Data (Alpaca Paid $9/mo or Polygon)

**What it is:**
- **S**ecurities **I**nformation **P**rocessor
- **Consolidated data from ALL exchanges**
- Complete picture of market activity
- What professional traders and quant funds use

**Advantages:**
- ✅ Complete volume data (100% of trades)
- ✅ Most accurate prices (consolidated best bid/offer)
- ✅ More accurate ATR, volatility calculations
- ✅ Professional-grade quality

**Cost:**
- Alpaca: $9/mo for unlimited historical
- Polygon.io: $29/mo for real-time + unlimited historical

**When to upgrade:**
- ✅ Moving to paper/live trading (need accuracy)
- ✅ Strategy performs well on IEX data, want to validate with SIP
- ✅ ATR-based stops seem problematic (underestimation issues)

---

## Data Requirements

### 1. Intraday 2-Minute Bars (QQQ)

**Purpose:** DP20 signal detection, entry/exit execution

**Time Range:**
- 9:30 AM - 4:00 PM ET (regular trading hours)
- 195 bars per day (390 minutes ÷ 2)

**Date Range:**
- Phase 1: Last 2-3 months (~60 trading days = 11,700 bars)
- Phase 2: Years of data (250 days/year = 48,750 bars/year)

**Fields Required:**
```python
{
    'timestamp': datetime,  # Bar open time (ET)
    'open': float,          # Open price
    'high': float,          # High price
    'low': float,           # Low price
    'close': float,         # Close price
    'volume': int,          # Share volume
}
```

**Calculated Fields (added in pipeline):**
- `ema20`: 20-period EMA of close
- `atr14`: 14-period ATR

---

### 2. Daily Bars (QQQ)

**Purpose:** 200-day SMA calculation for trend filter

**Date Range:**
- Need minimum 200 bars before backtest start date
- Example: Backtest starts 2025-09-01 → need daily bars from ~2025-01-01 (or earlier)

**Fields Required:**
```python
{
    'date': date,           # Trading date
    'open': float,          # Daily open
    'high': float,          # Daily high
    'low': float,           # Daily low
    'close': float,         # Daily close
    'volume': int,          # Daily volume
}
```

**Calculated Fields:**
- `sma200`: 200-period SMA of close

---

## Data Fetching Architecture

### AlpacaDataFetcher Class

**Responsibilities:**
1. Authenticate with Alpaca API
2. Fetch intraday 2-min bars
3. Fetch daily bars
4. Convert Alpaca response to pandas DataFrame
5. Handle rate limits and errors

**Interface:**
```python
class AlpacaDataFetcher:
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        """Initialize Alpaca client"""

    def fetch_intraday_bars(
        self,
        symbol: str,
        start: date,
        end: date
    ) -> pd.DataFrame:
        """
        Fetch 2-minute bars for symbol between dates.

        Returns DataFrame with columns:
        timestamp, open, high, low, close, volume
        """

    def fetch_daily_bars(
        self,
        symbol: str,
        start: date,
        end: date
    ) -> pd.DataFrame:
        """
        Fetch daily bars for symbol between dates.

        Returns DataFrame with columns:
        date, open, high, low, close, volume
        """
```

**Implementation Details:**
- Use `alpaca-py` SDK
- Endpoint: `StockHistoricalDataClient`
- Timeframe: `TimeFrame.Minute2` for intraday, `TimeFrame.Day` for daily
- Auto-retry on rate limit errors (exponential backoff)
- Convert timestamps to ET timezone

---

## Local Caching Strategy

### Why Cache?

**Problem:** Repeatedly fetching same data wastes time and API quota

**Example Scenario:**
```
Without cache:
- Tweak strategy parameter
- Run backtest → fetch 60 days of data (30 seconds)
- See results, tweak again
- Run backtest → fetch same 60 days again (30 seconds)
- Repeat 20 times = 10 minutes waiting

With cache:
- First run: fetch + cache (30 seconds)
- Subsequent runs: read from cache (1 second)
- Repeat 20 times = 30 seconds total
```

**Savings:** ~95% faster iteration during development

---

### Cache Implementation

**Storage Format:** Apache Parquet
- Binary format (faster than CSV)
- Compressed (smaller file size)
- Preserves data types (no parsing needed)
- Industry standard for data science

**Cache Location:**
```
data/cache/
├── qqq_2min_2025-09-01_2025-11-04.parquet
├── qqq_1day_2025-01-01_2025-11-04.parquet
└── ...
```

**Cache Key Format:**
```
{symbol}_{timeframe}_{start_date}_{end_date}.parquet
```

**CachedDataFetcher Logic:**
```python
def get_data(symbol, timeframe, start, end):
    cache_file = f"data/cache/{symbol}_{timeframe}_{start}_{end}.parquet"

    # Check if cached
    if os.path.exists(cache_file):
        print(f"✓ Using cached data: {cache_file}")
        return pd.read_parquet(cache_file)

    # Fetch from API
    print(f"→ Fetching from Alpaca: {symbol} {start} to {end}")
    data = alpaca_fetcher.fetch_bars(symbol, timeframe, start, end)

    # Save to cache
    os.makedirs("data/cache", exist_ok=True)
    data.to_parquet(cache_file)
    print(f"✓ Cached to {cache_file}")

    return data
```

---

### Cache Invalidation Strategy

**Historical Data (Past):**
- ✅ Cache forever - historical data never changes
- Only refresh if `--force-refresh` flag used

**Current Day Data:**
- ⚠️ May change during trading hours
- Option 1: Don't cache today's data
- Option 2: Cache with TTL (Time To Live) of 1 hour

**For MVP:** Cache all data forever, add `--force-refresh` flag for manual invalidation

---

## Data Validation

### Checks to Implement:

**1. Completeness Check:**
```python
# Expect 195 bars per trading day (9:30-4:00 PM, 2-min bars)
expected_bars = 195
actual_bars = df[df['date'] == '2025-11-04'].shape[0]

if actual_bars < expected_bars * 0.95:  # Allow 5% tolerance
    warn(f"Incomplete data: {actual_bars}/{expected_bars} bars")
```

**2. Gap Detection:**
```python
# Check for missing time periods
df['time_diff'] = df['timestamp'].diff()
gaps = df[df['time_diff'] > timedelta(minutes=4)]  # >2min = gap

if not gaps.empty:
    warn(f"Data gaps detected: {gaps['timestamp'].tolist()}")
```

**3. Price Sanity Checks:**
```python
# Detect anomalous prices (errors, halts, etc.)
df['price_change_pct'] = df['close'].pct_change()

anomalies = df[df['price_change_pct'].abs() > 0.05]  # >5% move in 2-min

if not anomalies.empty:
    warn(f"Anomalous price moves: {anomalies[['timestamp', 'price_change_pct']]}")
```

**4. Volume Sanity:**
```python
# Very low volume can indicate bad data
low_volume_bars = df[df['volume'] < 1000]

if low_volume_bars.shape[0] / df.shape[0] > 0.1:  # >10% low volume
    warn("Suspiciously low volume in >10% of bars")
```

---

## Time Zone Handling

### Challenge:
- Alpaca API returns timestamps in **UTC**
- Strategy logic expects **ET** (Eastern Time)
- US market hours: 9:30 AM - 4:00 PM **ET**

### Solution:

**1. Fetch in UTC (as returned by API)**
```python
# Alpaca returns: 2025-11-04 14:30:00 UTC (9:30 AM ET)
```

**2. Convert to ET immediately after fetch**
```python
df['timestamp'] = df['timestamp_utc'].dt.tz_convert('America/New_York')
# Result: 2025-11-04 09:30:00-05:00 (ET)
```

**3. Store in cache as ET**
- Parquet preserves timezone information
- No conversion needed on cache reads

**4. All logic uses ET timestamps**
- Signal window: 10:00-10:30 **ET**
- Exit time: 3:55 PM **ET**

**5. Display times in ET**
- Trade journal: all times in ET
- User-facing output: ET (with timezone label)

---

## Rate Limiting

### Alpaca Rate Limits:
- **Free tier:** 200 requests/minute
- **Paid tier:** 200 requests/minute (same, but unlimited data lookback)

### Our Usage:
- Fetch 60 days of 2-min data: **1-2 API calls** (Alpaca batches by date range)
- Fetch 200 days of daily data: **1 API call**
- **Total for typical backtest: ~3 API calls**

**Conclusion:** Rate limits are not a concern for our use case.

**But:** Implement retry logic with exponential backoff for robustness:
```python
@retry(max_attempts=3, backoff=2.0)
def fetch_with_retry(symbol, timeframe, start, end):
    try:
        return alpaca_client.get_bars(...)
    except RateLimitError as e:
        wait_time = e.retry_after or 60
        time.sleep(wait_time)
        raise  # Retry via decorator
```

---

## Data Pipeline Flow

### Full Pipeline:

```
1. Request Data
   ↓
2. Check Cache
   ├─→ HIT → Load from parquet → (skip to step 5)
   └─→ MISS → Continue to step 3
   ↓
3. Fetch from Alpaca API
   - Authenticate
   - Call StockBarsAPI
   - Get response (UTC timestamps)
   ↓
4. Process & Cache
   - Convert to pandas DataFrame
   - Convert timestamps UTC → ET
   - Validate data (completeness, gaps, sanity)
   - Save to parquet cache
   ↓
5. Calculate Indicators
   - Add EMA20 column (20-period EMA of close)
   - Add ATR14 column (14-period ATR)
   - Add SMA200 column (for daily data)
   ↓
6. Return to Backtest Engine
   - DataFrame ready for signal detection
```

---

## Error Handling

### Scenarios to Handle:

**1. API Authentication Failure:**
```python
try:
    client = StockHistoricalDataClient(api_key, secret_key)
except AuthenticationError:
    print("ERROR: Invalid Alpaca API credentials")
    print("Check ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables")
    sys.exit(1)
```

**2. Network Errors:**
```python
try:
    bars = client.get_bars(request)
except (ConnectionError, Timeout):
    print("ERROR: Network connection failed")
    print("Retrying in 5 seconds...")
    time.sleep(5)
    # Retry logic
```

**3. Invalid Date Range:**
```python
if start_date > end_date:
    raise ValueError(f"Invalid date range: {start_date} to {end_date}")

if start_date > date.today():
    raise ValueError(f"Start date {start_date} is in the future")
```

**4. No Data Returned:**
```python
if bars.empty:
    warn(f"No data returned for {symbol} from {start} to {end}")
    # Possible reasons: non-trading days, symbol doesn't exist, date too far back
```

**5. Cache Corruption:**
```python
try:
    df = pd.read_parquet(cache_file)
except Exception as e:
    warn(f"Cache file corrupted: {cache_file}")
    os.remove(cache_file)
    # Re-fetch from API
```

---

## Configuration

### Environment Variables:

```bash
# Alpaca API credentials
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here

# Alpaca environment
ALPACA_PAPER=true  # true for paper trading, false for live

# Cache settings
DATA_CACHE_DIR=./data/cache
CACHE_ENABLED=true
```

### Config File (config.yaml):

```yaml
data:
  provider: alpaca
  cache:
    enabled: true
    directory: ./data/cache
    format: parquet

alpaca:
  paper: true
  rate_limit:
    max_retries: 3
    backoff_seconds: 2

validation:
  min_bars_per_day: 185  # 95% of 195
  max_price_change_pct: 0.05  # 5%
  min_volume: 1000
```

---

## Performance Considerations

### Fetch Performance:
- 60 days × 195 bars = 11,700 bars
- API fetch time: ~5-10 seconds
- Cache read time: ~0.1 seconds
- **Speedup: 50-100x**

### Cache Storage:
- 60 days of 2-min data: ~5 MB (parquet compressed)
- 2 years of 2-min data: ~40 MB
- **Negligible disk space**

### Memory Usage:
- 60 days loaded in memory: ~10 MB
- Pandas DataFrame is efficient
- No memory concerns for years of data

---

## Future Enhancements

### Phase 2: Real-time Data (Paper Trading)
- WebSocket connection to Alpaca
- Subscribe to QQQ 2-min bar updates
- Process bars as they arrive (event-driven)

### Phase 3: Multiple Symbols
- Support basket of symbols (SPY, QQQ, IWM, etc.)
- Parallel fetching (threading)
- Consolidated cache management

### Phase 4: Alternative Data Sources
- Polygon.io adapter (for comparison)
- CSV file adapter (for testing with custom data)
- Database adapter (for pre-downloaded datasets)

---

**Related Documents:**
- [Architecture Overview](./architecture-overview.md)
- [Backtest Engine](./backtest-engine.md)
- [Signal Detection](./signal-detection.md)
