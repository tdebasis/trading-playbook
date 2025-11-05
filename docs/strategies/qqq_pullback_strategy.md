
---

## 9) Journaling Schema (for Expectancy, Time-of-Day, Volatility)

> **Goal coverage:** A (expectancy), C (time-of-entry effects), D (volatility regimes).  
> Keep it simple: log **one row per session** (trade or no-trade).

### 9.1 Columns (minimal but powerful)

| Column | Type | Example | Why it matters |
|---|---|---|---|
| `trade_date` | date | 2025-02-14 | Regime tracking |
| `trend_valid` | bool | TRUE | Confirms open > 200D SMA |
| `sma200_daily_at_open` | number | 421.14 | Trend context |
| `entry_window` | text | 10:00-10:30 | Time filter recorded |
| `first_close_below_time` | time | 10:12 | Pullback start marker |
| `reversal_candle_time` | time | 10:16 | First close back above EMA20 |
| `reversal_strength_ok` | bool | TRUE | (Close−Low)/(High−Low) > 0.60 |
| `confirmation_candle_time` | time | 10:18 | One bar after reversal |
| `entered?` | bool | TRUE | Whether entry was taken |
| `entry_time_et` | time | 10:20 | Entry candle open time |
| `entry_price` | number | 436.12 | Baseline price |
| `shares` | number | 20 | Fixed for paper phase |
| `ema20_at_entry` | number | 435.98 | Entry context |
| `atr_14_2m_at_entry` | number | 0.42 | Volatility tag |
| `atr_pct_of_price` | number | 0.00096 | = atr / entry_price |
| `stop_distance` | number | 0.50 | = 1.2 × ATR |
| `stop_price` | number | 435.62 | Entry − stop_distance |
| `entry_bucket` | text | 10:00-10:10 | Time-of-day analysis |
| `bars_since_open` | number | 25 | Extra time context |
| `eod_exit_time` | time | 15:55 | Fixed exit |
| `eod_exit_price` | number | 437.00 | Closing result |
| `gross_pnl` | number | 17.6 | (exit − entry) × shares |
| `fees_slippage` | number | 0.0 | Optional est. |
| `net_pnl` | number | 17.6 | gross − fees |
| `risk_per_share` | number | 0.50 | entry − stop_price |
| `R_multiple` | number | 1.76 | (exit − entry)/risk_per_share |
| `dist_to_ema_bps` | number | 32 | ((entry−EMA)/EMA)*10000 |
| `notes` | short text | "clean bounce" | Qualitative tag |
| `chart_link_entry` | url | link | Optional visual |

> **No-trade days:** still log a row with `entered? = FALSE` and a short reason in `notes` (e.g., "no pullback," "invalid after confirmation," "outside window").

### 9.2 Sheet / CSV Formulas (Google Sheets style)

- `atr_pct_of_price` → `=IF(entry_price>0, atr_14_2m_at_entry / entry_price, )`
- `stop_distance` → `=1.2 * atr_14_2m_at_entry`
- `stop_price` → `=entry_price - stop_distance`
- `gross_pnl` → `=(eod_exit_price - entry_price) * shares`
- `net_pnl` → `=gross_pnl - fees_slippage`
- `risk_per_share` → `=entry_price - stop_price`
- `R_multiple` → `=IF(risk_per_share>0, (eod_exit_price - entry_price) / risk_per_share, )`
- `dist_to_ema_bps` → `=IF(ema20_at_entry>0, (entry_price - ema20_at_entry) / ema20_at_entry * 10000, )`

### 9.3 Review Queries (weekly / monthly)

- **Expectancy:** average of `R_multiple` (exclude blanks and no-trade rows).
- **Time-of-day:** Pivot `entry_bucket` vs avg `R_multiple` and win %.
- **Volatility:** Bucket `atr_pct_of_price` into terciles (low/med/high) → compare expectancy.
- **Signal quality:** Filter `reversal_strength_ok = TRUE` vs FALSE to confirm the strength filter adds edge.

---

*Journaling template updated on 2025-11-04.*
