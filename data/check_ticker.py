import yfinance as yf
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
        return bool(ticker_info)
    except Exception as e:
        log_error(f"Error checking ticker {ticker}", "TICKER_VALIDATION", e)
        return False