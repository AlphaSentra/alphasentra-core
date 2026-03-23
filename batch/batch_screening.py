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

from logging_utils import log_info, AgLogger
from helpers import DatabaseManager
from data.tickers_01_performance_filter import collect_all_tickers_performance_metrics
from data.tickers_02_metrics_collection import update_ticker_data_in_db, get_equity_tickers_from_db, get_crypto_tickers_from_db, get_fx_tickers_from_db

# Initialize logger
logger = AgLogger('batch_screening')

def reset_screener_flags():
    """
    Reset the screener_flag field to 0 for all documents in the tickers collection.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting reset of screener_flag field in tickers collection")
        
        # Get MongoDB client using DatabaseManager
        client = DatabaseManager().get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        db = client[db_name]
        collection = db['tickers']
        
        # Update all documents to set screener_flag to 0
        result = collection.update_many(
            filter={},
            update={"$set": {"screener_flag": 0}}
        )
        
        logger.info(f"Successfully updated {result.modified_count} documents in tickers collection")
        logger.info("Reset of screener_flag field completed")
        return True
        
    except Exception as e:
        logger.error("Failed to reset screener_flag field", "DATABASE_OPERATION", e)
        return False

def run_batch_screening():
    """
    Executes the complete batch screening workflow.

    This function coordinates the sequential execution of several data processing steps:
    1. Calls `collect_all_tickers_performance_metrics` to gather initial performance data.
    2. Calls `reset_screener_flags` to clear flags from previous runs.
    3. Invokes `update_ticker_data_in_db` multiple times to fetch and update detailed metrics
       for equities (growth and income in US/AU regions), cryptocurrencies, and forex pairs.
   
    Logging messages are used throughout the process to indicate the status and progress of each step.
    """
    log_info("Starting batch screening process...")

    # Step 1: Collect all tickers performance metrics
    log_info("Step 1: Collecting all tickers performance metrics...")
    collect_all_tickers_performance_metrics()
    log_info("Step 1: Completed collecting all tickers performance metrics.")

    # Step 2: Reset screener flags
    log_info("Step 2: Resetting screener flags...")
    reset_screener_flags()
    log_info("Step 2: Completed resetting screener flags.")


    # Step 3: Update ticker data in DB for various categories
    log_info("Step 3: Updating ticker data in database...")
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["US"], category=["growth"])
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["US"], category=["income"])

    update_ticker_data_in_db(get_equity_tickers_from_db, region=["UK"], category=["growth"])
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["UK"], category=["income"])

    update_ticker_data_in_db(get_equity_tickers_from_db, region=["Australia"], category=["growth"])
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["Australia"], category=["income"])

    update_ticker_data_in_db(get_equity_tickers_from_db, region=["France"], category=["growth"])
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["France"], category=["income"])

    update_ticker_data_in_db(get_equity_tickers_from_db, region=["Germany"], category=["growth"])
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["Germany"], category=["income"])

    update_ticker_data_in_db(get_equity_tickers_from_db, region=["Hong Kong"], category=["growth"])
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["Hong Kong"], category=["income"])


    update_ticker_data_in_db(get_crypto_tickers_from_db, region=None, category=["crypto"])
    update_ticker_data_in_db(get_fx_tickers_from_db, region=None, category=["forex"])
    log_info("Step 3: Completed updating ticker data in database.")

    log_info("Batch screening process completed.")

if __name__ == '__main__':
    run_batch_screening()
