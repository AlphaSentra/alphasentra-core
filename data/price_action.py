
import yfinance as yf
import numpy as np

def get_close_prices(ticker, days=90):
  """
  Collects the last '''days''' of close prices for a given ticker from Yahoo Finance.

  Args:
    ticker: The stock ticker symbol.
    days: The number of days of historical data to retrieve.

  Returns:
    A pandas Series of close prices.
  """
  stock = yf.Ticker(ticker)
  hist = stock.history(period=f"{days}d")
  return hist['Close']

def calculate_volatility(ticker, days=90):
  """
  Calculates the annualized volatility (sigma) of a series of close prices for a given ticker.

  Args:
    ticker: The stock ticker symbol.
    days: The number of days of historical data to retrieve.

  Returns:
    The annualized volatility.
  """
  close_prices = get_close_prices(ticker, days)
  log_returns = np.log(close_prices / close_prices.shift(1))
  daily_volatility = log_returns.std()
  annualized_volatility = daily_volatility * np.sqrt(252) # Assuming 252 trading days in a year
  return annualized_volatility

def calculate_drift(ticker, days=90):
  """
  Calculates the annualized drift (mu) of a series of close prices for a given ticker.

  Args:
    ticker: The stock ticker symbol.
    days: The number of days of historical data to retrieve.

  Returns:
    The annualized drift.
  """
  close_prices = get_close_prices(ticker, days)
  log_returns = np.log(close_prices / close_prices.shift(1))
  daily_drift = log_returns.mean()
  annualized_drift = daily_drift * 252 # Assuming 252 trading days in a year
  return annualized_drift
