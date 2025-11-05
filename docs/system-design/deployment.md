# Deployment Strategy

**Version:** 1.0
**Last Updated:** 2025-11-04
**Status:** Design Phase

---

## Purpose

This document outlines the deployment strategy across different phases, from local development to cloud production.

---

## Deployment Phases

### Phase 1: Local Development (Current)

**Environment:** Local laptop/desktop
**Purpose:** Strategy development, backtesting, validation

**Architecture:**
```
┌─────────────────────────────────┐
│   Local Machine                 │
│                                 │
│   Python Script                 │
│   ├─ Alpaca API (free tier)    │
│   ├─ Local parquet cache       │
│   └─ CSV output                 │
│                                 │
│   Output: ./output/trades.csv   │
└─────────────────────────────────┘
```

**Setup:**
```bash
# Install dependencies
poetry install

# Set environment variables
export ALPACA_API_KEY=your_key
export ALPACA_SECRET_KEY=your_secret
export ALPACA_PAPER=true

# Run backtest
python -m trading_playbook.cli.backtest \
  --symbol QQQ \
  --start 2025-09-01 \
  --end 2025-11-04 \
  --output ./output/trades.csv
```

**Pros:**
- ✅ Zero infrastructure cost
- ✅ Fast iteration
- ✅ Easy debugging
- ✅ Full control

**Cons:**
- ❌ Manual execution
- ❌ No automation
- ❌ Single machine dependency

---

### Phase 2: Scheduled Local Execution

**Environment:** Local machine with cron/scheduler
**Purpose:** Automated daily backtesting, paper trading preparation

**Architecture:**
```
┌─────────────────────────────────┐
│   Local Machine                 │
│                                 │
│   Cron Job (daily 5PM ET)       │
│   └─→ Run backtest script       │
│       ├─ Fetch today's data     │
│       ├─ Detect signals         │
│       └─ Append to journal      │
│                                 │
│   Output: ./output/trades.csv   │
└─────────────────────────────────┘
```

**Setup:**
```bash
# Add to crontab
# Run at 5:00 PM ET daily (after market close)
0 17 * * 1-5 cd /path/to/trading-playbook && poetry run python -m trading_playbook.cli.backtest --today >> logs/backtest.log 2>&1
```

**Pros:**
- ✅ Automated execution
- ✅ Still zero infrastructure cost
- ✅ Simple setup

**Cons:**
- ❌ Machine must stay on
- ❌ No redundancy
- ❌ Limited scalability

---

### Phase 3: Cloud Deployment (GCP)

**Environment:** Google Cloud Platform
**Purpose:** Production-grade automated backtesting and paper trading

**Architecture:**
```
┌─────────────────────────────────────────┐
│   Google Cloud Platform                 │
│                                         │
│   Cloud Scheduler (cron)                │
│   └─→ Trigger Cloud Run                │
│         ├─ Container: Python app        │
│         ├─ Fetch data (Alpaca)          │
│         ├─ Detect signals               │
│         └─ Write results                │
│              ├─→ GCS (CSV backup)       │
│              └─→ MongoDB (journal)      │
│                                         │
│   Cloud Storage (GCS)                   │
│   ├─ data/cache/*.parquet               │
│   └─ output/trades/*.csv                │
│                                         │
│   MongoDB Atlas (optional)              │
│   └─ Trade journal database             │
└─────────────────────────────────────────┘
```

**Components:**

**1. Cloud Run Service:**
- Serverless container execution
- Auto-scales (0 to N instances)
- Pay per execution
- Stateless (read/write to GCS)

**2. Cloud Scheduler:**
- Managed cron service
- Triggers Cloud Run via HTTP
- Example: Daily at 5:00 PM ET

**3. Cloud Storage (GCS):**
- Data cache storage
- Trade journal backups
- Logs and reports

**4. MongoDB Atlas (optional):**
- Trade journal database
- Query and analysis
- Historical tracking

