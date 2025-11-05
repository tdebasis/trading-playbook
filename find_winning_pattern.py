"""
Deep analysis to find ACTUAL winning patterns in the data.

Forget preconceived strategies - let the DATA tell us what works.
"""

import os
from datetime import date, time, datetime
from dotenv import load_dotenv
import pandas as pd
import numpy as np

from trading_playbook.adapters.alpaca_fetcher import AlpacaDataFetcher
from trading_playbook.adapters.cached_fetcher import CachedDataFetcher
from trading_playbook.models.market_data import TimeFrame


def analyze_all_patterns(fetcher, symbol, start_date, end_date):
    """
    Comprehensive analysis of ALL possible patterns.
    
    We'll test:
    1. Every possible entry time (9:30 - 3:00 PM)
    2. Hold to close strategy
    3. Find which entry times are MOST profitable
    """
    print("\n" + "="*80)
    print("COMPREHENSIVE PATTERN ANALYSIS")
    print("="*80)
    
    daily_df = fetcher.fetch_daily_bars(symbol, start_date, end_date)
    trading_days = [d.date() for d in daily_df.index]
    
    # Test every 30-minute entry window
    entry_times = [
        time(9, 30), time(10, 0), time(10, 30), time(11, 0),
        time(11, 30), time(12, 0), time(12, 30), time(13, 0),
        time(13, 30), time(14, 0), time(14, 30), time(15, 0)
    ]
    
    results_by_time = {}
    
    for entry_time in entry_times:
        print(f"\nTesting entry at {entry_time.strftime('%I:%M %p')}...")
        
        trades = []
        
        for trade_date in trading_days:
            bars = fetcher.fetch_intraday_bars(symbol, trade_date, TimeFrame.MINUTE_2)
            if not bars:
                continue
            
            df = pd.DataFrame([{
                'timestamp': bar.timestamp,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
            } for bar in bars])
            
            df['time'] = df['timestamp'].dt.time
            
            # Find entry bar (at or after entry_time)
            entry_bars = df[df['time'] >= entry_time]
            if entry_bars.empty:
                continue
            
            entry_bar = entry_bars.iloc[0]
            entry_price = entry_bar['open']
            
            # Find exit (3:55 PM or last bar)
            exit_bars = df[df['time'] >= time(15, 55)]
            if exit_bars.empty:
                exit_bar = df.iloc[-1]
            else:
                exit_bar = exit_bars.iloc[0]
            
            exit_price = exit_bar['close']
            
            # Calculate P&L
            pnl = (exit_price - entry_price) * 100  # 100 shares
            
            trades.append({
                'date': trade_date,
                'entry_time': entry_time,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl
            })
        
        trades_df = pd.DataFrame(trades)
        total_pnl = trades_df['pnl'].sum()
        win_rate = (trades_df['pnl'] > 0).sum() / len(trades_df) * 100
        avg_pnl = trades_df['pnl'].mean()
        
        results_by_time[entry_time] = {
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'num_trades': len(trades_df)
        }
        
        print(f"  Total P&L: ${total_pnl:,.2f}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Avg P&L: ${avg_pnl:.2f}")
    
    # Find best entry time
    print("\n" + "="*80)
    print("RESULTS BY ENTRY TIME")
    print("="*80)
    
    results_df = pd.DataFrame(results_by_time).T
    results_df = results_df.sort_values('total_pnl', ascending=False)
    
    print("\nRanked by Total P&L:")
    for idx, row in results_df.iterrows():
        print(f"{idx.strftime('%I:%M %p')}: ${row['total_pnl']:>10,.2f}  |  "
              f"{row['win_rate']:>5.1f}% win  |  "
              f"${row['avg_pnl']:>7.2f} avg")
    
    best_time = results_df.index[0]
    best_pnl = results_df.iloc[0]['total_pnl']
    
    print(f"\n🏆 BEST ENTRY TIME: {best_time.strftime('%I:%M %p')}")
    print(f"   Total P&L: ${best_pnl:,.2f} over {len(trading_days)} days")
    print(f"   Avg per day: ${best_pnl/len(trading_days):.2f}")
    
    return results_df


