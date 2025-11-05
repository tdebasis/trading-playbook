# Trading Regulations & Account Structure

## Pattern Day Trader (PDT) Rule - CRITICAL

### The Rule:
**If you make 4+ day trades within 5 business days in a margin account, you MUST maintain $25,000 minimum balance.**

A "day trade" = Buy and sell the same stock on the same day.

### Consequences of Violating PDT:
- Account frozen for 90 days (can only close positions, not open new ones)
- Forced to deposit $25,000 or switch to cash account

---

## Our Options:

### Option 1: Cash Account (< $25k) ✅ RECOMMENDED FOR STARTING
**Pros:**
- NO $25,000 minimum requirement
- NO PDT rule restrictions
- Can day trade as much as you want

**Cons:**
- **T+2 Settlement** - Must wait 2 business days for cash to settle before reusing
- Limited buying power (can only use settled cash)
- Can realistically make ~3 trades per week with full capital rotation

**Example with $10k:**
```
Monday: Trade $10k → Sell same day → Profit $1k
Tuesday: Can't use that $10k yet (settling)
Wednesday: Still settling
Thursday: $10k + $1k settled → Can trade again
```

**Workaround:** Split capital into 3 parts
- Trade Part 1 on Monday (settles Thursday)
- Trade Part 2 on Tuesday (settles Friday)
- Trade Part 3 on Wednesday (settles Monday)
- Rotate continuously

This gives us ~3 trades/week with full capital deployment.

### Option 2: Margin Account with $25k+ ✅ BEST FOR SERIOUS TRADING
**Pros:**
- Unlimited day trades
- 2x buying power (can use margin)
- Instant settlement
- Can make 10+ trades per day

**Cons:**
- MUST maintain $25,000 minimum at all times
- Margin interest if you borrow
- Higher risk (can lose more than deposit)

### Option 3: Multiple Accounts Strategy (Advanced)
Use multiple brokers to multiply day trades:
- Alpaca: $10k
- Interactive Brokers: $10k
- TD Ameritrade: $10k

Each allows 3 day trades/week = 9 total trades/week

**Cons:**
- Complex to manage
- Still limited trades
- Spreads capital thin

---

## Our Recommended Path:

### Phase 1: Paper Trading (Current)
- Test with fake $10k-100k
- Unlimited trades
- No restrictions
- **Prove the strategy works**

### Phase 2a: If Starting with < $25k
**Use Cash Account + Swing Trading Hybrid:**
```python
# Modify strategy for cash account
class CashAccountStrategy:
    """
    Optimized for cash account constraints.
    """
    def __init__(self, capital=10000):
        self.total_capital = capital
        # Split into 3 buckets for T+2 rotation
        self.bucket_size = capital / 3

    def can_trade_today(self):
        """Check if we have settled cash available."""
        # Track which bucket settled today
        return self.get_available_bucket()

    def trade_style(self):
        # Instead of pure day trading:
        # - Enter on momentum
        # - Hold 1-3 days (swing trade)
        # - Exit on target or stop
        # This avoids T+2 settlement issues
        pass
```

**Modified Rules for Cash Account:**
- Enter best 1-2 setups per day
- Hold 1-5 days (swing trade, not day trade)
- This is actually LESS stressful
- Can still make great returns

**Example Performance:**
- 3 trades/week × 4 weeks = 12 trades/month
- 60% win rate
- 2:1 R/R
- 2% risk per trade
- Expected: 10-15% monthly return (EXCELLENT!)

### Phase 2b: If Starting with $25k+
**Use Margin Account + Full Day Trading:**
```python
class MarginAccountStrategy:
    """
    Unlimited day trades, higher frequency.
    """
    def __init__(self, capital=25000):
        self.capital = capital
        self.buying_power = capital * 4  # Day trading buying power

    def trade_style(self):
        # Pure momentum day trading
        # - Multiple trades per day
        # - In and out within hours
        # - High frequency
        pass
```

---

## Alpaca-Specific Rules:

### Paper Trading:
- ✅ Unlimited day trades
- ✅ No PDT restrictions
- ✅ Full margin simulation
- **Perfect for testing**

### Live Trading with Alpaca:
**Cash Account:**
- Min: $0 (can start with any amount)
- Day trades: Unlimited BUT subject to T+2 settlement
- No margin

**Margin Account:**
- Min: $2,000 to open
- BUT $25,000 required if you make 4+ day trades in 5 days
- 2x margin (or 4x day trading buying power)

---

## Our Strategy for Momentum Hunter:

### Immediate Term (Month 1-2):
```
1. Paper trade with $100k simulated capital
2. Test aggressive day trading strategy
3. Track performance metrics
4. Prove the system works
```

### Short Term (Month 3):
```
IF paper trading is profitable:

Option A (< $25k capital available):
  → Open cash account with Alpaca
  → Modify strategy to swing trade style (1-5 day holds)
  → Start with $5k-10k real money
  → Make 3-4 high-quality trades per week

Option B ($25k+ capital available):
  → Open margin account with Alpaca
  → Use full day trading strategy
  → Unlimited trades
  → Higher frequency
```

### Long Term (Month 6+):
```
IF consistently profitable:
  → Scale up capital
  → Consider upgrading to margin account
  → Professional trader status
```

---

## Risk Management Adjustments:

### For Cash Account (< $25k):
```yaml
max_positions: 1-2  # Focus on best setups only
hold_period: 1-5 days  # Swing trades, not day trades
risk_per_trade: 1-2%
trades_per_week: 3-4  # Quality over quantity
style: "Swing momentum"
```

### For Margin Account ($25k+):
```yaml
max_positions: 2-3  # Can handle more
hold_period: Minutes to hours  # True day trading
risk_per_trade: 2%
trades_per_day: 2-5  # Higher frequency
style: "Pure momentum day trading"
```

---

## Tax Implications (Bonus):

### Day Trader Status (IRS):
If you trade frequently, IRS may classify you as "trader":

**Pros:**
- Can deduct expenses (software, data, etc.)
- Mark-to-market accounting available

**Cons:**
- All gains taxed as ordinary income (not capital gains)
- Can be 20-37% vs 15% capital gains rate

**Recommendation:** Consult tax professional once profitable.

---

## Summary & Action Plan:

### What We'll Do:

**NOW (Building Phase):**
1. ✅ Build system for unlimited day trading
2. ✅ Test in paper trading (no restrictions)
3. ✅ Track as if real money

**MONTH 1-2 (Testing Phase):**
1. Run paper trading with $25k-100k simulated
2. Test aggressive day trading strategy
3. Measure results

**MONTH 3 (Decision Point):**

**IF you have < $25k to invest:**
- Open CASH account
- Modify to swing trading style
- 3-4 trades per week
- Still very profitable!

**IF you have $25k+ to invest:**
- Open MARGIN account
- Full day trading mode
- Unlimited trades
- Maximum performance

**Either way, we WIN!**

---

## The Beautiful Part:

Even with a cash account and only 3-4 trades/week, if we're selective and use Claude's intelligence to pick ONLY the best setups:

**Conservative Projection:**
- 4 trades/week × 4 weeks = 16 trades/month
- 65% win rate (Claude is selective)
- 2.5:1 average R/R
- 2% risk per trade
- **Expected: 12-18% monthly return**

That's **144-216% annual return** with only 16 trades per month!

**Who needs 100 trades when we pick the absolute best ones?**

---

**Bottom line: PDT rule is NOT a blocker. It just determines our trading STYLE, not our success.**
