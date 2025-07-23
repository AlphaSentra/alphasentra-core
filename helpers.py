"""
Project:     Alphagora Trading System
File:        helpers.py
Author:      Daiviet Huynh
Created:     2025-07-22
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Helper functions for the Alphagora Trading System.
"""


from sklearn.linear_model import HuberRegressor
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

# --- HELPER FUNCTIONS ---

def get_beta(ticker, market='SPY', lookback_years=1):
    """Estimate beta of a security relative to the market (default: SPY) using HuberRegressor."""
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365 * lookback_years)

    data = yf.download([ticker, market], start=start_date, end=end_date, auto_adjust=True, progress=False)['Close']
    data = data.dropna()
    if data.empty or len(data) < 50:
        return None

    returns = np.log(data / data.shift(1)).dropna()
    X = returns[market].values.reshape(-1, 1)
    y = returns[ticker].values

    model = HuberRegressor().fit(X, y)
    return model.coef_[0]
