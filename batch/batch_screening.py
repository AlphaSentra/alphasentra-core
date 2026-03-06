"""
This script orchestrates a comprehensive batch screening process for various financial instruments.
It performs the following key steps sequentially:
1. Collects initial performance metrics for all tickers.
2. Updates detailed ticker data in the database across different regions and categories (growth, income, crypto, forex).
3. Identifies and retrieves top-performing tickers for further selection analysis in each specified category.

This script is designed to be run as a scheduled task to ensure that the database contains the most up-to-date and relevant data for subsequent analysis and model consumption.
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logging_utils import log_info
from data.tickers_01_performance_filter import collect_all_tickers_performance_metrics
from data.tickers_02_metrics_collection import update_ticker_data_in_db, get_equity_tickers_from_db, get_crypto_tickers_from_db, get_fx_tickers_from_db
from data.tickers_03_selection_analysis import get_top_equities_for_selection_analysis, get_top_cryptos_for_selection_analysis, get_top_forex_for_selection_analysis

def run_batch_screening():
    """
    Executes the complete batch screening workflow.

    This function coordinates the sequential execution of several data processing steps:
    1. Calls `collect_all_tickers_performance_metrics` to gather initial performance data.
    2. Invokes `update_ticker_data_in_db` multiple times to fetch and update detailed metrics
       for equities (growth and income in US/AU regions), cryptocurrencies, and forex pairs.
    3. Triggers `get_top_equities_for_selection_analysis`, `get_top_cryptos_for_selection_analysis`,
       and `get_top_forex_for_selection_analysis` to identify top performers based on updated data.

    Logging messages are used throughout the process to indicate the status and progress of each step.
    """
    log_info("Starting batch screening process...")

    # Step 1: Collect all tickers performance metrics
    log_info("Step 1: Collecting all tickers performance metrics...")
    collect_all_tickers_performance_metrics()
    log_info("Step 1: Completed collecting all tickers performance metrics.")

    # Step 2: Update ticker data in DB for various categories
    log_info("Step 2: Updating ticker data in database...")
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["US"], category=["growth"])
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["AU"], category=["growth"])
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["US"], category=["income"])
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["AU"], category=["income"])
    update_ticker_data_in_db(get_crypto_tickers_from_db, region=None, category=["crypto"])
    update_ticker_data_in_db(get_fx_tickers_from_db, region=None, category=["forex"])
    log_info("Step 2: Completed updating ticker data in database.")

    # Step 3: Get top tickers for selection analysis
    log_info("Step 3: Getting top tickers for selection analysis...")
    get_top_equities_for_selection_analysis(region=["US"], category=["growth"])
    get_top_equities_for_selection_analysis(region=["US"], category=["income"])
    get_top_equities_for_selection_analysis(region=["AU"], category=["growth"])
    get_top_equities_for_selection_analysis(region=["AU"], category=["income"])
    get_top_cryptos_for_selection_analysis(region=None, category=None)
    get_top_forex_for_selection_analysis(region=None, category=None)
    log_info("Step 3: Completed getting top tickers for selection analysis.")

    log_info("Batch screening process completed.")

if __name__ == '__main__':
    run_batch_screening()
