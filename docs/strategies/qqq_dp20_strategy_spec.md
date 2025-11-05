# QQQ Deep Pullback Continuation (DP20) — Strategy Specification (v1.1)

Intraday trend continuation strategy for QQQ using deep pullbacks to EMA20, confirmation strength, ATR-based stops, and end-of-day exits. Intended for extended paper trading and journaling.

---

## 1) Strategy Intent
Capture continuation legs in bullish intraday trends after a controlled pullback.

---

## 2) Data & Timeframes
- Symbol: QQQ
- Bars: 2-minute intraday candles
- Daily data: for SMA200 trend filter
- Indicators: SMA200 (daily), EMA20 (2-min), ATR(14, 2-min)

---

## 3) Entry Rules

### Trend Filter
Trade only if today's open > SMA200.

### Time Window
Evaluate signals only between 10:00 AM and 10:30 AM ET.

### Pullback
Wait for a candle CLOSE below EMA20.

### Reversal
Later, wait for a candle CLOSE back above EMA20.

### Strength Filter
(Close - Low) / (High - Low) > 0.60.

### Confirmation
Wait one full additional candle. If confirmation closes below EMA20 → invalidate.

### Entry
Enter long at open of the candle after confirmation.

---

## 4) Stop & Exit
Stop = Entry - (1.2 × ATR(14)).
Exit at 3:55 PM ET.

---

## 5) Risk Rules
- One trade per day
- Fixed share size
- No averaging or re-entry

---

## 6) Journaling Schema
Record one row per day.

- trade_date
- trend_valid
- reversal_time
- confirmation_time
- entered?
- entry_price
- atr_at_entry
- stop_price
- eod_exit_price
- R_multiple
- notes

Expectancy = average R_multiple over 20–50 trades.

---

End of specification.
