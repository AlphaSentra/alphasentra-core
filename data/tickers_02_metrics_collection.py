"""
This script is responsible for collecting and updating comprehensive ticker data in the MongoDB database.
To initiate the data collection and update process, execute the `update_ticker_data_in_db()` function.
This function orchestrates the retrieval of tickers, fetches various financial and market data points,
and persists the updated information into the database.
"""

import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
import pymongo
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional
import numpy as np
import time

from helpers import DatabaseManager
from logging_utils import log_error, log_warning, log_info
from data.treasury_yield_utils import get_tlt_dividend_yield

def get_equity_tickers_from_db(region: Optional[list] = None, category: Optional[list] = None) -> list:
    """
    Retrieves a list of equity ticker symbols from the 'tickers' collection in the MongoDB database.

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
        query = {"asset_class": "EQ"}
        if region:
            query["region"] = {"$in": region}
        log_info(f"Querying for equity tickers with conditions: {query}")
        
        sort_fields = {}
        if category and "growth" in category:
            query["eps_growth"] = {"$gt": 0}
            sort_fields = {"3m": pymongo.DESCENDING, "1m": pymongo.DESCENDING, "1w": pymongo.DESCENDING, "eps_growth": pymongo.DESCENDING}
        elif category and "income" in category:
            query["payout_ratio"] = {"$lt": 1}
            tlt_yield = get_tlt_dividend_yield() # yfinance returns dividend yield as a decimal (e.g., 0.04 for 4%)
            if tlt_yield > 0:
                query["dividend_yield"] = {"$gt": tlt_yield}
            else:
                log_warning("TLT dividend yield could not be fetched or was 0. Skipping dividend yield filter.")
            sort_fields = {"3m": pymongo.DESCENDING, "1m": pymongo.DESCENDING, "1w": pymongo.DESCENDING, "dividend_yield": pymongo.DESCENDING}

        if sort_fields:
            cursor = collection.find(query, {"ticker": 1, "_id": 0}).sort(list(sort_fields.items())).limit(50)
        else:
            cursor = collection.find(query, {"ticker": 1, "_id": 0}).limit(50)

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

def get_crypto_tickers_from_db(region: Optional[list] = None, category: Optional[list] = None) -> list:
    """
    Retrieves a list of crypto ticker symbols from the 'tickers' collection in the MongoDB database.
    Filters for tickers where 'asset_class' is 'CR'.

    Returns:
        list: A list of crypto ticker symbols (strings). Returns an empty list if no tickers
              are found or an error occurs.
    """
    load_dotenv()
    tickers_list = []
    client = None
    category = category or []
    region = region or []
        
    try:
        # Get MongoDB connection
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        collection = db["tickers"]

        # Query to get all documents and extract the 'ticker' field, filtering for asset_class = CR
        cursor = collection.find({"asset_class": "CR"}, {"ticker": 1, "_id": 0}).sort([("3m", pymongo.DESCENDING), ("1m", pymongo.DESCENDING), ("1w", pymongo.DESCENDING), ("market_cap", pymongo.DESCENDING)]).limit(50)

        for doc in cursor:
            if 'ticker' in doc:
                tickers_list.append(doc['ticker'])
        
        log_info(f"Successfully retrieved {len(tickers_list)} crypto tickers from the database.")

    except pymongo.errors.ServerSelectionTimeoutError as e:
        log_error("MongoDB server not found. Ensure MongoDB is running on the specified host/port.", "MONGODB_CONNECTION", e)
    except pymongo.errors.OperationFailure as e:
        log_error(f"MongoDB operation failed: {e}", "MONGODB_OPERATION", e)
    except Exception as e:
        log_error(f"An unexpected error occurred while fetching crypto tickers from DB: {e}", "DATA_FETCHING", e)
    finally:
        if client:
            DatabaseManager().close_connection() # Using the singleton instance to close connection
    return tickers_list

def get_fx_tickers_from_db(region: Optional[list] = None, category: Optional[list] = None) -> list:
    """
    Retrieves a list of FX ticker symbols from the 'tickers' collection in the MongoDB database.
    Filters for tickers where 'asset_class' is 'FX'.

    Returns:
        list: A list of FX ticker symbols (strings). Returns an empty list if no tickers
              are found or an error occurs.
    """
    load_dotenv()
    tickers_list = []
    client = None
    region = region or []
    category = category or []
    
    try:
        # Get MongoDB connection
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        collection = db["tickers"]

        # Query to get all documents and extract the 'ticker' field, filtering for asset_class = FX
        cursor = collection.find({"asset_class": "FX"}, {"ticker": 1, "_id": 0})

        for doc in cursor:
            if 'ticker' in doc:
                tickers_list.append(doc["ticker"])
        
        log_info(f"Successfully retrieved {len(tickers_list)} FX tickers from the database.")

    except pymongo.errors.ServerSelectionTimeoutError as e:
        log_error("MongoDB server not found. Ensure MongoDB is running on the specified host/port.", "MONGODB_CONNECTION", e)
    except pymongo.errors.OperationFailure as e:
        log_error(f"MongoDB operation failed: {e}", "MONGODB_OPERATION", e)
    except Exception as e:
        log_error(f"An unexpected error occurred while fetching FX tickers from DB: {e}", "DATA_FETCHING", e)
    finally:
        if client:
            DatabaseManager().close_connection() # Using the singleton instance to close connection
    return tickers_list

def collect_ticker_data(tickers: list) -> dict:
    """
    Collects various data points for a list of tickers using yfinance,
    including market capitalization, forward P/E ratio, and EPS growth.

    Args:
        tickers (list): A list of ticker symbols (e.g., ['AAPL', 'MSFT']).

    Returns:
        dict: A dictionary where keys are ticker symbols and values are dictionaries
              containing collected data (e.g., {'market_cap': 12345, 'forward_pe': 25.5, 'eps_growth': 0.15}).
              Returns None for a data point if not available for a ticker.
    """
    if not tickers:
        log_warning(
            "No tickers provided for data collection. Skipping market cap, forward P/E ratio, and EPS growth collection."
        )
        return {}

    ticker_data = {}

    for ticker_symbol in tickers:
        try:
            log_info(f"Collecting data for ticker: {ticker_symbol}")
            time.sleep(1)
            ticker_obj = yf.Ticker(ticker_symbol)
            
            # Fetch history and info once
            history_df = ticker_obj.history(period="3mo")
            info = ticker_obj.info

            forward_pe = None
            dilution_proxy = None
            average_daily_range_pips = None
            momentum_spread = None
            absolute_momentum_spread = None
            average_daily_volume = None
            thirty_day_volume_change = None
            sector = None

            if info:
                forward_pe = info.get('forwardPE')
                sector = info.get('sector')
                
                if sector is not None:
                    log_info(f"Collected sector for {ticker_symbol}: {sector}")
                else:
                    log_warning(f"Sector not found for {ticker_symbol}.", "DATA_MISSING")
                
                # Collect circulatingSupply and maxSupply for dilution_proxy calculation
                circulating_supply = info.get('circulatingSupply')
                max_supply = info.get('maxSupply')

                if circulating_supply is not None and max_supply is not None and max_supply > 0:
                    dilution_proxy = circulating_supply / max_supply
                    log_info(f"Collected dilution proxy for {ticker_symbol}: {dilution_proxy}")
                else:
                    log_warning(f"Circulating supply or max supply not found or max supply is zero for {ticker_symbol}. Cannot calculate dilution proxy.", "DATA_PROCESSING")

                if forward_pe is not None:
                    log_info(f"Collected forward P/E for {ticker_symbol}: {forward_pe}")
                else:
                    log_warning(f"Forward P/E not found for {ticker_symbol}.", "DATA_MISSING")
            else:
                log_warning(f"No info data found for {ticker_symbol}.")
            
            # Collect 30-day average daily range in pips for FX pairs
            if ticker_symbol.endswith('=X'): # Assuming FX pairs end with '=X'
                average_daily_range_pips = _calculate_30d_average_daily_range_in_pips(ticker_symbol, history_df)
                if average_daily_range_pips is not None:
                    log_info(f"Collected 30-day average daily range for {ticker_symbol}: {average_daily_range_pips} pips.")
                else:
                    log_warning(f"Could not collect 30-day average daily range for FX pair {ticker_symbol}.", "DATA_MISSING")

            # Collect momentum spread
            momentum_spread = _calculate_momentum_spread(ticker_symbol, history_df)
            if momentum_spread is not None:
                log_info(f"Collected momentum spread for {ticker_symbol}: {momentum_spread:.2f}.")
                absolute_momentum_spread = abs(momentum_spread) # Calculate absolute momentum spread
                log_info(f"Calculated absolute momentum spread for {ticker_symbol}: {absolute_momentum_spread:.2f}.")
            else:
                log_warning(f"Could not collect momentum spread for {ticker_symbol}.", "DATA_MISSING")

            # Collect average daily volume
            average_daily_volume = _calculate_average_daily_volume(ticker_symbol, history_df)
            if average_daily_volume is not None:
                log_info(f"Collected average daily volume for {ticker_symbol}: {average_daily_volume:.2f}.")
            else:
                log_warning(f"Could not collect average daily volume for {ticker_symbol}.", "DATA_MISSING")

            # Collect 30-day volume change
            thirty_day_volume_change = _calculate_30d_volume_change(ticker_symbol, history_df)
            if thirty_day_volume_change is not None:
                log_info(f"Collected 30-day volume change for {ticker_symbol}: {thirty_day_volume_change:.4f}")
            else:
                log_warning(f"Could not collect 30-day volume change for {ticker_symbol}.", "DATA_MISSING")

            ticker_data[ticker_symbol] = {
                'forward_pe': forward_pe,
                'dilution_proxy': dilution_proxy,
                '30d_average_daily_range_pips': average_daily_range_pips,
                'momentum_spread': momentum_spread,
                'absolute_momentum_spread': absolute_momentum_spread,
                'average_daily_volume': average_daily_volume,
                '30d_volume_change': thirty_day_volume_change,
                'sector': sector
            }

        except Exception as e:
            log_error(f"An error occurred while fetching data for ticker {ticker_symbol}: {e}", "DATA_COLLECTION_ERROR", e)
            ticker_data[ticker_symbol] = {
                'forward_pe': None, 
                'dilution_proxy': None, 
                '30d_average_daily_range_pips': None, 
                'momentum_spread': None, 
                'absolute_momentum_spread': None,
                'average_daily_volume': None, 
                '30d_volume_change': None,
                'sector': None
            }

    return ticker_data

def _calculate_30d_average_daily_range_in_pips(ticker_symbol: str, history_df: pd.DataFrame) -> Optional[float]:
    """
    Calculates the 30-day average daily range in pips for a given FX ticker using pre-fetched historical data.
    Handles JPY pairs differently for pip calculation.

    Args:
        ticker_symbol (str): The FX ticker symbol (e.g., 'EURUSD=X', 'USDJPY=X').
        history_df (pd.DataFrame): Pre-fetched historical data.

    Returns:
        float: The 30-day average daily range in pips, or None if data is unavailable or an error occurs.
    """
    try:
        if history_df.empty:
            log_warning(f"No historical data available for {ticker_symbol} to calculate 30-day average daily range", "AVG_DAILY_RANGE_CALCULATION")
            return None

        # Ensure we have at least 30 days of data
        if len(history_df) < 30:
            log_warning(f"Less than 30 days of historical data for {ticker_symbol}. Cannot accurately calculate 30-day average daily range.", "AVG_DAILY_RANGE_CALCULATION")
            return None

        # Get the last 30 trading days
        ticker_data = history_df.tail(30)

        daily_ranges_in_pips = []
        is_jpy_pair = "JPY" in ticker_symbol.upper()

        for index, row in ticker_data.iterrows():
            high = row["High"]
            low = row["Low"]
            daily_range = high - low

            # Convert to pips
            if is_jpy_pair:
                # For JPY pairs, 1 pip is 0.01
                daily_range_pips = daily_range * 100
            else:
                # For most other pairs, 1 pip is 0.0001
                daily_range_pips = daily_range * 10000
            
            daily_ranges_in_pips.append(daily_range_pips)

        if not daily_ranges_in_pips:
            return None

        average_daily_range_pips = sum(daily_ranges_in_pips) / len(daily_ranges_in_pips)
        log_info(f"Calculated 30-day average daily range for {ticker_symbol}: {average_daily_range_pips:.2f} pips.")
        return round(average_daily_range_pips, 2)

    except Exception as e:
        log_error(f"Error calculating 30-day average daily range for {ticker_symbol}: {e}", "AVG_DAILY_RANGE_CALCULATION", e)
        return None


def _calculate_momentum_spread(ticker_symbol: str, history_df: pd.DataFrame) -> Optional[float]:
    """
    Calculates the momentum spread for a given ticker using pre-fetched historical data.

    Args:
        ticker_symbol (str): The ticker symbol (e.g., 'AAPL').
        history_df (pd.DataFrame): Pre-fetched historical data.

    Returns:
        float: The momentum spread, or None if data is unavailable or an error occurs.
    """
    try:
        lookback_momentum = 20  # Approximately 1 month of trading days
        lookback_range = 20     # For average daily range calculation

        if history_df.empty:
            log_warning(f"No historical data available for {ticker_symbol} to calculate momentum spread.", "MOMENTUM_SPREAD_CALCULATION")
            return None

        if len(history_df) < max(lookback_momentum, lookback_range):
            log_warning(f"Not enough historical data for {ticker_symbol} to calculate momentum spread.", "MOMENTUM_SPREAD_CALCULATION")
            return None

        ticker_data = history_df

        close = ticker_data["Close"]
        high = ticker_data["High"]
        low = ticker_data["Low"]

        # 1M Momentum (%)
        momentum = close.pct_change(lookback_momentum).iloc[-1] * 100

        # Average daily range as % of price (spread proxy)
        range_pct = ((high - low) / close).rolling(lookback_range).mean().iloc[-1] * 100

        # Avoid divide-by-zero
        if range_pct == 0:
            range_pct = np.nan # Use numpy.nan for consistency

        # Momentum per unit of friction
        if pd.isna(momentum) or pd.isna(range_pct):
            momentum_spread = None
        else:
            momentum_spread = momentum / range_pct

        log_info(f"Calculated momentum spread for {ticker_symbol}: {momentum_spread:.2f}")
        return momentum_spread

    except Exception as e:
        log_error(f"Error calculating momentum spread for {ticker_symbol}: {e}", "MOMENTUM_SPREAD_CALCULATION", e)
        return None


def _calculate_average_daily_volume(ticker_symbol: str, history_df: pd.DataFrame, lookback_days: int = 30) -> Optional[float]:
    """
    Calculates the average daily volume for a given ticker over a specified lookback period using pre-fetched historical data.

    Args:
        ticker_symbol (str): The ticker symbol (e.g., 'AAPL').
        history_df (pd.DataFrame): Pre-fetched historical data.
        lookback_days (int): The number of days to look back for calculating the average volume.

    Returns:
        float: The average daily volume, or None if data is unavailable or an error occurs.
    """
    try:
        if history_df.empty:
            log_warning(f"No historical data available for {ticker_symbol} to calculate average daily volume.", "AVG_DAILY_VOLUME_CALCULATION")
            return None

        if len(history_df) < lookback_days:
            log_warning(f"Less than {lookback_days} days of historical data for {ticker_symbol}. Cannot accurately calculate average daily volume.", "AVG_DAILY_VOLUME_CALCULATION")
            return None

        ticker_data = history_df

        # Get the volume for the specified lookback days
        recent_volume = ticker_data['Volume'].tail(lookback_days)

        average_volume = recent_volume.mean()

        log_info(f"Calculated {lookback_days}-day average daily volume for {ticker_symbol}: {average_volume:.2f}")
        return round(average_volume, 2)

    except Exception as e:
        log_error(f"Error calculating average daily volume for {ticker_symbol}: {e}", "AVG_DAILY_VOLUME_CALCULATION", e)
        return None


def _calculate_30d_volume_change(ticker_symbol: str, history_df: pd.DataFrame) -> Optional[float]:
    """
    Calculates the 30-day volume change for a given ticker using pre-fetched historical data.
    This is the percentage change of the last 30-day average volume compared to the previous 30-day average volume.

    Args:
        ticker_symbol (str): The ticker symbol (e.g., 'AAPL').
        history_df (pd.DataFrame): Pre-fetched historical data.

    Returns:
        float: The 30-day volume change percentage, or None if data is unavailable or an error occurs.
    """
    try:
        lookback_days = 30

        if history_df.empty:
            log_warning(f"No historical data available for {ticker_symbol} to calculate 30-day volume change.", "30D_VOLUME_CHANGE_CALCULATION")
            return None

        if len(history_df) < lookback_days * 2:
            log_warning(f"Less than {lookback_days * 2} days of historical data for {ticker_symbol}. Cannot accurately calculate 30-day volume change.", "30D_VOLUME_CHANGE_CALCULATION")
            return None

        ticker_data = history_df

        # Get the volume for the last two 30-day periods
        recent_60_days_volume = ticker_data['Volume'].tail(lookback_days * 2)

        current_30d_avg_volume = recent_60_days_volume.iloc[-lookback_days:].mean()
        previous_30d_avg_volume = recent_60_days_volume.iloc[:-lookback_days].mean()

        if previous_30d_avg_volume == 0:
            log_warning(f"Previous 30-day average volume is zero for {ticker_symbol}. Cannot calculate 30-day volume change.", "30D_VOLUME_CHANGE_CALCULATION")
            return None
        
        thirty_day_volume_change = (current_30d_avg_volume - previous_30d_avg_volume) / previous_30d_avg_volume

        log_info(f"Calculated 30-day volume change for {ticker_symbol}: {thirty_day_volume_change:.4f}")
        return round(thirty_day_volume_change, 4)

    except Exception as e:
        log_error(f"Error calculating 30-day volume change for {ticker_symbol}: {e}", "30D_VOLUME_CHANGE_CALCULATION", e)
        return None




def update_ticker_data_in_db(ticker_source_function, region: Optional[list] = None, category: Optional[list] = None):
    """
    Orchestrates the complete process of fetching all active ticker symbols from the MongoDB database,
    collecting a comprehensive suite of financial and market data points for each ticker,
    and subsequently updating these data points in the database.

    The collected data includes:
    - Forward Price-to-Earnings ratio (`forward_pe`)
    - Earnings Per Share growth (`eps_growth`)
    - Dilution proxy (`dilution_proxy`), calculated from circulating and max supply for cryptocurrencies.
    - 30-day average daily range in pips (`30d_average_daily_range_pips`) for FX pairs.
    - Momentum spread (`momentum_spread`), indicating momentum per unit of price friction.
    - Average daily volume (`average_daily_volume`)
    - 30-day volume change (`30d_volume_change`), reflecting recent volume trends.
    - 1-week percentage performance (`1w`).
    - 1-month percentage performance (`1m`).
    - 3-month percentage performance (`3m`).
    - Sector (`sector`).

    This function ensures that the ticker data in the database is current and comprehensive,
    handling potential errors during data collection and database operations with robust logging.
    """
    load_dotenv()
    log_info("Starting ticker data update process...")

    tickers_from_db = ticker_source_function(region=region, category=category)

    if not tickers_from_db:
        log_warning("No tickers found in the database to update data.")
        return

    log_info(f"Total {len(tickers_from_db)} tickers to process in batches.")
    
    batch_size = 50
    total_updated_count = 0
    client = None
    try:
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        collection = db["tickers"]

        for i in range(0, len(tickers_from_db), batch_size):
            ticker_batch = tickers_from_db[i:i + batch_size]
            log_info(f"Processing batch {int(i/batch_size) + 1}/{(len(tickers_from_db) + batch_size - 1) // batch_size} with {len(ticker_batch)} tickers.")
            
            batch_data = collect_ticker_data(ticker_batch)
            
            if not batch_data:
                log_warning(f"No ticker data collected for batch starting with {ticker_batch[0] if ticker_batch else 'N/A'}. Skipping update for this batch.")
            else:
                batch_updated_count = 0
                for ticker_symbol, data in batch_data.items():
                    update_fields = {}
                    if data["forward_pe"] is not None:
                        update_fields["forward_pe"] = data["forward_pe"]
                    if data["dilution_proxy"] is not None:
                        update_fields["dilution_proxy"] = data["dilution_proxy"]
                    if data["30d_average_daily_range_pips"] is not None:
                        update_fields["30d_average_daily_range_pips"] = data["30d_average_daily_range_pips"]
                    if data["momentum_spread"] is not None:
                        update_fields["momentum_spread"] = data["momentum_spread"]
                    if data["absolute_momentum_spread"] is not None:
                        update_fields["absolute_momentum_spread"] = data["absolute_momentum_spread"]
                    if data["average_daily_volume"] is not None:
                        update_fields["average_daily_volume"] = data["average_daily_volume"]
                    if data["30d_volume_change"] is not None:
                        update_fields["30d_volume_change"] = data["30d_volume_change"]
                    if "sector" in data and data["sector"] is not None:
                        update_fields["sector"] = data["sector"]

                    if update_fields:
                        result = collection.update_one(
                            {"ticker": ticker_symbol},
                            {"$set": update_fields}
                        )
                        if result.modified_count > 0:
                            log_info(f"Updated data for {ticker_symbol} in current batch: {update_fields}.")
                            batch_updated_count += 1
                        elif result.upserted_id is not None:
                            log_warning(f"Inserted data for new ticker {ticker_symbol} in current batch: {update_fields}.")
                            batch_updated_count += 1
                        else:
                            log_info(f"Data for {ticker_symbol} already up-to-date or no change in current batch.")
                    else:
                        log_warning(f"No valid data to update for {ticker_symbol} in current batch. Skipping.")
                
                total_updated_count += batch_updated_count
                log_info(f"Finished updating data for batch. {batch_updated_count} tickers updated/inserted in this batch.")

            if (i + batch_size) < len(tickers_from_db):
                log_info("Pausing for 15 seconds before next batch...")
                time.sleep(15) # Pause for 15 seconds between batches
        
        log_info(f"Finished updating all ticker data. Total {total_updated_count} tickers updated/inserted across all batches.")

    except pymongo.errors.ServerSelectionTimeoutError as e:
        log_error("MongoDB server not found. Ensure MongoDB is running on the specified host/port.", "MONGODB_CONNECTION", e)
    except pymongo.errors.OperationFailure as e:
        log_error(f"MongoDB operation failed during ticker data update: {e}", "MONGODB_OPERATION", e)
    except Exception as e:
        log_error(f"An unexpected error occurred during ticker data update: {e}", "DATA_UPDATE_ERROR", e)
    finally:
        if client:
            DatabaseManager().close_connection()


if __name__ == '__main__':
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["US"], category=["growth"])
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["AU"], category=["growth"])
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["US"], category=["income"])
    update_ticker_data_in_db(get_equity_tickers_from_db, region=["AU"], category=["income"])
    update_ticker_data_in_db(get_crypto_tickers_from_db, region=None, category=["crypto"])
    update_ticker_data_in_db(get_fx_tickers_from_db, region=None, category=["forex"])
