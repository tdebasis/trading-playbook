#!/usr/bin/env python3
"""
Analyze actual 2025 trades to see how scoring system would have evaluated them.
Compare winners vs losers to find scoring patterns.
"""
import sys
from pathlib import Path
from datetime import datetime
import os
import re

backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

from scanner.daily_breakout_scanner_scoring import DailyBreakoutScannerScoring
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

scanner = DailyBreakoutScannerScoring(api_key, secret_key)

# Sample trades from 2025 (extracted from logs)
trades = [
    # Winners
    {'symbol': 'BNTX', 'date': datetime(2025, 1, 7), 'result': 'WIN', 'pnl_pct': 7.5},
    {'symbol': 'RBLX', 'date': datetime(2025, 1, 17), 'result': 'WIN', 'pnl_pct': 7.4},
    {'symbol': 'RBLX', 'date': datetime(2025, 1, 17), 'result': 'WIN', 'pnl_pct': 5.9},
    {'symbol': 'CRWD', 'date': datetime(2025, 1, 23), 'result': 'WIN', 'pnl_pct': 8.8},
    {'symbol': 'META', 'date': datetime(2025, 1, 29), 'result': 'WIN', 'pnl_pct': 5.4},
    {'symbol': 'META', 'date': datetime(2025, 1, 31), 'result': 'WIN', 'pnl_pct': 5.5},
    {'symbol': 'ZS', 'date': datetime(2025, 3, 17), 'result': 'WIN', 'pnl_pct': 6.5},
    {'symbol': 'GME', 'date': datetime(2025, 5, 23), 'result': 'WIN', 'pnl_pct': 7.6},
    {'symbol': 'SNOW', 'date': datetime(2025, 5, 23), 'result': 'LOSS', 'pnl_pct': -0.4},
    {'symbol': 'NVDA', 'date': datetime(2025, 5, 30), 'result': 'WIN', 'pnl_pct': 2.0},
    {'symbol': 'AMD', 'date': datetime(2025, 7, 14), 'result': 'WIN', 'pnl_pct': 5.1},
    {'symbol': 'DDOG', 'date': datetime(2025, 7, 14), 'result': 'WIN', 'pnl_pct': 5.5},

    # Losers
    {'symbol': 'SHOP', 'date': datetime(2025, 1, 7), 'result': 'LOSS', 'pnl_pct': -8.0},
    {'symbol': 'BNTX', 'date': datetime(2025, 1, 8), 'result': 'LOSS', 'pnl_pct': -8.0},
    {'symbol': 'RBLX', 'date': datetime(2025, 1, 31), 'result': 'LOSS', 'pnl_pct': -8.0},
    {'symbol': 'GOOGL', 'date': datetime(2025, 2, 3), 'result': 'LOSS', 'pnl_pct': -8.0},
    {'symbol': 'ZS', 'date': datetime(2025, 2, 14), 'result': 'LOSS', 'pnl_pct': -8.0},
    {'symbol': 'GME', 'date': datetime(2025, 3, 11), 'result': 'LOSS', 'pnl_pct': -1.8},
    {'symbol': 'BNTX', 'date': datetime(2025, 3, 17), 'result': 'LOSS', 'pnl_pct': -8.0},
    {'symbol': 'NET', 'date': datetime(2025, 6, 11), 'result': 'LOSS', 'pnl_pct': -3.1},
    {'symbol': 'GOOGL', 'date': datetime(2025, 6, 16), 'result': 'LOSS', 'pnl_pct': -8.0},
]

print(f"\n{'='*80}")
print(f"ANALYZING ACTUAL 2025 TRADES - SCORING SYSTEM EVALUATION")
print(f"{'='*80}\n")

winners = []
losers = []

for trade in trades:
    symbol = trade['symbol']
    date = trade['date']
    result = trade['result']
    pnl_pct = trade['pnl_pct']

    print(f"\n{'='*80}")
    print(f"{symbol} on {date.date()} - {result} ({pnl_pct:+.1f}%)")
    print(f"{'='*80}")

    try:
        candidate = scanner._check_symbol(symbol, date)

        if candidate:
            scoring = candidate.score_with_volume_compensation()

            print(f"✅ PASSED BASE SCREENING")
            print(f"   Score: {scoring['total']:.1f} / Required: {scoring['required']:.1f}")
            print(f"   Passes Threshold: {'YES' if scoring['passes'] else 'NO'}")
            print(f"   Volume: {scoring['breakdown']['volume']:.1f} pts ({scoring['volume_tier']})")
            print(f"   Trend: {scoring['breakdown']['trend']:.1f} pts")
            print(f"   Base: {scoring['breakdown']['base']:.1f} pts")
            print(f"   RS: {scoring['breakdown']['rs']:.1f} pts")

            trade_info = {
                'symbol': symbol,
                'date': date,
                'result': result,
                'pnl_pct': pnl_pct,
                'passed_base': True,
                'passed_scoring': scoring['passes'],
                'score': scoring['total'],
                'required': scoring['required'],
                'volume': scoring['breakdown']['volume'],
                'trend': scoring['breakdown']['trend'],
                'base': scoring['breakdown']['base'],
                'rs': scoring['breakdown']['rs']
            }

            if result == 'WIN':
                winners.append(trade_info)
            else:
                losers.append(trade_info)

        else:
            print(f"❌ REJECTED IN BASE SCREENING")
            print(f"   (Failed: trend, distance, or consolidation filter)")

            trade_info = {
                'symbol': symbol,
                'date': date,
                'result': result,
                'pnl_pct': pnl_pct,
                'passed_base': False,
                'passed_scoring': False,
                'score': 0.0,
                'required': 0.0
            }

            if result == 'WIN':
                winners.append(trade_info)
            else:
                losers.append(trade_info)

    except Exception as e:
        print(f"❌ ERROR: {e}")

