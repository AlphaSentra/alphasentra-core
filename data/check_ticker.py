import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from logging_utils import log_error
from data.provider_factory import get_data_provider

provider = get_data_provider()

def ticker_exists(ticker):
    """
    Check if a ticker exists.
    """
    return provider.ticker_exists(ticker)
