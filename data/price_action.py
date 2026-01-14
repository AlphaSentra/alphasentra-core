
import yfinance as yf
import numpy as np
from logging_utils import log_error, log_info
from _config import MONTE_CARLO_MODEL_TIME_HORIZON

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
      The annualized volatility as a 2-decimal percentage, or None if an error occurs.
    """
    try:
        log_info(f"Calculating volatility for {ticker}...")
        close_prices = get_close_prices(ticker, days)
        if close_prices is None:
            return None
        log_returns = np.log(close_prices / close_prices.shift(1))
        daily_volatility = log_returns.std()
        annualized_volatility = daily_volatility * np.sqrt(252) # Assuming 252 trading days in a year
        result = round(annualized_volatility * 100, 2)
        log_info(f"Calculated volatility for {ticker}: {result}%")
        return result
    except Exception as e:
        log_error(f"Error calculating volatility for {ticker}", "CALCULATION", e)
        return None

def calculate_drift(ticker, days=MONTE_CARLO_MODEL_TIME_HORIZON):
    """
    Calculates the annualized drift (mu) of an asset using the Ito Calculus 
    adjustment (volatility drag) for Monte Carlo simulations.
    
    Args:
      ticker: The asset ticker symbol (AAPL, EURUSD=X, BTC-USD).
      days: Number of days (recommend 252 for stability).

    Returns:
      The annualized drift as a decimal (e.g., 0.12 for 12%).
    """
    try:
        log_info(f"Calculating drift for {ticker}...")
        close_prices = get_close_prices(ticker, days)
        
        if close_prices is None or len(close_prices) < 2:
            log_error(f"Insufficient data for {ticker}", "DATA_ISSUE")
            return None

        # 1. Calculate Daily Log Returns
        log_returns = np.log(close_prices / close_prices.shift(1)).dropna()

        # 2. Daily Components
        u = log_returns.mean()
        var = log_returns.var()

        # 3. Apply Drift Adjustment (mu = mean - 0.5 * variance)
        # This prevents the simulation from overestimating growth due to volatility.
        daily_drift = u - (0.5 * var)

        # 4. Annualize (252 days for stocks, ~365 for crypto)
        annual_factor = 365 if "USD" in ticker else 252
        annualized_drift = daily_drift * annual_factor
        
        # 5. Sanity Check / Log Result
        # Convert to percentage only for the log message as requested
        display_result = round(annualized_drift * 100, 2)
        log_info(f"Calculated drift for {ticker}: {display_result}%")
        
        # Return as decimal for the simulation engine
        return annualized_drift

    except Exception as e:
        log_error(f"Error calculating drift for {ticker}", "CALCULATION", e)
        return None