def analyze_directional_bias(fetcher, symbol, start_date, end_date):
    """
    Check if there's a directional bias we can exploit.
    """
    print("\n\n" + "="*80)
    print("DIRECTIONAL BIAS ANALYSIS")
    print("="*80)
    
    daily_df = fetcher.fetch_daily_bars(symbol, start_date, end_date)
    trading_days = [d.date() for d in daily_df.index]
    
    patterns = {
        'gap_up_days': [],
        'gap_down_days': [],
        'up_days': [],
        'down_days': []
    }
    
    for trade_date in trading_days:
        bars = fetcher.fetch_intraday_bars(symbol, trade_date, TimeFrame.MINUTE_2)
        if not bars:
            continue
        
        df = pd.DataFrame([{
            'timestamp': bar.timestamp,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
        } for bar in bars])
        
        day_open = df.iloc[0]['open']
        day_close = df.iloc[-1]['close']
        
        # Get previous day close from daily data
        try:
            prev_close = daily_df[daily_df.index < pd.Timestamp(trade_date)].iloc[-1]['close']
            gap = (day_open - prev_close) / prev_close * 100
            
            if gap > 0.5:  # Gap up > 0.5%
                patterns['gap_up_days'].append((trade_date, day_close - day_open))
            elif gap < -0.5:  # Gap down > 0.5%
                patterns['gap_down_days'].append((trade_date, day_close - day_open))
        except:
            pass
        
        if day_close > day_open:
            patterns['up_days'].append((trade_date, day_close - day_open))
        else:
            patterns['down_days'].append((trade_date, day_close - day_open))
    
    print(f"\nTotal Days: {len(trading_days)}")
    print(f"Up Days: {len(patterns['up_days'])} ({len(patterns['up_days'])/len(trading_days)*100:.1f}%)")
    print(f"Down Days: {len(patterns['down_days'])} ({len(patterns['down_days'])/len(trading_days)*100:.1f}%)")
    print(f"Gap Up Days: {len(patterns['gap_up_days'])}")
    print(f"Gap Down Days: {len(patterns['gap_down_days'])}")
    
    # Analyze gap days
    if patterns['gap_up_days']:
        gap_up_moves = [move for _, move in patterns['gap_up_days']]
        print(f"\nGap Up Days (open > prev close by >0.5%):")
        print(f"  Avg intraday move: ${np.mean(gap_up_moves):.2f}")
        print(f"  Fade the gap? {sum(1 for m in gap_up_moves if m < 0)} times ({sum(1 for m in gap_up_moves if m < 0)/len(gap_up_moves)*100:.1f}%)")
    
    if patterns['gap_down_days']:
        gap_down_moves = [move for _, move in patterns['gap_down_days']]
        print(f"\nGap Down Days (open < prev close by >0.5%):")
        print(f"  Avg intraday move: ${np.mean(gap_down_moves):.2f}")
        print(f"  Buy the dip? {sum(1 for m in gap_down_moves if m > 0)} times ({sum(1 for m in gap_down_moves if m > 0)/len(gap_down_moves)*100:.1f}%)")


def main():
    load_dotenv()
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    
    print("Setting up data fetcher...")
    alpaca_fetcher = AlpacaDataFetcher(api_key, secret_key, paper=True)
    cached_fetcher = CachedDataFetcher(alpaca_fetcher, cache_dir="./data/cache")
    
    symbol = "QQQ"
    start_date = date(2024, 6, 1)
    end_date = date(2024, 11, 30)
    
    # Comprehensive analysis
    results_df = analyze_all_patterns(cached_fetcher, symbol, start_date, end_date)
    analyze_directional_bias(cached_fetcher, symbol, start_date, end_date)
    
    print("\n\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("\nBest entry time found! Build strategy around this.")


if __name__ == "__main__":
    main()
