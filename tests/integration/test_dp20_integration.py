"""
Integration test for DP20 signal detection with real QQQ data.

This tests the full pipeline:
1. Fetch data from Alpaca (with caching)
2. Calculate indicators (EMA20, ATR14)
3. Detect DP20 signals
4. Display results

Run with: python3 -m poetry run python test_dp20_integration.py
"""

import os
from datetime import date, datetime
from dotenv import load_dotenv
import pandas as pd

from trading_playbook.models.market_data import TimeFrame
from trading_playbook.adapters.alpaca_fetcher import AlpacaDataFetcher
from trading_playbook.adapters.cached_fetcher import CachedDataFetcher
from trading_playbook.core.indicators import calculate_ema, calculate_sma, calculate_atr
from trading_playbook.core.dp20_detector import detect_dp20_signal


def fetch_and_prepare_day_data(fetcher, symbol, trade_date):
    """
    Fetch and prepare data for one trading day.

    Returns DataFrame with all required indicators calculated.
    """
    print(f"\nFetching {symbol} data for {trade_date}...")

    # Fetch intraday 2-min bars
    bars = fetcher.fetch_intraday_bars(symbol, trade_date, TimeFrame.MINUTE_2)

    if not bars:
        print(f"  No data available for {trade_date}")
        return None

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

    print(f"  Fetched {len(df)} bars")

    # Calculate indicators
    df['ema20'] = calculate_ema(df['close'], period=20)
    df['atr14'] = calculate_atr(df, period=14)

    return df


def get_sma200(fetcher, symbol, trade_date):
    """
    Calculate 200-day SMA as of the trade date.

    Fetch 210 days of daily data prior to trade_date.
    """
    print(f"\nCalculating 200-day SMA for {symbol}...")

    # Calculate date range (210 days before trade_date to get 200 trading days)
    from datetime import timedelta
    start_date = trade_date - timedelta(days=300)  # ~300 calendar days to get 210 trading days

    # Fetch daily bars
    daily_df = fetcher.fetch_daily_bars(symbol, start_date, trade_date)

    if len(daily_df) < 200:
        print(f"  WARNING: Only {len(daily_df)} days of data (need 200)")

    # Calculate SMA200
    sma200_series = calculate_sma(daily_df['close'], period=200)

    # Get most recent SMA200 value
    sma200 = sma200_series.iloc[-1]

    print(f"  SMA200 = ${sma200:.2f}")

    return sma200


def main():
    # Load credentials
    load_dotenv()
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        print("ERROR: ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env")
        return

    print("=" * 80)
    print("DP20 SIGNAL DETECTION - INTEGRATION TEST")
    print("=" * 80)

    # Create fetchers
    print("\n1. Setting up data fetchers...")
    alpaca_fetcher = AlpacaDataFetcher(api_key, secret_key, paper=True)
    cached_fetcher = CachedDataFetcher(alpaca_fetcher, cache_dir="./data/cache")
    print("   Fetchers ready")

    # Test on a recent trading day
    symbol = "QQQ"
    test_date = date(2024, 11, 1)  # Friday, Nov 1, 2024

    print(f"\n2. Testing DP20 detection on {symbol} for {test_date}")

    # Get SMA200
    sma200 = get_sma200(cached_fetcher, symbol, test_date)

    # Fetch and prepare day data
    day_data = fetch_and_prepare_day_data(cached_fetcher, symbol, test_date)

    if day_data is None:
        print("Failed to fetch data")
        return

    # Detect signal
    print(f"\n3. Running DP20 signal detection...")
    signal = detect_dp20_signal(day_data, sma200)

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print(f"\nDate: {test_date}")
    print(f"Symbol: {symbol}")
    print(f"SMA200: ${sma200:.2f}")
    print(f"Day Open: ${day_data.iloc[0]['open']:.2f}")

    print(f"\nSignal Detected: {signal.signal_detected}")
    print(f"Notes: {signal.notes}")

    if signal.signal_detected:
        print(f"\n--- SIGNAL DETAILS ---")
        print(f"Pullback Time:      {signal.pullback_time.time()}")
        print(f"Reversal Time:      {signal.reversal_time.time()}")
        print(f"Reversal Strength:  {signal.reversal_strength:.1%}")
        print(f"Confirmation Time:  {signal.confirmation_time.time()}")
        print(f"\n--- ENTRY SETUP ---")
        print(f"Entry Time:         {signal.entry_time.time()}")
        print(f"Entry Price:        ${signal.entry_price:.2f}")
        print(f"EMA20 at Entry:     ${signal.ema20_at_entry:.2f}")
        print(f"ATR14 at Entry:     ${signal.atr14_at_entry:.2f}")
        print(f"Stop Distance:      ${signal.stop_distance:.2f}")
        print(f"Stop Price:         ${signal.stop_price:.2f}")
        print(f"Risk per Share:     ${signal.entry_price - signal.stop_price:.2f}")

    # Try a few more recent dates
    print("\n" + "=" * 80)
    print("TESTING MULTIPLE DAYS")
    print("=" * 80)

    test_dates = [
        date(2024, 10, 31),  # Thursday
        date(2024, 10, 30),  # Wednesday
        date(2024, 10, 29),  # Tuesday
        date(2024, 10, 28),  # Monday
    ]

    print(f"\nScanning {len(test_dates)} trading days for DP20 signals...\n")

    signals_found = []

    for test_date in test_dates:
        # Get SMA200 for this date
        sma200 = get_sma200(cached_fetcher, symbol, test_date)

        # Fetch day data
        day_data = fetch_and_prepare_day_data(cached_fetcher, symbol, test_date)

        if day_data is None:
            continue

        # Detect signal
        signal = detect_dp20_signal(day_data, sma200)

        status = "SIGNAL" if signal.signal_detected else "No signal"
        print(f"{test_date}: {status} - {signal.notes}")

        if signal.signal_detected:
            signals_found.append((test_date, signal))

    # Summary
    print("\n" + "=" * 80)
    print(f"SUMMARY: Found {len(signals_found)} DP20 signal(s) in {len(test_dates)} days")
    print("=" * 80)

    for trade_date, signal in signals_found:
        print(f"\n{trade_date}:")
        print(f"  Entry: {signal.entry_time.time()} @ ${signal.entry_price:.2f}")
        print(f"  Stop:  ${signal.stop_price:.2f}")
        print(f"  Risk:  ${signal.entry_price - signal.stop_price:.2f}")


if __name__ == "__main__":
    main()
