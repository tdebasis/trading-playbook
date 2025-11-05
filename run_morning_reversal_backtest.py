"""
Run Morning Reversal backtest on extended dataset.

Tests the "buy morning low bounce, hold to EOD" strategy over 6 months.
"""

import os
from datetime import date, time
from dotenv import load_dotenv
import pandas as pd

from trading_playbook.adapters.alpaca_fetcher import AlpacaDataFetcher
from trading_playbook.adapters.cached_fetcher import CachedDataFetcher
from trading_playbook.models.market_data import TimeFrame
from trading_playbook.core.indicators import calculate_ema
from trading_playbook.core.morning_reversal_detector import detect_morning_reversal_signal
from trading_playbook.models.trade import Trade, BacktestResults, ExitReason


def run_morning_reversal_backtest(fetcher, symbol, start_date, end_date, shares_per_trade=100, strategy_params=None):
    """Run backtest for Morning Reversal strategy."""
    
    print(f"\n{'='*80}")
    print(f"MORNING REVERSAL BACKTEST: {symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Shares per trade: {shares_per_trade}")
    if strategy_params:
        print(f"Parameters: {strategy_params}")
    print(f"{'='*80}\n")
    
    # Get trading days
    daily_df = fetcher.fetch_daily_bars(symbol, start_date, end_date)
    trading_days = [d.date() for d in daily_df.index]
    
    print(f"Scanning {len(trading_days)} trading days for signals...\n")
    
    trades = []
    
    for i, trade_date in enumerate(trading_days, 1):
        print(f"[{i}/{len(trading_days)}] {trade_date}...", end=" ")
        
        # Fetch 2-min bars
        bars = fetcher.fetch_intraday_bars(symbol, trade_date, TimeFrame.MINUTE_2)
        if not bars:
            print("Skip (no data)")
            continue
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'timestamp': bar.timestamp,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume
            }
            for bar in bars
        ])
        
        # Detect signal
        signal = detect_morning_reversal_signal(df, strategy_params)
        
        if signal.signal_detected:
            print(f"SIGNAL @ {signal.entry_time.time()}", end=" ")
            
            # Simulate trade - hold to EOD
            entry_time = signal.entry_time
            entry_price = signal.entry_price
            
            # Find EOD exit (3:55 PM or last bar)
            exit_target_time = time(15, 55)
            after_entry = df[df['timestamp'] >= entry_time]
            eod_bars = after_entry[after_entry['timestamp'].dt.time >= exit_target_time]
            
            if eod_bars.empty:
                exit_bar = after_entry.iloc[-1]
            else:
                exit_bar = eod_bars.iloc[0]
            
            exit_price = exit_bar['close']
            exit_time = exit_bar['timestamp']
            
            # Calculate P&L
            pnl = (exit_price - entry_price) * shares_per_trade
            
            # Track MAE/MFE
            mae = (after_entry['low'].min() - entry_price) * shares_per_trade
            mfe = (after_entry['high'].max() - entry_price) * shares_per_trade
            
            trade = Trade(
                symbol=symbol,
                entry_time=entry_time,
                entry_price=entry_price,
                exit_time=exit_time,
                exit_price=exit_price,
                exit_reason=ExitReason.END_OF_DAY,
                shares=shares_per_trade,
                stop_price=0,  # No stop in this strategy
                signal_date=signal.date,
                pullback_time=signal.pullback_time,
                pnl=pnl,
                mae=mae,
                mfe=mfe
            )
            
            trades.append(trade)
            
            win_loss = "WIN" if trade.is_winner() else "LOSS"
            print(f"-> {win_loss}: ${trade.pnl:+.2f}")
        else:
            print("No signal")
    
    # Create results
    from datetime import datetime
    results = BacktestResults(
        trades=trades,
        start_date=datetime.combine(start_date, time(0, 0)),
        end_date=datetime.combine(end_date, time(0, 0)),
        symbol=symbol
    )
    
    return results


def main():
    load_dotenv()
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    
    print("Setting up data fetcher...")
    alpaca_fetcher = AlpacaDataFetcher(api_key, secret_key, paper=True)
    cached_fetcher = CachedDataFetcher(alpaca_fetcher, cache_dir="./data/cache")
    
    # Test on 6 months: June 1 - Nov 30, 2024
    results = run_morning_reversal_backtest(
        fetcher=cached_fetcher,
        symbol="QQQ",
        start_date=date(2024, 6, 1),
        end_date=date(2024, 11, 30),
        shares_per_trade=100
    )
    
    print(results.summary())
    
    # Monthly breakdown
    if results.trades:
        print("\n" + "="*80)
        print("MONTHLY BREAKDOWN")
        print("="*80)
        
        trades_df = pd.DataFrame([
            {
                'date': t.signal_date.date(),
                'pnl': t.pnl,
                'month': t.signal_date.strftime('%Y-%m')
            }
            for t in results.trades
        ])
        
        monthly = trades_df.groupby('month').agg({
            'pnl': ['sum', 'count', 'mean']
        }).round(2)
        
        print(monthly)
        
        # Additional metrics
        print("\n" + "="*80)
        print("ADDITIONAL METRICS")
        print("="*80)
        
        avg_mae = sum(t.mae for t in results.trades) / len(results.trades)
        avg_mfe = sum(t.mfe for t in results.trades) / len(results.trades)
        
        print(f"\nDrawdown/Excursion:")
        print(f"  Avg MAE (worst): ${avg_mae:.2f}")
        print(f"  Avg MFE (best):  ${avg_mfe:.2f}")
        
        # Compare to DP20
        print("\n" + "="*80)
        print("COMPARISON TO DP20 STRATEGY")
        print("="*80)
        print("DP20 (Sep-Nov):      -$874.72 loss, 6.7% win rate")
        print(f"Morning Reversal:    ${results.total_pnl:+,.2f}, {results.win_rate:.1f}% win rate")
        
        if results.total_pnl > 0:
            print(f"\n🎉 Morning Reversal WINS by ${results.total_pnl + 874.72:,.2f}!")
        else:
            print(f"\n😞 Morning Reversal also loses: ${results.total_pnl:,.2f}")


if __name__ == "__main__":
    main()