# Summary Analysis
print(f"\n\n{'='*80}")
print(f"SUMMARY ANALYSIS")
print(f"{'='*80}\n")

winners_passed_base = [w for w in winners if w['passed_base']]
losers_passed_base = [l for l in losers if l['passed_base']]

print(f"WINNERS ({len(winners)} total):")
print(f"  Passed Base Screening: {len(winners_passed_base)}/{len(winners)} ({len(winners_passed_base)/len(winners)*100:.1f}%)")
if winners_passed_base:
    avg_score = sum(w['score'] for w in winners_passed_base) / len(winners_passed_base)
    passed_scoring = len([w for w in winners_passed_base if w['passed_scoring']])
    print(f"  Passed Scoring Threshold: {passed_scoring}/{len(winners_passed_base)} ({passed_scoring/len(winners_passed_base)*100:.1f}%)")
    print(f"  Average Score: {avg_score:.2f}")

print(f"\nLOSERS ({len(losers)} total):")
print(f"  Passed Base Screening: {len(losers_passed_base)}/{len(losers)} ({len(losers_passed_base)/len(losers)*100:.1f}%)")
if losers_passed_base:
    avg_score = sum(l['score'] for l in losers_passed_base) / len(losers_passed_base)
    passed_scoring = len([l for l in losers_passed_base if l['passed_scoring']])
    print(f"  Passed Scoring Threshold: {passed_scoring}/{len(losers_passed_base)} ({passed_scoring/len(losers_passed_base)*100:.1f}%)")
    print(f"  Average Score: {avg_score:.2f}")

print(f"\n{'='*80}")
print(f"KEY FINDINGS")
print(f"{'='*80}\n")

winners_rejected_base = len(winners) - len(winners_passed_base)
losers_rejected_base = len(losers) - len(losers_passed_base)

print(f"1. BASE SCREENING IMPACT:")
print(f"   - Rejected {winners_rejected_base} WINNERS in base screening")
print(f"   - Rejected {losers_rejected_base} LOSERS in base screening")
print(f"   - Net: Threw away {winners_rejected_base} winners to avoid {losers_rejected_base} losers")

if winners_passed_base and losers_passed_base:
    winner_avg = sum(w['score'] for w in winners_passed_base) / len(winners_passed_base)
    loser_avg = sum(l['score'] for l in losers_passed_base) / len(losers_passed_base)
    print(f"\n2. SCORING DIFFERENTIATION:")
    print(f"   - Winners avg score: {winner_avg:.2f}")
    print(f"   - Losers avg score: {loser_avg:.2f}")
    print(f"   - Difference: {winner_avg - loser_avg:.2f} pts")

    if abs(winner_avg - loser_avg) < 0.5:
        print(f"   ⚠️  POOR DIFFERENTIATION - Scoring doesn't separate winners from losers!")
    elif winner_avg > loser_avg:
        print(f"   ✅ GOOD - Winners score higher")
    else:
        print(f"   ❌ BAD - Losers score higher than winners!")

print(f"\n3. RECOMMENDATION:")
if winners_rejected_base > losers_rejected_base:
    print(f"   ❗ Base screening is TOO STRICT - rejecting more winners than losers")
    print(f"   → Relax consolidation filter (12% → 18%)")
    print(f"   → Relax trend filter (allow close > SMA20 without SMA20 > SMA50)")
elif winners_passed_base and losers_passed_base:
    winner_avg = sum(w['score'] for w in winners_passed_base) / len(winners_passed_base)
    loser_avg = sum(l['score'] for l in losers_passed_base) / len(losers_passed_base)
    if winner_avg > loser_avg + 0.5:
        print(f"   ✅ Scoring is working well - can use it to filter quality")
    else:
        print(f"   ⚠️  Scoring doesn't differentiate well - may not add value over simple volume filter")

print(f"\n{'='*80}\n")
