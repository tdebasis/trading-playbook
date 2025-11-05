"""
Analyze momentum conditions on Wed/Tue 11 AM trades.

Goal: Find what separates the BIG winners from the BIG losers.
- Best trade: Sep 11 Wed +$1,625
- Worst trade: Aug 7 Wed -$1,308

What momentum indicators were present on winners vs losers?
"""

import os
from datetime import date, time
from dotenv import load_dotenv
import pandas as pd
import numpy as np

from trading_playbook.adapters.alpaca_fetcher import AlpacaDataFetcher
from trading_playbook.adapters.cached_fetcher import CachedDataFetcher
from trading_playbook.models.market_data import TimeFrame
from trading_playbook.core.indicators import calculate_ema, calculate_sma


def analyze_momentum_conditions(fetcher, symbol, start_date, end_date):
    """
    Analyze momentum indicators on Wed/Tue to find what predicts winners.
    """
    print("\n" + "="*80)
    print("MOMENTUM ANALYSIS: Wed/Tue 11 AM Trades")
    print("="*80)

    # Get daily data for longer-term trend
    daily_df = fetcher.fetch_daily_bars(symbol, start_date, end_date)
    trading_days = [d.date() for d in daily_df.index]

    # Calculate daily EMAs
    daily_df['ema9'] = calculate_ema(daily_df['close'], period=9)
    daily_df['ema20'] = calculate_ema(daily_df['close'], period=20)
    daily_df['ema50'] = calculate_ema(daily_df['close'], period=50)
    daily_df['sma200'] = calculate_sma(daily_df['close'], period=200)

    trades = []

    for trade_date in trading_days:
        day_of_week = trade_date.strftime('%A')

        # Only analyze Wed/Tue
        if day_of_week not in ['Wednesday', 'Tuesday']:
            continue

        # Get intraday bars
        bars = fetcher.fetch_intraday_bars(symbol, trade_date, TimeFrame.MINUTE_2)
        if not bars:
            continue

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

        # Calculate intraday EMAs
        df['ema20'] = calculate_ema(df['close'], period=20)
        df['ema50'] = calculate_ema(df['close'], period=50)
        df['time'] = df['timestamp'].dt.time

        # Get 11 AM entry
        entry_bars = df[df['time'] >= time(11, 0)]
        if entry_bars.empty:
            continue

        entry_bar = entry_bars.iloc[0]
        entry_time = entry_bar['timestamp']
        entry_price = entry_bar['open']

        # Get EOD exit
        exit_target_time = time(15, 55)
        after_entry = df[df['timestamp'] >= entry_time]
        eod_bars = after_entry[after_entry['time'] >= exit_target_time]

        if eod_bars.empty:
            exit_bar = after_entry.iloc[-1]
        else:
            exit_bar = eod_bars.iloc[0]

        exit_price = exit_bar['close']
        pnl = (exit_price - entry_price) * 100

        # Get daily trend indicators for this date
        daily_row = daily_df[daily_df.index.date == trade_date]
        if daily_row.empty:
            continue

        daily_row = daily_row.iloc[0]

        # Momentum indicators at entry
        momentum_indicators = {
            'date': trade_date,
            'day_of_week': day_of_week,
            'pnl': pnl,
            'entry_price': entry_price,
            'exit_price': exit_price,

            # Daily trend (where are we vs moving averages?)
            'price_vs_ema9': entry_price - daily_row['ema9'],
            'price_vs_ema20': entry_price - daily_row['ema20'],
            'price_vs_ema50': entry_price - daily_row['ema50'],
            'price_vs_sma200': entry_price - daily_row['sma200'],

            # Daily trend strength
            'ema9_above_ema20': 1 if daily_row['ema9'] > daily_row['ema20'] else 0,
            'ema20_above_ema50': 1 if daily_row['ema20'] > daily_row['ema50'] else 0,
            'above_sma200': 1 if entry_price > daily_row['sma200'] else 0,

            # Intraday momentum at 11 AM
            'intraday_ema20': entry_bar['ema20'] if pd.notna(entry_bar['ema20']) else 0,
            'intraday_ema50': entry_bar['ema50'] if pd.notna(entry_bar['ema50']) else 0,
            'price_vs_intraday_ema20': entry_price - entry_bar['ema20'] if pd.notna(entry_bar['ema20']) else 0,
            'price_vs_intraday_ema50': entry_price - entry_bar['ema50'] if pd.notna(entry_bar['ema50']) else 0,

            # Morning behavior (9:30-11:00)
            'morning_bars': df[(df['time'] >= time(9, 30)) & (df['time'] < time(11, 0))],
        }

        # Calculate morning momentum
        morning = momentum_indicators['morning_bars']
        if not morning.empty:
            open_price = df.iloc[0]['open']
            morning_low = morning['low'].min()
            morning_high = morning['high'].max()
            price_at_11am = entry_price

            momentum_indicators['morning_range'] = morning_high - morning_low
            momentum_indicators['morning_move'] = price_at_11am - open_price
            momentum_indicators['morning_move_pct'] = (price_at_11am - open_price) / open_price * 100
            momentum_indicators['bounce_from_low'] = price_at_11am - morning_low
            momentum_indicators['bounce_from_low_pct'] = (price_at_11am - morning_low) / morning_low * 100
            momentum_indicators['distance_from_high'] = morning_high - price_at_11am

        # Remove the DataFrame from dict before storing
        del momentum_indicators['morning_bars']

        trades.append(momentum_indicators)

    # Analyze
    trades_df = pd.DataFrame(trades)

    print(f"\nAnalyzed {len(trades_df)} Wed/Tue 11 AM trades\n")

    # Split winners vs losers
    big_winners = trades_df[trades_df['pnl'] > 200].sort_values('pnl', ascending=False)
    big_losers = trades_df[trades_df['pnl'] < -200].sort_values('pnl')
    small_trades = trades_df[(trades_df['pnl'] >= -200) & (trades_df['pnl'] <= 200)]

    print("="*80)
    print("BIG WINNERS (P&L > $200)")
    print("="*80)
    print(f"Count: {len(big_winners)}")
    print(f"Avg P&L: ${big_winners['pnl'].mean():.2f}")
    print(f"\nTop 5:")
    for _, row in big_winners.head(5).iterrows():
        print(f"  {row['date']} ({row['day_of_week'][:3]}): ${row['pnl']:+.2f}")

    print("\n" + "="*80)
    print("BIG LOSERS (P&L < -$200)")
    print("="*80)
    print(f"Count: {len(big_losers)}")
    print(f"Avg P&L: ${big_losers['pnl'].mean():.2f}")
    print(f"\nWorst 5:")
    for _, row in big_losers.head(5).iterrows():
        print(f"  {row['date']} ({row['day_of_week'][:3]}): ${row['pnl']:+.2f}")

    # Compare momentum conditions
    print("\n" + "="*80)
    print("MOMENTUM CONDITIONS COMPARISON")
    print("="*80)

    if len(big_winners) > 0 and len(big_losers) > 0:
        print(f"\n{'Indicator':<30} {'Big Winners':>15} {'Big Losers':>15} {'Difference':>15}")
        print("-"*80)

        indicators = [
            'above_sma200',
            'ema9_above_ema20',
            'ema20_above_ema50',
            'morning_move_pct',
            'bounce_from_low_pct',
            'price_vs_ema9',
            'price_vs_ema20',
            'price_vs_sma200',
        ]

        for indicator in indicators:
            if indicator in big_winners.columns:
                winner_avg = big_winners[indicator].mean()
                loser_avg = big_losers[indicator].mean()
                diff = winner_avg - loser_avg

                if indicator.endswith('_pct'):
                    print(f"{indicator:<30} {winner_avg:>14.2f}% {loser_avg:>14.2f}% {diff:>14.2f}%")
                elif indicator.startswith('above') or indicator.endswith('above_ema20') or indicator.endswith('above_ema50'):
                    # Convert to percentage
                    winner_pct = winner_avg * 100
                    loser_pct = loser_avg * 100
                    diff_pct = diff * 100
                    print(f"{indicator:<30} {winner_pct:>14.1f}% {loser_pct:>14.1f}% {diff_pct:>14.1f}%")
                else:
                    print(f"{indicator:<30} ${winner_avg:>13.2f} ${loser_avg:>13.2f} ${diff:>13.2f}")

    # Find best filter
    print("\n" + "="*80)
    print("TESTING MOMENTUM FILTERS")
    print("="*80)

    filters = [
        ('Above SMA200', lambda row: row['above_sma200'] == 1),
        ('EMA9 > EMA20', lambda row: row['ema9_above_ema20'] == 1),
        ('EMA20 > EMA50', lambda row: row['ema20_above_ema50'] == 1),
        ('All EMAs aligned', lambda row: row['ema9_above_ema20'] == 1 and row['ema20_above_ema50'] == 1 and row['above_sma200'] == 1),
        ('Morning up > 0.1%', lambda row: row['morning_move_pct'] > 0.1),
        ('Morning up > 0.2%', lambda row: row['morning_move_pct'] > 0.2),
        ('Bounce > 0.3%', lambda row: row['bounce_from_low_pct'] > 0.3),
        ('Above SMA200 + Morning up', lambda row: row['above_sma200'] == 1 and row['morning_move_pct'] > 0.1),
    ]

    print(f"\n{'Filter':<30} {'Trades':>8} {'Win Rate':>10} {'Avg P&L':>12} {'Total P&L':>12}")
    print("-"*80)

    for filter_name, filter_func in filters:
        filtered = trades_df[trades_df.apply(filter_func, axis=1)]

        if len(filtered) > 0:
            win_rate = (filtered['pnl'] > 0).sum() / len(filtered) * 100
            avg_pnl = filtered['pnl'].mean()
            total_pnl = filtered['pnl'].sum()

            print(f"{filter_name:<30} {len(filtered):>8} {win_rate:>9.1f}% ${avg_pnl:>10.2f} ${total_pnl:>10.2f}")

    # Baseline (no filter)
    win_rate_all = (trades_df['pnl'] > 0).sum() / len(trades_df) * 100
    avg_pnl_all = trades_df['pnl'].mean()
    total_pnl_all = trades_df['pnl'].sum()
    print("-"*80)
    print(f"{'NO FILTER (baseline)':<30} {len(trades_df):>8} {win_rate_all:>9.1f}% ${avg_pnl_all:>10.2f} ${total_pnl_all:>10.2f}")

    return trades_df


def main():
    load_dotenv()
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    print("Setting up data fetcher...")
    alpaca_fetcher = AlpacaDataFetcher(api_key, secret_key, paper=True)
    cached_fetcher = CachedDataFetcher(alpaca_fetcher, cache_dir="./data/cache")

    # Analyze 6 months
    trades_df = analyze_momentum_conditions(
        cached_fetcher,
        "QQQ",
        date(2024, 6, 1),
        date(2024, 11, 30)
    )

    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    print("\nBased on analysis, the best momentum filter will be implemented in the next strategy.")


if __name__ == "__main__":
    main()
