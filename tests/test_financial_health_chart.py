"""
Smoke test for financial_health_chart using AAPL and MSFT.

Run:
    python3 tests/test_financial_health_chart.py
"""

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def test_financial_health_chart(ticker):
    from data.price import financial_health_chart
    from helpers import get_asset_classes

    chart = {"title": "", "xAxis": {}, "yAxis": {}, "series": []}

    asset_classes = get_asset_classes(ticker)
    if "EQ" not in asset_classes:
        print(f"Ticker: {ticker}")
        print(f"  Asset classes: {asset_classes}")
        print("  -> Skipped: not an equity instrument")
        print()
        return False

    try:
        from data.provider_factory import get_data_provider
        provider = get_data_provider()
        bs = provider.get_balance_sheet(ticker, quarterly=True)
        cf = provider.get_cashflow(ticker, quarterly=True)
        print(f"Ticker: {ticker}")
        print(f"  Balance sheet type : {type(bs).__name__}")
        print(f"  Balance sheet shape: {bs.shape if bs is not None else 'None'}")
        print(f"  Cash flow type     : {type(cf).__name__}")
        print(f"  Cash flow shape    : {cf.shape if cf is not None else 'None'}")
        if bs is not None and not bs.empty:
            print(f"  BS index (first 8) : {list(bs.index[:8])}")
            print(f"  BS columns (first 8): {list(bs.columns[:8])}")
        if cf is not None and not cf.empty:
            print(f"  CF index (first 8) : {list(cf.index[:8])}")
    except Exception as e:
        print(f"  Provider fetch error: {e}")
    print()

    result = financial_health_chart(ticker)
    chart = result.get("financial_health_chart", {}) if result else {}

    print(f"Ticker: {ticker}")
    print(f"  Result keys: {list(result.keys()) if result else 'None'}")
    print(f"  Chart keys  : {list(chart.keys()) if chart else 'None'}")

    if not chart or not chart.get("series"):
        print(f"  -> No chart data collected for {ticker}")
        print()
        return False

    series_names = [s.get("name") for s in chart.get("series", [])]
    print(f"  Title       : {chart.get('title')}")
    print(f"  Categories  : {chart.get('xAxis', {}).get('categories', [])}")
    print(f"  Series      : {series_names}")
    print(f"  -> Chart OK for {ticker}")
    print()
    return True


if __name__ == "__main__":
    tickers = ["AAPL", "MSFT", "ARM", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "JNJ", "WMT", "PG", "DIS", "MA"]
    results = {}

    for ticker in tickers:
        results[ticker] = test_financial_health_chart(ticker)

    failed = [t for t, ok in results.items() if not ok]

    if failed:
        print(f"Failed tickers: {failed}")
        sys.exit(1)

    print(f"All {len(tickers)} tickers have financial_health_chart data.")