**Setup Steps:**

**1. Containerize Application:**
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-dev

COPY src/ ./src/

# Entry point
CMD ["python", "-m", "trading_playbook.cli.backtest", "--today", "--cloud"]
```

**2. Build and Push Container:**
```bash
# Build image
docker build -t gcr.io/YOUR_PROJECT/trading-playbook:latest .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT/trading-playbook:latest
```

**3. Deploy to Cloud Run:**
```bash
gcloud run deploy trading-playbook \
  --image gcr.io/YOUR_PROJECT/trading-playbook:latest \
  --platform managed \
  --region us-central1 \
  --memory 1Gi \
  --timeout 600s \
  --set-env-vars ALPACA_API_KEY=$ALPACA_KEY,ALPACA_SECRET_KEY=$ALPACA_SECRET \
  --set-secrets ALPACA_API_KEY=alpaca-key:latest \
  --no-allow-unauthenticated
```

**4. Create Cloud Scheduler Job:**
```bash
gcloud scheduler jobs create http trading-playbook-daily \
  --schedule="0 17 * * 1-5" \
  --time-zone="America/New_York" \
  --uri="https://trading-playbook-xxxx-uc.a.run.app/backtest" \
  --http-method=POST \
  --oidc-service-account-email=scheduler@YOUR_PROJECT.iam.gserviceaccount.com
```

**Cost Estimate:**
- Cloud Run: ~$1-5/month (minimal usage)
- Cloud Storage: ~$1-2/month (few GB)
- Cloud Scheduler: ~$0.10/month
- MongoDB Atlas: $0 (free tier) or ~$10/month (shared cluster)
- **Total: ~$2-18/month**

**Pros:**
- ✅ Fully automated
- ✅ Reliable (managed infrastructure)
- ✅ Scalable
- ✅ Monitoring built-in
- ✅ No local machine dependency

**Cons:**
- ❌ Monthly cost
- ❌ More complex setup
- ❌ Requires cloud knowledge

---

### Phase 4: Live Trading (Future)

**Environment:** Cloud with real-time processing
**Purpose:** Execute real trades based on strategy signals

**Architecture:**
```
┌──────────────────────────────────────────┐
│   Google Cloud Platform                  │
│                                          │
│   Cloud Run (always-on instance)         │
│   ├─ WebSocket: Alpaca real-time bars   │
│   ├─ Event-driven signal detection      │
│   ├─ Order execution                    │
│   └─ Position monitoring                │
│                                          │
│   Firestore / Cloud SQL                 │
│   └─ Position tracking, order history   │
│                                          │
│   Cloud Monitoring / Alerting           │
│   └─ Notifications on trades, errors    │
└──────────────────────────────────────────┘
```

**Additional Requirements:**
- Real-time data subscription (Alpaca paid or Polygon)
- Order management system
- Risk controls (position limits, circuit breakers)
- Monitoring and alerting
- Audit logging
- Disaster recovery

**Not in scope for initial phases.**

---

## Writer Adapters Implementation

### CSV Writer (Local)

```python
class CSVTradeWriter:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.trades = []

    def write_trade(self, trade_record: dict):
        self.trades.append(trade_record)

    def finalize(self):
        df = pd.DataFrame(self.trades)
        df.to_csv(self.filepath, index=False)
        print(f"✓ Wrote {len(self.trades)} trades to {self.filepath}")
```

### GCS Writer (Cloud)

```python
from google.cloud import storage

class GCSTradeWriter:
    def __init__(self, bucket_name: str, blob_name: str):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.blob_name = blob_name
        self.trades = []

    def write_trade(self, trade_record: dict):
        self.trades.append(trade_record)

    def finalize(self):
        df = pd.DataFrame(self.trades)
        csv_data = df.to_csv(index=False)

        blob = self.bucket.blob(self.blob_name)
        blob.upload_from_string(csv_data, content_type='text/csv')

        print(f"✓ Uploaded {len(self.trades)} trades to gs://{self.bucket.name}/{self.blob_name}")
