
import yfinance as yf
import numpy as np
from logging_utils import log_error, log_info

# Defines the default time horizon for the model
MONTE_CARLO_MODEL_TIME_HORIZON = 252 

def get_close_prices(ticker, days=90):
    """
    Collects the last 'days' of close prices for a given ticker from Yahoo Finance.

    Args:
      ticker: The stock ticker symbol.
      days: The number of days of historical data to retrieve.

    Returns:
      A pandas Series of close prices, or None if an error occurs.
    """
    try:
        log_info(f"Fetching {days} days of close prices for {ticker}...")
        stock = yf.Ticker(ticker)
        hist = stock.history(period=f"{days}d")
        log_info(f"Successfully fetched data for {ticker}.")
        return hist['Close']
    except Exception as e:
        log_error(f"Error fetching data for {ticker}", "DATA_FETCH", e)
        return None

def calculate_volatility(ticker, days=MONTE_CARLO_MODEL_TIME_HORIZON):
    """
    Calculates the annualized volatility (sigma) of a series of close prices for a given ticker.

    Args:
      ticker: The stock ticker symbol.
      days: The number of days of historical data to retrieve.

    Returns:
      The annualized volatility as a 2-decimal double. Defaults to 0.3 if an error occurs.
    """
    try:
        log_info(f"Calculating volatility for {ticker}...")
        close_prices = get_close_prices(ticker, days)
        
        if close_prices is None or len(close_prices) < 2:
            log_error(f"Insufficient data for {ticker}, defaulting volatility to 0.3", "DATA_ISSUE")
            return 0.3

        # 1. Calculate Daily Log Returns and drop NaN
        log_returns = np.log(close_prices / close_prices.shift(1)).dropna()

        # 2. Calculate Daily Volatility
        daily_volatility = log_returns.std()

        # 3. Annualize
        annualized_volatility = daily_volatility * np.sqrt(252)

        # 4. Format as percentage for display
        result = annualized_volatility
        log_info(f"Calculated volatility for {ticker}: {result}")
        return result
        
    except Exception as e:
        log_error(f"Error calculating volatility for {ticker}, defaulting to 0.3", "CALCULATION", e)
        return 0.3

def calculate_drift(ticker, days=MONTE_CARLO_MODEL_TIME_HORIZON):
    """
    Calculates the annualized drift (mu) from log returns for use in a
    Geometric Brownian Motion Monte Carlo simulation.

    Args:
      ticker: The asset ticker symbol.
      days: Number of days of historical data (typically 252 or more).

    Returns:
      The annualized drift as a decimal (e.g., 0.12 for 12%). Defaults to 0.0 on error.
    """
    try:
        log_info(f"Calculating drift for {ticker}...")
        close_prices = get_close_prices(ticker, days)

        if close_prices is None or len(close_prices) < 2:
            log_error(f"Insufficient data for {ticker}, defaulting drift to 0.0", "DATA_ISSUE")
            return 0.0

        # 1. Daily log returns
        log_returns = np.log(close_prices / close_prices.shift(1)).dropna()

        # 2. Estimate daily drift from log returns
        daily_drift = log_returns.mean()

        # 3. Annualize
        annualized_drift = daily_drift * 252

        log_info(
            f"Calculated drift for {ticker}: {round(annualized_drift, 4)}"
        )

        return annualized_drift

    except Exception as e:
        log_error(f"Error calculating drift for {ticker}, defaulting to 0.0", "CALCULATION", e)
        return 0.0
