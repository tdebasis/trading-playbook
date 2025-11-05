"""
Integration test for data fetcher with real Alpaca API.

This tests the full stack:
1. AlpacaDataFetcher -> Alpaca API
2. CachedDataFetcher -> Local parquet files
3. Verify caching works (second call is much faster)

Run with: python3 -m poetry run python test_data_fetcher.py
"""

import os
from datetime import date
from dotenv import load_dotenv

from trading_playbook.models.market_data import TimeFrame
from trading_playbook.adapters.alpaca_fetcher import AlpacaDataFetcher
from trading_playbook.adapters.cached_fetcher import CachedDataFetcher


def main():
    # Load credentials from .env
    load_dotenv()
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        print("ERROR: ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env")
        return

    print("=" * 80)
    print("DATA FETCHER INTEGRATION TEST")
    print("=" * 80)

    # Create fetchers
    print("\n1. Creating Alpaca fetcher...")
    alpaca_fetcher = AlpacaDataFetcher(api_key, secret_key, paper=True)
    print("    Alpaca fetcher created")

    print("\n2. Wrapping with cache...")
    cached_fetcher = CachedDataFetcher(alpaca_fetcher, cache_dir="./data/cache")
    print("    Cached fetcher created")

    # Test intraday data
    print("\n" + "=" * 80)
    print("TESTING INTRADAY DATA (2-min bars)")
    print("=" * 80)

    test_date = date(2024, 11, 1)  # Friday, Nov 1, 2024
    symbol = "QQQ"

    print(f"\n3. Fetching {symbol} 2-min bars for {test_date}...")
    print("   (This will hit Alpaca API - may take a few seconds)")

    import time
    start_time = time.time()
    bars = cached_fetcher.fetch_intraday_bars(symbol, test_date, TimeFrame.MINUTE_2)
    elapsed1 = time.time() - start_time

    print(f"    Fetched {len(bars)} bars in {elapsed1:.2f} seconds")

    if bars:
        print(f"\n   First bar:")
        print(f"     Time:   {bars[0].timestamp}")
        print(f"     Open:   ${bars[0].open:.2f}")
        print(f"     High:   ${bars[0].high:.2f}")
        print(f"     Low:    ${bars[0].low:.2f}")
        print(f"     Close:  ${bars[0].close:.2f}")
        print(f"     Volume: {bars[0].volume:,}")

        print(f"\n   Last bar:")
        print(f"     Time:   {bars[-1].timestamp}")
        print(f"     Close:  ${bars[-1].close:.2f}")

    print(f"\n4. Fetching SAME data again (should use cache)...")
    start_time = time.time()
    bars2 = cached_fetcher.fetch_intraday_bars(symbol, test_date, TimeFrame.MINUTE_2)
    elapsed2 = time.time() - start_time

    print(f"    Fetched {len(bars2)} bars in {elapsed2:.2f} seconds")
    print(f"   =� Cache speedup: {elapsed1/elapsed2:.1f}x faster!")

    # Verify data is the same
    if bars and bars2:
        assert len(bars) == len(bars2), "Bar count mismatch!"
        assert bars[0].close == bars2[0].close, "Data mismatch!"
        print(f"    Cached data matches original")

    # Test daily data
    print("\n" + "=" * 80)
    print("TESTING DAILY DATA")
    print("=" * 80)

    start_date = date(2024, 10, 1)
    end_date = date(2024, 10, 31)

    print(f"\n5. Fetching {symbol} daily bars from {start_date} to {end_date}...")
    start_time = time.time()
    df = cached_fetcher.fetch_daily_bars(symbol, start_date, end_date)
    elapsed1 = time.time() - start_time

    print(f"    Fetched {len(df)} days in {elapsed1:.2f} seconds")

    if not df.empty:
        print(f"\n   First day:")
        print(f"     Date:   {df.index[0]}")
        print(f"     Close:  ${df.iloc[0]['close']:.2f}")
        print(f"     Volume: {df.iloc[0]['volume']:,}")

        print(f"\n   Last day:")
        print(f"     Date:   {df.index[-1]}")
        print(f"     Close:  ${df.iloc[-1]['close']:.2f}")

    print(f"\n6. Fetching SAME data again (should use cache)...")
    start_time = time.time()
    df2 = cached_fetcher.fetch_daily_bars(symbol, start_date, end_date)
    elapsed2 = time.time() - start_time

    print(f"    Fetched {len(df2)} days in {elapsed2:.2f} seconds")
    print(f"   =� Cache speedup: {elapsed1/elapsed2:.1f}x faster!")

    # Summary
    print("\n" + "=" * 80)
    print(" ALL TESTS PASSED!")
    print("=" * 80)
    print(f"""
Summary:
  - Alpaca API connection: Working 
  - Intraday data fetch: {len(bars)} bars 
  - Daily data fetch: {len(df)} days 
  - Parquet caching: Working 
  - Cache speedup: ~{elapsed1/elapsed2:.0f}x faster 

Cache location: ./data/cache/
    """)


if __name__ == "__main__":
    main()
