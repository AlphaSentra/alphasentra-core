import yfinance as yf
import os
import sys

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from logging_utils import log_error

def ticker_exists(ticker):
    """
    Check if a ticker exists on Yahoo Finance.
    
    Parameters:
    ticker (str): The ticker symbol to check
    
    Returns:
    bool: True if ticker exists, False otherwise
    """
    try:
        ticker_info = yf.Ticker(ticker).info
        # Check for specific fundamental fields that only exist in valid tickers
        return 'symbol' in ticker_info and ticker_info['symbol'] == ticker
    except Exception as e:
        log_error(f"Error checking ticker {ticker}", "TICKER_VALIDATION", e)
        return False