```

### MongoDB Writer (Cloud)

```python
from pymongo import MongoClient

class MongoTradeWriter:
    def __init__(self, connection_string: str, database: str, collection: str):
        self.client = MongoClient(connection_string)
        self.collection = self.client[database][collection]

    def write_trade(self, trade_record: dict):
        self.collection.insert_one(trade_record)

    def finalize(self):
        print(f"✓ Wrote trades to MongoDB")
```

---

## Configuration Management

### Environment-Specific Config

**Local (.env file):**
```bash
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_PAPER=true
DATA_CACHE_DIR=./data/cache
OUTPUT_DIR=./output
WRITER_TYPE=csv
```

**Cloud (Secret Manager + Environment Variables):**
```bash
# Secrets in Google Secret Manager
ALPACA_API_KEY=<from secret manager>
ALPACA_SECRET_KEY=<from secret manager>

# Environment variables in Cloud Run
ALPACA_PAPER=true
GCS_BUCKET=trading-playbook-data
WRITER_TYPE=gcs
MONGODB_CONNECTION=<from secret manager>
```

### Config Loader:

```python
import os
from dataclasses import dataclass

@dataclass
class Config:
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_paper: bool
    writer_type: str  # 'csv', 'gcs', 'mongodb'
    output_location: str  # file path, GCS path, or MongoDB connection

    @classmethod
    def from_env(cls):
        return cls(
            alpaca_api_key=os.getenv('ALPACA_API_KEY'),
            alpaca_secret_key=os.getenv('ALPACA_SECRET_KEY'),
            alpaca_paper=os.getenv('ALPACA_PAPER', 'true').lower() == 'true',
            writer_type=os.getenv('WRITER_TYPE', 'csv'),
            output_location=os.getenv('OUTPUT_LOCATION', './output/trades.csv')
        )
```

---

## Monitoring & Alerting

### Metrics to Track:

**Operational:**
- Backtest execution time
- API call latency
- Cache hit rate
- Error rate

**Business:**
- Trades detected per day
- Win rate (trailing 30 days)
- Expectancy
- Drawdown

### Logging Strategy:

**Levels:**
- INFO: Normal operation (trades detected, files written)
- WARN: Recoverable issues (missing data, retries)
- ERROR: Failures (API errors, invalid data)

**Example:**
```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Backtest started for {start_date} to {end_date}")
logger.info(f"Detected signal: entry at {entry_time}")
logger.warn(f"Data gap detected for {date}")
logger.error(f"API call failed: {error_msg}")
```

### Alerting (Cloud):

**Google Cloud Monitoring:**
- Alert on error rate > 5%
- Alert on no trades for 5 consecutive days (system issue?)
- Alert on execution time > 10 minutes

**Email/Slack Notifications:**
- Daily summary report
- Trade alerts (optional for paper trading)

---

## Deployment Checklist

**Phase 1 → Phase 2 (Local Scheduled):**
- [ ] Test backtest runs successfully end-to-end
- [ ] Set up cron job / task scheduler
- [ ] Verify logs are captured
- [ ] Test handles market holidays gracefully

**Phase 2 → Phase 3 (Cloud):**
- [ ] Create GCP project
- [ ] Set up billing alerts
- [ ] Store secrets in Secret Manager
- [ ] Build and test Docker container locally
- [ ] Deploy to Cloud Run
- [ ] Test Cloud Run endpoint manually
- [ ] Set up Cloud Scheduler
- [ ] Configure GCS bucket for outputs
- [ ] Set up monitoring dashboard
- [ ] Test end-to-end automated run
- [ ] Document runbooks for common issues

---

**Related Documents:**
- [Architecture Overview](./architecture-overview.md)
- [Data Pipeline](./data-pipeline.md)
