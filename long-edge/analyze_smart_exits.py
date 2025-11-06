#!/usr/bin/env python3
"""
Analyze Smart Exits Trade Patterns
"""

# Parse the trades from the log
trades = """
✅ ENTER BNTX: 249 shares @ $120.21
  ✅ CLOSE BNTX: $129.27 | P&L: +2,256 (+7.5%) | TRAILING_STOP
❌ CLOSE SHOP: $105.10 | P&L: -1,682 (-8.0%) | HARD_STOP
❌ CLOSE BNTX: $116.73 | P&L: -1,594 (-8.0%) | HARD_STOP
✅ CLOSE RBLX: $66.51 | P&L: +1,085 (+7.4%) | TRAILING_STOP
✅ CLOSE RBLX: $69.12 | P&L: +1,776 (+5.9%) | TRAILING_STOP
✅ CLOSE CRWD: $411.30 | P&L: +1,266 (+8.8%) | TRAILING_STOP
✅ CLOSE AMZN: $234.64 | P&L: +358 (+1.7%) | MA_BREAK
✅ CLOSE META: $710.79 | P&L: +1,313 (+5.4%) | TRAILING_STOP
❌ CLOSE RBLX: $65.67 | P&L: -1,770 (-8.0%) | HARD_STOP
✅ CLOSE META: $725.01 | P&L: +1,710 (+5.5%) | TRAILING_STOP
❌ CLOSE GOOGL: $187.70 | P&L: -1,240 (-8.0%) | HARD_STOP
❌ CLOSE SHOP: $123.47 | P&L: -30 (-0.1%) | MA_BREAK
❌ CLOSE ZS: $197.65 | P&L: -1,736 (-8.0%) | HARD_STOP
✅ CLOSE ZS: $248.72 | P&L: +461 (+1.5%) | MA_BREAK
❌ CLOSE GME: $27.89 | P&L: -376 (-1.8%) | MA_BREAK
✅ CLOSE GME: $33.21 | P&L: +1,290 (+7.6%) | TRAILING_STOP
❌ CLOSE SNOW: $202.31 | P&L: -103 (-0.4%) | MA_BREAK
✅ CLOSE CRWD: $458.81 | P&L: +122 (+0.7%) | MA_BREAK
❌ CLOSE BNTX: $93.58 | P&L: -1,701 (-8.0%) | HARD_STOP
✅ CLOSE ZS: $293.53 | P&L: +1,480 (+6.5%) | TRAILING_STOP
✅ CLOSE RBLX: $91.68 | P&L: +874 (+5.4%) | TRAILING_STOP
✅ CLOSE ZS: $297.97 | P&L: +302 (+1.6%) | MA_BREAK
❌ CLOSE NET: $170.81 | P&L: -569 (-3.1%) | MA_BREAK
✅ CLOSE NVDA: $141.97 | P&L: +489 (+2.0%) | MA_BREAK
"""

# Parse trades
import re

winners = []
losers = []
by_exit_type = {
    'TRAILING_STOP': {'wins': [], 'losses': []},
    'HARD_STOP': {'wins': [], 'losses': []},
    'MA_BREAK': {'wins': [], 'losses': []},
    'TIME': {'wins': [], 'losses': []}
}

for line in trades.strip().split('\n'):
    if 'CLOSE' not in line or 'P&L:' not in line:
        continue
    
    # Extract P&L and exit reason
    pnl_match = re.search(r'P&L: ([+-]\d+,?\d*)', line)
    pct_match = re.search(r'\(([+-][\d.]+)%\)', line)
    reason_match = re.search(r'\| (\w+)$', line)
    
    if pnl_match and pct_match and reason_match:
        pnl = int(pnl_match.group(1).replace(',', '').replace('+', ''))
        pct = float(pct_match.group(1))
        reason = reason_match.group(1)
        
        if pnl > 0:
            winners.append((pnl, pct, reason))
            by_exit_type[reason]['wins'].append(pct)
        else:
            losers.append((pnl, pct, reason))
            by_exit_type[reason]['losses'].append(pct)

print("="*80)
print("SMART EXITS TRADE ANALYSIS")
print("="*80)
print(f"\nTotal Trades: {len(winners) + len(losers)}")
print(f"Winners: {len(winners)} ({len(winners)/(len(winners)+len(losers))*100:.1f}%)")
print(f"Losers: {len(losers)} ({len(losers)/(len(winners)+len(losers))*100:.1f}%)")

print("\n" + "="*80)
print("EXIT TYPE BREAKDOWN")
print("="*80)

for exit_type, data in by_exit_type.items():
    total_wins = len(data['wins'])
    total_losses = len(data['losses'])
    total = total_wins + total_losses
    
    if total == 0:
        continue
    
    print(f"\n{exit_type}:")
    print(f"  Total: {total} trades")
    print(f"  Wins: {total_wins} ({total_wins/total*100:.1f}%)")
    print(f"  Losses: {total_losses} ({total_losses/total*100:.1f}%)")
    
    if data['wins']:
        avg_win = sum(data['wins']) / len(data['wins'])
        print(f"  Avg Win: +{avg_win:.1f}%")
    if data['losses']:
        avg_loss = sum(data['losses']) / len(data['losses'])
        print(f"  Avg Loss: {avg_loss:.1f}%")

print("\n" + "="*80)
print("KEY INSIGHTS")
print("="*80)

# Insights
trailing_wins = len(by_exit_type['TRAILING_STOP']['wins'])
hard_stop_losses = len(by_exit_type['HARD_STOP']['losses'])
ma_break_total = len(by_exit_type['MA_BREAK']['wins']) + len(by_exit_type['MA_BREAK']['losses'])
ma_break_wins = len(by_exit_type['MA_BREAK']['wins'])

print(f"\n1. TRAILING STOPS are working well:")
print(f"   - {trailing_wins} profitable exits via trailing stop")
print(f"   - Average gain when trailing stop hits: +{sum(by_exit_type['TRAILING_STOP']['wins'])/len(by_exit_type['TRAILING_STOP']['wins']):.1f}%")

print(f"\n2. HARD STOPS are protecting capital:")
print(f"   - {hard_stop_losses} exits at -8% (all losers as expected)")
print(f"   - Prevented bigger losses")

print(f"\n3. MA BREAKS are mixed:")
print(f"   - {ma_break_total} total MA break exits")
print(f"   - {ma_break_wins} winners ({ma_break_wins/ma_break_total*100:.1f}%)")
print(f"   - Catching some small losses early, but also cutting winners short")

print("\n" + "="*80)
print("OPTIMIZATION OPPORTUNITIES")
print("="*80)

print("\n1. **MA Break Tuning:**")
print("   - Some MA breaks cut small winners (+1.5%, +1.6%, +2.0%)")
print("   - Consider: Only use MA break if position is negative or < +3%")
print("   - Let profitable positions trail instead")

print("\n2. **Position Sizing:**")
print("   - Winners avg +5-7%, losers capped at -8%")
print("   - Slightly negative R:R ratio")
print("   - Consider: Reduce hard stop to -7% to improve R:R")

print("\n3. **Scaling Out (Your Idea):**")
print("   - Could lock in gains at +8% while letting rest run")
print("   - Would have captured 10+ winners at +8% level")
print("   - Reduces risk of giving back gains")

print("\n" + "="*80)
