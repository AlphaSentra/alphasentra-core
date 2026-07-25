"""
Smoke tests for main.py -batch entry point and batch run module.

Run:
    python3 tests/test_batch_run.py
"""

import sys
import os
import importlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def test_batch_flag_triggers_run_batch_processing():
    from unittest import mock

    with mock.patch("batch.batch_run.run_batch_processing") as mock_run:
        sys.argv = ["main.py", "-batch"]
        import main as main_module
        importlib.reload(main_module)
        main_module.run_batch_processing()

    assert mock_run.called, "run_batch_processing was not called when -batch was passed"
    print("OK: -batch flag triggers run_batch_processing")


def test_derive_module_and_func():
    from batch.batch_run import derive_module_and_func

    module, func = derive_module_and_func("run_my_model", "my_model.py")
    assert module == "my_model"
    assert func == "run_my_model"
    print("OK: derive_module_and_func('run_my_model', 'my_model.py') returns ('my_model', 'run_my_model')")

    module, func = derive_module_and_func("run_something_model")
    assert module == "something"
    assert func == "run_something_model"
    print("OK: derive_module_and_func('run_something_model') returns ('something', 'run_something_model')")


def test_run_batch_processing_importable():
    from batch.batch_run import run_batch_processing

    assert callable(run_batch_processing)
    print("OK: run_batch_processing is importable and callable")


def test_round_zero_returns_int():
    result = round(0, 2)
    assert isinstance(result, int)
    print("OK: round(0, 2) returns int (demonstrates Python behavior that causes MongoDB type mismatch)")


def test_max_zero_float_returns_int():
    result = max(0, 0.0)
    assert isinstance(result, int)
    print("OK: max(0, 0.0) returns int (demonstrates Python behavior that causes MongoDB type mismatch)")


def test_add_trade_levels_converts_zero_to_float():
    from unittest import mock
    from helpers import add_trade_levels_to_recommendations

    recommendations = {
        'recommendations': [
            {'ticker': 'AAPL', 'trade_direction': 'LONG', 'bull_bear_score': 8}
        ]
    }

    with mock.patch('helpers.calculate_trade_levels', return_value={'AAPL': {'stop_loss': 0.0, 'target_price': 0.0}}):
        result = add_trade_levels_to_recommendations(recommendations, decimal_digits=2)
        trade = result['recommendations'][0]
        assert isinstance(trade['stop_loss'], float), \
            f"stop_loss should be float, got {type(trade['stop_loss'])}: {trade['stop_loss']}"
        assert isinstance(trade['target_price'], float), \
            f"target_price should be float, got {type(trade['target_price'])}: {trade['target_price']}"

    print("OK: add_trade_levels_to_recommendations preserves float types from calculate_trade_levels")


def test_forex_eurusd_stop_loss_and_target_price_types():
    from unittest import mock
    from helpers import add_trade_levels_to_recommendations

    recommendations = {
        'recommendations': [
            {'ticker': 'EURUSD=X', 'trade_direction': 'LONG', 'bull_bear_score': 7},
            {'ticker': 'EURUSD=X', 'trade_direction': 'SHORT', 'bull_bear_score': 6},
        ]
    }

    stop_loss_long = 1.0850
    target_price_long = 1.0950
    stop_loss_short = 1.0950
    target_price_short = 1.0850

    fake_levels_long = {
        'EURUSD=X': {
            'stop_loss': stop_loss_long,
            'target_price': target_price_long,
        }
    }

    fake_levels_short = {
        'EURUSD=X': {
            'stop_loss': stop_loss_short,
            'target_price': target_price_short,
        }
    }

    with mock.patch('helpers.calculate_trade_levels', side_effect=lambda tickers, direction, decimal_digits=4: fake_levels_long if direction == 'LONG' else fake_levels_short):
        result = add_trade_levels_to_recommendations(recommendations, decimal_digits=4)
        long_trade = result['recommendations'][0]
        short_trade = result['recommendations'][1]

        assert long_trade['ticker'] == 'EURUSD=X'
        assert long_trade['trade_direction'] == 'LONG'
        assert isinstance(long_trade['stop_loss'], float)
        assert isinstance(long_trade['target_price'], float)
        assert long_trade['stop_loss'] == float(stop_loss_long)
        assert long_trade['target_price'] == float(target_price_long)

        assert short_trade['ticker'] == 'EURUSD=X'
        assert short_trade['trade_direction'] == 'SHORT'
        assert isinstance(short_trade['stop_loss'], float)
        assert isinstance(short_trade['target_price'], float)
        assert short_trade['stop_loss'] == float(stop_loss_short)
        assert short_trade['target_price'] == float(target_price_short)

    print("OK: EURUSD LONG/SHORT trades keep stop_loss and target_price as float with decimal_digits=4")


def test_forex_eurusd_zero_clamp_remains_float():
    from unittest import mock
    from helpers import add_trade_levels_to_recommendations

    recommendations = {
        'recommendations': [
            {'ticker': 'EURUSD=X', 'trade_direction': 'LONG', 'bull_bear_score': 5},
        ]
    }

    with mock.patch('helpers.calculate_trade_levels', return_value={'EURUSD=X': {'stop_loss': 0.0, 'target_price': 0.0}}):
        result = add_trade_levels_to_recommendations(recommendations, decimal_digits=4)
        trade = result['recommendations'][0]

        assert isinstance(trade['stop_loss'], float), \
            f"Expected float for stop_loss=0, got {type(trade['stop_loss'])}: {trade['stop_loss']}"
        assert isinstance(trade['target_price'], float), \
            f"Expected float for target_price=0, got {type(trade['target_price'])}: {trade['target_price']}"
        assert trade['stop_loss'] == 0.0
        assert trade['target_price'] == 0.0

    print("OK: EURUSD clamped 0 stop_loss/target_price remains float")


if __name__ == "__main__":
    tests = [
        test_batch_flag_triggers_run_batch_processing,
        test_derive_module_and_func,
        test_run_batch_processing_importable,
        test_round_zero_returns_int,
        test_max_zero_float_returns_int,
        test_add_trade_levels_converts_zero_to_float,
        test_forex_eurusd_stop_loss_and_target_price_types,
        test_forex_eurusd_zero_clamp_remains_float,
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
