"""
Run Momentum-Filtered Wednesday/Tuesday 11 AM strategy backtest.

This adds momentum filter to the basic Wed/Tue 11 AM strategy.
Only trades when price is bouncing UP from morning low.
"""

import os
from datetime import date, time
from dotenv import load_dotenv
import pandas as pd

from trading_playbook.adapters.alpaca_fetcher import AlpacaDataFetcher
from trading_playbook.adapters.cached_fetcher import CachedDataFetcher
from trading_playbook.models.market_data import TimeFrame
from trading_playbook.core.momentum_wed_tue_detector import detect_momentum_wed_tue_signal
from trading_playbook.models.trade import Trade, BacktestResults, ExitReason


def run_momentum_backtest(fetcher, symbol, start_date, end_date, shares_per_trade=100, strategy_params=None):
    """Run backtest for Momentum-Filtered Wed/Tue 11 AM strategy."""

    print(f"\n{'='*80}")
    print(f"MOMENTUM-FILTERED WED/TUE 11 AM BACKTEST: {symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Shares per trade: {shares_per_trade}")
    print(f"Strategy: Wed/Tue at 11 AM + Momentum Filter (bounce > 0.3%)")
    print(f"{'='*80}\n")

    # Get trading days
    daily_df = fetcher.fetch_daily_bars(symbol, start_date, end_date)
    trading_days = [d.date() for d in daily_df.index]

    print(f"Scanning {len(trading_days)} trading days for signals...\n")

    trades = []
    filtered_count = 0

    for i, trade_date in enumerate(trading_days, 1):
        print(f"[{i}/{len(trading_days)}] {trade_date} ({trade_date.strftime('%A')})...", end=" ")

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

        # Detect signal with momentum filter
        signal = detect_momentum_wed_tue_signal(df, strategy_params)

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
                pullback_time=entry_time,
                pnl=pnl,
                mae=mae,
                mfe=mfe
            )

            trades.append(trade)

            win_loss = "WIN" if trade.is_winner() else "LOSS"
            print(f"-> {win_loss}: ${trade.pnl:+.2f} ({signal.notes})")
        else:
            # Count how many were filtered by momentum
            if "Insufficient bounce" in signal.notes:
                filtered_count += 1
                print(f"FILTERED: {signal.notes}")
            else:
                print(signal.notes)

    print(f"\n{'='*80}")
    print(f"FILTERING STATS")
    print(f"{'='*80}")
    print(f"Total Wed/Tue days: ~{len([d for d in trading_days if d.strftime('%A') in ['Wednesday', 'Tuesday']])}")
    print(f"Filtered out by momentum: {filtered_count}")
    print(f"Trades taken: {len(trades)}")

    # Create results
    from datetime import datetime
    results = BacktestResults(
        trades=trades,
        start_date=datetime.combine(start_date, time(0, 0)),
        end_date=datetime.combine(end_date, time(0, 0)),
        symbol=symbol
    )

    return results


def calculate_returns_on_investment(results, initial_capital=10000):
    """Calculate realistic returns based on initial capital."""
    if not results.trades:
        return {
            'initial_capital': initial_capital,
            'final_capital': initial_capital,
            'total_return_dollars': 0,
            'total_return_percent': 0,
            'annualized_return_percent': 0
        }

    first_entry_price = results.trades[0].entry_price
    shares_we_can_buy = int(initial_capital / first_entry_price)
    scale_factor = shares_we_can_buy / 100
    total_pnl_scaled = results.total_pnl * scale_factor

    final_capital = initial_capital + total_pnl_scaled
    total_return_pct = (total_pnl_scaled / initial_capital) * 100

    days_in_period = (results.end_date - results.start_date).days
    years_in_period = days_in_period / 365.25
    annualized_return_pct = total_return_pct / years_in_period if years_in_period > 0 else 0

    return {
        'initial_capital': initial_capital,
        'shares_per_trade': shares_we_can_buy,
        'first_entry_price': first_entry_price,
        'final_capital': final_capital,
        'total_return_dollars': total_pnl_scaled,
        'total_return_percent': total_return_pct,
        'annualized_return_percent': annualized_return_pct,
        'period_days': days_in_period,
        'period_years': years_in_period
    }


