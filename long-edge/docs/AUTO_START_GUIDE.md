# Momentum Hunter - Automatic Startup Guide

## ✅ System is Ready for Automatic Trading!

Your trading system will now start automatically every weekday morning when markets open.

---

## 🚀 Enable Automatic Startup

```bash
cd /Users/tanambamsinha/projects/trading-playbook/momentum-hunter
./control.sh start
```

This will:
- ✅ Start trading automatically Monday-Friday at **6:25 AM PT** (9:25 AM ET)
- ✅ Run until **12:45 PM PT** (3:45 PM ET)
- ✅ Close all positions before market close
- ✅ Log everything to files

---

## 📊 Check Status Anytime

```bash
./control.sh status
```

Shows:
- Is automatic startup enabled?
- Is trading system running right now?
- Today's log file location
- Runtime duration

---

## 📋 View Live Logs

```bash
./control.sh logs
```

This shows real-time trading activity:
- When Claude makes decisions
- Trades executed
- Positions opened/closed
- P&L updates

Press `Ctrl+C` to exit log view.

---

## 👀 Monitor Dashboard (Optional)

While trading is running, open another terminal:

```bash
cd /Users/tanambamsinha/projects/trading-playbook/momentum-hunter
python3 monitor.py
```

Shows:
- Live P&L
- Open positions
- Win rate
- Recent trades

Refreshes every 10 seconds.

---

## 🛑 Stop Automatic Startup

```bash
./control.sh stop
```

This disables automatic startup. The system will NOT start tomorrow.

---

## 🚨 Emergency Stop

If you need to stop trading immediately:

```bash
./control.sh kill
```

This:
- Kills all trading processes instantly
- Does NOT disable automatic startup (will start again tomorrow)
- Use if something goes wrong

Then:
```bash
./control.sh stop    # Disable tomorrow's auto-start
```

---

## 📁 Log Files

All logs are saved in `/Users/tanambamsinha/projects/trading-playbook/momentum-hunter/logs/`:

- `trading_2025-11-05.log` - Main trading activity (one per day)
- `errors_2025-11-05.log` - Errors and warnings
- `startup_2025-11-05_06-25-00.log` - Startup process log
- `launchd_stdout.log` - macOS LaunchAgent output
- `launchd_stderr.log` - macOS LaunchAgent errors

---

## ⏰ Schedule

**System runs automatically:**
- **Monday-Friday** only (skips weekends)
- **6:25 AM PT** - System starts, waits for market open
- **6:30 AM PT** - Market opens, begins scanning
- **6:30-8:30 AM PT** - Trading window (scans every 5 min)
- **8:30 AM-12:45 PM PT** - Monitors positions only
- **12:45 PM PT** - Closes all positions
- **1:00 PM PT** - Market closes, system stops

---

## 🖥️ Computer Requirements

For automatic startup to work:

✅ **Your Mac must be:**
- Powered ON or in Sleep mode (not shut down)
- Awake at 6:25 AM on weekdays

❌ **Will NOT work if:**
- Computer is shut down
- Computer is in hibernation
- You're not logged in (depends on settings)

**Recommendation:**
- Leave your Mac in Sleep mode overnight
- Or set it to wake automatically at 6:20 AM
  - System Preferences → Energy Saver → Schedule

---

## 🔔 Notifications

On startup, you'll see a macOS notification:
```
Trading System Started
Momentum Hunter is now trading
```

---

## ✅ First-Time Setup Checklist

Before enabling automatic startup, make sure:

1. ✅ API keys are in `.env` file (Alpaca + Anthropic)
2. ✅ You have credits in Anthropic account ($100+ recommended)
3. ✅ You've tested the system works: `python3 run.py` (manually)
4. ✅ Computer will be ON or sleeping on weekday mornings
5. ✅ You understand it's PAPER TRADING (no real money)

Then run:
```bash
./control.sh start
```

---

## 📊 Daily Routine (Optional)

You can check on the system anytime, or just let it run:

**Morning (optional):**
```bash
./control.sh status    # Verify it started
./control.sh logs      # Watch it work
```

**During Day (optional):**
```bash
python3 monitor.py     # View live dashboard
```

**Evening (optional):**
```bash
cat logs/trading_$(date +%Y-%m-%d).log    # Review the day
```

**Or just let it run completely hands-off!**

---

## 🔍 Troubleshooting

### "System didn't start this morning"

Check:
1. Was computer ON/awake at 6:25 AM?
   ```bash
   pmset -g log | grep -i wake
   ```

2. Is automatic startup enabled?
   ```bash
   ./control.sh status
   ```

3. Check startup logs:
   ```bash
   cat logs/startup_*.log | tail -50
   ```

### "System started but crashed"

Check error log:
```bash
cat logs/errors_$(date +%Y-%m-%d).log
```

Common issues:
- Missing API keys
- Out of Anthropic credits
- Network connection issues

### "How do I test without waiting until tomorrow?"

Manually run the startup script:
```bash
./start_trading.sh
```

This starts trading NOW (if market is open).

---

## 🎯 What Happens Automatically

1. **6:25 AM** - LaunchAgent triggers `start_trading.sh`
2. Script checks:
   - Is it a weekday?
   - Is it within trading hours?
   - Are API keys present?
   - Is system already running?
3. If all checks pass → starts `python3 run.py` in background
4. System runs until 12:45 PM, then closes all positions
5. Logs everything to files
6. **Next morning** - Repeats automatically

---

## 📈 Monitoring Performance

**Weekly review:**
```bash
# See all trades from this week
sqlite3 momentum_hunter.db "SELECT * FROM trades WHERE date(entry_time) >= date('now', '-7 days');"

# Check win rate
sqlite3 momentum_hunter.db "SELECT
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(AVG(CASE WHEN pnl > 0 THEN 1.0 ELSE 0.0 END) * 100, 1) as win_rate_pct
FROM trades
WHERE status = 'closed';"
```

Or use the monitor:
```bash
python3 monitor.py
```

---

## 🚀 You're All Set!

To start automatic trading:

```bash
cd /Users/tanambamsinha/projects/trading-playbook/momentum-hunter
./control.sh start
```

**Tomorrow morning at 6:25 AM, Momentum Hunter will begin trading automatically!**

Leave your Mac on (or sleeping), and the system will:
- Scan for opportunities
- Ask Claude to decide
- Execute trades
- Manage positions
- Close everything before market close
- Log all activity

**Check back in the evening to see how Claude did!**

---

## 🛡️ Safety Reminders

- ✅ This is **PAPER TRADING** - no real money at risk
- ✅ All positions close daily at 12:45 PM PT
- ✅ Stop losses protect every trade
- ✅ Max 3 positions at once
- ✅ Max 2% risk per trade
- ✅ $500 daily loss limit

**Run this for 30+ days before considering live trading.**

---

**Built with 🧠 by Claude AI + Tanam Bam Sinha**
**November 2025**
