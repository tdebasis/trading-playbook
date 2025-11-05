"""
Verify the 11 AM strategy claim against actual data.

Cross-check: Did Morning Reversal trades that entered around 11 AM actually perform better?
"""

import os
from datetime import date, time
from dotenv import load_dotenv
import pandas as pd

from trading_playbook.adapters.alpaca_fetcher import AlpacaDataFetcher
from trading_playbook.adapters.cached_fetcher import CachedDataFetcher
from trading_playbook.models.market_data import TimeFrame


def analyze_by_entry_time(fetcher, symbol, start_date, end_date):
    """
    Compare ACTUAL trades grouped by entry time.
    
    This will show us if the 11 AM pattern holds up.
    """
    print("\n" + "="*80)
    print("VERIFYING 11 AM STRATEGY")
    print("="*80)
    
    daily_df = fetcher.fetch_daily_bars(symbol, start_date, end_date)
    trading_days = [d.date() for d in daily_df.index]
    
    all_trades = []
    
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
        
        # Test EVERY possible entry time throughout the day
        for _, entry_bar in df.iterrows():
            entry_time = entry_bar['time']
            
            # Only look at times before 3 PM (need time to exit)
            if entry_time >= time(15, 0):
                continue
            
            entry_price = entry_bar['open']
            
            # Exit at close
            exit_bar = df.iloc[-1]
            exit_price = exit_bar['close']
            
            pnl = (exit_price - entry_price) * 100
            
            # Categorize by hour
            hour = entry_time.hour
            minute_bucket = "early" if entry_time.minute < 30 else "late"
            
            all_trades.append({
                'date': trade_date,
                'entry_time': entry_time,
                'hour': hour,
                'minute_bucket': minute_bucket,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl
            })
    
    trades_df = pd.DataFrame(all_trades)
    
    # Group by hour
    print("\nPERFORMANCE BY HOUR:")
    print("="*80)
    
    hourly = trades_df.groupby('hour').agg({
        'pnl': ['sum', 'mean', 'count', lambda x: (x > 0).sum() / len(x) * 100]
    }).round(2)
    
    hourly.columns = ['Total P&L', 'Avg P&L', 'Count', 'Win Rate %']
    hourly = hourly.sort_values('Total P&L', ascending=False)
    
    print(hourly)
    
    # Detailed breakdown for 10 AM vs 11 AM
    print("\n" + "="*80)
    print("10 AM vs 11 AM COMPARISON")
    print("="*80)
    
    ten_am = trades_df[trades_df['hour'] == 10]
    eleven_am = trades_df[trades_df['hour'] == 11]
    
    print(f"\n10:00 AM Hour:")
    print(f"  Trades: {len(ten_am)}")
    print(f"  Total P&L: ${ten_am['pnl'].sum():,.2f}")
    print(f"  Avg P&L: ${ten_am['pnl'].mean():.2f}")
    print(f"  Win Rate: {(ten_am['pnl'] > 0).sum() / len(ten_am) * 100:.1f}%")
    print(f"  Best trade: ${ten_am['pnl'].max():.2f}")
    print(f"  Worst trade: ${ten_am['pnl'].min():.2f}")
    
    print(f"\n11:00 AM Hour:")
    print(f"  Trades: {len(eleven_am)}")
    print(f"  Total P&L: ${eleven_am['pnl'].sum():,.2f}")
    print(f"  Avg P&L: ${eleven_am['pnl'].mean():.2f}")
    print(f"  Win Rate: {(eleven_am['pnl'] > 0).sum() / len(eleven_am) * 100:.1f}%")
    print(f"  Best trade: ${eleven_am['pnl'].max():.2f}")
    print(f"  Worst trade: ${eleven_am['pnl'].min():.2f}")
    
    # Look for the actual WORST performing times
    print("\n" + "="*80)
    print("WORST PERFORMING TIMES (Avoid These!)")
    print("="*80)
    
    worst_times = trades_df.groupby(['hour', 'minute_bucket']).agg({
        'pnl': ['sum', 'mean', 'count']
    }).round(2)
    worst_times.columns = ['Total P&L', 'Avg P&L', 'Count']
    worst_times = worst_times.sort_values('Total P&L')
    
    print("\nBottom 5:")
    print(worst_times.head(5))
    
    print("\n" + "="*80)
    print("BEST PERFORMING TIMES")
    print("="*80)
    print("\nTop 5:")
    print(worst_times.tail(5))
    
    # Check for any other patterns
    print("\n" + "="*80)
    print("CORRELATION CHECKS")
    print("="*80)
    
    # Does day of week matter?
    trades_df['day_of_week'] = pd.to_datetime(trades_df['date']).dt.day_name()
    dow = trades_df.groupby('day_of_week')['pnl'].agg(['sum', 'mean', 'count']).round(2)
    print("\nBy Day of Week:")
    print(dow)


def main():
    load_dotenv()
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    
    print("Setting up data fetcher...")
    alpaca_fetcher = AlpacaDataFetcher(api_key, secret_key, paper=True)
    cached_fetcher = CachedDataFetcher(alpaca_fetcher, cache_dir="./data/cache")
    
    # Analyze Sep-Nov (smaller dataset, faster)
    analyze_by_entry_time(
        cached_fetcher,
        "QQQ",
        date(2024, 9, 1),
        date(2024, 11, 30)
    )


if __name__ == "__main__":
    main()