def main():
    load_dotenv()
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    print("Setting up data fetcher...")
    alpaca_fetcher = AlpacaDataFetcher(api_key, secret_key, paper=True)
    cached_fetcher = CachedDataFetcher(alpaca_fetcher, cache_dir="./data/cache")

    # Test on full 6 months: June 1 - Nov 30, 2024
    results = run_momentum_backtest(
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
                'day_of_week': t.signal_date.strftime('%A'),
                'pnl': t.pnl,
                'month': t.signal_date.strftime('%Y-%m')
            }
            for t in results.trades
        ])

        monthly = trades_df.groupby('month').agg({
            'pnl': ['sum', 'count', 'mean']
        }).round(2)

        print(monthly)

        # Day of week breakdown
        print("\n" + "="*80)
        print("DAY OF WEEK BREAKDOWN")
        print("="*80)

        dow = trades_df.groupby('day_of_week').agg({
            'pnl': ['sum', 'count', 'mean']
        }).round(2)

        print(dow)

        # Calculate returns on $10k investment
        print("\n" + "="*80)
        print("RETURNS ON $10,000 INVESTMENT")
        print("="*80)

        roi_full = calculate_returns_on_investment(results, initial_capital=10000)

        print(f"\nStarting Capital:    ${roi_full['initial_capital']:,.2f}")
        print(f"Shares per trade:    {roi_full['shares_per_trade']} shares @ ${roi_full['first_entry_price']:.2f}")
        print(f"\nEnding Capital:      ${roi_full['final_capital']:,.2f}")
        print(f"Total Return:        ${roi_full['total_return_dollars']:+,.2f}")
        print(f"Return %:            {roi_full['total_return_percent']:+.2f}%")
        print(f"Annualized Return:   {roi_full['annualized_return_percent']:+.2f}%")

        # 3-month subset (Sep-Nov)
        print("\n" + "="*80)
        print("3-MONTH RETURNS (SEP-NOV 2024)")
        print("="*80)

        sep_nov_trades = [t for t in results.trades if t.signal_date.date() >= date(2024, 9, 1)]

        if sep_nov_trades:
            from datetime import datetime
            sep_nov_results = BacktestResults(
                trades=sep_nov_trades,
                start_date=datetime.combine(date(2024, 9, 1), time(0, 0)),
                end_date=datetime.combine(date(2024, 11, 30), time(0, 0)),
                symbol="QQQ"
            )

            roi_3mo = calculate_returns_on_investment(sep_nov_results, initial_capital=10000)

            print(f"\nStarting Capital:    ${roi_3mo['initial_capital']:,.2f}")
            print(f"Shares per trade:    {roi_3mo['shares_per_trade']} shares")
            print(f"\nEnding Capital:      ${roi_3mo['final_capital']:,.2f}")
            print(f"Total Return:        ${roi_3mo['total_return_dollars']:+,.2f}")
            print(f"Return %:            {roi_3mo['total_return_percent']:+.2f}%")
            print(f"Annualized Return:   {roi_3mo['annualized_return_percent']:+.2f}%")

        # Comparison to previous strategies
        print("\n" + "="*80)
        print("STRATEGY COMPARISON (6 months)")
        print("="*80)
        print("\nStrategy                             Total P&L    Win Rate    Trades    Avg P&L")
        print("-"*80)
        print(f"DP20                                  -$874.72        6.7%        15     -$58.31")
        print(f"Morning Reversal                       +$398.00       51.0%        75      +$5.31")
        print(f"Wed/Tue 11AM (no filter)            +$2,888.46       64.7%        51     +$56.64")
        print(f"Wed/Tue 11AM + MOMENTUM             +${results.total_pnl:,.2f}       {results.win_rate:.1f}%        {results.total_trades}    +${results.expectancy:.2f}")

        improvement = results.total_pnl - 2888.46
        if improvement > 0:
            print(f"\n🎉 Momentum filter IMPROVES by ${improvement:,.2f}!")
        else:
            print(f"\n⚠️  Momentum filter reduces P&L by ${abs(improvement):,.2f}")

        if results.total_pnl > 0:
            print(f"\n✅ This strategy is PROFITABLE over 6 months")


if __name__ == "__main__":
    main()
