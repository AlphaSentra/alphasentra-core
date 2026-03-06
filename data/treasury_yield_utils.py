import yfinance as yf
from logging_utils import log_error, log_warning, log_info

def get_tlt_dividend_yield() -> float:
    """
    Fetches the current dividend yield for TLT using yfinance.
    """
    try:
        tlt = yf.Ticker("TLT")
        # Fetching the info can give a lot of data, dividendYield is one of them
        info = tlt.info
        dividend_yield = info.get("dividendYield")
        if dividend_yield is not None:
            dividend_yield_decimal = dividend_yield / 100
            log_info(f"Successfully fetched TLT dividend yield: {dividend_yield_decimal} (converted from {dividend_yield}%)")
            return dividend_yield_decimal
        else:
            log_warning("TLT dividend yield not found in yfinance info. Returning 0.0.")
            return 0.0
    except Exception as e:
        log_error(f"Error fetching TLT dividend yield: {e}", "YFINANCE_FETCH_ERROR", e)
        return 0.0 # Return 0.0 in case of an error
