import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import Optional
from datetime import datetime, timedelta
import yfinance as yf
import time
from concurrent.futures import ProcessPoolExecutor
import pandas as pd

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


def _calculate_performance(df: pd.DataFrame, days: int) -> Optional[float]:
    """
    Calculates percentage performance from a historical DataFrame.
    """
    if df.empty or len(df) < 2:
        return None
    
    # Target date is ~days ago
    target_date = df.index[-1] - pd.Timedelta(days=days)
    
    # Find the closest date in the index that is <= target_date
    idx = df.index.asof(target_date)
    
    if pd.isna(idx):
        # If target_date is before the first date in df, it means we don't have enough history
        return None

    initial_price = df.loc[idx, "Close"]
    final_price = df.iloc[-1]["Close"]

    if initial_price == 0 or pd.isna(initial_price) or pd.isna(final_price):
        return None

    return (final_price - initial_price) / initial_price


def _get_performance_metrics(ticker_symbol: str) -> Optional[dict]:
    """
    Extracts performance and (if applicable) dividend metrics
    using a single yf.Ticker instance and single history call.
    """
    time.sleep(1)
    
    def _safe_float(value):
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    dividend_yield = None
    payout_ratio = None
    eps_growth = None
    market_cap = None
    one_week = None
    one_month = None
    three_month = None

    try:
        yf_ticker = yf.Ticker(ticker_symbol)
        
        # 1. Fetch History once (3 months)
        history = yf_ticker.history(period="3mo")
        if not history.empty:
            one_week = _calculate_performance(history, 7)
            one_month = _calculate_performance(history, 30)
            three_month = _calculate_performance(history, 90)

        # 2. Fetch Info
        summary_details = yf_ticker.info
        if not summary_details:
            log_warning(f"No info data found for {ticker_symbol}.", "DATA_MISSING")
            return None

        quote_type = summary_details.get("quoteType")

        market_cap = _safe_float(summary_details.get("marketCap"))
        if market_cap is not None:
            log_info(f"{ticker_symbol} market cap: {market_cap:,.2f}")
        else:
            log_warning(f"{ticker_symbol} market cap missing", "DATA_MISSING")

        # Only equities logically support payout ratios and EPS growth
        if quote_type == "EQUITY":
            if isinstance(summary_details, dict):
                dividend_yield = _safe_float(summary_details.get("dividendYield"))
                if dividend_yield is not None:
                    dividend_yield /= 100.0

                payout_ratio = _safe_float(summary_details.get("payoutRatio"))
                if payout_ratio is not None:
                    payout_ratio /= 100.0

                eps_growth = _safe_float(summary_details.get("earningsGrowth"))
                if eps_growth is not None and eps_growth > 1:
                    eps_growth /= 100.0

                if dividend_yield is not None:
                    log_info(f"{ticker_symbol} dividend yield: {dividend_yield:.4f}")
                if payout_ratio is not None:
                    log_info(f"{ticker_symbol} payout ratio: {payout_ratio:.4f}")
                if eps_growth is not None:
                    log_info(f"{ticker_symbol} EPS growth: {eps_growth:.4f}")

    except Exception as e:
        log_error(
            f"Metric extraction failed for {ticker_symbol}: {e}",
            "DATA_COLLECTION_ERROR",
            e
        )

    # --- Logging for performance ---
    if one_week is not None:
        log_info(f"{ticker_symbol} 1-week: {one_week:.2%}")
    if one_month is not None:
        log_info(f"{ticker_symbol} 1-month: {one_month:.2%}")
    if three_month is not None:
        log_info(f"{ticker_symbol} 3-month: {three_month:.2%}\n")

    return {
        "ticker_symbol": ticker_symbol,
        "1w": one_week,
        "1m": one_month,
        "3m": three_month,
        "dividend_yield": dividend_yield,
        "payout_ratio": payout_ratio,
        "eps_growth": eps_growth,
        "market_cap": market_cap,
    }


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
            # Create a new dictionary excluding None values
            filtered_metric_data = {k: v for k, v in metric_data.items() if v is not None}

            if not filtered_metric_data: # If all metrics are None, no update is needed for metrics fields
                log_warning(f"No valid performance metrics to update for {ticker}.", "DB_UPDATE_WARNING")
                continue

            update_result = collection.update_one(
                {"ticker": ticker},
                {"$set": filtered_metric_data} # Use the filtered data for update
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
    Fetches all tickers from the database and collects their performance metrics
    using parallel processing and batch saving.
    """
    load_dotenv()
    tickers = get_tickers_from_db()
    if not tickers:
        log_warning("No tickers found in the database to collect performance metrics.", "PERFORMANCE_COLLECTION")
        return

    log_info(f"Starting performance metrics collection for {len(tickers)} tickers.")
    
    batch_size = 100
    
    with ProcessPoolExecutor() as executor:
        # Correct use of executor.map
        results = list(executor.map(_get_performance_metrics, tickers))
        
        # Filter out None results
        valid_results = [r for r in results if r is not None]
        
        # Save in batches of 100
        for i in range(0, len(valid_results), batch_size):
            batch = valid_results[i : i + batch_size]
            log_info(f"Saving batch of {len(batch)} performance metrics to database.")
            save_performance_metrics_to_db(batch)

    log_info("Finished collecting and saving performance metrics for all tickers.")


if __name__ == '__main__':
    collect_all_tickers_performance_metrics()
