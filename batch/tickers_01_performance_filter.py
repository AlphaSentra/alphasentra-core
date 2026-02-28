import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import Optional
from datetime import datetime, timedelta
from yahooquery import Ticker
from concurrent.futures import ProcessPoolExecutor

from logging_utils import log_error, log_warning, log_info
from dotenv import load_dotenv
import pymongo
from db.create_mongodb_db import DatabaseManager


def get_tickers_from_db() -> list:
    """
    Retrieves a list of ticker symbols from the 'tickers' collection in the MongoDB database.

    Returns:
        list: A list of ticker symbols (strings). Returns an empty list if no tickers
              are found or an error occurs.
    """
    load_dotenv()
    tickers_list = []
    client = None
    try:
        # Get MongoDB connection
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        collection = db["tickers"]

        # Query to get all documents and extract the 'ticker' field
        # We use a projection to only retrieve the 'ticker' field and exclude '_id'
        cursor = collection.find({}, {"ticker": 1, "_id": 0})

        for doc in cursor:
            if 'ticker' in doc:
                tickers_list.append(doc['ticker'])
        
        log_info(f"Successfully retrieved {len(tickers_list)} tickers from the database.")

    except pymongo.errors.ServerSelectionTimeoutError as e:
        log_error("MongoDB server not found. Ensure MongoDB is running on the specified host/port.", "MONGODB_CONNECTION", e)
    except pymongo.errors.OperationFailure as e:
        log_error(f"MongoDB operation failed: {e}", "MONGODB_OPERATION", e)
    except Exception as e:
        log_error(f"An unexpected error occurred while fetching tickers from DB: {e}", "DATA_FETCHING", e)
    finally:
        if client:
            DatabaseManager().close_connection() # Using the singleton instance to close connection
    return tickers_list


def _get_performance_metrics(ticker_symbol: str) -> Optional[dict]:
    """
    Calculates the 1-week, 1-month, and 3-month percentage performance for a given ticker.

    Args:
        ticker_symbol (str): The ticker symbol (e.g., 'AAPL').

    Returns:
        tuple: A tuple containing (one_week_performance, one_month_performance, three_month_performance).
               Returns None for any performance metric if data is unavailable or an error occurs.
    """
    one_week_performance = _calculate_percentage_performance(ticker_symbol, 7)
    one_month_performance = _calculate_percentage_performance(ticker_symbol, 30)
    three_month_performance = _calculate_percentage_performance(ticker_symbol, 90)
    
    if one_week_performance is not None:
        log_info(f"Collected 1-week performance for {ticker_symbol}: {one_week_performance:.2f}%")
    else:
        log_warning(f"Could not collect 1-week performance for {ticker_symbol}.", "DATA_MISSING")
    
    if one_month_performance is not None:
        log_info(f"Collected 1-month performance for {ticker_symbol}: {one_month_performance:.2f}%")
    else:
        log_warning(f"Could not collect 1-month performance for {ticker_symbol}.", "DATA_MISSING")

    if three_month_performance is not None:
        log_info(f"Collected 3-month performance for {ticker_symbol}: {three_month_performance:.2f}%")
    else:
        log_warning(f"Could not collect 3-month performance for {ticker_symbol}.", "DATA_MISSING")

    return {
        "ticker_symbol": ticker_symbol,
        "1w": one_week_performance / 100.0 if one_week_performance is not None else None,
        "1m": one_month_performance / 100.0 if one_month_performance is not None else None,
        "3m": three_month_performance / 100.0 if three_month_performance is not None else None,
    }


