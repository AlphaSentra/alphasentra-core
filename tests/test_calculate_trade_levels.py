"""
Tests for calculate_trade_levels fallback behavior.

Run:
    python3 tests/test_calculate_trade_levels.py
"""

import sys
import os
import math
from unittest import mock
from datetime import datetime, timedelta

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _make_price_dataframe(close=1.0850, atr=0.0, adx=0.0):
    dates = pd.date_range(end=datetime.now(), periods=60, freq="D")
    data = pd.DataFrame({
        "Open": [close] * 60,
        "High": [close] * 60,
        "Low": [close] * 60,
        "Close": [close] * 60,
        "Volume": [1000] * 60,
        "ATR": [atr] * 60,
        "ADX": [adx] * 60,
    }, index=dates)
    return data


def _mock_cerebro_run(data, atr_value=0.0, adx_value=0.0):
    class FakeIndicator:
        def __init__(self):
            self._data = [atr_value, adx_value]
        def __getitem__(self, idx):
            return self._data[idx]

    class FakeStrategy:
        def __init__(self):
            self.atr = FakeIndicator()
            self.adx = FakeIndicator()

    class FakeCerebro:
        def __init__(self, *args, **kwargs):
            pass
        def adddata(self, *args, **kwargs):
            pass
        def addstrategy(self, *args, **kwargs):
            pass
        def run(self):
            return [FakeStrategy()]

    return FakeCerebro


def test_fallback_long_when_atr_zero():
    from data.price import calculate_trade_levels

    close = 1.0850
    data = _make_price_dataframe(close=close, atr=0.0, adx=0.0)
    # For LONG fallback: need ATR large enough that close - atr * atr_multiplier <= 0
    # atr_multiplier ranges from 1.5 to 2.5, so use atr >= close / 1.5
    atr_value = close / 1.5 + 0.01

    with mock.patch("data.price.provider.get_price", return_value=data):
        with mock.patch("data.price.bt.Cerebro", side_effect=_mock_cerebro_run(data, atr_value=atr_value, adx_value=50.0)):
            with mock.patch("data.price.calculate_entry_price", return_value={}):
                result = calculate_trade_levels(["EURUSD=X"], "LONG", decimal_digits=4)

    trade = result.get("EURUSD=X")
    assert trade is not None
    assert isinstance(trade["stop_loss"], float)
    assert isinstance(trade["target_price"], float)
    assert math.isclose(trade["stop_loss"], close * 0.975, rel_tol=1e-9)
    assert math.isclose(trade["target_price"], close * 1.05, rel_tol=1e-9)
    print("OK: LONG fallback uses 2.5% stop / 5% target when ATR produces invalid levels")


def test_fallback_short_when_entry_price_zero():
    from data.price import calculate_trade_levels

    close = 1.0850
    data = _make_price_dataframe(close=close, atr=0.001, adx=10.0)

    with mock.patch("data.price.provider.get_price", return_value=data):
        with mock.patch("data.price.bt.Cerebro", side_effect=_mock_cerebro_run(data, atr_value=0.001, adx_value=10.0)):
            with mock.patch("data.price.calculate_entry_price", return_value={"EURUSD=X": 0.0}):
                result = calculate_trade_levels(["EURUSD=X"], "SHORT", decimal_digits=4)

    trade = result.get("EURUSD=X")
    assert trade is not None
    assert isinstance(trade["stop_loss"], float)
    assert isinstance(trade["target_price"], float)
    assert math.isclose(trade["stop_loss"], close * 1.025, rel_tol=1e-9)
    assert math.isclose(trade["target_price"], close * 0.95, rel_tol=1e-9)
    print("OK: SHORT fallback uses 2.5% stop / 5% target when entry_price is 0")


def test_fallback_returns_float_for_all_asset_classes():
    from data.price import calculate_trade_levels

    close = 150.0
    data = _make_price_dataframe(close=close, atr=0.0, adx=0.0)
    # For equity LONG fallback: need ATR large enough to make stop_loss_price <= 0
    atr_value = close / 1.5 + 0.01

    with mock.patch("data.price.provider.get_price", return_value=data):
        with mock.patch("data.price.bt.Cerebro", side_effect=_mock_cerebro_run(data, atr_value=atr_value, adx_value=50.0)):
            with mock.patch("data.price.calculate_entry_price", return_value={}):
                result = calculate_trade_levels(["AAPL"], "LONG", decimal_digits=2)

    trade = result.get("AAPL")
    assert trade is not None
    assert isinstance(trade["stop_loss"], float)
    assert isinstance(trade["target_price"], float)
    assert math.isclose(trade["stop_loss"], close * 0.975, rel_tol=1e-9)
    assert math.isclose(trade["target_price"], close * 1.05, rel_tol=1e-9)
    print("OK: Equity LONG fallback returns float values with 2.5%/5%")


if __name__ == "__main__":
    tests = [
        test_fallback_long_when_atr_zero,
        test_fallback_short_when_entry_price_zero,
        test_fallback_returns_float_for_all_asset_classes,
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
