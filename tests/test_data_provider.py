"""
Smoke tests for the data provider abstraction.

Run:
    python3 tests/test_data_provider.py
"""

import sys
import os

os.environ.setdefault("ALPHASENTRA_DATA_PROVIDER", "yfinance")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def test_factory_returns_provider():
    from data.provider_factory import get_data_provider
    from data.provider_interface import BaseDataProvider

    provider = get_data_provider()
    assert provider is not None
    assert isinstance(provider, BaseDataProvider)
    print("OK: get_data_provider() returns a BaseDataProvider instance")


def test_yfinance_is_registered():
    from data.provider_factory import _registry

    assert "yfinance" in _registry, f"yfinance not registered. Registry: {list(_registry.keys())}"
    print("OK: yfinance is registered in provider factory")


def test_info_endpoint():
    from data.provider_factory import get_data_provider

    provider = get_data_provider()
    info = provider.get_info("AAPL")
    assert isinstance(info, dict)
    assert info.get("symbol") == "AAPL", f"Unexpected symbol in info: {info.get('symbol')}"
    print("OK: get_info('AAPL') returns AAPL info")


def test_history_endpoint():
    from data.provider_factory import get_data_provider
    import pandas as pd

    provider = get_data_provider()
    hist = provider.get_history("AAPL", "5d")
    assert isinstance(hist, pd.DataFrame), f"Expected DataFrame, got {type(hist)}"
    assert not hist.empty, "History should not be empty for AAPL"
    assert "Close" in hist.columns
    print("OK: get_history('AAPL', '5d') returns non-empty DataFrame with 'Close'")


def test_price_endpoint():
    from data.provider_factory import get_data_provider
    import pandas as pd
    from datetime import datetime, timedelta

    provider = get_data_provider()
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    df = provider.get_price("AAPL", start=start, end=end)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    print("OK: get_price('AAPL', start, end) returns non-empty DataFrame")


def test_ticker_exists():
    from data.provider_factory import get_data_provider

    provider = get_data_provider()
    assert provider.ticker_exists("AAPL") is True
    assert provider.ticker_exists("NOT_A_REAL_TICKER_XYZ123") is False
    print("OK: ticker_exists correctly identifies valid and invalid tickers")


def test_optional_endpoints():
    from data.provider_factory import get_data_provider

    provider = get_data_provider()

    financials = provider.get_financials("AAPL")
    assert financials is None or hasattr(financials, "empty")

    quarterly = provider.get_quarterly_financials("AAPL")
    assert quarterly is None or hasattr(quarterly, "empty")

    bs = provider.get_balance_sheet("AAPL")
    assert bs is None or hasattr(bs, "empty")

    cf = provider.get_cashflow("AAPL")
    assert cf is None or hasattr(cf, "empty")

    divs = provider.get_dividends("AAPL")
    assert divs is None or hasattr(divs, "empty")

    print("OK: optional financial endpoints execute without error")


if __name__ == "__main__":
    tests = [
        test_factory_returns_provider,
        test_yfinance_is_registered,
        test_info_endpoint,
        test_history_endpoint,
        test_price_endpoint,
        test_ticker_exists,
        test_optional_endpoints,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except Exception as exc:
            failed += 1
            print(f"FAIL: {test.__name__}: {exc}")

    print()
    if failed:
        print(f"{failed} test(s) failed.")
        sys.exit(1)
    print(f"All {len(tests)} tests passed.")