def _calculate_percentage_performance(ticker_symbol: str, lookback_days: int) -> Optional[float]:
    """
    Calculates the percentage performance of a ticker over a specified number of lookback days.

    Args:
        ticker_symbol (str): The ticker symbol (e.g., 'AAPL').
        lookback_days (int): The number of days to look back for calculating the percentage change.

    Returns:
        float: The percentage performance, or None if data is unavailable or an error occurs.
    """
    try:
        end_date = datetime.now()
        # Fetch enough data to cover the lookback period, adding a buffer for non-trading days.
        start_date = end_date - timedelta(days=lookback_days * 2) # Get more days to be safe
        
        yq_ticker = Ticker(ticker_symbol)
        data = yq_ticker.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))

        if data.empty or ticker_symbol not in data.index.get_level_values("symbol"):
            log_warning(f"No historical data available for {ticker_symbol} to calculate {lookback_days}-day percentage performance.", "PERFORMANCE_CALCULATION")
            return None

        ticker_data = data.loc[ticker_symbol]

        # Ensure we have enough data points for the lookback period
        if len(ticker_data) < lookback_days:
            log_warning(f"Less than {lookback_days} days of historical data for {ticker_symbol}. Cannot accurately calculate {lookback_days}-day performance.", "PERFORMANCE_CALCULATION")
            return None

        # Get the closing prices for the relevant period
        close_prices = ticker_data["close"].tail(lookback_days + 1) # Need current day and 'lookback_days' previous days

        if len(close_prices) < lookback_days + 1:
            log_warning(f"Not enough closing prices for {ticker_symbol} to calculate {lookback_days}-day performance.", "PERFORMANCE_CALCULATION")
            return None

        initial_price = close_prices.iloc[0]
        final_price = close_prices.iloc[-1]

        if initial_price == 0:
            log_warning(f"Initial price is zero for {ticker_symbol}. Cannot calculate {lookback_days}-day percentage performance.", "PERFORMANCE_CALCULATION")
            return None

        percentage_performance = ((final_price - initial_price) / initial_price) * 100

        log_info(f"Calculated {lookback_days}-day percentage performance for {ticker_symbol}: {percentage_performance:.2f}%")
        return percentage_performance

    except Exception as e:
        log_error(f"Error calculating {lookback_days}-day percentage performance for {ticker_symbol}: {e}", "PERFORMANCE_CALCULATION", e)
        return None
    
def save_performance_metrics_to_db(metrics_batch: list[dict]):
    """
    Saves a batch of performance metrics to the MongoDB 'tickers' collection.
    Updates existing ticker documents with new performance data.
    """
    load_dotenv()
    client = None
    try:
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        collection = db["tickers"]

        for metric_data in metrics_batch:
            ticker = metric_data.pop("ticker_symbol")
            update_result = collection.update_one(
                {"ticker": ticker},
                {"$set": metric_data}
            )
            if update_result.matched_count == 0:
                log_warning(f"Ticker {ticker} not found in database for update.", "DB_UPDATE_ERROR")
            else:
                log_info(f"Updated performance metrics for {ticker}.")

    except pymongo.errors.ServerSelectionTimeoutError as e:
        log_error("MongoDB server not found. Ensure MongoDB is running on the specified host/port.", "MONGODB_CONNECTION", e)
    except pymongo.errors.OperationFailure as e:
        log_error(f"MongoDB operation failed: {e}", "MONGODB_OPERATION", e)
    except Exception as e:
        log_error(f"An unexpected error occurred while saving metrics to DB: {e}", "DATA_SAVING", e)
    finally:
        if client:
            DatabaseManager().close_connection()

def collect_all_tickers_performance_metrics():
    """
    Fetches all tickers from the database and collects their 1-week, 1-month,
    and 3-month performance metrics.
    """
    load_dotenv() # Ensure environment variables are loaded for DB connection
    tickers = get_tickers_from_db()
    if tickers:
        log_info(f"Starting performance metrics collection for {len(tickers)} tickers.")
        
        all_metrics = []
        metrics_batch = []
        batch_size = 100
        
        with ProcessPoolExecutor() as executor:
            for i, result in enumerate(executor.map(_get_performance_metrics, tickers)):
                if result:
                    all_metrics.append(result)
                    metrics_batch.append(result)

                if (i + 1) % batch_size == 0:
                    log_info(f"Saving batch of {len(metrics_batch)} performance metrics to database.")
                    save_performance_metrics_to_db(metrics_batch)
                    metrics_batch = [] # Reset batch

            # Save any remaining metrics in the last batch
            if metrics_batch:
                log_info(f"Saving final batch of {len(metrics_batch)} performance metrics to database.")
                save_performance_metrics_to_db(metrics_batch)

        log_info("Finished collecting and saving performance metrics for all tickers.")
    else:
        log_warning("No tickers found in the database to collect performance metrics.", "PERFORMANCE_COLLECTION")


if __name__ == '__main__':
        collect_all_tickers_performance_metrics()
